"""
Room Polygonization module (Phase 9).

Converts cleaned WallSegment geometry into bounded RoomPolygon objects
representing enclosed room spaces.
"""

from __future__ import annotations

import math
from typing import Sequence

from shapely.geometry import LineString, Point as ShapelyPoint, Polygon
from shapely.ops import polygonize, unary_union

from app.geometry.graph import build_wall_graph
from app.geometry.types import Point, RoomPolygon, WallSegment


def _round_coord(p: tuple[float, float], decimals: int = 2) -> Point:
    """Round a 2D coordinate to specified decimals."""
    return (round(float(p[0]), decimals), round(float(p[1]), decimals))


def _canonicalize_ring(ring_coords: list[tuple[float, float]]) -> list[Point]:
    """Canonicalize ring coordinates: CCW orientation and minimum vertex start.

    Removes repeated closing coordinate and returns unique vertices.
    """
    if len(ring_coords) > 1 and ring_coords[0] == ring_coords[-1]:
        coords = ring_coords[:-1]
    else:
        coords = list(ring_coords)

    if len(coords) < 3:
        return [_round_coord(c) for c in coords]

    # Ensure counter-clockwise orientation
    poly = Polygon(coords)
    if not poly.exterior.is_ccw:
        coords = coords[::-1]

    rounded = [_round_coord(c) for c in coords]

    # Rotate list so that lexicographically smallest vertex is at index 0
    min_idx = min(range(len(rounded)), key=lambda i: (rounded[i][0], rounded[i][1]))
    return rounded[min_idx:] + rounded[:min_idx]


def polygonize_rooms(
    walls: list[WallSegment],
    *,
    min_area_px2: float = 25.0,
    node_tolerance_px: float = 3.0,
) -> list[RoomPolygon]:
    """Extract closed room regions from wall segments.

    Parameters
    ----------
    walls : list[WallSegment]
        List of wall segments forming the floor plan geometry.
    min_area_px2 : float, optional
        Minimum area threshold in square pixels to qualify as a valid room (default: 25.0).
    node_tolerance_px : float, optional
        Tolerance in pixels for snapping nearby wall endpoints into shared graph nodes (default: 3.0).

    Returns
    -------
    list[RoomPolygon]
        Deterministic list of reconstructed RoomPolygon objects.
    """
    if not walls:
        return []

    # 1. Build snapped wall graph to resolve endpoint tolerances
    graph = build_wall_graph(walls, tolerance=node_tolerance_px)
    if not graph.edges:
        return []

    # 2. Extract snapped line segments from the graph
    lines: list[LineString] = []
    for edge in graph.edges.values():
        start_node = graph.get_node(edge.start_node_id)
        end_node = graph.get_node(edge.end_node_id)
        if start_node is None or end_node is None:
            continue
        p1 = (start_node.x, start_node.y)
        p2 = (end_node.x, end_node.y)
        if math.hypot(p2[0] - p1[0], p2[1] - p1[1]) >= 1e-4:
            lines.append(LineString([p1, p2]))

    if not lines:
        return []

    # 3. Node intersecting lines and extract elementary polygons
    noded_network = unary_union(lines)
    raw_polygons = list(polygonize(noded_network))

    # 4. Filter, canonicalize, and deduplicate valid room polygons
    candidates: list[tuple[tuple[float, float], float, list[Point], list[str], float]] = []
    seen_polygons: set[tuple[Point, ...]] = set()

    for poly in raw_polygons:
        if not poly.is_valid or poly.geom_type != "Polygon":
            continue

        area_px2 = round(float(poly.area), 2)
        if area_px2 < min_area_px2:
            continue

        ring = _canonicalize_ring(list(poly.exterior.coords))
        if len(ring) < 3:
            continue

        ring_tuple = tuple(ring)
        if ring_tuple in seen_polygons:
            continue
        seen_polygons.add(ring_tuple)

        # Find contributing walls along the boundary of this polygon
        contributing_walls: list[WallSegment] = []
        for w in walls:
            mid_x = (w.start[0] + w.end[0]) / 2.0
            mid_y = (w.start[1] + w.end[1]) / 2.0
            mid_pt = ShapelyPoint(mid_x, mid_y)
            if mid_pt.distance(poly.exterior) <= node_tolerance_px:
                contributing_walls.append(w)

        # Conservative confidence: minimum confidence among contributing walls
        if contributing_walls:
            confidence = round(min(w.confidence for w in contributing_walls), 3)
            sources = list(dict.fromkeys(src for w in contributing_walls for src in w.source))
        else:
            confidence = 0.0
            sources = []

        centroid = (round(float(poly.centroid.x), 2), round(float(poly.centroid.y), 2))
        candidates.append((centroid, area_px2, ring, sources, confidence))

    # 5. Sort rooms deterministically by centroid (y, then x)
    candidates.sort(key=lambda item: (item[0][1], item[0][0], item[1]))

    # 6. Construct final RoomPolygon objects with deterministic IDs
    room_polygons: list[RoomPolygon] = []
    for idx, (centroid, area_px2, ring, sources, confidence) in enumerate(candidates):
        room_polygons.append(
            RoomPolygon(
                id=f"room_{idx + 1}",
                polygon=ring,
                area_px2=area_px2,
                area_m2=None,
                label=None,
                confidence=confidence,
                source=sources,
            )
        )

    return room_polygons
