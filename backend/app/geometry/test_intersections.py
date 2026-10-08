"""
Unit tests for Phase 7: Intersection + Geometry Cleanup.
"""

import math
import random
import pytest

from app.geometry.intersections import split_wall_intersections
from app.geometry.types import WallSegment


def test_empty_input():
    """Empty segment list produces empty output."""
    assert split_wall_intersections([]) == []


def test_single_segment():
    """Single segment remains geometrically unchanged and returns a new object."""
    seg = WallSegment(
        id="w1",
        start=(10.0, 20.0),
        end=(50.0, 20.0),
        length_px=40.0,
        angle_deg=0.0,
        confidence=0.9,
        source=["ocr"],
        thickness_px=4.0,
    )
    result = split_wall_intersections([seg])
    assert len(result) == 1
    out = result[0]
    assert out.id == "w1"
    assert out.start == (10.0, 20.0)
    assert out.end == (50.0, 20.0)
    assert out.length_px == 40.0
    assert out.angle_deg == 0.0
    assert out.confidence == 0.9
    assert out.source == ["ocr"]
    assert out.thickness_px == 4.0
    # Immutability
    assert out is not seg
    assert out.source is not seg.source


def test_proper_crossing_horizontal_vertical():
    """Horizontal and vertical segments crossing internally split into 4 parts."""
    h = WallSegment(id="h1", start=(0.0, 50.0), end=(100.0, 50.0), confidence=0.8)
    v = WallSegment(id="v1", start=(50.0, 0.0), end=(50.0, 100.0), confidence=0.9)

    result = split_wall_intersections([h, v])
    assert len(result) == 4

    h_parts = [s for s in result if s.id.startswith("h1")]
    v_parts = [s for s in result if s.id.startswith("v1")]

    assert len(h_parts) == 2
    assert len(v_parts) == 2

    # Verify horizontal parts meet at (50, 50)
    assert h_parts[0].start == (0.0, 50.0)
    assert h_parts[0].end == (50.0, 50.0)
    assert h_parts[0].length_px == 50.0
    assert h_parts[0].angle_deg == 0.0

    assert h_parts[1].start == (50.0, 50.0)
    assert h_parts[1].end == (100.0, 50.0)
    assert h_parts[1].length_px == 50.0
    assert h_parts[1].angle_deg == 0.0

    # Verify vertical parts meet at (50, 50)
    assert v_parts[0].start == (50.0, 0.0)
    assert v_parts[0].end == (50.0, 50.0)
    assert v_parts[0].length_px == 50.0
    assert v_parts[0].angle_deg == 90.0

    assert v_parts[1].start == (50.0, 50.0)
    assert v_parts[1].end == (50.0, 100.0)
    assert v_parts[1].length_px == 50.0
    assert v_parts[1].angle_deg == 90.0


def test_t_junction():
    """Segment ending on another segment splits the cross wall, but not the stem."""
    h = WallSegment(id="h1", start=(0.0, 50.0), end=(100.0, 50.0), confidence=0.8)
    v = WallSegment(id="v1", start=(50.0, 50.0), end=(50.0, 100.0), confidence=0.9)

    result = split_wall_intersections([h, v])
    assert len(result) == 3

    h_parts = [s for s in result if s.id.startswith("h1")]
    v_parts = [s for s in result if s.id.startswith("v1")]

    assert len(h_parts) == 2
    assert len(v_parts) == 1

    assert h_parts[0].start == (0.0, 50.0)
    assert h_parts[0].end == (50.0, 50.0)
    assert h_parts[1].start == (50.0, 50.0)
    assert h_parts[1].end == (100.0, 50.0)

    # v1 retains original ID and unchanged geometry
    assert v_parts[0].id == "v1"
    assert v_parts[0].start == (50.0, 50.0)
    assert v_parts[0].end == (50.0, 100.0)


def test_endpoint_touching():
    """Segments touching at an endpoint are not split internally."""
    s1 = WallSegment(id="s1", start=(0.0, 0.0), end=(50.0, 0.0))
    s2 = WallSegment(id="s2", start=(50.0, 0.0), end=(50.0, 50.0))

    result = split_wall_intersections([s1, s2])
    assert len(result) == 2
    assert {s.id for s in result} == {"s1", "s2"}
    assert any(s.start == (0.0, 0.0) and s.end == (50.0, 0.0) for s in result)
    assert any(s.start == (50.0, 0.0) and s.end == (50.0, 50.0) for s in result)


def test_near_intersection_within_tolerance():
    """Segments close to intersecting within tolerance are normalized and split."""
    h = WallSegment(id="h1", start=(0.0, 50.0), end=(100.0, 50.0))
    # v starts 0.5px below h (gap = 0.5px <= tolerance = 1.0px)
    v = WallSegment(id="v1", start=(50.0, 50.5), end=(50.0, 100.0))

    result = split_wall_intersections(
        [h, v],
        intersection_tolerance_px=1.0,
        endpoint_tolerance_px=2.0,
    )
    assert len(result) == 3

    h_parts = [s for s in result if s.id.startswith("h1")]
    v_parts = [s for s in result if s.id.startswith("v1")]

    assert len(h_parts) == 2
    assert len(v_parts) == 1

    # v1's start is snapped to (50.0, 50.0)
    assert v_parts[0].start == (50.0, 50.0)
    assert v_parts[0].end == (50.0, 100.0)


def test_parallel_non_intersecting_walls():
    """Parallel walls must not be split or merged."""
    s1 = WallSegment(id="w1", start=(0.0, 50.0), end=(100.0, 50.0))
    s2 = WallSegment(id="w2", start=(0.0, 60.0), end=(100.0, 60.0))

    result = split_wall_intersections([s1, s2])
    assert len(result) == 2
    assert {s.id for s in result} == {"w1", "w2"}
    assert any(s.start == (0.0, 50.0) and s.end == (100.0, 50.0) for s in result)
    assert any(s.start == (0.0, 60.0) and s.end == (100.0, 60.0) for s in result)


def test_collinear_overlapping_segments():
    """Collinear overlapping segments are preserved without splitting fragments."""
    s1 = WallSegment(id="w1", start=(0.0, 50.0), end=(60.0, 50.0))
    s2 = WallSegment(id="w2", start=(40.0, 50.0), end=(100.0, 50.0))

    result = split_wall_intersections([s1, s2])
    assert len(result) == 2
    assert {s.id for s in result} == {"w1", "w2"}


def test_diagonal_crossing():
    """Diagonal non-Manhattan segments crossing each other are split properly."""
    d1 = WallSegment(id="d1", start=(0.0, 0.0), end=(100.0, 100.0))
    d2 = WallSegment(id="d2", start=(0.0, 100.0), end=(100.0, 0.0))

    result = split_wall_intersections([d1, d2])
    assert len(result) == 4

    d1_parts = [s for s in result if s.id.startswith("d1")]
    d2_parts = [s for s in result if s.id.startswith("d2")]

    assert len(d1_parts) == 2
    assert len(d2_parts) == 2

    # Both cross at (50, 50)
    assert d1_parts[0].start == (0.0, 0.0)
    assert d1_parts[0].end == (50.0, 50.0)
    assert d1_parts[1].start == (50.0, 50.0)
    assert d1_parts[1].end == (100.0, 100.0)

    assert d2_parts[0].start == (0.0, 100.0)
    assert d2_parts[0].end == (50.0, 50.0)
    assert d2_parts[1].start == (50.0, 50.0)
    assert d2_parts[1].end == (100.0, 0.0)


def test_reversed_endpoint_ordering():
    """Reversed endpoint direction is handled properly with orientation preserved."""
    h = WallSegment(id="h1", start=(100.0, 50.0), end=(0.0, 50.0))
    v = WallSegment(id="v1", start=(50.0, 100.0), end=(50.0, 0.0))

    result = split_wall_intersections([h, v])
    assert len(result) == 4

    h_parts = sorted([s for s in result if s.id.startswith("h1")], key=lambda s: s.id)
    v_parts = sorted([s for s in result if s.id.startswith("v1")], key=lambda s: s.id)

    assert h_parts[0].id == "h1_part_0"
    assert h_parts[0].start == (100.0, 50.0)
    assert h_parts[0].end == (50.0, 50.0)
    assert h_parts[0].angle_deg == 180.0

    assert h_parts[1].id == "h1_part_1"
    assert h_parts[1].start == (50.0, 50.0)
    assert h_parts[1].end == (0.0, 50.0)
    assert h_parts[1].angle_deg == 180.0

    assert v_parts[0].id == "v1_part_0"
    assert v_parts[0].start == (50.0, 100.0)
    assert v_parts[0].end == (50.0, 50.0)
    assert v_parts[0].angle_deg == -90.0

    assert v_parts[1].id == "v1_part_1"
    assert v_parts[1].start == (50.0, 50.0)
    assert v_parts[1].end == (50.0, 0.0)
    assert v_parts[1].angle_deg == -90.0


def test_one_segment_multiple_intersections():
    """One segment intersecting multiple segments splits at all intersection points."""
    h = WallSegment(id="h1", start=(0.0, 50.0), end=(100.0, 50.0))
    v1 = WallSegment(id="v1", start=(30.0, 0.0), end=(30.0, 100.0))
    v2 = WallSegment(id="v2", start=(70.0, 0.0), end=(70.0, 100.0))

    result = split_wall_intersections([h, v1, v2])
    assert len(result) == 7  # h splits into 3, v1 into 2, v2 into 2

    h_parts = [s for s in result if s.id.startswith("h1")]
    assert len(h_parts) == 3

    assert h_parts[0].start == (0.0, 50.0)
    assert h_parts[0].end == (30.0, 50.0)
    assert h_parts[0].length_px == 30.0

    assert h_parts[1].start == (30.0, 50.0)
    assert h_parts[1].end == (70.0, 50.0)
    assert h_parts[1].length_px == 40.0

    assert h_parts[2].start == (70.0, 50.0)
    assert h_parts[2].end == (100.0, 50.0)
    assert h_parts[2].length_px == 30.0


def test_multiple_walls_at_one_intersection():
    """Multiple segments crossing at the same junction normalize to identical coordinates."""
    h = WallSegment(id="h1", start=(0.0, 50.0), end=(100.0, 50.0))
    v = WallSegment(id="v1", start=(50.0, 0.0), end=(50.0, 100.0))
    d = WallSegment(id="d1", start=(0.0, 0.0), end=(100.0, 100.0))

    result = split_wall_intersections([h, v, d])
    assert len(result) == 6  # all 3 split into 2

    # Every segment meeting at the center has (50.0, 50.0) as start or end
    for s in result:
        assert (s.start == (50.0, 50.0)) or (s.end == (50.0, 50.0))


def test_duplicate_segments():
    """Identical duplicate segments are deduplicated deterministically."""
    h1 = WallSegment(id="h1", start=(0.0, 50.0), end=(100.0, 50.0))
    h2 = WallSegment(id="h2", start=(0.0, 50.0), end=(100.0, 50.0))
    v = WallSegment(id="v1", start=(50.0, 0.0), end=(50.0, 100.0))

    result = split_wall_intersections([h1, h2, v])
    # Duplicate horizontal segment is deduplicated; result has 2 h parts and 2 v parts
    assert len(result) == 4


def test_zero_length_segment():
    """Zero-length segments are filtered out safely without zero-division errors."""
    zero_seg = WallSegment(id="z1", start=(50.0, 50.0), end=(50.0, 50.0))
    h = WallSegment(id="h1", start=(0.0, 50.0), end=(100.0, 50.0))

    result = split_wall_intersections([zero_seg, h])
    assert len(result) == 1
    assert result[0].id == "h1"


def test_tiny_post_split_segments():
    """Split pieces shorter than min_segment_length_px are dropped."""
    h = WallSegment(id="h1", start=(0.0, 50.0), end=(100.0, 50.0))
    # v crosses h at x = 0.5 (piece 0..0.5 has length 0.5 < 1.0)
    v = WallSegment(id="v1", start=(0.5, 0.0), end=(0.5, 100.0))

    result = split_wall_intersections(
        [h, v],
        endpoint_tolerance_px=0.2,
        min_segment_length_px=1.0,
    )
    # The tiny piece (0, 50) -> (0.5, 50) of length 0.5 is dropped
    h_parts = [s for s in result if s.id.startswith("h1")]
    assert len(h_parts) == 1
    assert h_parts[0].start == (0.5, 50.0)
    assert h_parts[0].end == (100.0, 50.0)


def test_metadata_preservation():
    """Metadata (confidence, source, thickness, metric coords) is preserved/interpolated."""
    h = WallSegment(
        id="wall_main",
        start=(0.0, 50.0),
        end=(100.0, 50.0),
        confidence=0.88,
        source=["model", "ocr"],
        thickness_px=5.5,
        start_metric=(0.0, 1.0),
        end_metric=(10.0, 1.0),
    )
    v = WallSegment(id="wall_cross", start=(50.0, 0.0), end=(50.0, 100.0))

    result = split_wall_intersections([h, v])
    h_parts = [s for s in result if s.id.startswith("wall_main")]
    assert len(h_parts) == 2

    # Part 0
    p0 = h_parts[0]
    assert p0.id == "wall_main_part_0"
    assert p0.confidence == 0.88
    assert p0.source == ["model", "ocr"]
    assert p0.thickness_px == 5.5
    assert p0.start_metric == (0.0, 1.0)
    assert p0.end_metric == (5.0, 1.0)

    # Part 1
    p1 = h_parts[1]
    assert p1.id == "wall_main_part_1"
    assert p1.confidence == 0.88
    assert p1.source == ["model", "ocr"]
    assert p1.thickness_px == 5.5
    assert p1.start_metric == (5.0, 1.0)
    assert p1.end_metric == (10.0, 1.0)


def test_input_immutability():
    """Original WallSegment objects and source lists are never mutated."""
    src = ["initial"]
    h = WallSegment(id="h1", start=(0.0, 50.0), end=(100.0, 50.0), source=src)
    v = WallSegment(id="v1", start=(50.0, 0.0), end=(50.0, 100.0))

    input_list = [h, v]
    result = split_wall_intersections(input_list)

    assert len(input_list) == 2
    assert h.start == (0.0, 50.0)
    assert h.end == (100.0, 50.0)
    assert src == ["initial"]


def test_deterministic_output():
    """Shuffled input list produces identical result and ordering."""
    h = WallSegment(id="h1", start=(0.0, 50.0), end=(100.0, 50.0))
    v = WallSegment(id="v1", start=(50.0, 0.0), end=(50.0, 100.0))
    d = WallSegment(id="d1", start=(0.0, 0.0), end=(100.0, 100.0))

    res1 = split_wall_intersections([h, v, d])
    res2 = split_wall_intersections([d, h, v])
    res3 = split_wall_intersections([v, d, h])

    assert [(s.id, s.start, s.end) for s in res1] == [(s.id, s.start, s.end) for s in res2]
    assert [(s.id, s.start, s.end) for s in res1] == [(s.id, s.start, s.end) for s in res3]


def test_recalculation_length_and_angle():
    """Recalculated length_px and angle_deg strictly match new endpoints."""
    d1 = WallSegment(id="d1", start=(0.0, 0.0), end=(60.0, 80.0))
    d2 = WallSegment(id="d2", start=(0.0, 80.0), end=(60.0, 0.0))

    result = split_wall_intersections([d1, d2])
    for s in result:
        dx = s.end[0] - s.start[0]
        dy = s.end[1] - s.start[1]
        expected_len = round(float(math.hypot(dx, dy)), 2)
        assert abs(s.length_px - expected_len) < 0.05
        expected_angle = round(float(math.degrees(math.atan2(dy, dx))), 2)
        assert abs(s.angle_deg - expected_angle) < 0.05


def test_configurable_tolerances():
    """Tolerances effectively govern splitting vs touching vs ignoring."""
    # Near T-junction with gap 1.5px
    h = WallSegment(id="h1", start=(0.0, 50.0), end=(100.0, 50.0))
    v = WallSegment(id="v1", start=(50.0, 51.5), end=(50.0, 100.0))

    # With default intersection_tolerance_px = 1.0, gap 1.5 is NOT split
    res_default = split_wall_intersections([h, v], intersection_tolerance_px=1.0)
    assert len(res_default) == 2

    # With intersection_tolerance_px = 2.0, gap 1.5 IS split
    res_wide = split_wall_intersections([h, v], intersection_tolerance_px=2.0)
    assert len(res_wide) == 3
