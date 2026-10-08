"""
Ablation Support module (Phase 13).

Provides controlled ablation framework for the Metric-Aware Geometric
Reconciliation (MGR) pipeline. Enables selective enabling/disabling of
individual reconciliation stages to evaluate their contributions to geometric,
topological, and metric reconstruction quality.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
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
from app.geometry.types import (
    DimensionEvidence,
    MGRResult,
    Opening,
    RoomPolygon,
    WallSegment,
)

STAGE_NAMES = (
    "snapping",
    "collinear_merging",
    "intersection_splitting",
    "opening_reconciliation",
    "room_polygonization",
    "metric_calibration",
)


@dataclass
class AblationConfig:
    """Configuration for toggling individual stages of the MGR pipeline.

    Attributes
    ----------
    snapping : bool
        Whether Manhattan angle snapping is enabled (Phase 5).
    collinear_merging : bool
        Whether collinear wall segment merging is enabled (Phase 6).
    intersection_splitting : bool
        Whether intersection detection and segment splitting is enabled (Phase 7).
    opening_reconciliation : bool
        Whether door/window matching and projection onto walls is enabled (Phase 8).
    room_polygonization : bool
        Whether enclosed room cycle polygonization is enabled (Phase 9).
    metric_calibration : bool
        Whether scale estimation and real-world metric calibration is enabled (Phase 10).
    """

    snapping: bool = True
    collinear_merging: bool = True
    intersection_splitting: bool = True
    opening_reconciliation: bool = True
    room_polygonization: bool = True
    metric_calibration: bool = True

    @classmethod
    def full(cls) -> AblationConfig:
        """Create a configuration with all stages enabled."""
        return cls(
            snapping=True,
            collinear_merging=True,
            intersection_splitting=True,
            opening_reconciliation=True,
            room_polygonization=True,
            metric_calibration=True,
        )

    @classmethod
    def baseline(cls) -> AblationConfig:
        """Create a baseline configuration with all intermediate stages disabled."""
        return cls(
            snapping=False,
            collinear_merging=False,
            intersection_splitting=False,
            opening_reconciliation=False,
            room_polygonization=False,
            metric_calibration=False,
        )

    def without(self, stage_name: str) -> AblationConfig:
        """Return a new configuration with the specified stage disabled.

        Parameters
        ----------
        stage_name : str
            Name of the stage to disable.

        Returns
        -------
        AblationConfig
            A new config with only the specified stage turned off.
        """
        if stage_name not in STAGE_NAMES:
            raise ValueError(
                f"Unknown stage '{stage_name}'. Valid stages are: {list(STAGE_NAMES)}"
            )
        kwargs = {s: getattr(self, s) for s in STAGE_NAMES}
        kwargs[stage_name] = False
        return AblationConfig(**kwargs)

    @classmethod
    def only(cls, *stage_names: str) -> AblationConfig:
        """Return a new configuration with only the specified stages enabled.

        Parameters
        ----------
        *stage_names : str
            Names of the stages to enable.

        Returns
        -------
        AblationConfig
            A new config where only the named stages are True.
        """
        for s in stage_names:
            if s not in STAGE_NAMES:
                raise ValueError(
                    f"Unknown stage '{s}'. Valid stages are: {list(STAGE_NAMES)}"
                )
        kwargs = {s: (s in stage_names) for s in STAGE_NAMES}
        return cls(**kwargs)


@dataclass
class AblationMetrics:
    """Summary metrics extracted from an ablation pipeline run."""

    wall_count: int
    total_wall_length_px: float
    room_count: int
    total_room_area_px2: float
    total_room_area_m2: float | None
    door_count: int
    reconciled_door_count: int
    window_count: int
    reconciled_window_count: int
    scale_mm_per_px: float | None
    is_calibrated: bool
    topology_valid: bool
    topology_error_count: int
    topology_warning_count: int

    def to_dict(self) -> dict[str, Any]:
        """Convert metrics to a deterministic dictionary."""
        return {
            "wall_count": self.wall_count,
            "total_wall_length_px": self.total_wall_length_px,
            "room_count": self.room_count,
            "total_room_area_px2": self.total_room_area_px2,
            "total_room_area_m2": self.total_room_area_m2,
            "door_count": self.door_count,
            "reconciled_door_count": self.reconciled_door_count,
            "window_count": self.window_count,
            "reconciled_window_count": self.reconciled_window_count,
            "scale_mm_per_px": self.scale_mm_per_px,
            "is_calibrated": self.is_calibrated,
            "topology_valid": self.topology_valid,
            "topology_error_count": self.topology_error_count,
            "topology_warning_count": self.topology_warning_count,
        }


@dataclass
class AblationResult:
    """Encapsulates the configuration, pipeline result, and metrics of an ablation run."""

    config: AblationConfig
    result: MGRResult
    metrics: AblationMetrics


def compute_ablation_metrics(result: MGRResult) -> AblationMetrics:
    """Compute structural and topological summary metrics from an MGRResult.

    Parameters
    ----------
    result : MGRResult
        Output of the MGR or ablation pipeline.

    Returns
    -------
    AblationMetrics
        Calculated metrics.
    """
    wall_count = len(result.walls)
    total_wall_length_px = round(sum(w.length_px for w in result.walls), 2)
    room_count = len(result.rooms)
    total_room_area_px2 = round(sum(r.area_px2 for r in result.rooms), 2)

    m2_vals = [r.area_m2 for r in result.rooms if r.area_m2 is not None]
    total_room_area_m2 = (
        round(sum(m2_vals), 2)
        if (m2_vals and result.scale_mm_per_px is not None)
        else None
    )

    door_count = len(result.doors)
    reconciled_door_count = sum(1 for d in result.doors if d.wall_id is not None)

    window_count = len(result.windows)
    reconciled_window_count = sum(1 for w in result.windows if w.wall_id is not None)

    scale_mm_per_px = result.scale_mm_per_px
    is_calibrated = scale_mm_per_px is not None

    topo_errors = sum(
        1 for a in result.assumptions if a.startswith("Topology Error:")
    )
    topo_warnings = sum(
        1 for a in result.assumptions if a.startswith("Topology Warning:")
    )
    topo_valid = result.confidence.get("topology_valid", topo_errors == 0)

    return AblationMetrics(
        wall_count=wall_count,
        total_wall_length_px=total_wall_length_px,
        room_count=room_count,
        total_room_area_px2=total_room_area_px2,
        total_room_area_m2=total_room_area_m2,
        door_count=door_count,
        reconciled_door_count=reconciled_door_count,
        window_count=window_count,
        reconciled_window_count=reconciled_window_count,
        scale_mm_per_px=scale_mm_per_px,
        is_calibrated=is_calibrated,
        topology_valid=bool(topo_valid),
        topology_error_count=topo_errors,
        topology_warning_count=topo_warnings,
    )


def compare_ablations(
    runs: dict[str, AblationResult],
) -> dict[str, dict[str, Any]]:
    """Format multiple ablation runs into a deterministic comparative metrics dictionary.

    Parameters
    ----------
    runs : dict[str, AblationResult]
        Dictionary mapping configuration/experiment name to its AblationResult.

    Returns
    -------
    dict[str, dict[str, Any]]
        Dictionary with preserved insertion order, mapping run name to metrics dict.
    """
    return {name: run.metrics.to_dict() for name, run in runs.items()}


def run_mgr_ablation(
    config: AblationConfig | None = None,
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
) -> AblationResult:
    """Execute the MGR pipeline under a controlled ablation configuration.

    Parameters
    ----------
    config : AblationConfig | None, optional
        Stage configuration. If None, defaults to AblationConfig.full().
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
    min_length_px : float, optional
        Minimum length of extracted wall segments in pixels (default: 3.0).
    min_pixels : int, optional
        Minimum pixel count for a skeleton branch (default: 3).
    rdp_tolerance : float, optional
        Ramer-Douglas-Peucker polygon approximation epsilon (default: 1.5).
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
    AblationResult
        Encapsulates the config, the canonical MGRResult, and computed AblationMetrics.
    """
    if config is None:
        config = AblationConfig.full()

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
        if (
            not isinstance(wall_mask, np.ndarray)
            or wall_mask.size == 0
            or not np.any(wall_mask)
        ):
            empty_res = MGRResult(
                walls=[],
                rooms=[],
                doors=[],
                windows=[],
                scale_mm_per_px=None,
                confidence={"overall": 0.0, "geometry": 0.0, "scale": 0.0},
                provenance={
                    "source": "MGR",
                    "method": "deterministic_geometric_reconciliation",
                },
                assumptions=["Wall mask was empty or all-zero"],
            )
            return AblationResult(
                config=config,
                result=empty_res,
                metrics=compute_ablation_metrics(empty_res),
            )

        skeleton = skeletonization(wall_mask)
        initial_walls = extract_wall_segments(
            skeleton,
            min_length_px=min_length_px,
            min_pixels=min_pixels,
            rdp_tolerance=rdp_tolerance,
        )
    else:
        empty_res = MGRResult(
            walls=[],
            rooms=[],
            doors=[],
            windows=[],
            scale_mm_per_px=None,
            confidence={"overall": 0.0, "geometry": 0.0, "scale": 0.0},
            provenance={
                "source": "MGR",
                "method": "deterministic_geometric_reconciliation",
            },
            assumptions=["No wall geometry or mask supplied"],
        )
        return AblationResult(
            config=config,
            result=empty_res,
            metrics=compute_ablation_metrics(empty_res),
        )

    # -------------------------------------------------------------------------
    # 2. Manhattan Snapping (Phase 5)
    # -------------------------------------------------------------------------
    if config.snapping:
        current_walls = snap_wall_segments(
            initial_walls,
            angle_tolerance_deg=snap_angle_tolerance_deg,
        )
    else:
        current_walls = initial_walls

    # -------------------------------------------------------------------------
    # 3. Collinear Merging (Phase 6)
    # -------------------------------------------------------------------------
    if config.collinear_merging:
        current_walls = merge_collinear_segments(
            current_walls,
            angle_tolerance_deg=collinear_angle_tolerance_deg,
            distance_tolerance_px=collinear_distance_tolerance_px,
            gap_tolerance_px=collinear_gap_tolerance_px,
        )

    # -------------------------------------------------------------------------
    # 4. Intersection Splitting (Phase 7)
    # -------------------------------------------------------------------------
    if config.intersection_splitting:
        cleaned_walls = split_wall_intersections(
            current_walls,
            intersection_tolerance_px=intersection_tolerance_px,
            endpoint_tolerance_px=endpoint_tolerance_px,
            min_segment_length_px=min_segment_length_px,
        )
    else:
        cleaned_walls = current_walls

    # -------------------------------------------------------------------------
    # 5. Opening Reconciliation (Phase 8) in Pixel Space
    # -------------------------------------------------------------------------
    raw_doors = (
        [
            Opening(
                id=d.id,
                type=d.type,
                start=d.start,
                end=d.end,
                wall_id=d.wall_id,
                confidence=d.confidence,
                source=list(d.source),
            )
            for d in doors
        ]
        if doors is not None
        else []
    )

    raw_windows = (
        [
            Opening(
                id=w.id,
                type=w.type,
                start=w.start,
                end=w.end,
                wall_id=w.wall_id,
                confidence=w.confidence,
                source=list(w.source),
            )
            for w in windows
        ]
        if windows is not None
        else []
    )

    if config.opening_reconciliation:
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
    else:
        # Preserved without matching or projecting
        reconciled_doors = [
            Opening(
                id=d.id,
                type=d.type,
                start=d.start,
                end=d.end,
                wall_id=None,
                confidence=d.confidence,
                source=list(d.source),
            )
            for d in raw_doors
        ]
        reconciled_windows = [
            Opening(
                id=w.id,
                type=w.type,
                start=w.start,
                end=w.end,
                wall_id=None,
                confidence=w.confidence,
                source=list(w.source),
            )
            for w in raw_windows
        ]

    # -------------------------------------------------------------------------
    # 6. Room Polygonization (Phase 9) in Pixel Space
    # -------------------------------------------------------------------------
    if config.room_polygonization:
        pixel_rooms = polygonize_rooms(
            cleaned_walls,
            min_area_px2=min_room_area_px2,
            node_tolerance_px=node_tolerance_px,
        )
    else:
        pixel_rooms = []

    # -------------------------------------------------------------------------
    # 7. Metric Calibration (Phase 10)
    # -------------------------------------------------------------------------
    scale_mm_per_px: float | None = None
    if config.metric_calibration and dimensions:
        cloned_dims = [
            DimensionEvidence(
                id=dim.id,
                value_mm=dim.value_mm,
                start_px=dim.start_px,
                end_px=dim.end_px,
                confidence=dim.confidence,
                source=list(dim.source),
            )
            for dim in dimensions
        ]
        scale_mm_per_px = estimate_scale_mm_per_px(
            cloned_dims,
            min_confidence=scale_min_confidence,
            relative_tolerance=scale_relative_tolerance,
        )

    if scale_mm_per_px is not None:
        calibrated_walls = calibrate_wall_segments(cleaned_walls, scale_mm_per_px)
        assumptions.append(f"Calibrated scale: {scale_mm_per_px:.4f} mm/px")
    else:
        calibrated_walls = cleaned_walls
        if dimensions and config.metric_calibration:
            assumptions.append(
                "Dimension evidence was present but failed consensus calibration"
            )
        else:
            assumptions.append(
                "No dimension evidence provided; uncalibrated pixel geometry"
            )

    # -------------------------------------------------------------------------
    # 8. Room Metric Area Calculation
    # -------------------------------------------------------------------------
    final_rooms: list[RoomPolygon] = []
    for r in pixel_rooms:
        area_m2: float | None = None
        if scale_mm_per_px is not None:
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
    # 9. Topology Validation (Phase 11)
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
    # 10. Confidence & Provenance Calculation
    # -------------------------------------------------------------------------
    conf_items: list[float] = [w.confidence for w in calibrated_walls] + [
        r.confidence for r in final_rooms
    ]
    geom_conf = round(sum(conf_items) / len(conf_items), 3) if conf_items else 0.0

    scale_conf = 1.0 if scale_mm_per_px is not None else 0.0

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

    mgr_result = MGRResult(
        walls=calibrated_walls,
        rooms=final_rooms,
        doors=reconciled_doors,
        windows=reconciled_windows,
        scale_mm_per_px=scale_mm_per_px,
        confidence=confidence,
        provenance=provenance,
        assumptions=assumptions,
    )

    metrics = compute_ablation_metrics(mgr_result)

    return AblationResult(
        config=config,
        result=mgr_result,
        metrics=metrics,
    )
