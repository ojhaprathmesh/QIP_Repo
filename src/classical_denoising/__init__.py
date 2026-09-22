"""Classical Baseline Filtering Suite.

Provides implementations and wrappers for Classical Mean, Median,
Gaussian, Bilateral, and BM3D state-of-the-art filters.
"""

from .standard_filters import (
    apply_mean_filter,
    apply_median_filter,
    apply_gaussian_filter,
    apply_bilateral_filter,
)
from .bm3d_wrapper import apply_bm3d_filter

__all__ = [
    "apply_mean_filter",
    "apply_median_filter",
    "apply_gaussian_filter",
    "apply_bilateral_filter",
    "apply_bm3d_filter",
]
