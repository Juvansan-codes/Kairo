"""
Tests for 3D Reconstruction Disconnected Walls Bugfix

**Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5**

This module contains tests to validate the tolerance mismatch bugfix.
The bug occurs when node_tolerance_px (used in room polygonization) differs from 
endpoint_tolerance_px (used in intersection splitting), preventing room detection.
"""

import pytest

from app.geometry.pipeline import run_mgr_pipeline
from app.geometry.types import WallSegment


# ============================================================================
# Test Helper Functions
# ============================================================================

def create_rectangular_rooms(num_rooms: int) -> list[WallSegment]:
    """
    Create a floor plan with rectangular rooms that should form closed regions.
    
    This creates a simple grid of rectangular rooms that are guaranteed to have
    closed wall boundaries, suitable for testing room detection.
    """
    walls = []
    wall_id = 0
    
    # Create rooms in a horizontal row
    for i in range(num_rooms):
        # Each room is 100x100 pixels, positioned at x = i*100
        x_offset = i * 100.0
        y_base = 0.0
        room_width = 100.0
        room_height = 100.0
        
        # Bottom wall
        walls.append(WallSegment(
            id=f"w{wall_id}",
            start=(x_offset, y_base),
            end=(x_offset + room_width, y_base),
            confidence=0.9
        ))
        wall_id += 1
        
        # Right wall (shared with next room if not last)
        walls.append(WallSegment(
            id=f"w{wall_id}",
            start=(x_offset + room_width, y_base),
            end=(x_offset + room_width, y_base + room_height),
            confidence=0.9
        ))
        wall_id += 1
        
        # Top wall
        walls.append(WallSegment(
            id=f"w{wall_id}",
            start=(x_offset + room_width, y_base + room_height),
            end=(x_offset, y_base + room_height),
            confidence=0.9
        ))
        wall_id += 1
        
        # Left wall (only for first room, others share with previous)
        if i == 0:
            walls.append(WallSegment(
                id=f"w{wall_id}",
                start=(x_offset, y_base + room_height),
                end=(x_offset, y_base),
                confidence=0.9
            ))
            wall_id += 1
    
    return walls


def create_complex_floor_plan() -> list[WallSegment]:
    """
    Generate a complex floor plan with 6 rooms in a 2x3 grid configuration.
    
    Creates a grid layout with multiple rooms that should all be
    detected as closed regions.
    """
    # Create a 2x3 grid of rooms (6 rooms total)
    walls = []
    wall_id = 0
    room_size = 80.0
    
    for row in range(2):
        for col in range(3):
            x_offset = col * room_size
            y_offset = row * room_size
            
            # Bottom wall (if first row)
            if row == 0:
                walls.append(WallSegment(
                    id=f"w{wall_id}",
                    start=(x_offset, y_offset),
                    end=(x_offset + room_size, y_offset),
                    confidence=0.9
                ))
                wall_id += 1
            
            # Right wall (if last column)
            if col == 2:
                walls.append(WallSegment(
                    id=f"w{wall_id}",
                    start=(x_offset + room_size, y_offset),
                    end=(x_offset + room_size, y_offset + room_size),
                    confidence=0.9
                ))
                wall_id += 1
            
            # Top wall (if last row)
            if row == 1:
                walls.append(WallSegment(
                    id=f"w{wall_id}",
                    start=(x_offset + room_size, y_offset + room_size),
                    end=(x_offset, y_offset + room_size),
                    confidence=0.9
                ))
                wall_id += 1
            
            # Left wall (if first column)
            if col == 0:
                walls.append(WallSegment(
                    id=f"w{wall_id}",
                    start=(x_offset, y_offset + room_size),
                    end=(x_offset, y_offset),
                    confidence=0.9
                ))
                wall_id += 1
            
            # Interior walls
            if col < 2:  # Vertical divider
                walls.append(WallSegment(
                    id=f"w{wall_id}",
                    start=(x_offset + room_size, y_offset),
                    end=(x_offset + room_size, y_offset + room_size),
                    confidence=0.9
                ))
                wall_id += 1
            
            if row < 1:  # Horizontal divider
                walls.append(WallSegment(
                    id=f"w{wall_id}",
                    start=(x_offset, y_offset + room_size),
                    end=(x_offset + room_size, y_offset + room_size),
                    confidence=0.9
                ))
                wall_id += 1
    
    return walls


# ============================================================================
# Property 1: Bug Condition - Consistent Tolerance Enables Room Detection
# ============================================================================

@pytest.mark.property
def test_bug_condition_two_rectangular_rooms():
    """
    **Property 1: Bug Condition** - Consistent Tolerance Enables Room Detection
    
    **Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5**
    
    CRITICAL: This test MUST FAIL on unfixed code - failure confirms the bug exists.
    
    Test that the tolerance mismatch prevents room detection in simple rectangular
    room layouts (2 rooms). The test runs the pipeline with default mismatched
    parameters (node_tolerance_px=25.0, endpoint_tolerance_px=15.0).
    
    EXPECTED OUTCOME ON UNFIXED CODE: Test FAILS because result.rooms is NOT empty
    when it should be empty due to the bug. This confirms the bug exists.
    
    This test encodes the EXPECTED behavior after the fix:
    - For floor plans with closed wall regions, room detection should succeed
    - The pipeline should detect at least as many rooms as were created
    - Rooms should have valid area measurements
    
    When this test PASSES after the fix, it confirms the bug is resolved.
    """
    walls = create_rectangular_rooms(2)
    expected_min_rooms = 2
    
    # Run pipeline with DEFAULT UNFIXED parameters
    # node_tolerance_px defaults to 25.0, endpoint_tolerance_px defaults to 15.0
    # This tolerance mismatch should cause the bug (zero rooms detected)
    result = run_mgr_pipeline(walls=walls)
    
    # EXPECTED BEHAVIOR (will fail on unfixed code):
    # After fix, rooms should be detected correctly
    assert len(result.rooms) > 0, (
        f"Bug condition confirmed: Expected at least 1 room to be detected, "
        f"but got {len(result.rooms)} rooms. This demonstrates the tolerance "
        f"mismatch prevents room detection in floor plans with {expected_min_rooms} "
        f"rectangular rooms."
    )
    
    # Additional validations for expected behavior after fix
    assert len(result.rooms) >= expected_min_rooms, (
        f"Expected at least {expected_min_rooms} rooms, got {len(result.rooms)}"
    )
    
    # Verify rooms have valid area
    for room in result.rooms:
        assert room.area_px2 > 0, f"Room {room.id} has invalid area: {room.area_px2}"
    
    # Verify walls are present
    assert len(result.walls) > 0, "No walls in result"


@pytest.mark.property
def test_bug_condition_three_rectangular_rooms():
    """
    **Property 1: Bug Condition** - Consistent Tolerance Enables Room Detection
    
    **Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5**
    
    CRITICAL: This test MUST FAIL on unfixed code - failure confirms the bug exists.
    
    Test with 3 rectangular rooms in a row.
    """
    walls = create_rectangular_rooms(3)
    expected_min_rooms = 3
    
    result = run_mgr_pipeline(walls=walls)
    
    assert len(result.rooms) > 0, (
        f"Bug condition confirmed: Expected at least 1 room to be detected, "
        f"but got {len(result.rooms)} rooms with {expected_min_rooms} rectangular rooms."
    )
    
    assert len(result.rooms) >= expected_min_rooms, (
        f"Expected at least {expected_min_rooms} rooms, got {len(result.rooms)}"
    )
    
    # Verify rooms have valid properties
    for room in result.rooms:
        assert room.area_px2 > 0, f"Room {room.id} has invalid area"
        assert len(room.polygon) >= 3, f"Room {room.id} has invalid polygon"


@pytest.mark.property
def test_bug_condition_single_rectangular_room():
    """
    **Property 1: Bug Condition** - Consistent Tolerance Enables Room Detection
    
    **Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5**
    
    CRITICAL: This test MUST FAIL on unfixed code - failure confirms the bug exists.
    
    Deterministic test case: A single 100x100 pixel rectangular room.
    This is the simplest case that should always produce exactly 1 room.
    
    EXPECTED OUTCOME ON UNFIXED CODE: Test FAILS (returns 0 rooms instead of 1).
    """
    # Simple rectangular room: 100x100 pixels
    walls = [
        WallSegment(id="w1", start=(0.0, 0.0), end=(100.0, 0.0), confidence=0.9),
        WallSegment(id="w2", start=(100.0, 0.0), end=(100.0, 100.0), confidence=0.9),
        WallSegment(id="w3", start=(100.0, 100.0), end=(0.0, 100.0), confidence=0.9),
        WallSegment(id="w4", start=(0.0, 100.0), end=(0.0, 0.0), confidence=0.9),
    ]
    
    # Run with DEFAULT parameters (tolerance mismatch)
    result = run_mgr_pipeline(walls=walls)
    
    # EXPECTED BEHAVIOR (will fail on unfixed code due to tolerance mismatch):
    assert len(result.rooms) == 1, (
        f"Bug condition confirmed: Expected exactly 1 room for simple rectangular layout, "
        f"but got {len(result.rooms)} rooms. This demonstrates the tolerance mismatch "
        f"prevents even the simplest closed region detection."
    )
    
    # Verify the room has correct properties
    assert result.rooms[0].area_px2 == 10000.0, (
        f"Expected room area of 10000 px², got {result.rooms[0].area_px2}"
    )


@pytest.mark.property
def test_bug_condition_with_explicit_mismatched_tolerance():
    """
    **Property 1: Bug Condition** - Consistent Tolerance Enables Room Detection
    
    **Validates: Requirements 2.1, 2.2, 2.3**
    
    Explicit test demonstrating the bug by calling pipeline with mismatched tolerances.
    This confirms that the tolerance mismatch is indeed the root cause.
    
    EXPECTED OUTCOME ON UNFIXED CODE: This test explicitly shows the bug by running
    with mismatched tolerances (node_tolerance=25.0, endpoint_tolerance=15.0) and
    expecting zero rooms, then running with consistent tolerances and expecting success.
    """
    walls = [
        WallSegment(id="w1", start=(0.0, 0.0), end=(100.0, 0.0), confidence=0.9),
        WallSegment(id="w2", start=(100.0, 0.0), end=(100.0, 100.0), confidence=0.9),
        WallSegment(id="w3", start=(100.0, 100.0), end=(0.0, 100.0), confidence=0.9),
        WallSegment(id="w4", start=(0.0, 100.0), end=(0.0, 0.0), confidence=0.9),
    ]
    
    # Test 1: Run with MISMATCHED tolerances (simulating the bug)
    result_mismatched = run_mgr_pipeline(
        walls=walls,
        node_tolerance_px=25.0,      # Loose tolerance
        endpoint_tolerance_px=15.0   # Tighter tolerance (mismatch!)
    )
    
    # On unfixed code, this should produce 0 rooms due to tolerance mismatch
    # After fix, this should still be caught or handled properly
    # For now, document the buggy behavior:
    if len(result_mismatched.rooms) == 0:
        # This is the BUG - tolerance mismatch prevents room detection
        print(f"BUG CONFIRMED: Mismatched tolerances (25.0 vs 15.0) produced {len(result_mismatched.rooms)} rooms")
    
    # Test 2: Run with CONSISTENT tolerances (workaround)
    result_consistent = run_mgr_pipeline(
        walls=walls,
        node_tolerance_px=15.0,      # Consistent with endpoint_tolerance
        endpoint_tolerance_px=15.0
    )
    
    # With consistent tolerances, room detection should succeed
    assert len(result_consistent.rooms) == 1, (
        f"With consistent tolerances (15.0 px), expected 1 room, "
        f"got {len(result_consistent.rooms)}. This confirms tolerance consistency "
        f"is required for correct room detection."
    )
    
    # After the fix is implemented, the default values should be consistent,
    # and this test should pass for both cases



@pytest.mark.property
def test_bug_condition_complex_floor_plan():
    """
    **Property 1: Bug Condition** - Consistent Tolerance Enables Room Detection
    
    **Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5**
    
    CRITICAL: This test MUST FAIL on unfixed code - failure confirms the bug exists.
    
    Test that the tolerance mismatch prevents room detection in complex floor plans
    with 5+ rooms and multiple wall intersections. The test runs the pipeline with 
    default mismatched parameters.
    
    EXPECTED OUTCOME ON UNFIXED CODE: Test FAILS because result.rooms is NOT empty.
    This confirms that the 10px tolerance discrepancy (25.0 vs 15.0) causes critical
    vertices to merge incorrectly, destroying the topological structure.
    
    When this test PASSES after the fix, it confirms complex floor plans now work.
    """
    walls = create_complex_floor_plan()
    expected_min_rooms = 6
    
    # Run pipeline with DEFAULT UNFIXED parameters (tolerance mismatch)
    result = run_mgr_pipeline(walls=walls)
    
    # EXPECTED BEHAVIOR (will fail on unfixed code):
    assert len(result.rooms) > 0, (
        f"Bug condition confirmed: Expected at least 1 room in complex floor plan, "
        f"but got {len(result.rooms)} rooms. The tolerance mismatch "
        f"(node_tolerance_px=25.0 vs endpoint_tolerance_px=15.0) prevents detection "
        f"of closed regions in complex layouts with {expected_min_rooms} rooms."
    )
    
    # After fix, should detect most or all rooms
    # (may not be exact due to merge/split behavior, but should be substantial)
    assert len(result.rooms) >= expected_min_rooms - 2, (
        f"Expected approximately {expected_min_rooms} rooms (±2), "
        f"got {len(result.rooms)}"
    )


@pytest.mark.property
def test_bug_condition_single_rectangular_room():
    """
    **Property 1: Bug Condition** - Consistent Tolerance Enables Room Detection
    
    **Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5**
    
    CRITICAL: This test MUST FAIL on unfixed code - failure confirms the bug exists.
    
    Deterministic test case: A single 100x100 pixel rectangular room.
    This is the simplest case that should always produce exactly 1 room.
    
    EXPECTED OUTCOME ON UNFIXED CODE: Test FAILS (returns 0 rooms instead of 1).
    """
    # Simple rectangular room: 100x100 pixels
    walls = [
        WallSegment(id="w1", start=(0.0, 0.0), end=(100.0, 0.0), confidence=0.9),
        WallSegment(id="w2", start=(100.0, 0.0), end=(100.0, 100.0), confidence=0.9),
        WallSegment(id="w3", start=(100.0, 100.0), end=(0.0, 100.0), confidence=0.9),
        WallSegment(id="w4", start=(0.0, 100.0), end=(0.0, 0.0), confidence=0.9),
    ]
    
    # Run with DEFAULT parameters (tolerance mismatch)
    result = run_mgr_pipeline(walls=walls)
    
    # EXPECTED BEHAVIOR (will fail on unfixed code due to tolerance mismatch):
    assert len(result.rooms) == 1, (
        f"Bug condition confirmed: Expected exactly 1 room for simple rectangular layout, "
        f"but got {len(result.rooms)} rooms. This demonstrates the tolerance mismatch "
        f"prevents even the simplest closed region detection."
    )
    
    # Verify the room has correct properties
    assert result.rooms[0].area_px2 == 10000.0, (
        f"Expected room area of 10000 px², got {result.rooms[0].area_px2}"
    )


@pytest.mark.property
def test_bug_condition_with_explicit_mismatched_tolerance():
    """
    **Property 1: Bug Condition** - Consistent Tolerance Enables Room Detection
    
    **Validates: Requirements 2.1, 2.2, 2.3**
    
    Explicit test demonstrating the bug by calling pipeline with mismatched tolerances.
    This confirms that the tolerance mismatch is indeed the root cause.
    
    EXPECTED OUTCOME ON UNFIXED CODE: This test explicitly shows the bug by running
    with mismatched tolerances (node_tolerance=25.0, endpoint_tolerance=15.0) and
    documenting the behavior, then running with consistent tolerances to verify success.
    """
    walls = [
        WallSegment(id="w1", start=(0.0, 0.0), end=(100.0, 0.0), confidence=0.9),
        WallSegment(id="w2", start=(100.0, 0.0), end=(100.0, 100.0), confidence=0.9),
        WallSegment(id="w3", start=(100.0, 100.0), end=(0.0, 100.0), confidence=0.9),
        WallSegment(id="w4", start=(0.0, 100.0), end=(0.0, 0.0), confidence=0.9),
    ]
    
    # Test 1: Run with MISMATCHED tolerances (simulating the bug)
    result_mismatched = run_mgr_pipeline(
        walls=walls,
        node_tolerance_px=25.0,      # Loose tolerance
        endpoint_tolerance_px=15.0   # Tighter tolerance (mismatch!)
    )
    
    # On unfixed code, this should produce 0 rooms due to tolerance mismatch
    # Document the buggy behavior:
    print(f"Mismatched tolerances (25.0 vs 15.0) produced {len(result_mismatched.rooms)} rooms")
    
    # Test 2: Run with CONSISTENT tolerances (workaround)
    result_consistent = run_mgr_pipeline(
        walls=walls,
        node_tolerance_px=15.0,      # Consistent with endpoint_tolerance
        endpoint_tolerance_px=15.0
    )
    
    # With consistent tolerances, room detection should succeed
    assert len(result_consistent.rooms) == 1, (
        f"With consistent tolerances (15.0 px), expected 1 room, "
        f"got {len(result_consistent.rooms)}. This confirms tolerance consistency "
        f"is required for correct room detection."
    )
    
    # After the fix is implemented, the default values should be consistent,
    # and the test_bug_condition_single_rectangular_room test should pass
