"""
Unit tests for Phase 9: Room Polygonization.
"""

import math
import pytest

from app.geometry.room_polygonization import polygonize_rooms
from app.geometry.types import RoomPolygon, WallSegment


def test_empty_walls():
    """Empty walls list returns empty room list."""
    assert polygonize_rooms([]) == []


def test_single_rectangle():
    """Single rectangular room is detected correctly with 4 vertices."""
    walls = [
        WallSegment(id="w1", start=(0.0, 0.0), end=(100.0, 0.0), confidence=0.9),
        WallSegment(id="w2", start=(100.0, 0.0), end=(100.0, 60.0), confidence=0.85),
        WallSegment(id="w3", start=(100.0, 60.0), end=(0.0, 60.0), confidence=0.95),
        WallSegment(id="w4", start=(0.0, 60.0), end=(0.0, 0.0), confidence=0.9),
    ]
    rooms = polygonize_rooms(walls)
    assert len(rooms) == 1
    r = rooms[0]
    assert r.id == "room_1"
    assert len(r.polygon) == 4
    assert r.area_px2 == 6000.0
    assert r.area_m2 is None
    assert r.label is None


def test_square():
    """Square room is recognized with area L^2."""
    walls = [
        WallSegment(id="w1", start=(0.0, 0.0), end=(50.0, 0.0)),
        WallSegment(id="w2", start=(50.0, 0.0), end=(50.0, 50.0)),
        WallSegment(id="w3", start=(50.0, 50.0), end=(0.0, 50.0)),
        WallSegment(id="w4", start=(0.0, 50.0), end=(0.0, 0.0)),
    ]
    rooms = polygonize_rooms(walls)
    assert len(rooms) == 1
    assert rooms[0].area_px2 == 2500.0


def test_correct_area():
    """Area calculation matches exact mathematical area."""
    # 30 x 40 right triangle with hypotenuse
    walls = [
        WallSegment(id="w1", start=(0.0, 0.0), end=(40.0, 0.0)),
        WallSegment(id="w2", start=(40.0, 0.0), end=(0.0, 30.0)),
        WallSegment(id="w3", start=(0.0, 30.0), end=(0.0, 0.0)),
    ]
    rooms = polygonize_rooms(walls)
    assert len(rooms) == 1
    # Area = 0.5 * 40 * 30 = 600.0
    assert rooms[0].area_px2 == 600.0


def test_multiple_adjacent_rooms():
    """Two adjacent rooms sharing an interior wall produce exactly two rooms."""
    # Room 1: (0,0) to (50,50); Room 2: (50,0) to (100,50)
    walls = [
        # Outer boundary
        WallSegment(id="w_top1", start=(0.0, 50.0), end=(50.0, 50.0)),
        WallSegment(id="w_top2", start=(50.0, 50.0), end=(100.0, 50.0)),
        WallSegment(id="w_right", start=(100.0, 50.0), end=(100.0, 0.0)),
        WallSegment(id="w_bot2", start=(100.0, 0.0), end=(50.0, 0.0)),
        WallSegment(id="w_bot1", start=(50.0, 0.0), end=(0.0, 0.0)),
        WallSegment(id="w_left", start=(0.0, 0.0), end=(0.0, 50.0)),
        # Shared interior dividing wall
        WallSegment(id="w_mid", start=(50.0, 50.0), end=(50.0, 0.0)),
    ]
    rooms = polygonize_rooms(walls)
    assert len(rooms) == 2
    assert rooms[0].area_px2 == 2500.0
    assert rooms[1].area_px2 == 2500.0


def test_shared_wall():
    """Shared dividing wall is correctly associated with both adjacent rooms."""
    walls = [
        WallSegment(id="w1", start=(0.0, 50.0), end=(50.0, 50.0), source=["srcA"]),
        WallSegment(id="w2", start=(50.0, 50.0), end=(100.0, 50.0), source=["srcA"]),
        WallSegment(id="w3", start=(100.0, 50.0), end=(100.0, 0.0), source=["srcA"]),
        WallSegment(id="w4", start=(100.0, 0.0), end=(50.0, 0.0), source=["srcA"]),
        WallSegment(id="w5", start=(50.0, 0.0), end=(0.0, 0.0), source=["srcA"]),
        WallSegment(id="w6", start=(0.0, 0.0), end=(0.0, 50.0), source=["srcA"]),
        WallSegment(id="w_shared", start=(50.0, 50.0), end=(50.0, 0.0), source=["srcShared"]),
    ]
    rooms = polygonize_rooms(walls)
    assert len(rooms) == 2
    # Both rooms contain srcShared from the dividing wall
    assert "srcShared" in rooms[0].source
    assert "srcShared" in rooms[1].source


def test_disconnected_rooms():
    """Separated rooms without shared walls are both identified."""
    # Room 1 at (0, 0)
    r1_walls = [
        WallSegment(id="r1_1", start=(0.0, 0.0), end=(50.0, 0.0)),
        WallSegment(id="r1_2", start=(50.0, 0.0), end=(50.0, 50.0)),
        WallSegment(id="r1_3", start=(50.0, 50.0), end=(0.0, 50.0)),
        WallSegment(id="r1_4", start=(0.0, 50.0), end=(0.0, 0.0)),
    ]
    # Room 2 far away at (200, 200)
    r2_walls = [
        WallSegment(id="r2_1", start=(200.0, 200.0), end=(260.0, 200.0)),
        WallSegment(id="r2_2", start=(260.0, 200.0), end=(260.0, 260.0)),
        WallSegment(id="r2_3", start=(260.0, 260.0), end=(200.0, 260.0)),
        WallSegment(id="r2_4", start=(200.0, 260.0), end=(200.0, 200.0)),
    ]
    rooms = polygonize_rooms(r1_walls + r2_walls)
    assert len(rooms) == 2
    assert {r.area_px2 for r in rooms} == {2500.0, 3600.0}


def test_open_wall_chain_rejected():
    """Open U-shaped wall chain missing one side produces no rooms."""
    open_walls = [
        WallSegment(id="w1", start=(0.0, 0.0), end=(50.0, 0.0)),
        WallSegment(id="w2", start=(50.0, 0.0), end=(50.0, 50.0)),
        WallSegment(id="w3", start=(50.0, 50.0), end=(0.0, 50.0)),
        # Missing w4 from (0, 50) to (0, 0)
    ]
    assert polygonize_rooms(open_walls) == []


def test_degenerate_geometry_rejected():
    """Collinear walls or zero-area polygons produce no rooms."""
    collinear = [
        WallSegment(id="w1", start=(0.0, 0.0), end=(50.0, 0.0)),
        WallSegment(id="w2", start=(50.0, 0.0), end=(100.0, 0.0)),
        WallSegment(id="w3", start=(100.0, 0.0), end=(0.0, 0.0)),
    ]
    assert polygonize_rooms(collinear) == []


def test_tiny_polygon_rejected():
    """Polygon with area smaller than min_area_px2 is rejected."""
    # 3x3 box = 9 px^2 < min_area_px2 (25.0)
    tiny_box = [
        WallSegment(id="w1", start=(0.0, 0.0), end=(3.0, 0.0)),
        WallSegment(id="w2", start=(3.0, 0.0), end=(3.0, 3.0)),
        WallSegment(id="w3", start=(3.0, 3.0), end=(0.0, 3.0)),
        WallSegment(id="w4", start=(0.0, 3.0), end=(0.0, 0.0)),
    ]
    assert polygonize_rooms(tiny_box, min_area_px2=25.0) == []


def test_non_manhattan_valid_polygon():
    """Irregular non-Manhattan polygon is polygonized correctly."""
    # Trapezoid: (0,0) -> (100,0) -> (70, 50) -> (30, 50) -> (0,0)
    walls = [
        WallSegment(id="w1", start=(0.0, 0.0), end=(100.0, 0.0)),
        WallSegment(id="w2", start=(100.0, 0.0), end=(70.0, 50.0)),
        WallSegment(id="w3", start=(70.0, 50.0), end=(30.0, 50.0)),
        WallSegment(id="w4", start=(30.0, 50.0), end=(0.0, 0.0)),
    ]
    rooms = polygonize_rooms(walls)
    assert len(rooms) == 1
    # Area = 0.5 * (100 + 40) * 50 = 3500.0
    assert rooms[0].area_px2 == 3500.0


def test_deterministic_output():
    """Identical input yields identical output regardless of input list permutation."""
    walls = [
        WallSegment(id="w1", start=(0.0, 0.0), end=(50.0, 0.0)),
        WallSegment(id="w2", start=(50.0, 0.0), end=(50.0, 50.0)),
        WallSegment(id="w3", start=(50.0, 50.0), end=(0.0, 50.0)),
        WallSegment(id="w4", start=(0.0, 50.0), end=(0.0, 0.0)),
    ]
    r1 = polygonize_rooms(walls)
    r2 = polygonize_rooms(list(reversed(walls)))
    assert [(r.id, r.area_px2, r.polygon) for r in r1] == [(r.id, r.area_px2, r.polygon) for r in r2]


def test_deterministic_ids():
    """IDs follow sequential room_1, room_2 naming deterministically."""
    walls = [
        WallSegment(id="w1", start=(0.0, 50.0), end=(50.0, 50.0)),
        WallSegment(id="w2", start=(50.0, 50.0), end=(100.0, 50.0)),
        WallSegment(id="w3", start=(100.0, 50.0), end=(100.0, 0.0)),
        WallSegment(id="w4", start=(100.0, 0.0), end=(50.0, 0.0)),
        WallSegment(id="w5", start=(50.0, 0.0), end=(0.0, 0.0)),
        WallSegment(id="w6", start=(0.0, 0.0), end=(0.0, 50.0)),
        WallSegment(id="w7", start=(50.0, 50.0), end=(50.0, 0.0)),
    ]
    rooms = polygonize_rooms(walls)
    assert [r.id for r in rooms] == ["room_1", "room_2"]


def test_no_duplicate_rooms():
    """Duplicate wall segments do not duplicate room outputs."""
    walls = [
        WallSegment(id="w1", start=(0.0, 0.0), end=(50.0, 0.0)),
        WallSegment(id="w1_dup", start=(0.0, 0.0), end=(50.0, 0.0)),
        WallSegment(id="w2", start=(50.0, 0.0), end=(50.0, 50.0)),
        WallSegment(id="w3", start=(50.0, 50.0), end=(0.0, 50.0)),
        WallSegment(id="w4", start=(0.0, 50.0), end=(0.0, 0.0)),
    ]
    rooms = polygonize_rooms(walls)
    assert len(rooms) == 1


def test_outer_face_not_returned():
    """The outer unbounded face is never returned as a room polygon."""
    walls = [
        WallSegment(id="w1", start=(0.0, 0.0), end=(100.0, 0.0)),
        WallSegment(id="w2", start=(100.0, 0.0), end=(100.0, 100.0)),
        WallSegment(id="w3", start=(100.0, 100.0), end=(0.0, 100.0)),
        WallSegment(id="w4", start=(0.0, 100.0), end=(0.0, 0.0)),
    ]
    rooms = polygonize_rooms(walls)
    # Returns exactly 1 enclosed room, not 2 (inner + outer)
    assert len(rooms) == 1


def test_input_immutability():
    """Input wall objects and coordinates are not mutated."""
    w1 = WallSegment(id="w1", start=(0.0, 0.0), end=(50.0, 0.0))
    w2 = WallSegment(id="w2", start=(50.0, 0.0), end=(50.0, 50.0))
    w3 = WallSegment(id="w3", start=(50.0, 50.0), end=(0.0, 50.0))
    w4 = WallSegment(id="w4", start=(0.0, 50.0), end=(0.0, 0.0))
    input_walls = [w1, w2, w3, w4]

    polygonize_rooms(input_walls)
    assert w1.start == (0.0, 0.0)
    assert w1.end == (50.0, 0.0)
    assert len(input_walls) == 4


def test_returned_room_objects_are_new_instances():
    """Returned RoomPolygon objects are newly instantiated."""
    walls = [
        WallSegment(id="w1", start=(0.0, 0.0), end=(50.0, 0.0)),
        WallSegment(id="w2", start=(50.0, 0.0), end=(50.0, 50.0)),
        WallSegment(id="w3", start=(50.0, 50.0), end=(0.0, 50.0)),
        WallSegment(id="w4", start=(0.0, 50.0), end=(0.0, 0.0)),
    ]
    r1 = polygonize_rooms(walls)[0]
    r2 = polygonize_rooms(walls)[0]
    assert r1 is not r2


def test_area_m2_remains_none():
    """area_m2 remains None pending metric calibration."""
    walls = [
        WallSegment(id="w1", start=(0.0, 0.0), end=(50.0, 0.0)),
        WallSegment(id="w2", start=(50.0, 0.0), end=(50.0, 50.0)),
        WallSegment(id="w3", start=(50.0, 50.0), end=(0.0, 50.0)),
        WallSegment(id="w4", start=(0.0, 50.0), end=(0.0, 0.0)),
    ]
    rooms = polygonize_rooms(walls)
    assert rooms[0].area_m2 is None


def test_label_remains_none():
    """label remains None without semantic guessing."""
    walls = [
        WallSegment(id="w1", start=(0.0, 0.0), end=(50.0, 0.0)),
        WallSegment(id="w2", start=(50.0, 0.0), end=(50.0, 50.0)),
        WallSegment(id="w3", start=(50.0, 50.0), end=(0.0, 50.0)),
        WallSegment(id="w4", start=(0.0, 50.0), end=(0.0, 0.0)),
    ]
    rooms = polygonize_rooms(walls)
    assert rooms[0].label is None


def test_confidence_and_source_handling():
    """Confidence takes conservative minimum and source combines contributing wall sources."""
    walls = [
        WallSegment(id="w1", start=(0.0, 0.0), end=(50.0, 0.0), confidence=0.9, source=["model"]),
        WallSegment(id="w2", start=(50.0, 0.0), end=(50.0, 50.0), confidence=0.75, source=["ocr"]),
        WallSegment(id="w3", start=(50.0, 50.0), end=(0.0, 50.0), confidence=0.85, source=["model"]),
        WallSegment(id="w4", start=(0.0, 50.0), end=(0.0, 0.0), confidence=0.95, source=["heuristic"]),
    ]
    rooms = polygonize_rooms(walls)
    assert len(rooms) == 1
    assert rooms[0].confidence == 0.75  # min(0.9, 0.75, 0.85, 0.95)
    assert set(rooms[0].source) == {"model", "ocr", "heuristic"}


def test_t_junction_room_layout():
    """T-junction dividing wall correctly generates two separate rooms."""
    # Outer box (0,0) to (100,50) with interior T-divider at x=50
    walls = [
        WallSegment(id="w_top", start=(0.0, 50.0), end=(100.0, 50.0)),
        WallSegment(id="w_bot", start=(0.0, 0.0), end=(100.0, 0.0)),
        WallSegment(id="w_left", start=(0.0, 0.0), end=(0.0, 50.0)),
        WallSegment(id="w_right", start=(100.0, 0.0), end=(100.0, 50.0)),
        WallSegment(id="w_mid", start=(50.0, 0.0), end=(50.0, 50.0)),
    ]
    rooms = polygonize_rooms(walls)
    assert len(rooms) == 2
    assert rooms[0].area_px2 == 2500.0
    assert rooms[1].area_px2 == 2500.0


def test_repeated_identical_input():
    """Repeated calls produce identical room outputs."""
    walls = [
        WallSegment(id="w1", start=(0.0, 0.0), end=(50.0, 0.0)),
        WallSegment(id="w2", start=(50.0, 0.0), end=(50.0, 50.0)),
        WallSegment(id="w3", start=(50.0, 50.0), end=(0.0, 50.0)),
        WallSegment(id="w4", start=(0.0, 50.0), end=(0.0, 0.0)),
    ]
    res1 = polygonize_rooms(walls)
    res2 = polygonize_rooms(walls)
    assert [(r.id, r.area_px2, r.polygon) for r in res1] == [(r.id, r.area_px2, r.polygon) for r in res2]
