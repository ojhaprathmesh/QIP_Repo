"""Image Quality Metrics: PSNR, SSIM, and MSE."""

from typing import Dict, Optional
import math
import numpy as np


def compute_mse(clean: np.ndarray, noisy: np.ndarray) -> float:
    """Compute Mean Squared Error (MSE) between clean and reconstructed images."""
    return float(np.mean((clean.astype(np.float64) - noisy.astype(np.float64)) ** 2))


def compute_psnr(
    clean: np.ndarray, noisy: np.ndarray, data_range: float = 1.0
) -> float:
    """Compute Peak Signal-to-Noise Ratio (PSNR) in decibels (dB).

    Args:
        clean: Ground truth reference image.
        noisy: Evaluated image.
        data_range: Dynamic range of pixel values (1.0 for normalized, 255.0 for uint8).

    Returns:
        float: PSNR in dB. Returns infinity if images are identical.
    """
    mse = compute_mse(clean, noisy)
    if mse == 0.0:
        return float("inf")
    return float(10.0 * math.log10((data_range**2) / mse))


def compute_ssim(
    clean: np.ndarray,
    noisy: np.ndarray,
    data_range: float = 1.0,
    win_size: Optional[int] = None,
) -> float:
    """Compute Structural Similarity Index Measure (SSIM).

    Args:
        clean: Ground truth reference image.
        noisy: Evaluated image.
        data_range: Dynamic range of pixel values.
        win_size: Filter window size (auto-adjusted for small images).

    Returns:
        float: SSIM score between -1.0 and 1.0.
    """
    min_side = min(clean.shape[0], clean.shape[1])
    if min_side < 3:
        mse = compute_mse(clean, noisy)
        return 1.0 if mse == 0.0 else float(max(-1.0, 1.0 - 2.0 * mse))

    if win_size is None:
        if min_side >= 7:
            win_size = 7
        else:
            win_size = min_side if (min_side % 2 != 0) else (min_side - 1)

    try:
        from skimage.metrics import structural_similarity

        return float(
            structural_similarity(clean, noisy, data_range=data_range, win_size=win_size)
        )
    except ImportError:
        raise ImportError(
            "scikit-image is required for SSIM calculation. Install with `pip install scikit-image`."
        )


def compute_all_image_metrics(
    clean: np.ndarray, evaluated: np.ndarray, data_range: float = 1.0
) -> Dict[str, float]:
    """Compute all standard image reconstruction quality metrics."""
    return {
        "mse": compute_mse(clean, evaluated),
        "psnr": compute_psnr(clean, evaluated, data_range=data_range),
        "ssim": compute_ssim(clean, evaluated, data_range=data_range),
    }
