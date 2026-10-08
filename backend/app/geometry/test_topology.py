"""
Unit tests for Phase 11: Topology Validation.
"""

import pytest

from app.geometry.topology import validate_topology
from app.geometry.types import Opening, RoomPolygon, WallSegment


def test_completely_valid_simple_floorplan():
    """A clean 4-wall box with 1 room, 1 door, and 1 window passes validation."""
    walls = [
        WallSegment(id="w1", start=(0.0, 0.0), end=(100.0, 0.0)),
        WallSegment(id="w2", start=(100.0, 0.0), end=(100.0, 100.0)),
        WallSegment(id="w3", start=(100.0, 100.0), end=(0.0, 100.0)),
        WallSegment(id="w4", start=(0.0, 100.0), end=(0.0, 0.0)),
    ]
    rooms = [
        RoomPolygon(id="r1", polygon=[(0.0, 0.0), (100.0, 0.0), (100.0, 100.0), (0.0, 100.0)], area_px2=10000.0)
    ]
    doors = [
        Opening(id="d1", type="door", start=(20.0, 0.0), end=(50.0, 0.0), wall_id="w1")
    ]
    windows = [
        Opening(id="win1", type="window", start=(20.0, 100.0), end=(60.0, 100.0), wall_id="w3")
    ]

    result = validate_topology(walls, rooms, doors, windows)
    assert result["valid"] is True
    assert result["errors"] == []
    assert result["stats"]["wall_count"] == 4
    assert result["stats"]["room_count"] == 1
    assert result["stats"]["door_count"] == 1
    assert result["stats"]["window_count"] == 1
    assert result["stats"]["connected_components"] == 1
    assert result["stats"]["dangling_endpoint_count"] == 0


def test_empty_inputs():
    """Empty inputs produce valid result with all 0 stats."""
    result = validate_topology([], [], [], [])
    assert result["valid"] is True
    assert result["errors"] == []
    assert result["warnings"] == []
    assert result["stats"]["wall_count"] == 0
    assert result["stats"]["room_count"] == 0


def test_duplicate_wall_ids():
    """Duplicate wall IDs flag an error and set valid=False."""
    walls = [
        WallSegment(id="w1", start=(0.0, 0.0), end=(100.0, 0.0)),
        WallSegment(id="w1", start=(100.0, 0.0), end=(100.0, 100.0)),  # Duplicate ID
    ]
    result = validate_topology(walls, [], [], [])
    assert result["valid"] is False
    assert any("Duplicate wall ID 'w1'" in err for err in result["errors"])


def test_zero_length_wall():
    """Zero-length wall flags an error."""
    walls = [
        WallSegment(id="w_zero", start=(50.0, 50.0), end=(50.0, 50.0))
    ]
    result = validate_topology(walls, [], [], [])
    assert result["valid"] is False
    assert any("zero length" in err for err in result["errors"])


def test_tiny_wall():
    """Tiny sub-pixel wall (<1.0px) flags an error."""
    walls = [
        WallSegment(id="w_tiny", start=(0.0, 0.0), end=(0.5, 0.0))
    ]
    result = validate_topology(walls, [], [], [])
    assert result["valid"] is False
    assert any("tiny length" in err for err in result["errors"])


def test_duplicate_room_ids():
    """Duplicate room IDs flag an error."""
    rooms = [
        RoomPolygon(id="r1", polygon=[(0.0, 0.0), (10.0, 0.0), (10.0, 10.0)], area_px2=50.0),
        RoomPolygon(id="r1", polygon=[(20.0, 20.0), (30.0, 20.0), (30.0, 30.0)], area_px2=50.0),
    ]
    result = validate_topology([], rooms, [], [])
    assert result["valid"] is False
    assert any("Duplicate room ID 'r1'" in err for err in result["errors"])


def test_invalid_degenerate_room():
    """Room with fewer than 3 vertices or self-intersecting polygon flags an error."""
    rooms = [
        RoomPolygon(id="r_bad", polygon=[(0.0, 0.0), (10.0, 10.0)], area_px2=10.0)  # Only 2 vertices
    ]
    result = validate_topology([], rooms, [], [])
    assert result["valid"] is False
    assert any("fewer than 3 vertices" in err for err in result["errors"])


def test_zero_area_room():
    """Room with reported zero or negative area flags an error."""
    rooms = [
        RoomPolygon(id="r_zero", polygon=[(0.0, 0.0), (10.0, 0.0), (20.0, 0.0)], area_px2=0.0)
    ]
    result = validate_topology([], rooms, [], [])
    assert result["valid"] is False
    assert any("non-positive area" in err for err in result["errors"])


def test_duplicate_door_ids():
    """Duplicate door IDs flag an error."""
    doors = [
        Opening(id="d1", type="door", start=(0.0, 0.0), end=(10.0, 0.0)),
        Opening(id="d1", type="door", start=(20.0, 0.0), end=(30.0, 0.0)),
    ]
    result = validate_topology([], [], doors, [])
    assert result["valid"] is False
    assert any("Duplicate door ID 'd1'" in err for err in result["errors"])


def test_duplicate_window_ids():
    """Duplicate window IDs flag an error."""
    windows = [
        Opening(id="win1", type="window", start=(0.0, 0.0), end=(10.0, 0.0)),
        Opening(id="win1", type="window", start=(20.0, 0.0), end=(30.0, 0.0)),
    ]
    result = validate_topology([], [], [], windows)
    assert result["valid"] is False
    assert any("Duplicate window ID 'win1'" in err for err in result["errors"])


def test_door_references_missing_wall():
    """Door referencing a non-existent wall ID flags an error."""
    walls = [WallSegment(id="w1", start=(0.0, 0.0), end=(50.0, 0.0))]
    doors = [Opening(id="d1", type="door", start=(10.0, 0.0), end=(20.0, 0.0), wall_id="w_missing")]
    result = validate_topology(walls, [], doors, [])
    assert result["valid"] is False
    assert any("Door 'd1' references missing wall 'w_missing'" in err for err in result["errors"])


def test_window_references_missing_wall():
    """Window referencing a non-existent wall ID flags an error."""
    walls = [WallSegment(id="w1", start=(0.0, 0.0), end=(50.0, 0.0))]
    windows = [Opening(id="win1", type="window", start=(10.0, 0.0), end=(20.0, 0.0), wall_id="w_missing")]
    result = validate_topology(walls, [], [], windows)
    assert result["valid"] is False
    assert any("Window 'win1' references missing wall 'w_missing'" in err for err in result["errors"])


def test_zero_length_opening():
    """Opening with start == end flags an error."""
    doors = [Opening(id="d1", type="door", start=(10.0, 0.0), end=(10.0, 0.0))]
    result = validate_topology([], [], doors, [])
    assert result["valid"] is False
    assert any("zero length" in err for err in result["errors"])


def test_disconnected_wall_components():
    """Disconnected wall sets generate a warning but do not invalidate valid walls."""
    # Box 1
    w_b1 = [
        WallSegment(id="b1_1", start=(0.0, 0.0), end=(50.0, 0.0)),
        WallSegment(id="b1_2", start=(50.0, 0.0), end=(50.0, 50.0)),
        WallSegment(id="b1_3", start=(50.0, 50.0), end=(0.0, 50.0)),
        WallSegment(id="b1_4", start=(0.0, 50.0), end=(0.0, 0.0)),
    ]
    # Box 2 (disconnected)
    w_b2 = [
        WallSegment(id="b2_1", start=(200.0, 200.0), end=(250.0, 200.0)),
        WallSegment(id="b2_2", start=(250.0, 200.0), end=(250.0, 250.0)),
        WallSegment(id="b2_3", start=(250.0, 250.0), end=(200.0, 250.0)),
        WallSegment(id="b2_4", start=(200.0, 250.0), end=(200.0, 200.0)),
    ]
    result = validate_topology(w_b1 + w_b2, [], [], [])
    assert result["valid"] is True
    assert result["errors"] == []
    assert result["stats"]["connected_components"] == 2
    assert any("2 disconnected components" in w for w in result["warnings"])


def test_dangling_wall_endpoint():
    """Open dead-end wall produces a dangling endpoint warning."""
    # Closed box plus a dead-end spur
    walls = [
        WallSegment(id="w1", start=(0.0, 0.0), end=(50.0, 0.0)),
        WallSegment(id="w2", start=(50.0, 0.0), end=(50.0, 50.0)),
        WallSegment(id="w3", start=(50.0, 50.0), end=(0.0, 50.0)),
        WallSegment(id="w4", start=(0.0, 50.0), end=(0.0, 0.0)),
        # Dangling wall extending out from (50, 50) to (80, 50)
        WallSegment(id="w_spur", start=(50.0, 50.0), end=(80.0, 50.0)),
    ]
    result = validate_topology(walls, [], [], [])
    assert result["valid"] is True
    assert result["stats"]["dangling_endpoint_count"] == 1
    assert any("dangling wall endpoint" in w for w in result["warnings"])


def test_isolated_wall():
    """Single detached wall generates an isolated wall warning."""
    walls = [
        WallSegment(id="w_iso", start=(10.0, 10.0), end=(50.0, 10.0))
    ]
    result = validate_topology(walls, [], [], [])
    assert result["valid"] is True
    assert result["stats"]["connected_components"] == 1
    assert result["stats"]["dangling_endpoint_count"] == 2
    assert any("isolated wall segment" in w.lower() for w in result["warnings"])


def test_valid_multiple_connected_rooms():
    """Two connected rooms with shared dividing wall validate cleanly."""
    walls = [
        WallSegment(id="w_top1", start=(0.0, 50.0), end=(50.0, 50.0)),
        WallSegment(id="w_top2", start=(50.0, 50.0), end=(100.0, 50.0)),
        WallSegment(id="w_right", start=(100.0, 50.0), end=(100.0, 0.0)),
        WallSegment(id="w_bot2", start=(100.0, 0.0), end=(50.0, 0.0)),
        WallSegment(id="w_bot1", start=(50.0, 0.0), end=(0.0, 0.0)),
        WallSegment(id="w_left", start=(0.0, 0.0), end=(0.0, 50.0)),
        WallSegment(id="w_mid", start=(50.0, 50.0), end=(50.0, 0.0)),
    ]
    rooms = [
        RoomPolygon(id="r1", polygon=[(0.0, 0.0), (50.0, 0.0), (50.0, 50.0), (0.0, 50.0)], area_px2=2500.0),
        RoomPolygon(id="r2", polygon=[(50.0, 0.0), (100.0, 0.0), (100.0, 50.0), (50.0, 50.0)], area_px2=2500.0),
    ]
    doors = [
        Opening(id="d1", type="door", start=(10.0, 0.0), end=(30.0, 0.0), wall_id="w_bot1")
    ]
    result = validate_topology(walls, rooms, doors, [])
    assert result["valid"] is True
    assert result["errors"] == []
    assert result["stats"]["room_count"] == 2
    assert result["stats"]["dangling_endpoint_count"] == 0


def test_mixed_valid_and_invalid_entities():
    """Floorplan with valid rooms but invalid door references correctly flags valid=False."""
    walls = [WallSegment(id="w1", start=(0.0, 0.0), end=(50.0, 0.0))]
    rooms = [RoomPolygon(id="r1", polygon=[(0.0, 0.0), (50.0, 0.0), (50.0, 50.0)], area_px2=1250.0)]
    doors = [Opening(id="d_bad", type="door", start=(0.0, 0.0), end=(10.0, 0.0), wall_id="w_ghost")]

    result = validate_topology(walls, rooms, doors, [])
    assert result["valid"] is False
    assert any("w_ghost" in err for err in result["errors"])


def test_deterministic_output():
    """Validation output is completely deterministic and stable across executions."""
    walls = [
        WallSegment(id="w1", start=(0.0, 0.0), end=(100.0, 0.0)),
        WallSegment(id="w2", start=(100.0, 0.0), end=(100.0, 100.0)),
    ]
    doors = [
        Opening(id="d_bad", type="door", start=(0.0, 0.0), end=(10.0, 0.0), wall_id="w_missing")
    ]
    res1 = validate_topology(walls, [], doors, [])
    res2 = validate_topology(walls, [], doors, [])
    assert res1 == res2


def test_no_input_mutation():
    """Inputs are strictly read-only and never mutated."""
    w = WallSegment(id="w1", start=(0.0, 0.0), end=(50.0, 0.0))
    r = RoomPolygon(id="r1", polygon=[(0.0, 0.0), (10.0, 0.0), (10.0, 10.0)], area_px2=50.0)
    d = Opening(id="d1", type="door", start=(10.0, 0.0), end=(20.0, 0.0), wall_id="w1")

    walls = [w]
    rooms = [r]
    doors = [d]

    validate_topology(walls, rooms, doors, [])
    assert w.start == (0.0, 0.0)
    assert w.end == (50.0, 0.0)
    assert len(walls) == 1
    assert len(rooms) == 1
    assert len(doors) == 1
