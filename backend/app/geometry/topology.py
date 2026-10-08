"""
Topology Validation module (Phase 11).

Validates the structural consistency, integrity, and connectivity of
reconstructed floorplan geometry (walls, rooms, doors, windows).
Performs validation only without mutating or repairing geometry.
"""

from __future__ import annotations

import math
from typing import Any

from shapely.geometry import Polygon

from app.geometry.graph import build_wall_graph
from app.geometry.types import Opening, RoomPolygon, WallSegment


def validate_topology(
    walls: list[WallSegment],
    rooms: list[RoomPolygon],
    doors: list[Opening],
    windows: list[Opening],
    *,
    node_tolerance_px: float = 3.0,
) -> dict[str, Any]:
    """Validate structural and topological consistency of reconstructed floorplan elements.

    Parameters
    ----------
    walls : list[WallSegment]
        List of reconstructed wall segments.
    rooms : list[RoomPolygon]
        List of polygonized room regions.
    doors : list[Opening]
        List of doors associated with walls.
    windows : list[Opening]
        List of windows associated with walls.
    node_tolerance_px : float, optional
        Tolerance in pixels for graph node endpoint deduplication (default: 3.0).

    Returns
    -------
    dict
        Structured validation result containing:
        - valid: bool (True if errors list is empty, False otherwise)
        - errors: list[str] (blocking structural inconsistencies)
        - warnings: list[str] (non-blocking topological advisories)
        - stats: dict (summary metrics of the floorplan structure)
    """
    errors: list[str] = []
    warnings: list[str] = []

    # ---------------------------------------------------------
    # 1. Wall validation
    # ---------------------------------------------------------
    seen_wall_ids: set[str] = set()
    valid_wall_ids: set[str] = set()

    for w in walls:
        # Check duplicate ID
        if w.id in seen_wall_ids:
            errors.append(f"Duplicate wall ID '{w.id}'")
        else:
            seen_wall_ids.add(w.id)

        # Check finite coordinates
        if not (
            math.isfinite(w.start[0])
            and math.isfinite(w.start[1])
            and math.isfinite(w.end[0])
            and math.isfinite(w.end[1])
        ):
            errors.append(f"Wall '{w.id}' has non-finite coordinates")
            continue

        # Check length
        dx = w.end[0] - w.start[0]
        dy = w.end[1] - w.start[1]
        length = math.hypot(dx, dy)

        if length < 1e-6:
            errors.append(f"Wall '{w.id}' has zero length")
        elif length < 1.0:
            errors.append(f"Wall '{w.id}' has tiny length ({length:.2f} px < 1.0 px)")
        else:
            valid_wall_ids.add(w.id)

    # ---------------------------------------------------------
    # 2. Graph & Connectivity validation
    # ---------------------------------------------------------
    graph = build_wall_graph(walls, tolerance=node_tolerance_px)
    node_count = len(graph.nodes)
    edge_count = len(graph.edges)

    # Compute connected components via BFS
    visited_nodes: set[str] = set()
    connected_components = 0

    for node_id in graph.nodes:
        if node_id in visited_nodes:
            continue
        connected_components += 1
        queue = [node_id]
        visited_nodes.add(node_id)
        while queue:
            curr = queue.pop(0)
            for nbr in graph.neighbors(curr):
                if nbr not in visited_nodes:
                    visited_nodes.add(nbr)
                    queue.append(nbr)

    # Count dangling endpoints (nodes of degree 1)
    dangling_endpoint_count = sum(
        1 for n_id in graph.nodes if len(graph.adjacent_edges(n_id)) == 1
    )

    # Warnings for connectivity anomalies
    if connected_components > 1:
        warnings.append(
            f"Wall graph contains {connected_components} disconnected components"
        )

    if dangling_endpoint_count > 0:
        warnings.append(
            f"Detected {dangling_endpoint_count} dangling wall endpoint(s)"
        )

    # Check for completely isolated wall segments
    for edge in graph.edges.values():
        start_deg = len(graph.adjacent_edges(edge.start_node_id))
        end_deg = len(graph.adjacent_edges(edge.end_node_id))
        if start_deg == 1 and end_deg == 1:
            warnings.append(
                f"Isolated wall segment '{edge.wall_id}' has no junction connections"
            )

    # ---------------------------------------------------------
    # 3. Room validation
    # ---------------------------------------------------------
    seen_room_ids: set[str] = set()

    for r in rooms:
        # Check duplicate room ID
        if r.id in seen_room_ids:
            errors.append(f"Duplicate room ID '{r.id}'")
        else:
            seen_room_ids.add(r.id)

        # Check vertex count
        if len(r.polygon) < 3:
            errors.append(
                f"Room '{r.id}' has fewer than 3 vertices ({len(r.polygon)})"
            )
            continue

        # Check reported area
        if r.area_px2 <= 0.0:
            errors.append(f"Room '{r.id}' has non-positive area ({r.area_px2})")

        # Validate geometry using Shapely
        try:
            poly = Polygon(r.polygon)
            if not poly.is_valid:
                errors.append(f"Room '{r.id}' has invalid polygon geometry")
            elif poly.area <= 0.0:
                errors.append(f"Room '{r.id}' has zero or degenerate geometric area")
        except Exception as e:
            errors.append(f"Room '{r.id}' polygon construction failed: {e}")

    # ---------------------------------------------------------
    # 4. Door validation
    # ---------------------------------------------------------
    seen_door_ids: set[str] = set()

    for d in doors:
        if d.id in seen_door_ids:
            errors.append(f"Duplicate door ID '{d.id}'")
        else:
            seen_door_ids.add(d.id)

        d_len = math.hypot(d.end[0] - d.start[0], d.end[1] - d.start[1])
        if d_len < 1e-4:
            errors.append(f"Door '{d.id}' has zero length")

        if d.wall_id is not None:
            if d.wall_id not in seen_wall_ids:
                errors.append(f"Door '{d.id}' references missing wall '{d.wall_id}'")
        else:
            warnings.append(f"Door '{d.id}' is not assigned to any wall")

    # ---------------------------------------------------------
    # 5. Window validation
    # ---------------------------------------------------------
    seen_window_ids: set[str] = set()

    for w_open in windows:
        if w_open.id in seen_window_ids:
            errors.append(f"Duplicate window ID '{w_open.id}'")
        else:
            seen_window_ids.add(w_open.id)

        w_len = math.hypot(w_open.end[0] - w_open.start[0], w_open.end[1] - w_open.start[1])
        if w_len < 1e-4:
            errors.append(f"Window '{w_open.id}' has zero length")

        if w_open.wall_id is not None:
            if w_open.wall_id not in seen_wall_ids:
                errors.append(
                    f"Window '{w_open.id}' references missing wall '{w_open.wall_id}'"
                )
        else:
            warnings.append(f"Window '{w_open.id}' is not assigned to any wall")

    # ---------------------------------------------------------
    # Deterministic sorting of output errors and warnings
    # ---------------------------------------------------------
    errors.sort()
    warnings.sort()

    stats = {
        "wall_count": len(walls),
        "room_count": len(rooms),
        "door_count": len(doors),
        "window_count": len(windows),
        "node_count": node_count,
        "edge_count": edge_count,
        "connected_components": connected_components,
        "dangling_endpoint_count": dangling_endpoint_count,
    }

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "stats": stats,
    }
