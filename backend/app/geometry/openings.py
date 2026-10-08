"""
Opening Reconciliation module (Phase 8).

Reconciles predicted Opening objects (doors and windows) against reconstructed
WallSegment geometry by projecting endpoints, assigning wall references, and
filtering out false-positive openings far from any supporting wall.
"""

from __future__ import annotations

import math
from typing import Sequence

from app.geometry.types import Opening, Point, WallSegment


def _round_pt(p: Point, decimals: int = 2) -> Point:
    """Round point coordinates to specified decimal places."""
    return (round(float(p[0]), decimals), round(float(p[1]), decimals))


def _dist(p1: Point, p2: Point) -> float:
    """Euclidean distance between two points."""
    return math.hypot(p2[0] - p1[0], p2[1] - p1[1])


def _project_point_on_wall(
    p: Point,
    w_start: Point,
    w_end: Point,
    length_sq: float,
) -> tuple[float, Point, float]:
    """Project point p onto infinite wall line.

    Returns (t, proj_pt, perp_dist).
    """
    dx = w_end[0] - w_start[0]
    dy = w_end[1] - w_start[1]
    t = ((p[0] - w_start[0]) * dx + (p[1] - w_start[1]) * dy) / length_sq
    proj_x = w_start[0] + t * dx
    proj_y = w_start[1] + t * dy
    perp_dist = math.hypot(p[0] - proj_x, p[1] - proj_y)
    return t, (proj_x, proj_y), perp_dist


def _evaluate_wall_candidate(
    opening: Opening,
    wall: WallSegment,
    *,
    wall_distance_tolerance_px: float,
    projection_tolerance_px: float,
) -> tuple[bool, float, float, tuple[float, Point], tuple[float, Point]]:
    """Evaluate whether a wall is a valid candidate for the given opening.

    Returns (is_valid, dist_to_wall, overlap_px, (t1, proj1), (t2, proj2)).
    """
    dx_w = wall.end[0] - wall.start[0]
    dy_w = wall.end[1] - wall.start[1]
    len_sq = dx_w * dx_w + dy_w * dy_w
    wall_len = math.sqrt(len_sq)

    if wall_len < 1e-4:
        return False, float("inf"), 0.0, (0.0, (0.0, 0.0)), (0.0, (0.0, 0.0))

    # Project both opening endpoints onto wall line
    t1, proj1, perp_dist1 = _project_point_on_wall(opening.start, wall.start, wall.end, len_sq)
    t2, proj2, perp_dist2 = _project_point_on_wall(opening.end, wall.start, wall.end, len_sq)

    # 1. Perpendicular distance tolerance check
    if perp_dist1 > wall_distance_tolerance_px or perp_dist2 > wall_distance_tolerance_px:
        return False, float("inf"), 0.0, (t1, proj1), (t2, proj2)

    # 2. Longitudinal position along wall
    s1 = t1 * wall_len
    s2 = t2 * wall_len
    s_min = min(s1, s2)
    s_max = max(s1, s2)

    ext_left = max(0.0, -s_min)
    ext_right = max(0.0, s_max - wall_len)

    if ext_left > projection_tolerance_px or ext_right > projection_tolerance_px:
        return False, float("inf"), 0.0, (t1, proj1), (t2, proj2)

    # 3. Overlap check with wall segment
    overlap = max(0.0, min(s_max, wall_len) - max(s_min, 0.0))
    open_len = math.hypot(opening.end[0] - opening.start[0], opening.end[1] - opening.start[1])

    if open_len > 1e-4 and overlap <= 0.0:
        return False, float("inf"), 0.0, (t1, proj1), (t2, proj2)

    # 4. Opening-to-wall distance (using clamped closest points on wall segment)
    t1_clamped = max(0.0, min(1.0, t1))
    t2_clamped = max(0.0, min(1.0, t2))
    p1_seg = (wall.start[0] + t1_clamped * dx_w, wall.start[1] + t1_clamped * dy_w)
    p2_seg = (wall.start[0] + t2_clamped * dx_w, wall.start[1] + t2_clamped * dy_w)
    dist_to_wall = (_dist(opening.start, p1_seg) + _dist(opening.end, p2_seg)) / 2.0

    return True, dist_to_wall, overlap, (t1, proj1), (t2, proj2)


def reconcile_openings(
    openings: list[Opening],
    walls: list[WallSegment],
    *,
    wall_distance_tolerance_px: float = 5.0,
    projection_tolerance_px: float = 3.0,
) -> list[Opening]:
    """Reconcile openings (doors and windows) against cleaned wall geometry.

    Parameters
    ----------
    openings : list[Opening]
        List of candidate Opening objects. Original objects are preserved.
    walls : list[WallSegment]
        List of reconstructed WallSegment objects. Original objects are preserved.
    wall_distance_tolerance_px : float, optional
        Maximum allowable perpendicular offset from a candidate wall (default: 5.0 px).
    projection_tolerance_px : float, optional
        Maximum allowable longitudinal extension beyond wall endpoints (default: 3.0 px).

    Returns
    -------
    list[Opening]
        New list of Opening objects with projected geometry, assigned wall_id,
        and canonical orientation matching wall direction where reconciled.
    """
    if not openings:
        return []

    # 1. Deduplicate identical opening inputs deterministically
    unique_openings: list[Opening] = []
    seen_openings: set[tuple[str, str, Point, Point]] = set()

    for op in openings:
        p1 = _round_pt(op.start)
        p2 = _round_pt(op.end)
        key = (op.id, op.type, min(p1, p2), max(p1, p2))
        if key in seen_openings:
            continue
        seen_openings.add(key)
        unique_openings.append(op)

    # Filter out degenerate walls
    valid_walls = [
        w for w in walls
        if math.hypot(w.end[0] - w.start[0], w.end[1] - w.start[1]) >= 1e-4
    ]

    reconciled_openings: list[Opening] = []

    for op in unique_openings:
        best_wall: WallSegment | None = None
        best_key: tuple[float, float, str] | None = None
        best_proj: tuple[Point, Point] | None = None

        for w in valid_walls:
            is_valid, dist_to_wall, overlap, (t1, proj1), (t2, proj2) = _evaluate_wall_candidate(
                op,
                w,
                wall_distance_tolerance_px=wall_distance_tolerance_px,
                projection_tolerance_px=projection_tolerance_px,
            )

            if not is_valid:
                continue

            # Tie-break key:
            # 1. smallest distance to wall
            # 2. largest overlap with wall (negated)
            # 3. lexicographically smallest wall.id
            candidate_key = (round(dist_to_wall, 4), -round(overlap, 4), w.id)

            if best_key is None or candidate_key < best_key:
                best_key = candidate_key
                best_wall = w

                # Orient projected endpoints canonically along the wall direction
                # (smaller parameter t comes first)
                if t1 <= t2:
                    best_proj = (_round_pt(proj1), _round_pt(proj2))
                else:
                    best_proj = (_round_pt(proj2), _round_pt(proj1))

        if best_wall is not None and best_proj is not None:
            # Reconciled opening with projected geometry on best wall
            reconciled_openings.append(
                Opening(
                    id=op.id,
                    type=op.type,
                    start=best_proj[0],
                    end=best_proj[1],
                    wall_id=best_wall.id,
                    confidence=op.confidence,
                    source=list(op.source),
                )
            )
        else:
            # Unmatched opening: preserve coordinates, keep wall_id as None
            reconciled_openings.append(
                Opening(
                    id=op.id,
                    type=op.type,
                    start=_round_pt(op.start),
                    end=_round_pt(op.end),
                    wall_id=None,
                    confidence=op.confidence,
                    source=list(op.source),
                )
            )

    return reconciled_openings
