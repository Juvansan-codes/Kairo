"""
Wall graph generation module (Phase 4).

Converts a list of WallSegment objects into a structured WallGraph comprising
nodes (endpoints, junctions) and edges (wall segments with metadata).
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Literal

from app.geometry.types import Point, WallSegment

NodeType = Literal["endpoint", "junction"]


@dataclass
class WallNode:
    """A geometric vertex in the wall graph.

    Represents an endpoint or a junction where one or more wall segments meet.
    """

    id: str
    x: float
    y: float
    type: NodeType = "endpoint"


@dataclass
class WallEdge:
    """A wall segment connecting two graph nodes with preserved metadata."""

    id: str
    start_node_id: str
    end_node_id: str
    wall_id: str

    length_px: float = 0.0
    angle_deg: float = 0.0

    confidence: float = 0.0
    source: list[str] = field(default_factory=list)

    thickness_px: float | None = None
    start_metric: Point | None = None
    end_metric: Point | None = None

    segment: WallSegment | None = None


@dataclass
class WallGraph:
    """Graph representation of reconstructed walls.

    Attributes
    ----------
    nodes : dict[str, WallNode]
        Dictionary mapping node IDs to WallNode objects.
    edges : dict[str, WallEdge]
        Dictionary mapping edge IDs to WallEdge objects.
    """

    nodes: dict[str, WallNode] = field(default_factory=dict)
    edges: dict[str, WallEdge] = field(default_factory=dict)

    def get_node(self, node_id: str) -> WallNode | None:
        """Return the WallNode with the given ID, or None if not found."""
        return self.nodes.get(node_id)

    def get_edge(self, edge_id: str) -> WallEdge | None:
        """Return the WallEdge with the given ID, or None if not found."""
        return self.edges.get(edge_id)

    def neighbors(self, node_id: str) -> list[str]:
        """Return a list of neighboring node IDs connected by edges."""
        nbrs: list[str] = []
        for edge in self.edges.values():
            if edge.start_node_id == node_id:
                nbrs.append(edge.end_node_id)
            elif edge.end_node_id == node_id:
                nbrs.append(edge.start_node_id)
        return nbrs

    def adjacent_edges(self, node_id: str) -> list[WallEdge]:
        """Return all edges incident to the specified node ID."""
        return [
            e
            for e in self.edges.values()
            if e.start_node_id == node_id or e.end_node_id == node_id
        ]


def _find_or_create_node(
    x: float,
    y: float,
    nodes: dict[str, WallNode],
    tolerance: float,
) -> str:
    """Find an existing node within *tolerance* distance, or create a new one.

    To avoid transitive chaining / drift, points are matched to the closest
    existing node within tolerance.
    """
    best_id: str | None = None
    min_dist = float("inf")

    for node_id, node in nodes.items():
        dist = math.hypot(node.x - x, node.y - y)
        if dist <= tolerance and dist < min_dist:
            min_dist = dist
            best_id = node_id

    if best_id is not None:
        return best_id

    new_id = f"node_{len(nodes)}"
    nodes[new_id] = WallNode(id=new_id, x=round(x, 2), y=round(y, 2))
    return new_id


def build_wall_graph(
    segments: list[WallSegment],
    *,
    tolerance: float = 3.0,
) -> WallGraph:
    """Build a structured WallGraph from a collection of WallSegment objects.

    Parameters
    ----------
    segments : list[WallSegment]
        List of wall segments (typically produced by extract_wall_segments).
    tolerance : float, optional
        Geometric distance threshold in pixels for deduplicating segment
        endpoints into shared graph nodes (default: 3.0).

    Returns
    -------
    WallGraph
        Structured graph containing deduplicated WallNodes and WallEdges.
    """
    if not segments:
        return WallGraph()

    nodes: dict[str, WallNode] = {}
    edges: dict[str, WallEdge] = {}
    seen_wall_ids: set[str] = set()

    for seg in segments:
        # Check for zero-length geometric segment before processing
        dx_raw = seg.end[0] - seg.start[0]
        dy_raw = seg.end[1] - seg.start[1]
        raw_len = math.hypot(dx_raw, dy_raw)
        if raw_len < 1e-6:
            continue

        # Avoid processing duplicate wall segment instances
        if seg.id in seen_wall_ids:
            continue

        start_node_id = _find_or_create_node(seg.start[0], seg.start[1], nodes, tolerance)
        end_node_id = _find_or_create_node(seg.end[0], seg.end[1], nodes, tolerance)

        # Ignore segments that collapse to the same node under tolerance
        if start_node_id == end_node_id:
            continue

        # Prevent duplicate edge connecting the exact same pair of nodes
        edge_key = (min(start_node_id, end_node_id), max(start_node_id, end_node_id))
        is_duplicate_pair = any(
            (min(e.start_node_id, e.end_node_id), max(e.start_node_id, e.end_node_id)) == edge_key
            for e in edges.values()
        )
        if is_duplicate_pair:
            continue

        seen_wall_ids.add(seg.id)

        # Preserve metadata or fallback if not populated
        length_px = seg.length_px if seg.length_px > 0.0 else round(raw_len, 2)
        if seg.angle_deg != 0.0 or raw_len == 0.0:
            angle_deg = seg.angle_deg
        else:
            angle_deg = round(math.degrees(math.atan2(dy_raw, dx_raw)), 2)

        edge_id = f"edge_{len(edges)}"
        edges[edge_id] = WallEdge(
            id=edge_id,
            start_node_id=start_node_id,
            end_node_id=end_node_id,
            wall_id=seg.id,
            length_px=length_px,
            angle_deg=angle_deg,
            confidence=seg.confidence,
            source=list(seg.source),
            thickness_px=seg.thickness_px,
            start_metric=seg.start_metric,
            end_metric=seg.end_metric,
            segment=seg,
        )

    # Classify node types based on incident edge degree
    node_degrees: dict[str, int] = {n_id: 0 for n_id in nodes}
    for e in edges.values():
        node_degrees[e.start_node_id] += 1
        node_degrees[e.end_node_id] += 1

    for n_id, deg in node_degrees.items():
        nodes[n_id].type = "junction" if deg >= 2 else "endpoint"

    return WallGraph(nodes=nodes, edges=edges)
