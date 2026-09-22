"""Standard classical image processing filter implementations."""

import numpy as np

try:
    import cv2
except ImportError:
    cv2 = None


def apply_mean_filter(image: np.ndarray, kernel_size: int = 3) -> np.ndarray:
    """Apply spatial box mean filter."""
    assert cv2 is not None, "OpenCV is required. Install opencv-python-headless."
    return cv2.blur(image, (kernel_size, kernel_size))


def apply_median_filter(image: np.ndarray, kernel_size: int = 3) -> np.ndarray:
    """Apply median filter optimal for impulse noise."""
    assert cv2 is not None, "OpenCV is required. Install opencv-python-headless."
    if image.dtype != np.uint8:
        image_uint8 = np.clip(image * 255.0, 0, 255).astype(np.uint8)
        filtered = cv2.medianBlur(image_uint8, kernel_size)
        return filtered.astype(np.float64) / 255.0
    return cv2.medianBlur(image, kernel_size)


def apply_gaussian_filter(
    image: np.ndarray, kernel_size: int = 3, sigma: float = 1.0
) -> np.ndarray:
    """Apply Gaussian smoothing filter."""
    assert cv2 is not None, "OpenCV is required. Install opencv-python-headless."
    return cv2.GaussianBlur(image, (kernel_size, kernel_size), sigmaX=sigma)


def apply_bilateral_filter(
    image: np.ndarray, d: int = 5, sigma_color: float = 50.0, sigma_space: float = 50.0
) -> np.ndarray:
    """Apply edge-preserving bilateral filter."""
    assert cv2 is not None, "OpenCV is required. Install opencv-python-headless."
    if image.dtype != np.uint8:
        image_uint8 = np.clip(image * 255.0, 0, 255).astype(np.uint8)
        filtered = cv2.bilateralFilter(image_uint8, d, sigma_color, sigma_space)
        return filtered.astype(np.float64) / 255.0
    return cv2.bilateralFilter(image, d, sigma_color, sigma_space)
