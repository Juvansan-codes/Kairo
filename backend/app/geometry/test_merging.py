"""
Unit tests for Phase 6 Collinear Segment Merging (backend/app/geometry/merging.py).
"""

from __future__ import annotations

import pytest

from app.geometry.merging import merge_collinear_segments
from app.geometry.types import WallSegment


def _make_segment(
    seg_id: str = "w1",
    start: tuple[float, float] = (0.0, 0.0),
    end: tuple[float, float] = (100.0, 0.0),
    length_px: float = 100.0,
    angle_deg: float = 0.0,
    confidence: float = 0.9,
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


class TestCollinearMerging:
    """Core test suite for merge_collinear_segments."""

    def test_empty_input(self):
        """1. Empty input list returns empty list."""
        assert merge_collinear_segments([]) == []

    def test_single_segment_unchanged(self):
        """2. Single segment remains unchanged geometrically."""
        seg = _make_segment("w1", (10.0, 20.0), (100.0, 20.0), length_px=90.0, angle_deg=0.0)
        res = merge_collinear_segments([seg])

        assert len(res) == 1
        assert res[0].id == "w1"
        assert res[0].start == (10.0, 20.0)
        assert res[0].end == (100.0, 20.0)
        assert res[0].length_px == 90.0
        assert res[0].angle_deg == 0.0

    def test_horizontal_overlapping_segments(self):
        """3. Horizontal overlapping segments merge into one covering complete extent."""
        # A: 10 to 60, B: 40 to 100
        segA = _make_segment("wA", (10.0, 20.0), (60.0, 20.0), length_px=50.0)
        segB = _make_segment("wB", (40.0, 20.0), (100.0, 20.0), length_px=60.0)

        res = merge_collinear_segments([segA, segB])

        assert len(res) == 1
        m = res[0]
        assert m.start == (10.0, 20.0)
        assert m.end == (100.0, 20.0)
        assert m.length_px == 90.0
        assert m.angle_deg == 0.0

    def test_horizontal_segments_with_small_gap(self):
        """4. Horizontal segments with gap <= gap_tolerance_px merge."""
        # A: 10 to 50, B: 53 to 100 (gap is 3.0 px <= 5.0 px)
        segA = _make_segment("wA", (10.0, 20.0), (50.0, 20.0), length_px=40.0)
        segB = _make_segment("wB", (53.0, 20.0), (100.0, 20.0), length_px=47.0)

        res = merge_collinear_segments([segA, segB], gap_tolerance_px=5.0)

        assert len(res) == 1
        m = res[0]
        assert m.start == (10.0, 20.0)
        assert m.end == (100.0, 20.0)
        assert m.length_px == 90.0

    def test_horizontal_segments_with_large_gap(self):
        """5. Horizontal segments with gap > gap_tolerance_px remain separate."""
        # A: 10 to 50, B: 70 to 100 (gap is 20.0 px > 5.0 px)
        segA = _make_segment("wA", (10.0, 20.0), (50.0, 20.0), length_px=40.0)
        segB = _make_segment("wB", (70.0, 20.0), (100.0, 20.0), length_px=30.0)

        res = merge_collinear_segments([segA, segB], gap_tolerance_px=5.0)

        assert len(res) == 2
        assert {s.id for s in res} == {"wA", "wB"}

    def test_vertical_overlapping_segments(self):
        """6. Vertical overlapping segments merge correctly."""
        # A: (20, 10) to (20, 60), B: (20, 50) to (20, 100)
        segA = _make_segment("vA", (20.0, 10.0), (20.0, 60.0), length_px=50.0, angle_deg=90.0)
        segB = _make_segment("vB", (20.0, 50.0), (20.0, 100.0), length_px=50.0, angle_deg=90.0)

        res = merge_collinear_segments([segA, segB])

        assert len(res) == 1
        m = res[0]
        assert m.start == (20.0, 10.0)
        assert m.end == (20.0, 100.0)
        assert m.length_px == 90.0
        assert m.angle_deg == 90.0

    def test_reversed_endpoint_direction(self):
        """7. Segments merge regardless of reversed endpoint ordering."""
        # A: (10, 20) -> (50, 20) (left-to-right)
        # B: (100, 20) -> (45, 20) (right-to-left)
        segA = _make_segment("wA", (10.0, 20.0), (50.0, 20.0), length_px=40.0, angle_deg=0.0)
        segB = _make_segment("wB", (100.0, 20.0), (45.0, 20.0), length_px=55.0, angle_deg=180.0)

        res = merge_collinear_segments([segA, segB])

        assert len(res) == 1
        m = res[0]
        # Coordinates cover 10 to 100
        x_coords = sorted([m.start[0], m.end[0]])
        assert x_coords == [10.0, 100.0]
        assert m.start[1] == 20.0
        assert m.end[1] == 20.0
        assert m.length_px == 90.0

    def test_slight_angular_difference(self):
        """8. Segments merge when angular difference is within tolerance."""
        # A: (0, 0) -> (50, 0) (0.0°)
        # B: (48, 0.5) -> (100, 1.5) (~1.1° difference, perpendicular dist < 2.0 px)
        segA = _make_segment("wA", (0.0, 0.0), (50.0, 0.0), length_px=50.0, angle_deg=0.0)
        segB = _make_segment("wB", (48.0, 0.5), (100.0, 1.5), length_px=52.01, angle_deg=1.1)

        res = merge_collinear_segments(
            [segA, segB],
            angle_tolerance_deg=5.0,
            distance_tolerance_px=3.0,
        )

        assert len(res) == 1
        m = res[0]
        assert m.length_px >= 99.0

    def test_excessive_angular_difference(self):
        """9. Segments with angular difference exceeding tolerance remain separate."""
        # A: horizontal (0°), B: ~15° tilted
        segA = _make_segment("wA", (0.0, 0.0), (50.0, 0.0), length_px=50.0, angle_deg=0.0)
        segB = _make_segment("wB", (50.0, 0.0), (100.0, 13.4), length_px=51.76, angle_deg=15.0)

        res = merge_collinear_segments([segA, segB], angle_tolerance_deg=5.0)

        assert len(res) == 2

    def test_parallel_but_spatially_separated_walls(self):
        """10. Parallel walls separated by perpendicular distance > tolerance remain separate."""
        # Two parallel walls 20 px apart (e.g. hallway walls)
        segA = _make_segment("wall_top", (0.0, 20.0), (100.0, 20.0), length_px=100.0)
        segB = _make_segment("wall_bottom", (0.0, 40.0), (100.0, 40.0), length_px=100.0)

        res = merge_collinear_segments([segA, segB], distance_tolerance_px=3.0)

        assert len(res) == 2
        assert {s.id for s in res} == {"wall_top", "wall_bottom"}

    def test_non_collinear_crossing_segments(self):
        """11. Crossing/perpendicular segments are not incorrectly merged."""
        # + shape
        seg_h = _make_segment("h_cross", (0.0, 50.0), (100.0, 50.0), length_px=100.0, angle_deg=0.0)
        seg_v = _make_segment("v_cross", (50.0, 0.0), (50.0, 100.0), length_px=100.0, angle_deg=90.0)

        res = merge_collinear_segments([seg_h, seg_v])

        assert len(res) == 2
        assert {s.id for s in res} == {"h_cross", "v_cross"}

    def test_transitive_chain(self):
        """12. Transitive chain A (0-30), B (29-60), C (59-100) merges to 0-100."""
        cA = _make_segment("cA", (0.0, 10.0), (30.0, 10.0), length_px=30.0)
        cB = _make_segment("cB", (29.0, 10.0), (60.0, 10.0), length_px=31.0)
        cC = _make_segment("cC", (59.0, 10.0), (100.0, 10.0), length_px=41.0)

        res = merge_collinear_segments([cA, cB, cC])

        assert len(res) == 1
        m = res[0]
        assert m.start == (0.0, 10.0)
        assert m.end == (100.0, 10.0)
        assert m.length_px == 100.0

    def test_duplicate_segments(self):
        """13. Duplicate segments do not create duplicate merged output."""
        seg = _make_segment("dup_w", (10.0, 10.0), (80.0, 10.0), length_px=70.0)

        res = merge_collinear_segments([seg, seg])

        assert len(res) == 1
        assert res[0].start == (10.0, 10.0)
        assert res[0].end == (80.0, 10.0)

    def test_metadata_preservation(self):
        """14. Merged segment combines confidence, source, thickness, and metric fields safely."""
        segA = _make_segment(
            seg_id="wA",
            start=(0.0, 0.0),
            end=(50.0, 0.0),
            length_px=50.0,
            confidence=0.8,
            source=["skeleton"],
            thickness_px=10.0,
            start_metric=(0.0, 0.0),
            end_metric=(1.0, 0.0),
        )
        segB = _make_segment(
            seg_id="wB",
            start=(48.0, 0.0),
            end=(100.0, 0.0),
            length_px=52.0,
            confidence=0.9,
            source=["manual_ocr"],
            thickness_px=14.0,
            start_metric=(0.95, 0.0),
            end_metric=(2.0, 0.0),
        )

        res = merge_collinear_segments([segA, segB])
        assert len(res) == 1
        m = res[0]

        # ID is deterministic (anchor segment ID)
        assert m.id in {"wA", "wB"}
        # Confidence is length-weighted: (50*0.8 + 52*0.9) / 102 = 0.851
        expected_conf = round((50.0 * 0.8 + 52.0 * 0.9) / 102.0, 3)
        assert m.confidence == expected_conf
        # Source combines unique values
        assert set(m.source) == {"skeleton", "manual_ocr"}
        # Mutating m.source does not affect original segments
        m.source.append("test_tag")
        assert "test_tag" not in segA.source
        assert "test_tag" not in segB.source
        # Thickness is length-weighted when differing: (50*10 + 52*14) / 102 = 12.04
        expected_thick = round((50.0 * 10.0 + 52.0 * 14.0) / 102.0, 2)
        assert m.thickness_px == expected_thick
        # Metric coordinates are None for newly merged extended extent
        assert m.start_metric is None
        assert m.end_metric is None

    def test_input_immutability(self):
        """15. Original input WallSegment objects are not mutated."""
        orig_start = (10.0, 20.0)
        orig_end = (50.0, 20.0)
        seg = _make_segment("w_orig", orig_start, orig_end, length_px=40.0)
        seg_copy = _make_segment("w_orig2", (48.0, 20.0), (100.0, 20.0), length_px=52.0)

        merge_collinear_segments([seg, seg_copy])

        assert seg.start == orig_start
        assert seg.end == orig_end
        assert seg.length_px == 40.0

    def test_zero_length_segment_safe(self):
        """16. Zero-length segment does not crash or produce invalid geometry."""
        z_seg = _make_segment("z1", (25.0, 25.0), (25.0, 25.0), length_px=0.0)
        valid = _make_segment("v1", (0.0, 0.0), (50.0, 0.0), length_px=50.0)

        res = merge_collinear_segments([z_seg, valid])

        assert len(res) == 2
        # Zero-length is preserved safely
        z_out = [s for s in res if s.id == "z1"][0]
        assert z_out.start == (25.0, 25.0)
        assert z_out.end == (25.0, 25.0)
        assert z_out.length_px == 0.0

    def test_determinism_and_order_invariance(self):
        """17. Output is identical regardless of input list permutation."""
        s1 = _make_segment("s1", (0.0, 0.0), (40.0, 0.0), length_px=40.0)
        s2 = _make_segment("s2", (38.0, 0.0), (80.0, 0.0), length_px=42.0)
        s3 = _make_segment("s3", (0.0, 50.0), (50.0, 50.0), length_px=50.0)

        res_123 = merge_collinear_segments([s1, s2, s3])
        res_321 = merge_collinear_segments([s3, s2, s1])
        res_213 = merge_collinear_segments([s2, s1, s3])

        assert len(res_123) == 2
        assert len(res_321) == 2
        assert len(res_213) == 2

        for r1, r2, r3 in zip(res_123, res_321, res_213):
            assert r1.start == r2.start == r3.start
            assert r1.end == r2.end == r3.end
            assert r1.length_px == r2.length_px == r3.length_px
            assert r1.angle_deg == r2.angle_deg == r3.angle_deg
            assert r1.id == r2.id == r3.id
