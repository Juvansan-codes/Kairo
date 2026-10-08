"""
Manhattan Snapping module (Phase 5).

Snaps wall segments that are sufficiently close to horizontal or vertical
orientations to exact Manhattan orientations (0°, 90°, 180°, -90°).
"""

from __future__ import annotations

import math
from app.geometry.types import WallSegment


def _angle_diff_deg(a: float, b: float) -> float:
    """Return the smallest absolute angular difference in degrees between two angles."""
    diff = (a - b) % 360.0
    if diff > 180.0:
        diff = 360.0 - diff
    return diff


def _snap_single_segment(
    seg: WallSegment,
    angle_tolerance_deg: float,
) -> WallSegment:
    """Snap a single WallSegment to horizontal or vertical if within tolerance."""
    dx_raw = seg.end[0] - seg.start[0]
    dy_raw = seg.end[1] - seg.start[1]
    raw_len = math.hypot(dx_raw, dy_raw)

    # Safely handle zero-length or effectively degenerate segments
    if raw_len < 1e-6:
        return WallSegment(
            id=seg.id,
            start=seg.start,
            end=seg.end,
            length_px=0.0,
            angle_deg=seg.angle_deg,
            confidence=seg.confidence,
            source=list(seg.source),
            thickness_px=seg.thickness_px,
            start_metric=tuple(seg.start_metric) if seg.start_metric is not None else None,
            end_metric=tuple(seg.end_metric) if seg.end_metric is not None else None,
        )

    # Compute orientation from coordinates
    angle = math.degrees(math.atan2(dy_raw, dx_raw))

    # Calculate smallest angular deviation to horizontal (0° or 180°) and vertical (90° or -90°)
    diff_h = min(_angle_diff_deg(angle, 0.0), _angle_diff_deg(angle, 180.0))
    diff_v = min(_angle_diff_deg(angle, 90.0), _angle_diff_deg(angle, -90.0))

    if diff_h <= angle_tolerance_deg and diff_h <= diff_v:
        # Snap to horizontal: retain x coordinates, set both y coordinates to midpoint y
        mid_y = round((seg.start[1] + seg.end[1]) / 2.0, 2)
        new_start = (round(float(seg.start[0]), 2), mid_y)
        new_end = (round(float(seg.end[0]), 2), mid_y)

        new_dx = new_end[0] - new_start[0]
        new_length = round(abs(new_dx), 2)
        # Preserve original orientation direction: pointing right -> 0°, pointing left -> 180°
        new_angle = 180.0 if new_dx < 0 else 0.0

    elif diff_v <= angle_tolerance_deg and diff_v < diff_h:
        # Snap to vertical: retain y coordinates, set both x coordinates to midpoint x
        mid_x = round((seg.start[0] + seg.end[0]) / 2.0, 2)
        new_start = (mid_x, round(float(seg.start[1]), 2))
        new_end = (mid_x, round(float(seg.end[1]), 2))

        new_dy = new_end[1] - new_start[1]
        new_length = round(abs(new_dy), 2)
        # Preserve original orientation direction: pointing down -> 90°, pointing up -> -90°
        new_angle = -90.0 if new_dy < 0 else 90.0

    else:
        # Outside snapping tolerance: keep original coordinates and recompute length/angle
        new_start = (round(float(seg.start[0]), 2), round(float(seg.start[1]), 2))
        new_end = (round(float(seg.end[0]), 2), round(float(seg.end[1]), 2))
        new_length = seg.length_px if seg.length_px > 0.0 else round(raw_len, 2)
        new_angle = seg.angle_deg

    return WallSegment(
        id=seg.id,
        start=new_start,
        end=new_end,
        length_px=new_length,
        angle_deg=new_angle,
        confidence=seg.confidence,
        source=list(seg.source),
        thickness_px=seg.thickness_px,
        start_metric=tuple(seg.start_metric) if seg.start_metric is not None else None,
        end_metric=tuple(seg.end_metric) if seg.end_metric is not None else None,
    )


def snap_wall_segments(
    segments: list[WallSegment],
    *,
    angle_tolerance_deg: float = 10.0,
) -> list[WallSegment]:
    """Snap wall segments close to horizontal or vertical to exact Manhattan orientations.

    Parameters
    ----------
    segments : list[WallSegment]
        List of input wall segments.
    angle_tolerance_deg : float, optional
        Maximum angular deviation in degrees from 0°, 90°, or 180° allowed
        for snapping (default: 10.0°).

    Returns
    -------
    list[WallSegment]
        New list of WallSegment objects with snapped orientations where applicable.
        Input objects are preserved and not mutated in-place.
    """
    return [
        _snap_single_segment(seg, angle_tolerance_deg=angle_tolerance_deg)
        for seg in segments
    ]
