"""Quantum Image Encoding Module.

Implements Flexible Representation of Quantum Images (FRQI) and
Novel Enhanced Quantum Representation (NEQR) state preparation and decoding.
"""

from .frqi import FRQIEncoder
from .neqr import NEQREncoder

__all__ = ["FRQIEncoder", "NEQREncoder"]
