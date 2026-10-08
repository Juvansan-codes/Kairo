"""
Unit and integration tests for Phase 12: MGR Pipeline Orchestration.
"""

import math
import numpy as np
import pytest

from app.geometry.pipeline import run_mgr_pipeline
from app.geometry.types import (
    DimensionEvidence,
    MGRResult,
    Opening,
    RoomPolygon,
    WallSegment,
)


def _create_synthetic_box_mask(size: int = 100, wall_thickness: int = 5) -> np.ndarray:
    """Create a synthetic binary mask with a square room box."""
    mask = np.zeros((size, size), dtype=bool)
    # Top and bottom walls
    mask[10 : 10 + wall_thickness, 10:90] = True
    mask[90 - wall_thickness : 90, 10:90] = True
    # Left and right walls
    mask[10:90, 10 : 10 + wall_thickness] = True
    mask[10:90, 90 - wall_thickness : 90] = True
    return mask


def test_empty_input_returns_empty_mgr_result():
    """Empty inputs produce an empty MGRResult safely without error."""
    result = run_mgr_pipeline()
    assert isinstance(result, MGRResult)
    assert result.walls == []
    assert result.rooms == []
    assert result.doors == []
    assert result.windows == []
    assert result.scale_mm_per_px is None
    assert result.confidence["overall"] == 0.0


def test_pipeline_from_wall_mask():
    """End-to-end pipeline run starting from a raw binary wall mask."""
    mask = _create_synthetic_box_mask(100, 5)
    result = run_mgr_pipeline(wall_mask=mask)

    assert isinstance(result, MGRResult)
    assert len(result.walls) >= 4
    assert len(result.rooms) == 1
    assert result.rooms[0].area_px2 > 4000.0
    assert result.scale_mm_per_px is None
    assert result.rooms[0].area_m2 is None


def test_pipeline_from_pre_extracted_walls():
    """Pipeline operates directly on supplied WallSegments without skeletonization."""
    walls = [
        WallSegment(id="w1", start=(0.0, 0.0), end=(100.0, 0.0), confidence=0.9),
        WallSegment(id="w2", start=(100.0, 0.0), end=(100.0, 100.0), confidence=0.9),
        WallSegment(id="w3", start=(100.0, 100.0), end=(0.0, 100.0), confidence=0.9),
        WallSegment(id="w4", start=(0.0, 100.0), end=(0.0, 0.0), confidence=0.9),
    ]
    result = run_mgr_pipeline(walls=walls)
    assert len(result.walls) == 4
    assert len(result.rooms) == 1
    assert result.rooms[0].area_px2 == 10000.0


def test_wall_cleanup_ordering():
    """Wall cleanup applies snapping, collinear merging, and intersection splitting."""
    # Near-horizontal walls that should snap and merge, and a cross wall that splits them
    walls = [
        # Collinear parts with slight angle deviation (1.0 degree)
        WallSegment(id="w1a", start=(0.0, 50.5), end=(49.0, 50.5)),
        WallSegment(id="w1b", start=(51.0, 50.5), end=(100.0, 50.5)),
        # Crossing vertical wall
        WallSegment(id="w2", start=(50.0, 0.0), end=(50.0, 100.0)),
    ]
    result = run_mgr_pipeline(walls=walls)
    # w1a and w1b snap to y=50.5, merge, and split with w2 at (50, 50.5)
    assert len(result.walls) >= 4


def test_opening_reconciliation_for_doors():
    """Doors are reconciled, snapped to supporting walls, and assigned wall_id."""
    walls = [
        WallSegment(id="w1", start=(0.0, 0.0), end=(100.0, 0.0)),
        WallSegment(id="w2", start=(100.0, 0.0), end=(100.0, 100.0)),
        WallSegment(id="w3", start=(100.0, 100.0), end=(0.0, 100.0)),
        WallSegment(id="w4", start=(0.0, 100.0), end=(0.0, 0.0)),
    ]
    # Door slightly offset by 2px from w1
    doors = [
        Opening(id="d1", type="door", start=(20.0, 2.0), end=(50.0, 2.0))
    ]
    result = run_mgr_pipeline(walls=walls, doors=doors)
    assert len(result.doors) == 1
    assert result.doors[0].wall_id == "w1"
    assert result.doors[0].start == (20.0, 0.0)
    assert result.doors[0].end == (50.0, 0.0)


def test_opening_reconciliation_for_windows():
    """Windows are reconciled against wall geometry separately from doors."""
    walls = [
        WallSegment(id="w1", start=(0.0, 0.0), end=(100.0, 0.0)),
        WallSegment(id="w2", start=(100.0, 0.0), end=(100.0, 100.0)),
        WallSegment(id="w3", start=(100.0, 100.0), end=(0.0, 100.0)),
        WallSegment(id="w4", start=(0.0, 100.0), end=(0.0, 0.0)),
    ]
    windows = [
        Opening(id="win1", type="window", start=(102.0, 20.0), end=(102.0, 60.0))
    ]
    result = run_mgr_pipeline(walls=walls, windows=windows)
    assert len(result.windows) == 1
    assert result.windows[0].wall_id == "w2"
    assert result.windows[0].start == (100.0, 20.0)
    assert result.windows[0].end == (100.0, 60.0)


def test_room_polygonization_integration():
    """Enclosed room regions are correctly extracted from wall network."""
    walls = [
        WallSegment(id="w1", start=(0.0, 0.0), end=(80.0, 0.0)),
        WallSegment(id="w2", start=(80.0, 0.0), end=(80.0, 80.0)),
        WallSegment(id="w3", start=(80.0, 80.0), end=(0.0, 80.0)),
        WallSegment(id="w4", start=(0.0, 80.0), end=(0.0, 0.0)),
    ]
    result = run_mgr_pipeline(walls=walls)
    assert len(result.rooms) == 1
    assert result.rooms[0].area_px2 == 6400.0


def test_metric_calibration_integration():
    """Valid DimensionEvidence estimates scale and calibrates wall metric coordinates."""
    walls = [
        WallSegment(id="w1", start=(0.0, 0.0), end=(100.0, 0.0)),
        WallSegment(id="w2", start=(100.0, 0.0), end=(100.0, 100.0)),
        WallSegment(id="w3", start=(100.0, 100.0), end=(0.0, 100.0)),
        WallSegment(id="w4", start=(0.0, 100.0), end=(0.0, 0.0)),
    ]
    # 100px represents 2000mm -> scale = 20.0 mm/px
    dims = [
        DimensionEvidence(id="d1", value_mm=2000.0, start_px=(0.0, 0.0), end_px=(100.0, 0.0), confidence=0.95)
    ]
    result = run_mgr_pipeline(walls=walls, dimensions=dims)
    assert result.scale_mm_per_px == 20.0
    # Walls have start_metric and end_metric populated
    w1_cal = next(w for w in result.walls if w.id == "w1")
    assert w1_cal.start_metric == (0.0, 0.0)
    assert w1_cal.end_metric == (2000.0, 0.0)


def test_uncalibrated_pipeline():
    """When dimensions are absent, scale and metric coordinates remain None."""
    walls = [
        WallSegment(id="w1", start=(0.0, 0.0), end=(50.0, 0.0)),
        WallSegment(id="w2", start=(50.0, 0.0), end=(50.0, 50.0)),
        WallSegment(id="w3", start=(50.0, 50.0), end=(0.0, 50.0)),
        WallSegment(id="w4", start=(0.0, 50.0), end=(0.0, 0.0)),
    ]
    result = run_mgr_pipeline(walls=walls)
    assert result.scale_mm_per_px is None
    for w in result.walls:
        assert w.start_metric is None
        assert w.end_metric is None
    for r in result.rooms:
        assert r.area_m2 is None


def test_room_area_m2_calculation():
    """Calibrated scale properly calculates room area in square meters."""
    # 100px x 100px = 10,000 px^2
    # scale = 20 mm/px -> 100px = 2000mm = 2m -> Area = 2m * 2m = 4.0 m^2
    walls = [
        WallSegment(id="w1", start=(0.0, 0.0), end=(100.0, 0.0)),
        WallSegment(id="w2", start=(100.0, 0.0), end=(100.0, 100.0)),
        WallSegment(id="w3", start=(100.0, 100.0), end=(0.0, 100.0)),
        WallSegment(id="w4", start=(0.0, 100.0), end=(0.0, 0.0)),
    ]
    dims = [
        DimensionEvidence(id="d1", value_mm=2000.0, start_px=(0.0, 0.0), end_px=(100.0, 0.0), confidence=0.9)
    ]
    result = run_mgr_pipeline(walls=walls, dimensions=dims)
    assert result.scale_mm_per_px == 20.0
    assert len(result.rooms) == 1
    assert result.rooms[0].area_px2 == 10000.0
    assert result.rooms[0].area_m2 == 4.0


def test_topology_validation_integration():
    """Topology validation runs and populates validation summary in result."""
    walls = [
        WallSegment(id="w1", start=(0.0, 0.0), end=(100.0, 0.0)),
        WallSegment(id="w2", start=(100.0, 0.0), end=(100.0, 100.0)),
        WallSegment(id="w3", start=(100.0, 100.0), end=(0.0, 100.0)),
        WallSegment(id="w4", start=(0.0, 100.0), end=(0.0, 0.0)),
    ]
    doors = [
        Opening(id="d1", type="door", start=(20.0, 0.0), end=(50.0, 0.0), wall_id="w1")
    ]
    result = run_mgr_pipeline(walls=walls, doors=doors)
    assert result.confidence["topology_valid"] is True
    assert result.provenance["topology_stats"]["wall_count"] == 4
    assert result.provenance["topology_stats"]["dangling_endpoint_count"] == 0


def test_confidence_and_provenance_output():
    """Confidence dictionary and provenance follow schema specifications."""
    walls = [
        WallSegment(id="w1", start=(0.0, 0.0), end=(100.0, 0.0), confidence=0.8),
        WallSegment(id="w2", start=(100.0, 0.0), end=(100.0, 100.0), confidence=0.8),
        WallSegment(id="w3", start=(100.0, 100.0), end=(0.0, 100.0), confidence=0.8),
        WallSegment(id="w4", start=(0.0, 100.0), end=(0.0, 0.0), confidence=0.8),
    ]
    dims = [
        DimensionEvidence(id="d1", value_mm=2000.0, start_px=(0.0, 0.0), end_px=(100.0, 0.0), confidence=0.9)
    ]
    result = run_mgr_pipeline(walls=walls, dimensions=dims)
    assert "overall" in result.confidence
    assert "geometry" in result.confidence
    assert "scale" in result.confidence
    assert result.confidence["scale"] == 1.0
    assert result.provenance["source"] == "MGR"
    assert result.provenance["method"] == "deterministic_geometric_reconciliation"


def test_deterministic_output():
    """Repeated calls with identical inputs yield identical MGRResult."""
    walls = [
        WallSegment(id="w1", start=(0.0, 0.0), end=(50.0, 0.0)),
        WallSegment(id="w2", start=(50.0, 0.0), end=(50.0, 50.0)),
        WallSegment(id="w3", start=(50.0, 50.0), end=(0.0, 50.0)),
        WallSegment(id="w4", start=(0.0, 50.0), end=(0.0, 0.0)),
    ]
    res1 = run_mgr_pipeline(walls=walls)
    res2 = run_mgr_pipeline(walls=walls)
    assert len(res1.walls) == len(res2.walls)
    assert [(r.id, r.area_px2) for r in res1.rooms] == [(r.id, r.area_px2) for r in res2.rooms]


def test_input_immutability():
    """Input wall and opening objects are not mutated."""
    w1 = WallSegment(id="w1", start=(0.0, 0.0), end=(100.0, 0.0))
    d1 = Opening(id="d1", type="door", start=(20.0, 2.0), end=(50.0, 2.0))
    dim1 = DimensionEvidence(id="dim1", value_mm=2000.0, start_px=(0.0, 0.0), end_px=(100.0, 0.0))

    walls = [w1]
    doors = [d1]
    dims = [dim1]

    run_mgr_pipeline(walls=walls, doors=doors, dimensions=dims)
    assert w1.start == (0.0, 0.0)
    assert w1.start_metric is None
    assert d1.start == (20.0, 2.0)
    assert d1.wall_id is None
    assert dim1.value_mm == 2000.0


def test_custom_tolerance_propagation():
    """Custom tolerances alter behavior as expected."""
    # Box with 16 px^2 area (4x4)
    walls = [
        WallSegment(id="w1", start=(0.0, 0.0), end=(4.0, 0.0)),
        WallSegment(id="w2", start=(4.0, 0.0), end=(4.0, 4.0)),
        WallSegment(id="w3", start=(4.0, 4.0), end=(0.0, 4.0)),
        WallSegment(id="w4", start=(0.0, 4.0), end=(0.0, 0.0)),
    ]
    # Default min_room_area_px2=25 rejects 16 px^2 room
    res_default = run_mgr_pipeline(walls=walls, node_tolerance_px=1.0)
    assert len(res_default.rooms) == 0

    # Custom min_room_area_px2=10 accepts 16 px^2 room
    res_custom = run_mgr_pipeline(walls=walls, min_room_area_px2=10.0, node_tolerance_px=1.0)
    assert len(res_custom.rooms) == 1
    assert res_custom.rooms[0].area_px2 == 16.0


def test_multiple_connected_rooms():
    """Two adjacent rooms with shared dividing wall produce 2 rooms."""
    walls = [
        WallSegment(id="w_top1", start=(0.0, 50.0), end=(50.0, 50.0)),
        WallSegment(id="w_top2", start=(50.0, 50.0), end=(100.0, 50.0)),
        WallSegment(id="w_right", start=(100.0, 50.0), end=(100.0, 0.0)),
        WallSegment(id="w_bot2", start=(100.0, 0.0), end=(50.0, 0.0)),
        WallSegment(id="w_bot1", start=(50.0, 0.0), end=(0.0, 0.0)),
        WallSegment(id="w_left", start=(0.0, 0.0), end=(0.0, 50.0)),
        WallSegment(id="w_mid", start=(50.0, 50.0), end=(50.0, 0.0)),
    ]
    result = run_mgr_pipeline(walls=walls)
    assert len(result.rooms) == 2


def test_shared_wall_rooms():
    """Shared dividing wall is preserved and correctly connects rooms."""
    walls = [
        WallSegment(id="w_top1", start=(0.0, 50.0), end=(50.0, 50.0)),
        WallSegment(id="w_top2", start=(50.0, 50.0), end=(100.0, 50.0)),
        WallSegment(id="w_right", start=(100.0, 50.0), end=(100.0, 0.0)),
        WallSegment(id="w_bot2", start=(100.0, 0.0), end=(50.0, 0.0)),
        WallSegment(id="w_bot1", start=(50.0, 0.0), end=(0.0, 0.0)),
        WallSegment(id="w_left", start=(0.0, 0.0), end=(0.0, 50.0)),
        WallSegment(id="w_mid", start=(50.0, 50.0), end=(50.0, 0.0)),
    ]
    doors = [
        Opening(id="d_int", type="door", start=(50.0, 10.0), end=(50.0, 30.0))
    ]
    result = run_mgr_pipeline(walls=walls, doors=doors)
    assert len(result.doors) == 1
    assert result.doors[0].wall_id == "w_mid"


def test_no_room_open_geometry():
    """Open wall geometry produces 0 rooms and records topology warnings."""
    walls = [
        WallSegment(id="w1", start=(0.0, 0.0), end=(50.0, 0.0)),
        WallSegment(id="w2", start=(50.0, 0.0), end=(50.0, 50.0)),
        WallSegment(id="w3", start=(50.0, 50.0), end=(0.0, 50.0)),
    ]
    result = run_mgr_pipeline(walls=walls)
    assert len(result.rooms) == 0
    assert any("dangling" in a.lower() for a in result.assumptions)


def test_missing_optional_evidence():
    """Optional evidence (doors, windows, dimensions) omitted runs cleanly."""
    walls = [
        WallSegment(id="w1", start=(0.0, 0.0), end=(50.0, 0.0)),
        WallSegment(id="w2", start=(50.0, 0.0), end=(50.0, 50.0)),
        WallSegment(id="w3", start=(50.0, 50.0), end=(0.0, 50.0)),
        WallSegment(id="w4", start=(0.0, 50.0), end=(0.0, 0.0)),
    ]
    result = run_mgr_pipeline(walls=walls, doors=None, windows=None, dimensions=None)
    assert len(result.walls) == 4
    assert len(result.rooms) == 1
    assert result.doors == []
    assert result.windows == []
    assert result.scale_mm_per_px is None


def test_invalid_empty_dimension_evidence():
    """Invalid dimension evidence is safely rejected without halting pipeline."""
    walls = [
        WallSegment(id="w1", start=(0.0, 0.0), end=(50.0, 0.0)),
        WallSegment(id="w2", start=(50.0, 0.0), end=(50.0, 50.0)),
        WallSegment(id="w3", start=(50.0, 50.0), end=(0.0, 50.0)),
        WallSegment(id="w4", start=(0.0, 50.0), end=(0.0, 0.0)),
    ]
    bad_dims = [
        DimensionEvidence(id="bad1", value_mm=-100.0, start_px=(0.0, 0.0), end_px=(50.0, 0.0)),
        DimensionEvidence(id="bad2", value_mm=1000.0, start_px=(0.0, 0.0), end_px=(0.0, 0.0)),
    ]
    result = run_mgr_pipeline(walls=walls, dimensions=bad_dims)
    assert result.scale_mm_per_px is None
    assert len(result.walls) == 4
    assert len(result.rooms) == 1
