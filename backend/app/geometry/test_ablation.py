"""
Unit and integration tests for Phase 13: Ablation Support.
"""

from __future__ import annotations

import math
import numpy as np
import pytest

from app.geometry.ablation import (
    AblationConfig,
    AblationMetrics,
    AblationResult,
    compare_ablations,
    compute_ablation_metrics,
    run_mgr_ablation,
)
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
    mask[10 : 10 + wall_thickness, 10:90] = True
    mask[90 - wall_thickness : 90, 10:90] = True
    mask[10:90, 10 : 10 + wall_thickness] = True
    mask[10:90, 90 - wall_thickness : 90] = True
    return mask


def _make_box_walls(size: float = 100.0) -> list[WallSegment]:
    """Helper creating 4 orthogonal wall segments forming a square room."""
    return [
        WallSegment(id="w_top", start=(0.0, 0.0), end=(size, 0.0), length_px=size, angle_deg=0.0, confidence=0.9),
        WallSegment(id="w_right", start=(size, 0.0), end=(size, size), length_px=size, angle_deg=90.0, confidence=0.9),
        WallSegment(id="w_bottom", start=(size, size), end=(0.0, size), length_px=size, angle_deg=180.0, confidence=0.9),
        WallSegment(id="w_left", start=(0.0, size), end=(0.0, 0.0), length_px=size, angle_deg=270.0, confidence=0.9),
    ]


# -----------------------------------------------------------------------------
# 1. AblationConfig Tests
# -----------------------------------------------------------------------------

def test_ablation_config_full():
    """AblationConfig.full() has all 6 stages enabled."""
    cfg = AblationConfig.full()
    assert cfg.snapping is True
    assert cfg.collinear_merging is True
    assert cfg.intersection_splitting is True
    assert cfg.opening_reconciliation is True
    assert cfg.room_polygonization is True
    assert cfg.metric_calibration is True


def test_ablation_config_baseline():
    """AblationConfig.baseline() has all 6 stages disabled."""
    cfg = AblationConfig.baseline()
    assert cfg.snapping is False
    assert cfg.collinear_merging is False
    assert cfg.intersection_splitting is False
    assert cfg.opening_reconciliation is False
    assert cfg.room_polygonization is False
    assert cfg.metric_calibration is False


def test_ablation_config_without():
    """without() returns a new config with only the specified stage turned off."""
    orig = AblationConfig.full()
    new_cfg = orig.without("snapping")

    assert orig.snapping is True  # immutability of original
    assert new_cfg.snapping is False
    assert new_cfg.collinear_merging is True
    assert new_cfg.intersection_splitting is True
    assert new_cfg.opening_reconciliation is True
    assert new_cfg.room_polygonization is True
    assert new_cfg.metric_calibration is True


def test_ablation_config_only():
    """only() returns a new config where only the named stages are enabled."""
    cfg = AblationConfig.only("snapping", "metric_calibration")
    assert cfg.snapping is True
    assert cfg.metric_calibration is True
    assert cfg.collinear_merging is False
    assert cfg.intersection_splitting is False
    assert cfg.opening_reconciliation is False
    assert cfg.room_polygonization is False


def test_ablation_config_invalid_stage_names():
    """Invalid stage names in without() or only() raise ValueError."""
    cfg = AblationConfig.full()
    with pytest.raises(ValueError, match="Unknown stage"):
        cfg.without("invalid_stage")

    with pytest.raises(ValueError, match="Unknown stage"):
        AblationConfig.only("snapping", "nonexistent")


# -----------------------------------------------------------------------------
# 2. Equivalence to Phase 12 MGR Pipeline
# -----------------------------------------------------------------------------

def test_full_ablation_matches_mgr_pipeline():
    """AblationConfig.full() produces geometric output matching run_mgr_pipeline."""
    walls = _make_box_walls(100.0)
    doors = [Opening(id="d1", type="door", start=(40.0, 0.0), end=(60.0, 0.0), confidence=0.8)]
    windows = [Opening(id="win1", type="window", start=(100.0, 30.0), end=(100.0, 70.0), confidence=0.8)]
    dimensions = [
        DimensionEvidence(id="dim1", value_mm=5000.0, start_px=(0.0, 0.0), end_px=(100.0, 0.0), confidence=0.95),
        DimensionEvidence(id="dim2", value_mm=5000.0, start_px=(0.0, 0.0), end_px=(100.0, 0.0), confidence=0.95),
    ]

    ref_res = run_mgr_pipeline(
        walls=walls,
        doors=doors,
        windows=windows,
        dimensions=dimensions,
    )

    abl_res = run_mgr_ablation(
        config=AblationConfig.full(),
        walls=walls,
        doors=doors,
        windows=windows,
        dimensions=dimensions,
    )

    assert len(abl_res.result.walls) == len(ref_res.walls)
    assert len(abl_res.result.rooms) == len(ref_res.rooms)
    assert len(abl_res.result.doors) == len(ref_res.doors)
    assert len(abl_res.result.windows) == len(ref_res.windows)
    assert abl_res.result.scale_mm_per_px == ref_res.scale_mm_per_px
    assert abl_res.result.confidence == ref_res.confidence
    assert abl_res.result.doors[0].wall_id == ref_res.doors[0].wall_id


# -----------------------------------------------------------------------------
# 3. Baseline & Stage Toggles
# -----------------------------------------------------------------------------

def test_baseline_ablation_preserves_raw_geometry():
    """Baseline configuration preserves raw un-snapped, un-merged, un-calibrated geometry."""
    raw_walls = [
        WallSegment(id="w1", start=(0.0, 0.0), end=(100.0, 4.0), length_px=100.08, angle_deg=2.29, confidence=0.8),
        WallSegment(id="w2", start=(100.0, 4.0), end=(100.0, 100.0), length_px=96.0, angle_deg=90.0, confidence=0.8),
    ]
    doors = [Opening(id="d1", type="door", start=(40.0, 0.0), end=(60.0, 0.0), confidence=0.8)]
    dimensions = [
        DimensionEvidence(id="dim1", value_mm=5000.0, start_px=(0.0, 0.0), end_px=(100.0, 0.0), confidence=0.95)
    ]

    res = run_mgr_ablation(
        config=AblationConfig.baseline(),
        walls=raw_walls,
        doors=doors,
        dimensions=dimensions,
    )

    # Walls remain exactly raw
    assert len(res.result.walls) == 2
    assert res.result.walls[0].id == "w1"
    assert res.result.walls[0].end == (100.0, 4.0)
    assert res.result.walls[0].start_metric is None
    # No rooms polygonized
    assert res.result.rooms == []
    # No opening matched
    assert res.result.doors[0].wall_id is None
    # Uncalibrated scale
    assert res.result.scale_mm_per_px is None
    assert res.metrics.is_calibrated is False


def test_disable_snapping():
    """Disabling snapping preserves slight angle deviation, while full snaps it."""
    walls = [
        WallSegment(id="w1", start=(0.0, 0.0), end=(100.0, 4.0), length_px=100.08, angle_deg=2.29, confidence=0.9)
    ]

    res_no_snap = run_mgr_ablation(
        config=AblationConfig.full().without("snapping"),
        walls=walls,
    )
    assert res_no_snap.result.walls[0].end == (100.0, 4.0)

    res_full = run_mgr_ablation(
        config=AblationConfig.full(),
        walls=walls,
    )
    # 2.29° is within default 10.0° tolerance, snaps to horizontal y=0.0 or y=2.0
    assert abs(res_full.result.walls[0].start[1] - res_full.result.walls[0].end[1]) < 1e-4


def test_disable_collinear_merging():
    """Disabling collinear merging retains split segments on the same line."""
    walls = [
        WallSegment(id="w1", start=(0.0, 0.0), end=(50.0, 0.0), length_px=50.0, angle_deg=0.0, confidence=0.9),
        WallSegment(id="w2", start=(50.0, 0.0), end=(100.0, 0.0), length_px=50.0, angle_deg=0.0, confidence=0.9),
    ]

    res_no_merge = run_mgr_ablation(
        config=AblationConfig.full().without("collinear_merging"),
        walls=walls,
    )
    assert len(res_no_merge.result.walls) == 2

    res_full = run_mgr_ablation(
        config=AblationConfig.full(),
        walls=walls,
    )
    assert len(res_full.result.walls) == 1
    assert res_full.result.walls[0].start == (0.0, 0.0)
    assert res_full.result.walls[0].end == (100.0, 0.0)


def test_disable_intersection_splitting():
    """Disabling intersection splitting avoids splitting cross-shaped intersecting walls."""
    walls = [
        WallSegment(id="w_h", start=(0.0, 50.0), end=(100.0, 50.0), length_px=100.0, angle_deg=0.0, confidence=0.9),
        WallSegment(id="w_v", start=(50.0, 0.0), end=(50.0, 100.0), length_px=100.0, angle_deg=90.0, confidence=0.9),
    ]

    res_no_split = run_mgr_ablation(
        config=AblationConfig.full().without("intersection_splitting"),
        walls=walls,
    )
    assert len(res_no_split.result.walls) == 2

    res_full = run_mgr_ablation(
        config=AblationConfig.full(),
        walls=walls,
    )
    assert len(res_full.result.walls) == 4


def test_disable_opening_reconciliation():
    """Disabling opening reconciliation preserves openings without wall matching or projection."""
    walls = _make_box_walls(100.0)
    # Opening slightly offset from the top wall
    doors = [Opening(id="d1", type="door", start=(40.0, 2.0), end=(60.0, 2.0), confidence=0.8)]
    windows = [Opening(id="w1", type="window", start=(102.0, 40.0), end=(102.0, 60.0), confidence=0.8)]

    res_no_openings = run_mgr_ablation(
        config=AblationConfig.full().without("opening_reconciliation"),
        walls=walls,
        doors=doors,
        windows=windows,
    )
    assert res_no_openings.result.doors[0].wall_id is None
    assert res_no_openings.result.doors[0].start == (40.0, 2.0)
    assert res_no_openings.result.windows[0].wall_id is None
    assert res_no_openings.metrics.reconciled_door_count == 0

    res_full = run_mgr_ablation(
        config=AblationConfig.full(),
        walls=walls,
        doors=doors,
        windows=windows,
    )
    assert res_full.result.doors[0].wall_id is not None
    assert res_full.metrics.reconciled_door_count == 1
    assert res_full.metrics.reconciled_window_count == 1


def test_disable_room_polygonization():
    """Disabling room polygonization results in empty rooms list and 0 room metrics."""
    walls = _make_box_walls(100.0)

    res_no_rooms = run_mgr_ablation(
        config=AblationConfig.full().without("room_polygonization"),
        walls=walls,
    )
    assert res_no_rooms.result.rooms == []
    assert res_no_rooms.metrics.room_count == 0
    assert res_no_rooms.metrics.total_room_area_px2 == 0.0

    res_full = run_mgr_ablation(
        config=AblationConfig.full(),
        walls=walls,
    )
    assert len(res_full.result.rooms) == 1
    assert res_full.metrics.room_count == 1
    assert res_full.metrics.total_room_area_px2 > 0.0


def test_disable_metric_calibration():
    """Disabling metric calibration keeps scale None and preserves uncalibrated coordinates."""
    walls = _make_box_walls(100.0)
    dimensions = [
        DimensionEvidence(id="dim1", value_mm=5000.0, start_px=(0.0, 0.0), end_px=(100.0, 0.0), confidence=0.95),
        DimensionEvidence(id="dim2", value_mm=5000.0, start_px=(0.0, 0.0), end_px=(100.0, 0.0), confidence=0.95),
    ]

    res_no_calib = run_mgr_ablation(
        config=AblationConfig.full().without("metric_calibration"),
        walls=walls,
        dimensions=dimensions,
    )
    assert res_no_calib.result.scale_mm_per_px is None
    assert res_no_calib.metrics.is_calibrated is False
    assert res_no_calib.metrics.scale_mm_per_px is None
    assert res_no_calib.metrics.total_room_area_m2 is None
    assert res_no_calib.result.walls[0].start_metric is None

    res_full = run_mgr_ablation(
        config=AblationConfig.full(),
        walls=walls,
        dimensions=dimensions,
    )
    assert res_full.result.scale_mm_per_px == 50.0
    assert res_full.metrics.is_calibrated is True
    assert res_full.metrics.total_room_area_m2 is not None
    assert res_full.result.walls[0].start_metric is not None


# -----------------------------------------------------------------------------
# 4. Immutability & Determinism Tests
# -----------------------------------------------------------------------------

def test_input_immutability():
    """Caller input objects (walls, doors, windows, dimensions) are never mutated."""
    orig_walls = _make_box_walls(100.0)
    orig_doors = [Opening(id="d1", type="door", start=(40.0, 2.0), end=(60.0, 2.0), confidence=0.8)]
    orig_windows = [Opening(id="w1", type="window", start=(102.0, 40.0), end=(102.0, 60.0), confidence=0.8)]
    orig_dims = [DimensionEvidence(id="dim1", value_mm=5000.0, start_px=(0.0, 0.0), end_px=(100.0, 0.0), confidence=0.9)]

    # Keep snapshots
    wall_starts = [w.start for w in orig_walls]
    door_start = orig_doors[0].start
    door_wall_id = orig_doors[0].wall_id

    run_mgr_ablation(
        config=AblationConfig.full(),
        walls=orig_walls,
        doors=orig_doors,
        windows=orig_windows,
        dimensions=orig_dims,
    )

    # Verify input objects unchanged
    for w, start in zip(orig_walls, wall_starts):
        assert w.start == start
        assert w.start_metric is None
    assert orig_doors[0].start == door_start
    assert orig_doors[0].wall_id == door_wall_id


def test_deterministic_repeated_execution():
    """Repeated execution under identical inputs and config returns exact identical metrics."""
    walls = _make_box_walls(100.0)
    doors = [Opening(id="d1", type="door", start=(40.0, 0.0), end=(60.0, 0.0), confidence=0.8)]

    run1 = run_mgr_ablation(config=AblationConfig.full(), walls=walls, doors=doors)
    run2 = run_mgr_ablation(config=AblationConfig.full(), walls=walls, doors=doors)

    assert run1.metrics.to_dict() == run2.metrics.to_dict()
    assert [w.start for w in run1.result.walls] == [w.start for w in run2.result.walls]


# -----------------------------------------------------------------------------
# 5. Metrics & Comparison Utilities
# -----------------------------------------------------------------------------

def test_metrics_computation():
    """compute_ablation_metrics correctly populates all dictionary fields."""
    walls = _make_box_walls(100.0)
    mgr_res = MGRResult(
        walls=walls,
        rooms=[RoomPolygon(id="r1", polygon=[(0, 0), (100, 0), (100, 100), (0, 100)], area_px2=10000.0, area_m2=25.0)],
        doors=[Opening(id="d1", type="door", start=(40, 0), end=(60, 0), wall_id="w_top")],
        windows=[Opening(id="w1", type="window", start=(100, 30), end=(100, 70), wall_id=None)],
        scale_mm_per_px=50.0,
        confidence={"topology_valid": True},
        assumptions=["Topology Error: sample error"],
    )

    metrics = compute_ablation_metrics(mgr_res)
    assert metrics.wall_count == 4
    assert metrics.room_count == 1
    assert metrics.total_room_area_px2 == 10000.0
    assert metrics.total_room_area_m2 == 25.0
    assert metrics.door_count == 1
    assert metrics.reconciled_door_count == 1
    assert metrics.window_count == 1
    assert metrics.reconciled_window_count == 0
    assert metrics.scale_mm_per_px == 50.0
    assert metrics.is_calibrated is True
    assert metrics.topology_valid is True
    assert metrics.topology_error_count == 1
    assert metrics.topology_warning_count == 0

    m_dict = metrics.to_dict()
    assert isinstance(m_dict, dict)
    assert m_dict["wall_count"] == 4
    assert m_dict["total_room_area_m2"] == 25.0


def test_compare_ablations_utility():
    """compare_ablations returns a dictionary mapping run names to metrics dicts."""
    walls = _make_box_walls(100.0)

    res_full = run_mgr_ablation(config=AblationConfig.full(), walls=walls)
    res_base = run_mgr_ablation(config=AblationConfig.baseline(), walls=walls)

    comparison = compare_ablations({"full": res_full, "baseline": res_base})

    assert "full" in comparison
    assert "baseline" in comparison
    assert comparison["full"]["room_count"] == 1
    assert comparison["baseline"]["room_count"] == 0


def test_compare_multiple_named_ablation_runs():
    """compare_ablations preserves multiple named configurations in insertion order."""
    walls = _make_box_walls(100.0)

    runs = {
        "full": run_mgr_ablation(AblationConfig.full(), walls=walls),
        "no_snapping": run_mgr_ablation(AblationConfig.full().without("snapping"), walls=walls),
        "no_polygonization": run_mgr_ablation(AblationConfig.full().without("room_polygonization"), walls=walls),
        "baseline": run_mgr_ablation(AblationConfig.baseline(), walls=walls),
    }

    comp = compare_ablations(runs)
    assert list(comp.keys()) == ["full", "no_snapping", "no_polygonization", "baseline"]
    assert comp["no_polygonization"]["room_count"] == 0
    assert comp["full"]["room_count"] == 1


# -----------------------------------------------------------------------------
# 6. Inputs & Edge Cases
# -----------------------------------------------------------------------------

def test_empty_inputs():
    """Calling with no inputs safely produces an empty AblationResult."""
    res = run_mgr_ablation()
    assert isinstance(res, AblationResult)
    assert res.result.walls == []
    assert res.result.rooms == []
    assert res.metrics.wall_count == 0
    assert res.metrics.room_count == 0
    assert res.metrics.is_calibrated is False


def test_wall_mask_input():
    """Ablation pipeline works starting from a binary wall mask."""
    mask = _create_synthetic_box_mask(100, 5)
    res = run_mgr_ablation(config=AblationConfig.full(), wall_mask=mask)

    assert len(res.result.walls) >= 4
    assert len(res.result.rooms) == 1
    assert res.metrics.room_count == 1


def test_pre_extracted_wall_input():
    """Supplying pre-extracted walls operates directly without skeletonization."""
    walls = _make_box_walls(80.0)
    res = run_mgr_ablation(config=AblationConfig.full(), walls=walls)

    assert len(res.result.walls) == 4
    assert len(res.result.rooms) == 1


def test_multi_room_geometry():
    """Multi-room floorplan with shared wall handles ablations correctly."""
    # 2 adjacent 100x100 rooms sharing wall at x=100
    walls = [
        # Room 1
        WallSegment(id="r1_top", start=(0.0, 0.0), end=(100.0, 0.0), length_px=100.0, angle_deg=0.0, confidence=0.9),
        WallSegment(id="shared", start=(100.0, 0.0), end=(100.0, 100.0), length_px=100.0, angle_deg=90.0, confidence=0.9),
        WallSegment(id="r1_bot", start=(100.0, 100.0), end=(0.0, 100.0), length_px=100.0, angle_deg=180.0, confidence=0.9),
        WallSegment(id="r1_left", start=(0.0, 100.0), end=(0.0, 0.0), length_px=100.0, angle_deg=270.0, confidence=0.9),
        # Room 2
        WallSegment(id="r2_top", start=(100.0, 0.0), end=(200.0, 0.0), length_px=100.0, angle_deg=0.0, confidence=0.9),
        WallSegment(id="r2_right", start=(200.0, 0.0), end=(200.0, 100.0), length_px=100.0, angle_deg=90.0, confidence=0.9),
        WallSegment(id="r2_bot", start=(200.0, 100.0), end=(100.0, 100.0), length_px=100.0, angle_deg=180.0, confidence=0.9),
    ]

    res = run_mgr_ablation(config=AblationConfig.full(), walls=walls)
    assert len(res.result.rooms) == 2
    assert res.metrics.room_count == 2


def test_shared_wall_geometry():
    """Shared wall structure metrics accurately reflect wall and room counts."""
    walls = [
        WallSegment(id="w1", start=(0.0, 0.0), end=(100.0, 0.0), length_px=100.0, angle_deg=0.0, confidence=0.9),
        WallSegment(id="w2", start=(100.0, 0.0), end=(100.0, 100.0), length_px=100.0, angle_deg=90.0, confidence=0.9),
        WallSegment(id="w3", start=(100.0, 100.0), end=(0.0, 100.0), length_px=100.0, angle_deg=180.0, confidence=0.9),
        WallSegment(id="w4", start=(0.0, 100.0), end=(0.0, 0.0), length_px=100.0, angle_deg=270.0, confidence=0.9),
    ]

    res = run_mgr_ablation(config=AblationConfig.full(), walls=walls)
    assert res.metrics.wall_count == 4
    assert res.metrics.topology_valid is True


def test_missing_dimension_evidence():
    """Missing dimension evidence leaves scale uncalibrated but keeps geometry intact."""
    walls = _make_box_walls(100.0)
    res = run_mgr_ablation(config=AblationConfig.full(), walls=walls, dimensions=None)

    assert res.result.scale_mm_per_px is None
    assert res.metrics.is_calibrated is False
    assert res.metrics.total_room_area_m2 is None
    assert len(res.result.rooms) == 1


def test_invalid_dimension_evidence():
    """Contradictory dimension evidence fails consensus calibration safely."""
    walls = _make_box_walls(100.0)
    dims = [
        DimensionEvidence(id="d1", value_mm=2000.0, start_px=(0.0, 0.0), end_px=(100.0, 0.0), confidence=0.9),
        DimensionEvidence(id="d2", value_mm=10000.0, start_px=(0.0, 0.0), end_px=(100.0, 0.0), confidence=0.9),
    ]

    res = run_mgr_ablation(config=AblationConfig.full(), walls=walls, dimensions=dims)
    assert res.result.scale_mm_per_px is None
    assert res.metrics.is_calibrated is False


def test_disabled_calibration_preserving_pixel_geometry():
    """Disabled calibration preserves pixel room area and wall pixel length identically."""
    walls = _make_box_walls(100.0)
    dims = [DimensionEvidence(id="d1", value_mm=5000.0, start_px=(0.0, 0.0), end_px=(100.0, 0.0), confidence=0.9)]

    res_calib = run_mgr_ablation(AblationConfig.full(), walls=walls, dimensions=dims)
    res_no_calib = run_mgr_ablation(AblationConfig.full().without("metric_calibration"), walls=walls, dimensions=dims)

    assert res_calib.metrics.total_room_area_px2 == res_no_calib.metrics.total_room_area_px2
    assert res_calib.metrics.total_wall_length_px == res_no_calib.metrics.total_wall_length_px
    assert res_no_calib.metrics.total_room_area_m2 is None
    assert res_calib.metrics.total_room_area_m2 is not None


def test_opening_counts_and_reconciliation_counts():
    """Reconciled opening counts accurately reflect matches vs unassigned openings."""
    walls = _make_box_walls(100.0)
    doors = [
        Opening(id="d_close", type="door", start=(40.0, 0.0), end=(60.0, 0.0), confidence=0.9),
        Opening(id="d_far", type="door", start=(500.0, 500.0), end=(520.0, 500.0), confidence=0.9),
    ]

    res = run_mgr_ablation(AblationConfig.full(), walls=walls, doors=doors)
    assert res.metrics.door_count == 2
    assert res.metrics.reconciled_door_count == 1


def test_topology_metric_extraction():
    """Topology valid status and error/warning counts are properly extracted into metrics."""
    walls = _make_box_walls(100.0)
    # Intentionally add a duplicate door ID to trigger a topology error
    doors = [
        Opening(id="dup", type="door", start=(20.0, 0.0), end=(40.0, 0.0), confidence=0.9),
        Opening(id="dup", type="door", start=(60.0, 0.0), end=(80.0, 0.0), confidence=0.9),
    ]

    res = run_mgr_ablation(AblationConfig.full(), walls=walls, doors=doors)
    assert res.metrics.topology_error_count >= 1
    assert res.metrics.topology_valid is False
