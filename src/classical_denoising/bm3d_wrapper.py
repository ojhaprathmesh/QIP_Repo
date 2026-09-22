"""BM3D (Block-Matching and 3D filtering) classical baseline wrapper."""

import numpy as np


def apply_bm3d_filter(image: np.ndarray, sigma_psd: float = 0.1) -> np.ndarray:
    """Apply BM3D state-of-the-art collaborative filtering.

    Args:
        image: 2D normalized float array [0, 1].
        sigma_psd: Standard deviation of noise power spectral density.

    Returns:
        np.ndarray: Denoised image.
    """
    try:
        import bm3d

        result = bm3d.bm3d(image, sigma_psd=sigma_psd)
        if isinstance(result, tuple):
            return np.asarray(result[0])
        return np.asarray(result)
    except ImportError:
        # Fallback if BM3D is not yet installed in local environment
        raise ImportError(
            "BM3D package is required for BM3D baseline filtering. Run `pip install bm3d`."
        )
