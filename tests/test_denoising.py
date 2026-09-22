"""Unit tests for classical and quantum denoising filters."""

import pytest
import numpy as np

cv2 = pytest.importorskip("cv2")
from src.classical_denoising.standard_filters import (
    apply_mean_filter,
    apply_median_filter,
    apply_gaussian_filter,
)


def test_classical_filters_execution():
    """Verify that classical mean, median, and gaussian filters run on synthetic array."""
    test_img = np.random.rand(8, 8).astype(np.float32)

    mean_res = apply_mean_filter(test_img, kernel_size=3)
    assert mean_res.shape == (8, 8)

    med_res = apply_median_filter(test_img, kernel_size=3)
    assert med_res.shape == (8, 8)

    gauss_res = apply_gaussian_filter(test_img, kernel_size=3)
    assert gauss_res.shape == (8, 8)
