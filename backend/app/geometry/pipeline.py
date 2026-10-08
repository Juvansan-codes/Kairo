"""
MGR Pipeline Orchestration module (Phase 12).

Orchestrates the complete Metric-Aware Geometric Reconciliation (MGR) pipeline:
1. Input resolution & skeletonization / wall extraction
2. Manhattan snapping
3. Collinear segment merging
4. Intersection splitting
5. Opening reconciliation (doors & windows)
6. Room polygonization
7. Metric calibration (scale estimation & wall calibration)
8. Room metric area calculation
9. Topology validation
10. Final MGRResult packaging
"""

from __future__ import annotations

import math
from typing import Any

import numpy as np

from app.geometry.calibration import calibrate_wall_segments, estimate_scale_mm_per_px
from app.geometry.intersections import split_wall_intersections
from app.geometry.merging import merge_collinear_segments
from app.geometry.openings import reconcile_openings
from app.geometry.room_polygonization import polygonize_rooms
from app.geometry.snapping import snap_wall_segments
from app.geometry.solver import extract_wall_segments, skeletonization
from app.geometry.topology import validate_topology
from app.geometry.types import DimensionEvidence, MGRResult, Opening, RoomPolygon, WallSegment


def run_mgr_pipeline(
    wall_mask: np.ndarray | None = None,
    *,
    walls: list[WallSegment] | None = None,
    doors: list[Opening] | None = None,
    windows: list[Opening] | None = None,
    dimensions: list[DimensionEvidence] | None = None,
    # Phase 3 extraction parameters
    min_length_px: float = 3.0,
    min_pixels: int = 3,
    rdp_tolerance: float = 1.5,
    # Phase 5 snapping parameter
    snap_angle_tolerance_deg: float = 10.0,
    # Phase 6 collinearity parameters
    collinear_angle_tolerance_deg: float = 5.0,
    collinear_distance_tolerance_px: float = 3.0,
    collinear_gap_tolerance_px: float = 5.0,
    # Phase 7 intersection parameters
    intersection_tolerance_px: float = 1.0,
    endpoint_tolerance_px: float = 2.0,
    min_segment_length_px: float = 1.0,
    # Phase 8 opening parameters
    wall_distance_tolerance_px: float = 5.0,
    projection_tolerance_px: float = 3.0,
    # Phase 9 room polygonization parameters
    min_room_area_px2: float = 25.0,
    node_tolerance_px: float = 3.0,
    # Phase 10 calibration parameters
    scale_min_confidence: float = 0.0,
    scale_relative_tolerance: float = 0.10,
) -> MGRResult:
    """Execute the full Metric-Aware Geometric Reconciliation (MGR) pipeline.

    Parameters
    ----------
    wall_mask : np.ndarray | None, optional
        2D binary wall mask array. If provided and 'walls' is None, skeletonization
        and wall extraction are performed.
    walls : list[WallSegment] | None, optional
        Pre-extracted or supplied wall segments. Takes precedence over wall_mask.
    doors : list[Opening] | None, optional
        Predicted door openings to reconcile against wall geometry.
    windows : list[Opening] | None, optional
        Predicted window openings to reconcile against wall geometry.
    dimensions : list[DimensionEvidence] | None, optional
        OCR / annotation dimension measurements for physical metric scale calibration.
    snap_angle_tolerance_deg : float, optional
        Maximum angular deviation to snap to Manhattan orientations (default: 10.0°).
    collinear_angle_tolerance_deg : float, optional
        Angular tolerance for merging collinear wall segments (default: 5.0°).
    collinear_distance_tolerance_px : float, optional
        Perpendicular offset tolerance for collinear merging (default: 3.0 px).
    collinear_gap_tolerance_px : float, optional
        Maximum longitudinal gap for collinear merging (default: 5.0 px).
    intersection_tolerance_px : float, optional
        Tolerance for detecting intersecting and near-intersecting walls (default: 1.0 px).
    endpoint_tolerance_px : float, optional
        Threshold below which crossings are treated as endpoint touches (default: 2.0 px).
    min_segment_length_px : float, optional
        Minimum allowable wall segment length (default: 1.0 px).
    wall_distance_tolerance_px : float, optional
        Tolerance for matching doors/windows to candidate walls (default: 5.0 px).
    projection_tolerance_px : float, optional
        Allowable longitudinal extension for opening projections (default: 3.0 px).
    min_room_area_px2 : float, optional
        Minimum area threshold for valid room polygons (default: 25.0 px²).
    node_tolerance_px : float, optional
        Tolerance for graph node snapping during polygonization/validation (default: 3.0 px).
    scale_min_confidence : float, optional
        Minimum confidence threshold for dimension evidence (default: 0.0).
    scale_relative_tolerance : float, optional
        Relative deviation tolerance for dimension consensus (default: 0.10 = 10%).

    Returns
    -------
    MGRResult
        Structured reconciliation output containing clean walls, rooms, doors,
        windows, metric scale, confidence scores, provenance, and assumptions.
    """
    assumptions: list[str] = []

    # -------------------------------------------------------------------------
    # 1. Input Resolution
    # -------------------------------------------------------------------------
    initial_walls: list[WallSegment]

    if walls is not None:
        if wall_mask is not None:
            assumptions.append("Supplied 'walls' took precedence over 'wall_mask'")
        initial_walls = [
            WallSegment(
                id=w.id,
                start=w.start,
                end=w.end,
                length_px=w.length_px,
                angle_deg=w.angle_deg,
                confidence=w.confidence,
                source=list(w.source),
                thickness_px=w.thickness_px,
                start_metric=w.start_metric,
                end_metric=w.end_metric,
            )
            for w in walls
        ]
    elif wall_mask is not None:
        # Check for empty mask
        if not isinstance(wall_mask, np.ndarray) or wall_mask.size == 0 or not np.any(wall_mask):
            return MGRResult(
                walls=[],
                rooms=[],
                doors=[],
                windows=[],
                scale_mm_per_px=None,
                confidence={"overall": 0.0, "geometry": 0.0, "scale": 0.0},
                provenance={"source": "MGR", "method": "deterministic_geometric_reconciliation"},
                assumptions=["Wall mask was empty or all-zero"],
            )

        skeleton = skeletonization(wall_mask)
        initial_walls = extract_wall_segments(
            skeleton,
            min_length_px=min_length_px,
            min_pixels=min_pixels,
            rdp_tolerance=rdp_tolerance,
        )
    else:
        # Neither walls nor wall_mask supplied
        return MGRResult(
            walls=[],
            rooms=[],
            doors=[],
            windows=[],
            scale_mm_per_px=None,
            confidence={"overall": 0.0, "geometry": 0.0, "scale": 0.0},
            provenance={"source": "MGR", "method": "deterministic_geometric_reconciliation"},
            assumptions=["No wall geometry or mask supplied"],
        )

    # -------------------------------------------------------------------------
    # 2. Geometric Wall Cleanup (Phases 5 -> 6 -> 7)
    # -------------------------------------------------------------------------
    snapped_walls = snap_wall_segments(
        initial_walls,
        angle_tolerance_deg=snap_angle_tolerance_deg,
    )

    merged_walls = merge_collinear_segments(
        snapped_walls,
        angle_tolerance_deg=collinear_angle_tolerance_deg,
        distance_tolerance_px=collinear_distance_tolerance_px,
        gap_tolerance_px=collinear_gap_tolerance_px,
    )

    cleaned_walls = split_wall_intersections(
        merged_walls,
        intersection_tolerance_px=intersection_tolerance_px,
        endpoint_tolerance_px=endpoint_tolerance_px,
        min_segment_length_px=min_segment_length_px,
    )

    # -------------------------------------------------------------------------
    # 3. Opening Reconciliation (Phase 8) in Pixel Space
    # -------------------------------------------------------------------------
    raw_doors = doors if doors is not None else []
    raw_windows = windows if windows is not None else []

    reconciled_doors = reconcile_openings(
        raw_doors,
        cleaned_walls,
        wall_distance_tolerance_px=wall_distance_tolerance_px,
        projection_tolerance_px=projection_tolerance_px,
    )

    reconciled_windows = reconcile_openings(
        raw_windows,
        cleaned_walls,
        wall_distance_tolerance_px=wall_distance_tolerance_px,
        projection_tolerance_px=projection_tolerance_px,
    )

    # -------------------------------------------------------------------------
    # 4. Room Polygonization (Phase 9) in Pixel Space
    # -------------------------------------------------------------------------
    pixel_rooms = polygonize_rooms(
        cleaned_walls,
        min_area_px2=min_room_area_px2,
        node_tolerance_px=node_tolerance_px,
    )

    # -------------------------------------------------------------------------
    # 5. Metric Calibration (Phase 10)
    # -------------------------------------------------------------------------
    scale_mm_per_px: float | None = None
    if dimensions:
        scale_mm_per_px = estimate_scale_mm_per_px(
            dimensions,
            min_confidence=scale_min_confidence,
            relative_tolerance=scale_relative_tolerance,
        )

    if scale_mm_per_px is not None:
        calibrated_walls = calibrate_wall_segments(cleaned_walls, scale_mm_per_px)
        assumptions.append(f"Calibrated scale: {scale_mm_per_px:.4f} mm/px")
    else:
        calibrated_walls = cleaned_walls
        if dimensions:
            assumptions.append("Dimension evidence was present but failed consensus calibration")
        else:
            assumptions.append("No dimension evidence provided; uncalibrated pixel geometry")

    # -------------------------------------------------------------------------
    # 6. Room Metric Area Calculation
    # -------------------------------------------------------------------------
    final_rooms: list[RoomPolygon] = []
    for r in pixel_rooms:
        area_m2: float | None = None
        if scale_mm_per_px is not None:
            # 1 px^2 = (scale_mm_per_px / 1000.0)^2 m^2
            area_m2 = round(r.area_px2 * ((scale_mm_per_px / 1000.0) ** 2), 2)

        final_rooms.append(
            RoomPolygon(
                id=r.id,
                polygon=list(r.polygon),
                area_px2=r.area_px2,
                area_m2=area_m2,
                label=r.label,
                confidence=r.confidence,
                source=list(r.source),
            )
        )

    # -------------------------------------------------------------------------
    # 7. Topology Validation (Phase 11)
    # -------------------------------------------------------------------------
    topology_report = validate_topology(
        calibrated_walls,
        final_rooms,
        reconciled_doors,
        reconciled_windows,
        node_tolerance_px=node_tolerance_px,
    )

    for err in topology_report["errors"]:
        assumptions.append(f"Topology Error: {err}")

    for warn in topology_report["warnings"]:
        assumptions.append(f"Topology Warning: {warn}")

    # -------------------------------------------------------------------------
    # 8. Confidence & Provenance Calculation
    # -------------------------------------------------------------------------
    # Geometry confidence: average across walls and rooms
    conf_items: list[float] = [w.confidence for w in calibrated_walls] + [
        r.confidence for r in final_rooms
    ]
    geom_conf = round(sum(conf_items) / len(conf_items), 3) if conf_items else 0.0

    # Scale confidence: 1.0 if successfully calibrated, 0.0 otherwise
    scale_conf = 1.0 if scale_mm_per_px is not None else 0.0

    # Overall confidence: balanced weighting
    if geom_conf > 0.0 and scale_conf > 0.0:
        overall_conf = round(0.7 * geom_conf + 0.3 * scale_conf, 3)
    else:
        overall_conf = round(geom_conf, 3)

    confidence: dict[str, Any] = {
        "overall": overall_conf,
        "geometry": geom_conf,
        "scale": scale_conf,
        "topology_valid": topology_report["valid"],
    }

    provenance: dict[str, Any] = {
        "source": "MGR",
        "method": "deterministic_geometric_reconciliation",
        "topology_stats": topology_report["stats"],
    }

    # -------------------------------------------------------------------------
    # 9. Return Canonical MGRResult
    # -------------------------------------------------------------------------
    return MGRResult(
        walls=calibrated_walls,
        rooms=final_rooms,
        doors=reconciled_doors,
        windows=reconciled_windows,
        scale_mm_per_px=scale_mm_per_px,
        confidence=confidence,
        provenance=provenance,
        assumptions=assumptions,
    )
