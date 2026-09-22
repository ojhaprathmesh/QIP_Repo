"""Unit tests for image metric computations."""

import numpy as np
import pytest

pytest.importorskip("skimage")
from src.metrics.image_metrics import compute_mse, compute_psnr, compute_ssim


def test_perfect_reconstruction_metrics():
    """Identical images should yield MSE=0, PSNR=inf, SSIM=1.0."""
    img = np.ones((8, 8), dtype=np.float64) * 0.5
    assert compute_mse(img, img) == 0.0
    assert compute_psnr(img, img) == float("inf")
    assert np.isclose(compute_ssim(img, img), 1.0)


def test_perturbed_metrics():
    """Perturbed images should yield finite positive MSE and PSNR < inf."""
    img1 = np.ones((8, 8), dtype=np.float64) * 0.5
    img2 = img1.copy()
    img2[0, 0] = 1.0

    mse = compute_mse(img1, img2)
    assert mse > 0.0
    psnr = compute_psnr(img1, img2)
    assert 0.0 < psnr < float("inf")
