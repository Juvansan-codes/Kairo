"""
Tests for Phase 2 – morphological cleanup & skeletonization.

All masks are generated programmatically; no external files required.
"""

from __future__ import annotations

import math
import numpy as np
import pytest

from app.geometry.solver import (
    skeletonization,
    extract_wall_segments,
    _validate_mask,
    _normalize_mask,
    _cleanup_wall_mask,
)
from app.geometry.types import WallSegment


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_blank(h: int = 200, w: int = 200) -> np.ndarray:
    """Return a blank (all-False) boolean mask."""
    return np.zeros((h, w), dtype=bool)


def _draw_hline(
    mask: np.ndarray,
    row: int,
    col_start: int,
    col_end: int,
    thickness: int = 1,
) -> np.ndarray:
    """Draw a horizontal wall stripe on *mask* (in-place)."""
    half = thickness // 2
    r0 = max(row - half, 0)
    r1 = min(row + half + 1, mask.shape[0])
    mask[r0:r1, col_start:col_end] = True
    return mask


def _draw_vline(
    mask: np.ndarray,
    col: int,
    row_start: int,
    row_end: int,
    thickness: int = 1,
) -> np.ndarray:
    """Draw a vertical wall stripe on *mask* (in-place)."""
    half = thickness // 2
    c0 = max(col - half, 0)
    c1 = min(col + half + 1, mask.shape[1])
    mask[row_start:row_end, c0:c1] = True
    return mask


# ===================================================================
# 1. Simple horizontal wall
# ===================================================================

class TestHorizontalWall:
    """A thin horizontal wall should survive cleanup and skeletonization."""

    def test_skeleton_has_nonzero_pixels(self):
        mask = _make_blank()
        _draw_hline(mask, row=100, col_start=20, col_end=180, thickness=5)
        skel = skeletonization(mask)

        assert skel.any(), "skeleton should contain at least some True pixels"

    def test_skeleton_is_thinner_than_input(self):
        mask = _make_blank()
        _draw_hline(mask, row=100, col_start=20, col_end=180, thickness=10)
        skel = skeletonization(mask)

        # Count pixels in the vertical cross-section near the middle
        col = 100
        input_width = mask[:, col].sum()
        skel_width = skel[:, col].sum()
        assert skel_width < input_width, (
            f"skeleton cross-section ({skel_width}) should be thinner "
            f"than input ({input_width})"
        )


# ===================================================================
# 2. Simple vertical wall
# ===================================================================

class TestVerticalWall:
    """A thin vertical wall should survive cleanup and skeletonization."""

    def test_skeleton_has_nonzero_pixels(self):
        mask = _make_blank()
        _draw_vline(mask, col=100, row_start=20, row_end=180, thickness=5)
        skel = skeletonization(mask)

        assert skel.any(), "skeleton should contain at least some True pixels"

    def test_skeleton_is_thinner_than_input(self):
        mask = _make_blank()
        _draw_vline(mask, col=100, row_start=20, row_end=180, thickness=10)
        skel = skeletonization(mask)

        row = 100
        input_width = mask[row, :].sum()
        skel_width = skel[row, :].sum()
        assert skel_width < input_width


# ===================================================================
# 3. Thick wall → thin skeleton
# ===================================================================

class TestThickWall:
    """A wide wall slab should be reduced to a thin medial axis."""

    def test_thick_horizontal_wall(self):
        mask = _make_blank(300, 300)
        _draw_hline(mask, row=150, col_start=30, col_end=270, thickness=30)
        skel = skeletonization(mask)

        # At any column in the middle, the skeleton should be at most a few
        # pixels thick (ideally 1).
        for col in [80, 150, 220]:
            skel_width = skel[:, col].sum()
            assert skel_width <= 3, (
                f"skeleton cross-section at col={col} is {skel_width}; "
                "expected ≤3 for a proper skeleton"
            )

    def test_thick_vertical_wall(self):
        mask = _make_blank(300, 300)
        _draw_vline(mask, col=150, row_start=30, row_end=270, thickness=30)
        skel = skeletonization(mask)

        for row in [80, 150, 220]:
            skel_width = skel[row, :].sum()
            assert skel_width <= 3


# ===================================================================
# 4. Small isolated noise removed
# ===================================================================

class TestNoiseRemoval:
    """Tiny isolated blobs should be removed during cleanup."""

    def test_small_blobs_removed(self):
        mask = _make_blank()
        # Plant a few small 3x3 noise blobs
        for r, c in [(20, 30), (50, 150), (180, 60)]:
            mask[r : r + 3, c : c + 3] = True

        skel = skeletonization(mask)
        # Everything should be gone after cleanup
        assert not skel.any(), "small noise blobs should produce an empty skeleton"

    def test_noise_near_wall_does_not_kill_wall(self):
        mask = _make_blank()
        # A real wall
        _draw_hline(mask, row=100, col_start=20, col_end=180, thickness=6)
        # Some noise far away
        mask[10:13, 10:13] = True

        skel = skeletonization(mask)
        assert skel.any(), "wall skeleton should survive despite nearby noise"


# ===================================================================
# 5. Small wall gaps handled
# ===================================================================

class TestGapClosing:
    """Morphological closing should bridge small gaps in walls."""

    def test_small_gap_bridged(self):
        mask = _make_blank()
        # Two wall segments with a small gap in between
        _draw_hline(mask, row=100, col_start=20, col_end=95, thickness=6)
        _draw_hline(mask, row=100, col_start=100, col_end=180, thickness=6)
        # Gap is columns 95-99 (5 px) – close_radius=3 disk should bridge this

        skel = skeletonization(mask)
        # The skeleton should span the gap region
        assert skel.any(), "skeleton should exist after gap is bridged"

        # Check that skeleton pixels exist in the gap region (roughly)
        gap_region = skel[95:106, 93:103]
        assert gap_region.any(), (
            "skeleton should have pixels in the gap region after closing"
        )

    def test_large_gap_not_bridged(self):
        mask = _make_blank()
        # Two short wall segments with a large gap
        _draw_hline(mask, row=100, col_start=20, col_end=60, thickness=6)
        _draw_hline(mask, row=100, col_start=140, col_end=180, thickness=6)
        # Gap is 80 px – should NOT be bridged

        skel = skeletonization(mask)
        # Skeleton should consist of two separate pieces; the mid-gap
        # column should have no skeleton pixel at the wall row.
        mid_col = 100
        gap_pixels = skel[95:106, mid_col].sum()
        assert gap_pixels == 0, (
            "a large gap should not be bridged by morphological closing"
        )


# ===================================================================
# 6. Boolean mask input
# ===================================================================

class TestBooleanInput:
    """Masks provided as ``dtype=bool`` should be accepted."""

    def test_bool_mask(self):
        mask = np.zeros((200, 200), dtype=bool)
        mask[95:105, 30:170] = True
        skel = skeletonization(mask)

        assert skel.dtype == bool
        assert skel.any()


# ===================================================================
# 7. 0/255 mask input
# ===================================================================

class TestUint8Input:
    """Masks encoded as 0/255 uint8 images should be accepted."""

    def test_uint8_mask(self):
        mask = np.zeros((200, 200), dtype=np.uint8)
        mask[95:105, 30:170] = 255
        skel = skeletonization(mask)

        assert skel.dtype == bool
        assert skel.any()

    def test_uint8_and_bool_produce_same_skeleton(self):
        bool_mask = np.zeros((200, 200), dtype=bool)
        bool_mask[95:105, 30:170] = True

        uint8_mask = np.zeros((200, 200), dtype=np.uint8)
        uint8_mask[95:105, 30:170] = 255

        skel_bool = skeletonization(bool_mask)
        skel_uint8 = skeletonization(uint8_mask)

        np.testing.assert_array_equal(skel_bool, skel_uint8)

    def test_01_int_mask(self):
        """0/1 integer mask should also work."""
        mask = np.zeros((200, 200), dtype=np.int32)
        mask[95:105, 30:170] = 1
        skel = skeletonization(mask)

        assert skel.dtype == bool
        assert skel.any()


# ===================================================================
# 8. Invalid / empty input behaviour
# ===================================================================

class TestInvalidInput:
    """Invalid inputs should raise clear exceptions."""

    def test_non_array_raises_typeerror(self):
        with pytest.raises(TypeError, match="numpy ndarray"):
            skeletonization([[1, 0], [0, 1]])

    def test_3d_array_raises_valueerror(self):
        with pytest.raises(ValueError, match="2-D"):
            skeletonization(np.zeros((10, 10, 3)))

    def test_1d_array_raises_valueerror(self):
        with pytest.raises(ValueError, match="2-D"):
            skeletonization(np.zeros((100,)))

    def test_empty_array_raises_valueerror(self):
        with pytest.raises(ValueError, match="empty"):
            skeletonization(np.zeros((0, 0), dtype=bool))

    def test_all_zero_mask_returns_empty(self):
        """A fully black mask is valid but should yield an empty skeleton."""
        skel = skeletonization(np.zeros((200, 200), dtype=bool))
        assert not skel.any()
        assert skel.shape == (200, 200)

    def test_shape_preserved(self):
        """Output shape must match input shape."""
        mask = np.zeros((123, 456), dtype=bool)
        mask[50:60, 100:400] = True
        skel = skeletonization(mask)
        assert skel.shape == (123, 456)


# ===================================================================
# Phase 3 Tests: extract_wall_segments
# ===================================================================

class TestExtractHorizontalSkeleton:
    """Horizontal skeleton line should produce 1 wall segment."""

    def test_horizontal_segment_extraction(self):
        skel = np.zeros((100, 100), dtype=bool)
        skel[50, 20:80] = True  # columns 20 to 79 (length 59 px)

        segs = extract_wall_segments(skel)

        assert len(segs) == 1
        seg = segs[0]
        assert isinstance(seg, WallSegment)
        assert abs(seg.length_px - 59.0) <= 1.0
        # Horizontal angles are approximately 0° or ±180°
        assert abs(seg.angle_deg) <= 1.0 or abs(abs(seg.angle_deg) - 180.0) <= 1.0
        # Endpoints should align with row 50
        assert abs(seg.start[1] - 50.0) <= 1.0
        assert abs(seg.end[1] - 50.0) <= 1.0
        # X-coordinates should span approx 20 to 79
        x_coords = sorted([seg.start[0], seg.end[0]])
        assert abs(x_coords[0] - 20.0) <= 1.0
        assert abs(x_coords[1] - 79.0) <= 1.0


class TestExtractVerticalSkeleton:
    """Vertical skeleton line should produce 1 wall segment."""

    def test_vertical_segment_extraction(self):
        skel = np.zeros((100, 100), dtype=bool)
        skel[20:80, 50] = True  # rows 20 to 79 (length 59 px)

        segs = extract_wall_segments(skel)

        assert len(segs) == 1
        seg = segs[0]
        assert isinstance(seg, WallSegment)
        assert abs(seg.length_px - 59.0) <= 1.0
        # Vertical angle should be approximately 90° or -90°
        assert abs(abs(seg.angle_deg) - 90.0) <= 1.0
        # Endpoints should align with col 50
        assert abs(seg.start[0] - 50.0) <= 1.0
        assert abs(seg.end[0] - 50.0) <= 1.0
        # Y-coordinates should span approx 20 to 79
        y_coords = sorted([seg.start[1], seg.end[1]])
        assert abs(y_coords[0] - 20.0) <= 1.0
        assert abs(y_coords[1] - 79.0) <= 1.0


class TestExtractDiagonalSkeleton:
    """Diagonal skeleton line should produce 1 segment matching diagonal direction."""

    def test_diagonal_segment_extraction(self):
        skel = np.zeros((100, 100), dtype=bool)
        for i in range(20, 80):
            skel[i, i] = True

        segs = extract_wall_segments(skel)

        assert len(segs) == 1
        seg = segs[0]
        expected_len = math.hypot(59, 59)
        assert abs(seg.length_px - expected_len) <= 3.0
        # Diagonal direction should be approximately 45° or -135°
        assert abs(seg.angle_deg - 45.0) <= 2.0 or abs(seg.angle_deg - (-135.0)) <= 2.0


class TestExtractLShapedSkeleton:
    """L-shaped skeleton should produce multiple segments and handle the corner."""

    def test_l_shaped_segments(self):
        skel = np.zeros((100, 100), dtype=bool)
        skel[50, 20:61] = True  # horizontal: col 20..60 (length 40)
        skel[50:91, 60] = True  # vertical: row 50..90 (length 40)

        segs = extract_wall_segments(skel)

        assert len(segs) >= 2
        angles = [s.angle_deg for s in segs]
        has_horizontal = any(abs(a) <= 5.0 or abs(abs(a) - 180.0) <= 5.0 for a in angles)
        has_vertical = any(abs(abs(a) - 90.0) <= 5.0 for a in angles)
        assert has_horizontal, "Expected at least one horizontal segment in L-shape"
        assert has_vertical, "Expected at least one vertical segment in L-shape"


class TestExtractTShapedSkeleton:
    """T-shaped skeleton should produce 3 segments meeting at the junction."""

    def test_t_shaped_segments(self):
        skel = np.zeros((100, 100), dtype=bool)
        skel[50, 20:80] = True  # horizontal bar: col 20..79
        skel[50:90, 50] = True  # vertical stem: row 50..89

        segs = extract_wall_segments(skel)

        assert len(segs) == 3
        angles = [s.angle_deg for s in segs]
        horiz_count = sum(1 for a in angles if abs(a) <= 5.0 or abs(abs(a) - 180.0) <= 5.0)
        vert_count = sum(1 for a in angles if abs(abs(a) - 90.0) <= 5.0)
        assert horiz_count == 2, f"Expected 2 horizontal branches, got {horiz_count}"
        assert vert_count == 1, f"Expected 1 vertical branch, got {vert_count}"


class TestExtractNoiseSkeleton:
    """Isolated single pixels and short noise should not produce segments."""

    def test_isolated_pixels_ignored(self):
        skel = np.zeros((100, 100), dtype=bool)
        skel[10, 10] = True
        skel[20, 20] = True
        skel[30:32, 30:32] = True  # 2x2 clump

        segs = extract_wall_segments(skel)
        assert len(segs) == 0

    def test_empty_skeleton_returns_empty_list(self):
        skel = np.zeros((100, 100), dtype=bool)
        assert extract_wall_segments(skel) == []


class TestExtractEncodingInputs:
    """Functions should accept boolean, 0/1 integer, and 0/255 arrays."""

    def test_boolean_skeleton_input(self):
        skel = np.zeros((100, 100), dtype=bool)
        skel[50, 20:80] = True
        segs = extract_wall_segments(skel)
        assert len(segs) == 1
        assert isinstance(segs[0], WallSegment)

    def test_uint8_skeleton_input(self):
        skel = np.zeros((100, 100), dtype=np.uint8)
        skel[50, 20:80] = 255
        segs = extract_wall_segments(skel)
        assert len(segs) == 1
        assert isinstance(segs[0], WallSegment)

    def test_int_01_skeleton_input(self):
        skel = np.zeros((100, 100), dtype=np.int32)
        skel[50, 20:80] = 1
        segs = extract_wall_segments(skel)
        assert len(segs) == 1
        assert isinstance(segs[0], WallSegment)


class TestExtractInvalidInput:
    """Invalid inputs to extract_wall_segments must raise clear exceptions."""

    def test_non_array_raises_typeerror(self):
        with pytest.raises(TypeError, match="numpy ndarray"):
            extract_wall_segments([[1, 0], [0, 1]])

    def test_3d_array_raises_valueerror(self):
        with pytest.raises(ValueError, match="2-D"):
            extract_wall_segments(np.zeros((10, 10, 3)))

    def test_1d_array_raises_valueerror(self):
        with pytest.raises(ValueError, match="2-D"):
            extract_wall_segments(np.zeros((100,)))

    def test_empty_array_raises_valueerror(self):
        with pytest.raises(ValueError, match="empty"):
            extract_wall_segments(np.zeros((0, 0), dtype=bool))


class TestExtractClosedLoopSkeleton:
    """Closed loop skeletons should terminate cleanly and produce wall segments."""

    def test_rectangular_closed_loop(self):
        skel = np.zeros((100, 100), dtype=bool)
        skel[30:70, 30] = True
        skel[30:70, 70] = True
        skel[30, 30:71] = True
        skel[70, 30:71] = True

        segs = extract_wall_segments(skel)

        assert len(segs) >= 2
        for s in segs:
            assert isinstance(s, WallSegment)
            assert s.length_px >= 3.0


class TestWallSegmentProperties:
    """Verify WallSegment attributes, source, and confidence scores."""

    def test_confidence_and_source(self):
        skel = np.zeros((100, 100), dtype=bool)
        skel[50, 20:80] = True
        segs = extract_wall_segments(skel)

        assert len(segs) == 1
        seg = segs[0]
        assert seg.source == ["skeleton"]
        assert 0.0 < seg.confidence <= 1.0
        assert seg.id.startswith("wall_")
