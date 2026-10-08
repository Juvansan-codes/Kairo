"""
Collinear wall segment detection and merging module (Phase 6).

Combines wall segments that represent portions of the same physical wall based on:
1. Angular similarity (within angle_tolerance_deg modulo 180°)
2. Supporting line proximity (perpendicular offset within distance_tolerance_px)
3. Longitudinal overlap or small gap (gap within gap_tolerance_px)
"""

from __future__ import annotations

import math
from typing import Sequence

import numpy as np

from app.geometry.types import Point, WallSegment


def _angle_diff_180(theta1: float, theta2: float) -> float:
    """Return smallest angular difference in degrees modulo 180° (undirected)."""
    diff = abs(theta1 - theta2) % 180.0
    if diff > 90.0:
        diff = 180.0 - diff
    return diff


def _point_to_line_dist(p: Point, a: Point, b: Point) -> float:
    """Return perpendicular distance from point *p* to infinite line *ab*."""
    dx = b[0] - a[0]
    dy = b[1] - a[1]
    line_len = math.hypot(dx, dy)
    if line_len < 1e-6:
        return math.hypot(p[0] - a[0], p[1] - a[1])
    return abs(dx * (a[1] - p[1]) - (a[0] - p[0]) * dy) / line_len


def _project_interval(a: Point, b: Point, u: tuple[float, float]) -> tuple[float, float]:
    """Return projected 1D min and max coordinates of segment *ab* onto unit vector *u*."""
    ta = a[0] * u[0] + a[1] * u[1]
    tb = b[0] * u[0] + b[1] * u[1]
    return min(ta, tb), max(ta, tb)


def _are_segments_collinear(
    s1: WallSegment,
    s2: WallSegment,
    *,
    angle_tolerance_deg: float,
    distance_tolerance_px: float,
    gap_tolerance_px: float,
) -> bool:
    """Determine whether two segments satisfy all collinearity and proximity criteria."""
    dx1 = s1.end[0] - s1.start[0]
    dy1 = s1.end[1] - s1.start[1]
    len1 = math.hypot(dx1, dy1)

    dx2 = s2.end[0] - s2.start[0]
    dy2 = s2.end[1] - s2.start[1]
    len2 = math.hypot(dx2, dy2)

    # Zero-length segments do not define a direction and are not mergeable
    if len1 < 1e-6 or len2 < 1e-6:
        return False

    ang1 = math.degrees(math.atan2(dy1, dx1))
    ang2 = math.degrees(math.atan2(dy2, dx2))

    # 1. Orientation check (modulo 180°)
    if _angle_diff_180(ang1, ang2) > angle_tolerance_deg:
        return False

    # 2. Perpendicular distance to supporting lines
    d_s2_start = _point_to_line_dist(s2.start, s1.start, s1.end)
    d_s2_end = _point_to_line_dist(s2.end, s1.start, s1.end)
    d_s1_start = _point_to_line_dist(s1.start, s2.start, s2.end)
    d_s1_end = _point_to_line_dist(s1.end, s2.start, s2.end)
    if max(d_s2_start, d_s2_end, d_s1_start, d_s1_end) > distance_tolerance_px:
        return False

    # 3. Longitudinal overlap or small gap along supporting axis
    u = (dx1 / len1, dy1 / len1)
    min1, max1 = _project_interval(s1.start, s1.end, u)
    min2, max2 = _project_interval(s2.start, s2.end, u)

    gap = max(0.0, max(min1, min2) - min(max1, max2))
    return gap <= gap_tolerance_px


def _merge_segment_group(group: Sequence[WallSegment]) -> WallSegment:
    """Merge a compatible component of WallSegments into a single WallSegment.

    If the group contains only 1 segment, returns an immutable copy without
    recalculating geometry.
    """
    if len(group) == 1:
        s = group[0]
        return WallSegment(
            id=s.id,
            start=s.start,
            end=s.end,
            length_px=s.length_px,
            angle_deg=s.angle_deg,
            confidence=s.confidence,
            source=list(s.source),
            thickness_px=s.thickness_px,
            start_metric=tuple(s.start_metric) if s.start_metric is not None else None,
            end_metric=tuple(s.end_metric) if s.end_metric is not None else None,
        )

    # 1. Choose anchor segment deterministically (longest, tiebreak by ID)
    anchor = max(group, key=lambda s: (s.length_px, s.id))
    dx_a = anchor.end[0] - anchor.start[0]
    dy_a = anchor.end[1] - anchor.start[1]
    len_a = math.hypot(dx_a, dy_a)
    u_anchor = (dx_a / len_a, dy_a / len_a) if len_a >= 1e-6 else (1.0, 0.0)

    # 2. Collect all endpoints and perform PCA to find common line axis
    all_pts: list[Point] = []
    for s in group:
        all_pts.append(s.start)
        all_pts.append(s.end)
    pts_arr = np.array(all_pts, dtype=np.float64)

    centroid = np.mean(pts_arr, axis=0)
    centered = pts_arr - centroid
    cov = (centered.T @ centered) / len(pts_arr)
    eigvals, eigvecs = np.linalg.eigh(cov)
    v = eigvecs[:, -1]

    # Orient dominant vector with anchor direction
    if v[0] * u_anchor[0] + v[1] * u_anchor[1] < 0:
        v = -v

    # Project all endpoints onto dominant line
    projections = centered @ v
    t_min = float(np.min(projections))
    t_max = float(np.max(projections))

    p_start = centroid + t_min * v
    p_end = centroid + t_max * v

    # Preserve exact axis alignment if all constituent segments were axis-aligned
    if all(abs(s.start[1] - s.end[1]) < 1e-4 for s in group):
        avg_y = round(float(np.mean([p[1] for p in all_pts])), 2)
        p_start[1] = avg_y
        p_end[1] = avg_y
    elif all(abs(s.start[0] - s.end[0]) < 1e-4 for s in group):
        avg_x = round(float(np.mean([p[0] for p in all_pts])), 2)
        p_start[0] = avg_x
        p_end[0] = avg_x

    start_pt: Point = (round(float(p_start[0]), 2), round(float(p_start[1]), 2))
    end_pt: Point = (round(float(p_end[0]), 2), round(float(p_end[1]), 2))

    dx = end_pt[0] - start_pt[0]
    dy = end_pt[1] - start_pt[1]
    length_px = round(float(math.hypot(dx, dy)), 2)

    angle_deg = math.degrees(math.atan2(dy, dx))
    if angle_deg == -180.0:
        angle_deg = 180.0
    angle_deg = round(float(angle_deg), 2)
    if start_pt[1] == end_pt[1]:
        angle_deg = 0.0 if dx >= 0 else 180.0
    elif start_pt[0] == end_pt[0]:
        angle_deg = 90.0 if dy >= 0 else -90.0

    # 3. Confidence: length-weighted average
    total_len = sum(s.length_px for s in group)
    if total_len > 0:
        conf = sum(s.length_px * s.confidence for s in group) / total_len
    else:
        conf = max(s.confidence for s in group)
    confidence = round(float(conf), 3)

    # 4. Source: combined unique values preserving deterministic order
    source = list(dict.fromkeys(src for s in group for src in s.source))

    # 5. Thickness: length-weighted if values differ, preserved if equal, None if none
    thick_vals = [s.thickness_px for s in group if s.thickness_px is not None]
    if not thick_vals:
        thickness_px = None
    elif all(abs(t - thick_vals[0]) < 1e-4 for t in thick_vals):
        thickness_px = thick_vals[0]
    else:
        t_weights = [s.length_px for s in group if s.thickness_px is not None]
        if sum(t_weights) > 0:
            thickness_px = round(
                sum(t * w for t, w in zip(thick_vals, t_weights)) / sum(t_weights), 2
            )
        else:
            thickness_px = round(sum(thick_vals) / len(thick_vals), 2)

    # 6. Metric endpoints: None for newly extended merged geometries to avoid
    # fabricating invalid metric positions prior to calibration
    return WallSegment(
        id=anchor.id,
        start=start_pt,
        end=end_pt,
        length_px=length_px,
        angle_deg=angle_deg,
        confidence=confidence,
        source=source,
        thickness_px=thickness_px,
        start_metric=None,
        end_metric=None,
    )


def merge_collinear_segments(
    segments: list[WallSegment],
    *,
    angle_tolerance_deg: float = 5.0,
    distance_tolerance_px: float = 3.0,
    gap_tolerance_px: float = 5.0,
) -> list[WallSegment]:
    """Merge collinear, approximately co-linear wall segments.

    Parameters
    ----------
    segments : list[WallSegment]
        Input list of wall segments. Original objects are preserved.
    angle_tolerance_deg : float, optional
        Maximum angular difference allowed for collinearity modulo 180° (default: 5.0°).
    distance_tolerance_px : float, optional
        Maximum perpendicular offset from the supporting line (default: 3.0 px).
    gap_tolerance_px : float, optional
        Maximum longitudinal gap allowed between intervals (default: 5.0 px).

    Returns
    -------
    list[WallSegment]
        New list of merged and unmerged WallSegment objects in deterministic order.
    """
    if not segments:
        return []

    # Separate zero-length segments and deduplicate exact duplicate instances
    valid_segments: list[WallSegment] = []
    zero_length_segments: list[WallSegment] = []
    seen_unique: set[tuple[str, Point, Point]] = set()

    for seg in segments:
        key = (seg.id, seg.start, seg.end)
        if key in seen_unique:
            continue
        seen_unique.add(key)

        dx = seg.end[0] - seg.start[0]
        dy = seg.end[1] - seg.start[1]
        if math.hypot(dx, dy) < 1e-6:
            zero_length_segments.append(seg)
        else:
            valid_segments.append(seg)

    n = len(valid_segments)
    if n == 0:
        return [_merge_segment_group([z]) for z in zero_length_segments]

    # Build adjacency list for pairwise-compatible segments
    adj: list[list[int]] = [[] for _ in range(n)]
    for i in range(n):
        for j in range(i + 1, n):
            if _are_segments_collinear(
                valid_segments[i],
                valid_segments[j],
                angle_tolerance_deg=angle_tolerance_deg,
                distance_tolerance_px=distance_tolerance_px,
                gap_tolerance_px=gap_tolerance_px,
            ):
                adj[i].append(j)
                adj[j].append(i)

    # Find connected components deterministically
    visited = [False] * n
    merged_results: list[WallSegment] = []

    for i in range(n):
        if visited[i]:
            continue
        # BFS traversal
        comp_indices: list[int] = []
        queue = [i]
        visited[i] = True
        while queue:
            curr = queue.pop(0)
            comp_indices.append(curr)
            for nbr in sorted(adj[curr]):
                if not visited[nbr]:
                    visited[nbr] = True
                    queue.append(nbr)

        comp_segments = [valid_segments[idx] for idx in comp_indices]
        merged_results.append(_merge_segment_group(comp_segments))

    # Append zero-length segments safely
    for z in zero_length_segments:
        merged_results.append(_merge_segment_group([z]))

    # Sort deterministically by spatial coordinates and ID
    merged_results.sort(
        key=lambda s: (s.start[0], s.start[1], s.end[0], s.end[1], s.id)
    )

    return merged_results
