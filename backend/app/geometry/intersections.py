"""
Intersection detection and geometry cleanup for WallSegments (Phase 7).

Detects proper crossings, T-junctions, and near-intersections between wall
segments, splits segments at intersection points, normalizes junction
coordinates, and eliminates post-split micro-segments.
"""

from __future__ import annotations

import math
from typing import Sequence

import numpy as np

from app.geometry.types import Point, WallSegment


def _round_pt(p: Point, decimals: int = 2) -> Point:
    """Round point coordinates to specified decimal places."""
    return (round(float(p[0]), decimals), round(float(p[1]), decimals))


def _dist(p1: Point, p2: Point) -> float:
    """Euclidean distance between two points."""
    return math.hypot(p2[0] - p1[0], p2[1] - p1[1])


def _closest_points_between_segments(
    p1: Point, p2: Point, q1: Point, q2: Point
) -> tuple[Point, Point, float, float, float]:
    """Find closest points between segment p1->p2 and q1->q2.

    Returns (p_star, q_star, dist, s, t) where s, t in [0, 1].
    """
    d1 = (p2[0] - p1[0], p2[1] - p1[1])
    d2 = (q2[0] - q1[0], q2[1] - q1[1])
    r = (p1[0] - q1[0], p1[1] - q1[1])

    a = d1[0] * d1[0] + d1[1] * d1[1]
    e = d2[0] * d2[0] + d2[1] * d2[1]
    f = d2[0] * r[0] + d2[1] * r[1]

    if a < 1e-12 and e < 1e-12:
        return p1, q1, math.hypot(r[0], r[1]), 0.0, 0.0
    if a < 1e-12:
        s = 0.0
        t = max(0.0, min(1.0, f / e)) if e > 1e-12 else 0.0
    elif e < 1e-12:
        t = 0.0
        c = d1[0] * r[0] + d1[1] * r[1]
        s = max(0.0, min(1.0, -c / a))
    else:
        c = d1[0] * r[0] + d1[1] * r[1]
        b = d1[0] * d2[0] + d1[1] * d2[1]
        denom = a * e - b * b
        if denom > 1e-12:
            s = max(0.0, min(1.0, (b * f - c * e) / denom))
        else:
            s = 0.0
        t = (b * s + f) / e
        if t < 0.0:
            t = 0.0
            s = max(0.0, min(1.0, -c / a))
        elif t > 1.0:
            t = 1.0
            s = max(0.0, min(1.0, (b - c) / a))

    p_star = (p1[0] + s * d1[0], p1[1] + s * d1[1])
    q_star = (q1[0] + t * d2[0], q1[1] + t * d2[1])
    dist = math.hypot(p_star[0] - q_star[0], p_star[1] - q_star[1])
    return p_star, q_star, dist, s, t


def _compute_angle_deg(start: Point, end: Point) -> float:
    """Compute orientation angle in degrees in [-180, 180] with axis snapping."""
    dx = end[0] - start[0]
    dy = end[1] - start[1]
    angle_deg = math.degrees(math.atan2(dy, dx))
    if angle_deg == -180.0:
        angle_deg = 180.0
    angle_deg = round(float(angle_deg), 2)
    if abs(start[1] - end[1]) < 1e-4:
        angle_deg = 0.0 if dx >= 0 else 180.0
    elif abs(start[0] - end[0]) < 1e-4:
        angle_deg = 90.0 if dy >= 0 else -90.0
    return angle_deg


def _interpolate_metric(
    start_m: Point | None, end_m: Point | None, t: float
) -> Point | None:
    """Interpolate metric coordinate at parameter t in [0, 1]."""
    if start_m is None or end_m is None:
        return None
    mx = round(start_m[0] + t * (end_m[0] - start_m[0]), 4)
    my = round(start_m[1] + t * (end_m[1] - start_m[1]), 4)
    return (mx, my)


def split_wall_intersections(
    segments: list[WallSegment],
    *,
    intersection_tolerance_px: float = 1.0,
    endpoint_tolerance_px: float = 2.0,
    min_segment_length_px: float = 1.0,
) -> list[WallSegment]:
    """Split intersecting wall segments at their intersection points.

    Parameters
    ----------
    segments : list[WallSegment]
        Input list of wall segments. Original objects are preserved.
    intersection_tolerance_px : float, optional
        Tolerance for detecting crossing and near-intersections (default: 1.0 px).
    endpoint_tolerance_px : float, optional
        Distance threshold below which an intersection is treated as touching
        an existing endpoint rather than splitting the segment internally (default: 2.0 px).
    min_segment_length_px : float, optional
        Minimum allowable length for valid wall segments. Shorter pieces are discarded
        (default: 1.0 px).

    Returns
    -------
    list[WallSegment]
        New list of split and unsplit WallSegment objects in deterministic order.
    """
    if not segments:
        return []

    # 1. Deduplicate identical inputs deterministically & filter tiny segments
    unique_segments: list[WallSegment] = []
    seen_geom: set[tuple[Point, Point]] = set()

    for seg in segments:
        dx = seg.end[0] - seg.start[0]
        dy = seg.end[1] - seg.start[1]
        length = math.hypot(dx, dy)
        if length < min_segment_length_px:
            continue

        p_start = _round_pt(seg.start)
        p_end = _round_pt(seg.end)
        key = (min(p_start, p_end), max(p_start, p_end))
        if key in seen_geom:
            continue
        seen_geom.add(key)
        unique_segments.append(seg)

    n = len(unique_segments)
    if n == 0:
        return []

    # 2. Pairwise candidate intersection detection
    raw_candidates: list[Point] = []

    for i in range(n):
        s1 = unique_segments[i]
        dx1 = s1.end[0] - s1.start[0]
        dy1 = s1.end[1] - s1.start[1]
        len1 = math.hypot(dx1, dy1)
        if len1 < 1e-6:
            continue
        u1 = (dx1 / len1, dy1 / len1)

        for j in range(i + 1, n):
            s2 = unique_segments[j]
            dx2 = s2.end[0] - s2.start[0]
            dy2 = s2.end[1] - s2.start[1]
            len2 = math.hypot(dx2, dy2)
            if len2 < 1e-6:
                continue
            u2 = (dx2 / len2, dy2 / len2)

            # Skip parallel or collinear segments (angle < 5° modulo 180°)
            cp = abs(u1[0] * u2[1] - u1[1] * u2[0])
            if cp < math.sin(math.radians(5.0)):
                continue

            p_star, q_star, dist, s_param, t_param = _closest_points_between_segments(
                s1.start, s1.end, s2.start, s2.end
            )

            if dist > intersection_tolerance_px:
                continue

            # Determine appropriate contact point coordinate
            s_dist_start = s_param * len1
            s_dist_end = (1.0 - s_param) * len1
            is_s1_internal = (s_dist_start > endpoint_tolerance_px) and (
                s_dist_end > endpoint_tolerance_px
            )

            t_dist_start = t_param * len2
            t_dist_end = (1.0 - t_param) * len2
            is_s2_internal = (t_dist_start > endpoint_tolerance_px) and (
                t_dist_end > endpoint_tolerance_px
            )

            if is_s1_internal and not is_s2_internal:
                # T-junction ending on s1: preserve s1 supporting line
                cand_pt = p_star
            elif is_s2_internal and not is_s1_internal:
                # T-junction ending on s2: preserve s2 supporting line
                cand_pt = q_star
            else:
                cand_pt = ((p_star[0] + q_star[0]) / 2.0, (p_star[1] + q_star[1]) / 2.0)

            raw_candidates.append(_round_pt(cand_pt))

    # 3. Cluster candidate intersection points to canonical junction points
    canonical_points: list[Point] = []
    if raw_candidates:
        # Sort candidates for deterministic clustering
        raw_candidates.sort(key=lambda p: (p[0], p[1]))
        m = len(raw_candidates)
        visited = [False] * m

        for i in range(m):
            if visited[i]:
                continue
            cluster: list[Point] = []
            queue = [i]
            visited[i] = True
            while queue:
                curr = queue.pop(0)
                cluster.append(raw_candidates[curr])
                for k in range(m):
                    if not visited[k]:
                        if _dist(raw_candidates[curr], raw_candidates[k]) <= intersection_tolerance_px:
                            visited[k] = True
                            queue.append(k)

            cx = round(float(np.mean([p[0] for p in cluster])), 2)
            cy = round(float(np.mean([p[1] for p in cluster])), 2)
            canonical_points.append((cx, cy))

        canonical_points.sort(key=lambda p: (p[0], p[1]))

    # 4. Split and normalize segments with canonical intersection points
    result_segments: list[WallSegment] = []

    for seg in unique_segments:
        p_start = seg.start
        p_end = seg.end
        dx = p_end[0] - p_start[0]
        dy = p_end[1] - p_start[1]
        length = math.hypot(dx, dy)
        u = (dx / length, dy / length)

        snapped_start: Point = p_start
        snapped_end: Point = p_end
        internal_splits: list[tuple[float, Point]] = []

        for c_pt in canonical_points:
            w = (c_pt[0] - p_start[0], c_pt[1] - p_start[1])
            proj = w[0] * u[0] + w[1] * u[1]
            perp_dist = abs(w[0] * u[1] - w[1] * u[0])

            # Check if canonical point is within tolerance of the segment line and span
            if perp_dist > intersection_tolerance_px:
                continue
            if proj < -intersection_tolerance_px or proj > length + intersection_tolerance_px:
                continue

            # Classify as start contact, end contact, or internal split
            if proj <= endpoint_tolerance_px:
                if _dist(p_start, c_pt) <= endpoint_tolerance_px:
                    snapped_start = c_pt
            elif length - proj <= endpoint_tolerance_px:
                if _dist(p_end, c_pt) <= endpoint_tolerance_px:
                    snapped_end = c_pt
            else:
                # Internal split point: preserve axis alignment where applicable
                t_val = proj / length
                if abs(seg.start[1] - seg.end[1]) < 1e-4:
                    split_coord: Point = (c_pt[0], seg.start[1])
                elif abs(seg.start[0] - seg.end[0]) < 1e-4:
                    split_coord = (seg.start[0], c_pt[1])
                else:
                    split_coord = (
                        round(p_start[0] + t_val * dx, 2),
                        round(p_start[1] + t_val * dy, 2),
                    )
                internal_splits.append((t_val, split_coord))

        if not internal_splits:
            # Unsplit segment: update endpoints if snapped
            cur_dx = snapped_end[0] - snapped_start[0]
            cur_dy = snapped_end[1] - snapped_start[1]
            cur_len = round(float(math.hypot(cur_dx, cur_dy)), 2)

            if cur_len < min_segment_length_px:
                continue

            cur_angle = _compute_angle_deg(snapped_start, snapped_end)
            result_segments.append(
                WallSegment(
                    id=seg.id,
                    start=snapped_start,
                    end=snapped_end,
                    length_px=cur_len,
                    angle_deg=cur_angle,
                    confidence=seg.confidence,
                    source=list(seg.source),
                    thickness_px=seg.thickness_px,
                    start_metric=tuple(seg.start_metric) if seg.start_metric is not None else None,
                    end_metric=tuple(seg.end_metric) if seg.end_metric is not None else None,
                )
            )
        else:
            # Sort internal split points by parameter t
            internal_splits.sort(key=lambda item: item[0])

            # Deduplicate split points that are too close together
            filtered_splits: list[tuple[float, Point]] = []
            for t_val, coord in internal_splits:
                if not filtered_splits:
                    filtered_splits.append((t_val, coord))
                else:
                    prev_t = filtered_splits[-1][0]
                    if (t_val - prev_t) * length >= min_segment_length_px:
                        filtered_splits.append((t_val, coord))

            # Assemble piece endpoints sequence
            pts_sequence: list[tuple[float, Point]] = (
                [(0.0, snapped_start)]
                + filtered_splits
                + [(1.0, snapped_end)]
            )

            part_idx = 0
            for k in range(len(pts_sequence) - 1):
                t_a, pt_a = pts_sequence[k]
                t_b, pt_b = pts_sequence[k + 1]

                piece_dx = pt_b[0] - pt_a[0]
                piece_dy = pt_b[1] - pt_a[1]
                piece_len = round(float(math.hypot(piece_dx, piece_dy)), 2)

                if piece_len < min_segment_length_px:
                    continue

                piece_angle = _compute_angle_deg(pt_a, pt_b)
                piece_id = f"{seg.id}_part_{part_idx}"
                part_idx += 1

                m_start = _interpolate_metric(seg.start_metric, seg.end_metric, t_a)
                m_end = _interpolate_metric(seg.start_metric, seg.end_metric, t_b)

                result_segments.append(
                    WallSegment(
                        id=piece_id,
                        start=pt_a,
                        end=pt_b,
                        length_px=piece_len,
                        angle_deg=piece_angle,
                        confidence=seg.confidence,
                        source=list(seg.source),
                        thickness_px=seg.thickness_px,
                        start_metric=m_start,
                        end_metric=m_end,
                    )
                )

    # 5. Deterministic sorting of resulting segments
    result_segments.sort(
        key=lambda s: (round(s.start[0], 2), round(s.start[1], 2), round(s.end[0], 2), round(s.end[1], 2), s.id)
    )

    return result_segments
