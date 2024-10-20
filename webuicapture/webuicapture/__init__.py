"""Web UI Capture package."""

from .data import CaptureData, BBoxNode, ImageType
from . import serve

__all__ = ["CaptureData", "BBoxNode", "ImageType", "serve"]
