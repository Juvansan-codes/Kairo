"""
Unit tests for Phase 8: Door/Window Reconciliation.
"""

import math
import pytest

from app.geometry.openings import reconcile_openings
from app.geometry.types import Opening, WallSegment


def test_empty_openings():
    """Empty openings list returns empty list."""
    wall = WallSegment(id="w1", start=(0.0, 50.0), end=(100.0, 50.0))
    assert reconcile_openings([], [wall]) == []


def test_empty_walls():
    """Empty walls list leaves all openings unassigned (wall_id=None)."""
    op = Opening(id="d1", type="door", start=(20.0, 50.0), end=(40.0, 50.0))
    result = reconcile_openings([op], [])
    assert len(result) == 1
    assert result[0].id == "d1"
    assert result[0].wall_id is None
    assert result[0].start == (20.0, 50.0)
    assert result[0].end == (40.0, 50.0)


def test_opening_exactly_on_horizontal_wall():
    """Opening lying exactly on horizontal wall is matched and projected."""
    wall = WallSegment(id="w1", start=(0.0, 50.0), end=(100.0, 50.0))
    op = Opening(id="d1", type="door", start=(20.0, 50.0), end=(40.0, 50.0), confidence=0.95)

    result = reconcile_openings([op], [wall])
    assert len(result) == 1
    out = result[0]
    assert out.id == "d1"
    assert out.type == "door"
    assert out.wall_id == "w1"
    assert out.start == (20.0, 50.0)
    assert out.end == (40.0, 50.0)
    assert out.confidence == 0.95


def test_opening_exactly_on_vertical_wall():
    """Opening lying exactly on vertical wall is matched and projected."""
    wall = WallSegment(id="w1", start=(50.0, 0.0), end=(50.0, 100.0))
    op = Opening(id="w_open", type="window", start=(50.0, 30.0), end=(50.0, 60.0))

    result = reconcile_openings([op], [wall])
    assert len(result) == 1
    out = result[0]
    assert out.id == "w_open"
    assert out.type == "window"
    assert out.wall_id == "w1"
    assert out.start == (50.0, 30.0)
    assert out.end == (50.0, 60.0)


def test_opening_slightly_offset_from_horizontal_wall():
    """Opening with perpendicular offset <= tolerance is snapped to the wall."""
    wall = WallSegment(id="w1", start=(0.0, 50.0), end=(100.0, 50.0))
    # Offset by 2px in y (tolerance default is 5.0px)
    op = Opening(id="d1", type="door", start=(20.0, 52.0), end=(40.0, 52.0))

    result = reconcile_openings([op], [wall])
    assert len(result) == 1
    out = result[0]
    assert out.wall_id == "w1"
    assert out.start == (20.0, 50.0)
    assert out.end == (40.0, 50.0)


def test_opening_slightly_offset_from_vertical_wall():
    """Opening with perpendicular offset <= tolerance is snapped to vertical wall."""
    wall = WallSegment(id="w1", start=(50.0, 0.0), end=(50.0, 100.0))
    # Offset by 2px in x
    op = Opening(id="win1", type="window", start=(48.0, 20.0), end=(48.0, 45.0))

    result = reconcile_openings([op], [wall])
    assert len(result) == 1
    out = result[0]
    assert out.wall_id == "w1"
    assert out.start == (50.0, 20.0)
    assert out.end == (50.0, 45.0)


def test_diagonal_wall():
    """Opening along a diagonal wall projects correctly onto the wall line."""
    wall = WallSegment(id="w_diag", start=(0.0, 0.0), end=(100.0, 100.0))
    # Opening points close to (20, 20) and (40, 40)
    op = Opening(id="d_diag", type="door", start=(19.0, 21.0), end=(39.0, 41.0))

    result = reconcile_openings([op], [wall])
    assert len(result) == 1
    out = result[0]
    assert out.wall_id == "w_diag"
    assert out.start == (20.0, 20.0)
    assert out.end == (40.0, 40.0)


def test_reversed_opening_endpoints():
    """Reversed opening endpoints are normalized along the wall direction."""
    wall = WallSegment(id="w1", start=(0.0, 50.0), end=(100.0, 50.0))
    # Opening specified backwards: from x=40 to x=20
    op = Opening(id="d1", type="door", start=(40.0, 50.0), end=(20.0, 50.0))

    result = reconcile_openings([op], [wall])
    assert len(result) == 1
    out = result[0]
    assert out.wall_id == "w1"
    # Canonical ordering: smaller parameter t comes first (x=20 before x=40)
    assert out.start == (20.0, 50.0)
    assert out.end == (40.0, 50.0)


def test_reversed_wall_endpoints():
    """Reversed wall endpoints normalize opening along the wall's canonical direction."""
    # Wall goes right-to-left: start at x=100, end at x=0
    wall = WallSegment(id="w_rev", start=(100.0, 50.0), end=(0.0, 50.0))
    op = Opening(id="d1", type="door", start=(20.0, 50.0), end=(40.0, 50.0))

    result = reconcile_openings([op], [wall])
    assert len(result) == 1
    out = result[0]
    assert out.wall_id == "w_rev"
    # Smaller wall parameter along (100 -> 0) is at x=40 (t=0.60), then x=20 (t=0.80)
    assert out.start == (40.0, 50.0)
    assert out.end == (20.0, 50.0)


def test_opening_too_far_from_wall_remains_unassigned():
    """Opening exceeding wall_distance_tolerance_px remains unassigned."""
    wall = WallSegment(id="w1", start=(0.0, 50.0), end=(100.0, 50.0))
    # Offset by 15px (tolerance is 5px)
    op = Opening(id="d_far", type="door", start=(20.0, 65.0), end=(40.0, 65.0))

    result = reconcile_openings([op], [wall], wall_distance_tolerance_px=5.0)
    assert len(result) == 1
    assert result[0].wall_id is None
    assert result[0].start == (20.0, 65.0)
    assert result[0].end == (40.0, 65.0)


def test_opening_beyond_wall_endpoint_is_rejected():
    """Opening entirely beyond wall endpoint is rejected."""
    wall = WallSegment(id="w1", start=(0.0, 50.0), end=(100.0, 50.0))
    # Opening is at x in [110, 130], 10px beyond wall endpoint (tolerance is 3px)
    op = Opening(id="d_beyond", type="door", start=(110.0, 50.0), end=(130.0, 50.0))

    result = reconcile_openings([op], [wall], projection_tolerance_px=3.0)
    assert len(result) == 1
    assert result[0].wall_id is None


def test_opening_slightly_beyond_endpoint_within_tolerance_matches():
    """Opening slightly extending past wall endpoint within tolerance can match."""
    wall = WallSegment(id="w1", start=(0.0, 50.0), end=(100.0, 50.0))
    # Extends 2px beyond wall endpoint x=100 (projection_tolerance_px is 3.0)
    op = Opening(id="d_edge", type="door", start=(80.0, 51.0), end=(102.0, 51.0))

    result = reconcile_openings([op], [wall], projection_tolerance_px=3.0)
    assert len(result) == 1
    assert result[0].wall_id == "w1"
    assert result[0].start == (80.0, 50.0)
    assert result[0].end == (102.0, 50.0)


def test_multiple_openings_on_same_wall():
    """Multiple openings (door and window) on the same wall are both reconciled."""
    wall = WallSegment(id="w1", start=(0.0, 50.0), end=(200.0, 50.0))
    door = Opening(id="d1", type="door", start=(20.0, 51.0), end=(50.0, 51.0))
    win = Opening(id="w_open", type="window", start=(120.0, 49.0), end=(160.0, 49.0))

    result = reconcile_openings([door, win], [wall])
    assert len(result) == 2
    assert result[0].id == "d1"
    assert result[0].wall_id == "w1"
    assert result[0].start == (20.0, 50.0)
    assert result[0].end == (50.0, 50.0)

    assert result[1].id == "w_open"
    assert result[1].wall_id == "w1"
    assert result[1].start == (120.0, 50.0)
    assert result[1].end == (160.0, 50.0)


def test_multiple_candidate_walls_chooses_nearest():
    """When multiple walls are nearby, the nearest wall is selected."""
    # Wall 1 at y=50 (distance 2px to opening at y=48)
    w1 = WallSegment(id="w_near", start=(0.0, 50.0), end=(100.0, 50.0))
    # Wall 2 at y=44 (distance 4px to opening at y=48)
    w2 = WallSegment(id="w_far", start=(0.0, 44.0), end=(100.0, 44.0))

    op = Opening(id="d1", type="door", start=(20.0, 48.0), end=(50.0, 48.0))

    result = reconcile_openings([op], [w2, w1])
    assert len(result) == 1
    assert result[0].wall_id == "w_near"
    assert result[0].start == (20.0, 50.0)
    assert result[0].end == (50.0, 50.0)


def test_deterministic_tie_breaking_by_wall_id():
    """Equidistant walls tie-break deterministically by lexicographical wall.id."""
    # Opening at y=50 is exactly 2px away from w_a (y=52) and w_b (y=48)
    w_a = WallSegment(id="wall_A", start=(0.0, 52.0), end=(100.0, 52.0))
    w_b = WallSegment(id="wall_B", start=(0.0, 48.0), end=(100.0, 48.0))

    op = Opening(id="d1", type="door", start=(20.0, 50.0), end=(50.0, 50.0))

    result1 = reconcile_openings([op], [w_b, w_a])
    result2 = reconcile_openings([op], [w_a, w_b])

    assert result1[0].wall_id == "wall_A"
    assert result2[0].wall_id == "wall_A"


def test_duplicate_opening_handling():
    """Duplicate openings with identical id and geometry are deduplicated."""
    wall = WallSegment(id="w1", start=(0.0, 50.0), end=(100.0, 50.0))
    op1 = Opening(id="d1", type="door", start=(20.0, 50.0), end=(40.0, 50.0))
    op2 = Opening(id="d1", type="door", start=(20.0, 50.0), end=(40.0, 50.0))

    result = reconcile_openings([op1, op2], [wall])
    assert len(result) == 1
    assert result[0].id == "d1"


def test_zero_length_opening_safety():
    """Zero-length opening is handled safely without crashing."""
    wall = WallSegment(id="w1", start=(0.0, 50.0), end=(100.0, 50.0))
    zero_op = Opening(id="z1", type="door", start=(30.0, 51.0), end=(30.0, 51.0))

    result = reconcile_openings([zero_op], [wall])
    assert len(result) == 1
    assert result[0].wall_id == "w1"
    assert result[0].start == (30.0, 50.0)
    assert result[0].end == (30.0, 50.0)


def test_tiny_or_zero_length_wall_safety():
    """Degenerate zero-length walls do not cause division by zero or errors."""
    zero_wall = WallSegment(id="w_zero", start=(50.0, 50.0), end=(50.0, 50.0))
    normal_wall = WallSegment(id="w_normal", start=(0.0, 50.0), end=(100.0, 50.0))

    op = Opening(id="d1", type="door", start=(20.0, 50.0), end=(40.0, 50.0))

    result = reconcile_openings([op], [zero_wall, normal_wall])
    assert len(result) == 1
    assert result[0].wall_id == "w_normal"


def test_metadata_preservation():
    """Opening metadata (id, type, confidence, source) is strictly preserved."""
    wall = WallSegment(id="w1", start=(0.0, 50.0), end=(100.0, 50.0))
    op = Opening(
        id="door_custom",
        type="door",
        start=(20.0, 50.0),
        end=(40.0, 50.0),
        confidence=0.88,
        source=["detection_model", "ocr_evidence"],
    )

    result = reconcile_openings([op], [wall])
    out = result[0]
    assert out.id == "door_custom"
    assert out.type == "door"
    assert out.confidence == 0.88
    assert out.source == ["detection_model", "ocr_evidence"]


def test_source_list_is_copied():
    """Source list is copied so mutating the original does not alter output."""
    wall = WallSegment(id="w1", start=(0.0, 50.0), end=(100.0, 50.0))
    src = ["initial"]
    op = Opening(id="d1", type="door", start=(20.0, 50.0), end=(40.0, 50.0), source=src)

    result = reconcile_openings([op], [wall])
    out = result[0]
    assert out.source is not src

    src.append("modified_afterwards")
    assert out.source == ["initial"]


def test_input_immutability():
    """Input Opening and WallSegment objects are not mutated."""
    wall = WallSegment(id="w1", start=(0.0, 50.0), end=(100.0, 50.0))
    op = Opening(id="d1", type="door", start=(20.0, 52.0), end=(40.0, 52.0))

    result = reconcile_openings([op], [wall])
    assert op.start == (20.0, 52.0)
    assert op.end == (40.0, 52.0)
    assert op.wall_id is None
    assert wall.start == (0.0, 50.0)


def test_projected_coordinates_are_deterministic_and_rounded():
    """Projected coordinates are consistently rounded to 2 decimal places."""
    wall = WallSegment(id="w1", start=(0.0, 33.3333), end=(100.0, 33.3333))
    op = Opening(id="d1", type="door", start=(10.1111, 35.0), end=(40.9999, 35.0))

    result = reconcile_openings([op], [wall])
    out = result[0]
    assert out.start == (10.11, 33.33)
    assert out.end == (41.0, 33.33)


def test_returned_objects_are_new_instances():
    """All returned Opening objects are new instances."""
    wall = WallSegment(id="w1", start=(0.0, 50.0), end=(100.0, 50.0))
    op1 = Opening(id="d1", type="door", start=(20.0, 50.0), end=(40.0, 50.0))
    op2 = Opening(id="d2", type="door", start=(20.0, 80.0), end=(40.0, 80.0))  # far away

    result = reconcile_openings([op1, op2], [wall])
    assert len(result) == 2
    assert result[0] is not op1
    assert result[1] is not op2
