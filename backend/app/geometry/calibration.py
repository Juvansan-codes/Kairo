"""
Metric Calibration module (Phase 10).

Estimates physical scale (scale_mm_per_px) from DimensionEvidence measurements
using robust consensus/outlier rejection, and calibrates WallSegment geometry
with metric coordinate equivalents.
"""

from __future__ import annotations

import math
from typing import Sequence

from app.geometry.types import DimensionEvidence, Point, WallSegment


def estimate_scale_mm_per_px(
    dimensions: list[DimensionEvidence],
    *,
    min_confidence: float = 0.0,
    relative_tolerance: float = 0.10,
) -> float | None:
    """Robustly estimate real-world scale in mm per pixel from dimension evidence.

    Parameters
    ----------
    dimensions : list[DimensionEvidence]
        List of dimension measurements from OCR or blueprint annotations.
    min_confidence : float, optional
        Minimum confidence threshold for considering an evidence measurement (default: 0.0).
    relative_tolerance : float, optional
        Maximum allowable relative deviation (|scale - median| / median)
        to qualify as a consistent inlier (default: 0.10 = 10%).

    Returns
    -------
    float | None
        Estimated scale in mm/px rounded to 4 decimal places, or None if no
        usable/consistent evidence is found.
    """
    if not dimensions:
        return None

    valid_candidates: list[tuple[float, float]] = []

    for dim in dimensions:
        # Confidence filtering
        if dim.confidence < min_confidence:
            continue

        # Dimension value must be strictly positive and finite
        if dim.value_mm <= 0.0 or not math.isfinite(dim.value_mm):
            continue

        # Pixel distance between measurement markers
        dx = dim.end_px[0] - dim.start_px[0]
        dy = dim.end_px[1] - dim.start_px[1]
        dist_px = math.hypot(dx, dy)

        if dist_px < 1e-4 or not math.isfinite(dist_px):
            continue

        scale = dim.value_mm / dist_px
        if scale > 0.0 and math.isfinite(scale):
            valid_candidates.append((scale, max(dim.confidence, 1e-3)))

    if not valid_candidates:
        return None

    # Single valid candidate
    if len(valid_candidates) == 1:
        return round(float(valid_candidates[0][0]), 4)

    # Sort deterministically by scale value
    valid_candidates.sort(key=lambda item: item[0])
    scales = [c[0] for c in valid_candidates]

    # Compute median scale
    n = len(scales)
    mid = n // 2
    if n % 2 == 1:
        median_scale = scales[mid]
    else:
        median_scale = (scales[mid - 1] + scales[mid]) / 2.0

    if median_scale <= 0.0:
        return None

    # Filter inliers within relative_tolerance of median
    inliers = [
        (s, conf)
        for s, conf in valid_candidates
        if abs(s - median_scale) / median_scale <= relative_tolerance
    ]

    if not inliers:
        return None

    # Confidence-weighted average of inliers
    total_weight = sum(conf for _, conf in inliers)
    if total_weight > 0.0:
        weighted_scale = sum(s * conf for s, conf in inliers) / total_weight
    else:
        weighted_scale = sum(s for s, _ in inliers) / len(inliers)

    return round(float(weighted_scale), 4)


def calibrate_wall_segments(
    walls: list[WallSegment],
    scale_mm_per_px: float,
) -> list[WallSegment]:
    """Convert WallSegment pixel endpoints into real-world metric coordinates.

    Parameters
    ----------
    walls : list[WallSegment]
        Input wall segments. Original objects are not modified.
    scale_mm_per_px : float
        Calibration scale factor in millimeters per pixel. Must be strictly positive.

    Returns
    -------
    list[WallSegment]
        New WallSegment instances with start_metric and end_metric populated.
    """
    if scale_mm_per_px <= 0.0 or not math.isfinite(scale_mm_per_px):
        raise ValueError(f"scale_mm_per_px must be positive and finite, got {scale_mm_per_px}")

    calibrated_walls: list[WallSegment] = []

    for w in walls:
        m_start_x = round(float(w.start[0] * scale_mm_per_px), 2)
        m_start_y = round(float(w.start[1] * scale_mm_per_px), 2)
        m_end_x = round(float(w.end[0] * scale_mm_per_px), 2)
        m_end_y = round(float(w.end[1] * scale_mm_per_px), 2)

        calibrated_walls.append(
            WallSegment(
                id=w.id,
                start=w.start,
                end=w.end,
                length_px=w.length_px,
                angle_deg=w.angle_deg,
                confidence=w.confidence,
                source=list(w.source),
                thickness_px=w.thickness_px,
                start_metric=(m_start_x, m_start_y),
                end_metric=(m_end_x, m_end_y),
            )
        )

    return calibrated_walls
