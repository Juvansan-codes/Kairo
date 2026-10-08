"""
MGR geometry solver – Phase 2: morphological cleanup & skeletonization.

Pipeline implemented in this phase:

    wall mask  →  morphological cleanup  →  skeletonization  →  clean skeleton

Later phases will add wall-graph generation, room polygonization, etc.
"""

from __future__ import annotations

import numpy as np
from skimage.morphology import (
    skeletonize,
    closing,
    opening,
    disk,
    remove_small_objects,
)


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _validate_mask(mask: np.ndarray) -> None:
    """Raise *ValueError* if *mask* is not a usable 2-D array."""
    if not isinstance(mask, np.ndarray):
        raise TypeError(
            f"mask must be a numpy ndarray, got {type(mask).__name__}"
        )
    if mask.ndim != 2:
        raise ValueError(
            f"mask must be 2-D, got {mask.ndim}-D array with shape {mask.shape}"
        )
    if mask.size == 0:
        raise ValueError("mask is empty (zero elements)")


def _normalize_mask(mask: np.ndarray) -> np.ndarray:
    """Convert an arbitrary binary-ish mask to a strict ``bool`` array.

    Accepted encodings:

    * ``bool`` arrays  – used as-is.
    * ``0 / 1`` integer or float arrays.
    * ``0 / 255`` image-style arrays.

    Any value > 0 is treated as *True* (wall).
    """
    if mask.dtype == bool:
        return mask.copy()
    return mask.astype(bool)


def _cleanup_wall_mask(
    mask: np.ndarray,
    *,
    min_object_size: int = 64,
    close_radius: int = 3,
    open_radius: int = 1,
) -> np.ndarray:
    """Apply morphological cleanup to a **boolean** wall mask.

    Steps
    -----
    1. Remove small isolated noise blobs (area < *min_object_size* pixels).
    2. Morphological closing with a disk of *close_radius* to bridge
       small gaps between wall fragments.
    3. Morphological opening with a disk of *open_radius* to remove
       tiny protrusions introduced by closing.

    Parameters
    ----------
    mask:
        Boolean 2-D array where ``True`` marks wall pixels.
    min_object_size:
        Connected components smaller than this (in pixels) are removed.
    close_radius:
        Radius of the structuring element used for morphological closing.
    open_radius:
        Radius of the structuring element used for morphological opening.
        Set to 0 to skip opening.

    Returns
    -------
    np.ndarray
        Cleaned boolean mask.
    """
    # 1. Remove small noise blobs
    # max_size removes objects with area <= threshold
    cleaned = remove_small_objects(mask, max_size=min_object_size - 1)

    # 2. Close small gaps
    if close_radius > 0:
        selem_close = disk(close_radius)
        cleaned = closing(cleaned, footprint=selem_close)

    # 3. Light opening to smooth jagged edges from closing
    if open_radius > 0:
        selem_open = disk(open_radius)
        cleaned = opening(cleaned, footprint=selem_open)

    return cleaned.astype(bool)


# ---------------------------------------------------------------------------
# Public API – Phase 2
# ---------------------------------------------------------------------------

def skeletonization(mask: np.ndarray) -> np.ndarray:
    """Produce a one-pixel-wide skeleton from a binary wall mask.

    Full pipeline:

    1. **Validate** – ensure *mask* is a 2-D NumPy array with data.
    2. **Normalize** – convert any encoding (bool / 0-1 / 0-255) to bool.
    3. **Morphological cleanup** – remove noise, close small gaps.
    4. **Skeletonize** – reduce cleaned walls to a medial-axis skeleton.

    Parameters
    ----------
    mask : np.ndarray
        2-D array representing a binary wall mask.
        Accepted encodings: bool, 0/1, 0/255.

    Returns
    -------
    np.ndarray
        Boolean 2-D array of the same shape as *mask* where ``True``
        marks skeleton pixels.

    Raises
    ------
    TypeError
        If *mask* is not a NumPy array.
    ValueError
        If *mask* is not 2-D or is empty.
    """
    # Step 1 – validate
    _validate_mask(mask)

    # Step 2 – normalize to bool
    binary_mask = _normalize_mask(mask)

    # If the mask is entirely empty after normalization, return zeros
    if not binary_mask.any():
        return np.zeros_like(binary_mask, dtype=bool)

    # Step 3 – morphological cleanup
    cleaned = _cleanup_wall_mask(binary_mask)

    # If cleanup removed everything (e.g. the input was *only* noise),
    # return an empty skeleton rather than erroring.
    if not cleaned.any():
        return np.zeros_like(binary_mask, dtype=bool)

    # Step 4 – skeletonize
    skeleton = skeletonize(cleaned)

    return skeleton.astype(bool)


# ---------------------------------------------------------------------------
# Placeholders – later phases
# ---------------------------------------------------------------------------

def generate_wall_graph(skeleton: np.ndarray):  # noqa: D401
    """Generate a wall graph from a skeleton image.  *(Phase 3 placeholder)*"""
    pass


def polygonize_rooms(wall_graph):  # noqa: D401
    """Polygonize rooms from a wall graph.  *(Phase 4+ placeholder)*"""
    pass
