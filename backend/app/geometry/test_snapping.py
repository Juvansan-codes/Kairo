"""
Unit tests for Phase 5 Manhattan Snapping (backend/app/geometry/snapping.py).
"""

from __future__ import annotations

import math
import pytest

from app.geometry.snapping import snap_wall_segments
from app.geometry.types import WallSegment


def _make_segment(
    seg_id: str = "w1",
    start: tuple[float, float] = (0.0, 0.0),
    end: tuple[float, float] = (100.0, 0.0),
    length_px: float = 100.0,
    angle_deg: float = 0.0,
    confidence: float = 0.95,
    source: list[str] | None = None,
    thickness_px: float | None = 10.0,
    start_metric: tuple[float, float] | None = None,
    end_metric: tuple[float, float] | None = None,
) -> WallSegment:
    """Helper to instantiate a WallSegment for testing."""
    return WallSegment(
        id=seg_id,
        start=start,
        end=end,
        length_px=length_px,
        angle_deg=angle_deg,
        confidence=confidence,
        source=["skeleton"] if source is None else source,
        thickness_px=thickness_px,
        start_metric=start_metric,
        end_metric=end_metric,
    )


class TestManhattanSnapping:
    """Core test suite for snap_wall_segments."""

    def test_empty_input(self):
        """1. Empty input list returns an empty list."""
        assert snap_wall_segments([]) == []

    def test_slightly_tilted_horizontal_wall(self):
        """2. Slightly tilted horizontal wall (~2°) snaps to exact horizontal (0°)."""
        # dx = 100, dy = 3.49 -> angle ~ 2.0°
        seg = _make_segment(
            seg_id="w_tilted_h",
            start=(10.0, 20.0),
            end=(110.0, 23.5),
            length_px=100.06,
            angle_deg=2.0,
        )

        snapped = snap_wall_segments([seg], angle_tolerance_deg=10.0)
        assert len(snapped) == 1
        s = snapped[0]

        # y coordinates become equal (midpoint = (20.0 + 23.5) / 2 = 21.75)
        assert s.start[1] == s.end[1] == 21.75
        # x coordinates are preserved
        assert s.start[0] == 10.0
        assert s.end[0] == 110.0
        # angle becomes exactly 0°
        assert s.angle_deg == 0.0
        # length is recalculated to exact horizontal span
        assert s.length_px == 100.0

    def test_slightly_tilted_vertical_wall(self):
        """3. Slightly tilted vertical wall (~88°) snaps to exact vertical (90°)."""
        # dx = 3.49, dy = 100 -> angle ~ 88.0°
        seg = _make_segment(
            seg_id="w_tilted_v",
            start=(50.0, 10.0),
            end=(53.5, 110.0),
            length_px=100.06,
            angle_deg=88.0,
        )

        snapped = snap_wall_segments([seg], angle_tolerance_deg=10.0)
        assert len(snapped) == 1
        s = snapped[0]

        # x coordinates become equal (midpoint = (50.0 + 53.5) / 2 = 51.75)
        assert s.start[0] == s.end[0] == 51.75
        # y coordinates are preserved
        assert s.start[1] == 10.0
        assert s.end[1] == 110.0
        # angle becomes exactly 90°
        assert s.angle_deg == 90.0
        # length is recalculated to exact vertical span
        assert s.length_px == 100.0

    def test_negative_small_angle_horizontal(self):
        """4. Negative small angle (~-3°) snaps to horizontal (0°)."""
        # dx = 100, dy = -5.24 -> angle ~ -3.0°
        seg = _make_segment(
            seg_id="w_neg_h",
            start=(0.0, 50.0),
            end=(100.0, 45.0),
            length_px=100.12,
            angle_deg=-2.86,
        )

        snapped = snap_wall_segments([seg], angle_tolerance_deg=10.0)
        assert len(snapped) == 1
        s = snapped[0]

        assert s.start[1] == s.end[1] == 47.5
        assert s.start[0] == 0.0
        assert s.end[0] == 100.0
        assert s.angle_deg == 0.0
        assert s.length_px == 100.0

    def test_near_180_wall_horizontal(self):
        """5. Near-180° wall (~178°) snaps to horizontal (180°) without reversing endpoints."""
        # pointing left: dx = -100, dy = 3.49 -> angle ~ 178°
        seg = _make_segment(
            seg_id="w_near_180",
            start=(110.0, 20.0),
            end=(10.0, 23.5),
            length_px=100.06,
            angle_deg=178.0,
        )

        snapped = snap_wall_segments([seg], angle_tolerance_deg=10.0)
        assert len(snapped) == 1
        s = snapped[0]

        # start remains start, end remains end (orientation direction preserved)
        assert s.start[0] == 110.0
        assert s.end[0] == 10.0
        assert s.start[1] == s.end[1] == 21.75
        assert s.angle_deg == 180.0
        assert s.length_px == 100.0

    def test_near_negative_90_vertical(self):
        """8. Near -90° wall (~-88°) snaps to vertical (-90°) without reversing endpoints."""
        # pointing upwards: dx = 3.5, dy = -100 -> angle ~ -88°
        seg = _make_segment(
            seg_id="w_near_neg90",
            start=(50.0, 110.0),
            end=(53.5, 10.0),
            length_px=100.06,
            angle_deg=-88.0,
        )

        snapped = snap_wall_segments([seg], angle_tolerance_deg=10.0)
        assert len(snapped) == 1
        s = snapped[0]

        assert s.start[0] == s.end[0] == 51.75
        assert s.start[1] == 110.0
        assert s.end[1] == 10.0
        assert s.angle_deg == -90.0
        assert s.length_px == 100.0

    def test_diagonal_wall_remains_unchanged(self):
        """6. Diagonal wall (~45°) remains unchanged."""
        seg = _make_segment(
            seg_id="w_diag",
            start=(10.0, 10.0),
            end=(60.0, 60.0),
            length_px=70.71,
            angle_deg=45.0,
        )

        snapped = snap_wall_segments([seg], angle_tolerance_deg=10.0)
        assert len(snapped) == 1
        s = snapped[0]

        assert s.start == (10.0, 10.0)
        assert s.end == (60.0, 60.0)
        assert s.angle_deg == 45.0
        assert s.length_px == 70.71

    def test_custom_tolerance_respected(self):
        """7. A segment at 8° deviation snaps under 10° tolerance but remains unsnapped under 5°."""
        # dx = 100, dy = 14.05 -> angle = ~8.0°
        seg = _make_segment(
            seg_id="w_8deg",
            start=(0.0, 0.0),
            end=(100.0, 14.05),
            length_px=100.98,
            angle_deg=8.0,
        )

        # Under tolerance 10°: should snap
        snapped_10 = snap_wall_segments([seg], angle_tolerance_deg=10.0)
        assert snapped_10[0].angle_deg == 0.0
        assert snapped_10[0].start[1] == snapped_10[0].end[1]

        # Under tolerance 5°: should NOT snap
        snapped_5 = snap_wall_segments([seg], angle_tolerance_deg=5.0)
        assert snapped_5[0].angle_deg == 8.0
        assert snapped_5[0].start[1] != snapped_5[0].end[1]

    def test_zero_length_segment_safe(self):
        """8. Zero-length segment does not crash or produce NaN/invalid values."""
        seg_zero = _make_segment(
            seg_id="w_zero",
            start=(50.0, 50.0),
            end=(50.0, 50.0),
            length_px=0.0,
            angle_deg=0.0,
        )

        snapped = snap_wall_segments([seg_zero])
        assert len(snapped) == 1
        s = snapped[0]

        assert s.start == (50.0, 50.0)
        assert s.end == (50.0, 50.0)
        assert s.length_px == 0.0
        assert not math.isnan(s.angle_deg)
        assert not math.isnan(s.length_px)

    def test_already_horizontal_stable(self):
        """9. Already horizontal wall remains stable."""
        seg = _make_segment(
            seg_id="w_horiz",
            start=(10.0, 50.0),
            end=(110.0, 50.0),
            length_px=100.0,
            angle_deg=0.0,
        )

        snapped = snap_wall_segments([seg])
        s = snapped[0]

        assert s.start == (10.0, 50.0)
        assert s.end == (110.0, 50.0)
        assert s.angle_deg == 0.0
        assert s.length_px == 100.0

    def test_already_vertical_stable(self):
        """10. Already vertical wall remains stable."""
        seg = _make_segment(
            seg_id="w_vert",
            start=(50.0, 10.0),
            end=(50.0, 110.0),
            length_px=100.0,
            angle_deg=90.0,
        )

        snapped = snap_wall_segments([seg])
        s = snapped[0]

        assert s.start == (50.0, 10.0)
        assert s.end == (50.0, 110.0)
        assert s.angle_deg == 90.0
        assert s.length_px == 100.0

    def test_metadata_preservation_and_safe_copy(self):
        """11. All metadata fields are preserved and mutable fields like source are safely copied."""
        seg = _make_segment(
            seg_id="wall_meta_test",
            start=(0.0, 10.0),
            end=(100.0, 13.0),
            confidence=0.887,
            source=["skeleton", "manual"],
            thickness_px=15.0,
            start_metric=(1.0, 2.0),
            end_metric=(5.0, 2.0),
        )

        snapped = snap_wall_segments([seg])
        s = snapped[0]

        assert s.id == "wall_meta_test"
        assert s.confidence == 0.887
        assert s.thickness_px == 15.0
        assert s.start_metric == (1.0, 2.0)
        assert s.end_metric == (5.0, 2.0)
        assert s.source == ["skeleton", "manual"]

        # Mutating s.source must NOT affect seg.source (safe copy check)
        s.source.append("snapped")
        assert "snapped" not in seg.source

    def test_input_immutability(self):
        """12. Input objects are not mutated in place."""
        orig_start = (10.0, 20.0)
        orig_end = (100.0, 23.5)
        seg = _make_segment(
            seg_id="w_immutable",
            start=orig_start,
            end=orig_end,
            length_px=90.06,
            angle_deg=2.23,
        )

        snapped = snap_wall_segments([seg])
        assert len(snapped) == 1

        # Original segment properties are completely unchanged
        assert seg.start == orig_start
        assert seg.end == orig_end
        assert seg.length_px == 90.06
        assert seg.angle_deg == 2.23

    def test_duplicate_segment_ids_preserved(self):
        """13. Duplicate segment IDs are kept as-is without inventing new IDs."""
        seg1 = _make_segment(seg_id="dup_id", start=(0.0, 0.0), end=(100.0, 2.0))
        seg2 = _make_segment(seg_id="dup_id", start=(0.0, 50.0), end=(100.0, 52.0))

        snapped = snap_wall_segments([seg1, seg2])
        assert len(snapped) == 2
        assert snapped[0].id == "dup_id"
        assert snapped[1].id == "dup_id"
