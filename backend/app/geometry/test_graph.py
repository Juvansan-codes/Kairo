"""
Unit tests for Phase 4 WallGraph construction (backend/app/geometry/graph.py).
"""

from __future__ import annotations

import pytest

from app.geometry.graph import (
    WallEdge,
    WallGraph,
    WallNode,
    build_wall_graph,
)
from app.geometry.types import WallSegment


def _make_segment(
    seg_id: str,
    start: tuple[float, float],
    end: tuple[float, float],
    length_px: float = 100.0,
    angle_deg: float = 0.0,
    confidence: float = 0.95,
    source: list[str] | None = None,
    thickness_px: float | None = 10.0,
    start_metric: tuple[float, float] | None = None,
    end_metric: tuple[float, float] | None = None,
) -> WallSegment:
    """Helper to instantiate a WallSegment for testing."""
    return WallSegment(
        id=seg_id,
        start=start,
        end=end,
        length_px=length_px,
        angle_deg=angle_deg,
        confidence=confidence,
        source=["skeleton"] if source is None else source,
        thickness_px=thickness_px,
        start_metric=start_metric,
        end_metric=end_metric,
    )


class TestWallGraphConstruction:
    """Core tests for WallGraph creation and structure."""

    def test_empty_input_produces_empty_graph(self):
        """15. Empty input produces an empty graph."""
        graph = build_wall_graph([])
        assert isinstance(graph, WallGraph)
        assert len(graph.nodes) == 0
        assert len(graph.edges) == 0

    def test_one_isolated_wall_segment(self):
        """1. One isolated wall segment produces 2 endpoint nodes and 1 edge."""
        seg = _make_segment("wall_1", (10.0, 20.0), (110.0, 20.0), length_px=100.0, angle_deg=0.0)
        graph = build_wall_graph([seg])

        assert len(graph.nodes) == 2
        assert len(graph.edges) == 1

        edge = list(graph.edges.values())[0]
        assert edge.wall_id == "wall_1"
        assert edge.start_node_id in graph.nodes
        assert edge.end_node_id in graph.nodes
        assert edge.start_node_id != edge.end_node_id

        # Both nodes in an isolated segment are endpoints
        for node in graph.nodes.values():
            assert node.type == "endpoint"

    def test_two_connected_wall_segments(self):
        """2. Two connected wall segments share 1 junction node and have 2 endpoints."""
        seg1 = _make_segment("wall_1", (0.0, 0.0), (50.0, 0.0), length_px=50.0)
        seg2 = _make_segment("wall_2", (50.0, 0.0), (50.0, 50.0), length_px=50.0, angle_deg=90.0)

        graph = build_wall_graph([seg1, seg2])

        assert len(graph.nodes) == 3
        assert len(graph.edges) == 2

        # Node at (50, 0) should be classified as junction
        junction_nodes = [n for n in graph.nodes.values() if n.type == "junction"]
        endpoint_nodes = [n for n in graph.nodes.values() if n.type == "endpoint"]

        assert len(junction_nodes) == 1
        assert len(endpoint_nodes) == 2
        assert junction_nodes[0].x == 50.0
        assert junction_nodes[0].y == 0.0

    def test_three_or_more_segments_meeting_at_junction(self):
        """3. Three or more segments meeting at one junction share the junction node."""
        # T-junction: 3 segments meeting at (100, 100)
        seg_left = _make_segment("w_left", (0.0, 100.0), (100.0, 100.0))
        seg_right = _make_segment("w_right", (100.0, 100.0), (200.0, 100.0))
        seg_bottom = _make_segment("w_bottom", (100.0, 100.0), (100.0, 200.0))

        graph = build_wall_graph([seg_left, seg_right, seg_bottom])

        assert len(graph.nodes) == 4  # 3 endpoints + 1 shared junction
        assert len(graph.edges) == 3

        junc = [n for n in graph.nodes.values() if n.type == "junction"]
        assert len(junc) == 1
        assert junc[0].x == 100.0
        assert junc[0].y == 100.0

        # The junction node should be connected to all 3 edges
        incident = graph.adjacent_edges(junc[0].id)
        assert len(incident) == 3

        nbrs = graph.neighbors(junc[0].id)
        assert len(nbrs) == 3

    def test_nearly_identical_endpoints_deduplicated(self):
        """4. Endpoints within tolerance are merged into a single node."""
        seg1 = _make_segment("w1", (100.0, 100.0), (300.0, 100.0))
        # End of seg1 is (300, 100), start of seg2 is (300.3, 100.2) -> dist ~0.36 <= 3.0
        seg2 = _make_segment("w2", (300.3, 100.2), (300.0, 250.0))

        graph = build_wall_graph([seg1, seg2], tolerance=3.0)

        assert len(graph.nodes) == 3  # Start of w1, shared junction near (300, 100), end of w2
        assert len(graph.edges) == 2

        e1 = graph.edges["edge_0"]
        e2 = graph.edges["edge_1"]
        assert e1.end_node_id == e2.start_node_id

    def test_points_outside_tolerance_remain_separate(self):
        """5. Endpoints with distance greater than tolerance remain separate nodes."""
        seg1 = _make_segment("w1", (100.0, 100.0), (300.0, 100.0))
        # Gap is 5.0 px; tolerance is 2.0 px
        seg2 = _make_segment("w2", (305.0, 100.0), (305.0, 250.0))

        graph = build_wall_graph([seg1, seg2], tolerance=2.0)

        assert len(graph.nodes) == 4
        assert len(graph.edges) == 2
        for n in graph.nodes.values():
            assert n.type == "endpoint"

    def test_zero_length_segment_ignored(self):
        """6. Zero-length segment (identical start/end) is safely rejected."""
        seg_zero = _make_segment("w_zero", (50.0, 50.0), (50.0, 50.0), length_px=0.0)
        seg_valid = _make_segment("w_valid", (10.0, 10.0), (80.0, 10.0), length_px=70.0)

        graph = build_wall_graph([seg_zero, seg_valid])

        assert len(graph.edges) == 1
        assert len(graph.nodes) == 2
        assert list(graph.edges.values())[0].wall_id == "w_valid"

    def test_segment_collapsed_under_tolerance_ignored(self):
        """Segment whose endpoints fall within tolerance of each other is safely skipped."""
        seg_tiny = _make_segment("w_tiny", (50.0, 50.0), (50.5, 50.5))  # dist ~0.7 <= 3.0
        graph = build_wall_graph([seg_tiny], tolerance=3.0)

        assert len(graph.edges) == 0

    def test_duplicate_segment_ignored(self):
        """Duplicate wall segment is not added twice."""
        seg = _make_segment("w1", (10.0, 10.0), (100.0, 10.0))
        graph = build_wall_graph([seg, seg])

        assert len(graph.edges) == 1
        assert len(graph.nodes) == 2


class TestMetadataPreservation:
    """Verify that all WallSegment metadata fields are strictly preserved in WallEdge."""

    def test_preservation_of_all_metadata_fields(self):
        """7-12. Verification of ID, length_px, angle_deg, confidence, source, thickness_px."""
        seg = _make_segment(
            seg_id="custom_wall_99",
            start=(15.0, 25.0),
            end=(115.0, 25.0),
            length_px=100.5,
            angle_deg=0.0,
            confidence=0.887,
            source=["skeleton", "ocr_verified"],
            thickness_px=12.5,
            start_metric=(0.5, 1.0),
            end_metric=(3.5, 1.0),
        )

        graph = build_wall_graph([seg])
        edge = list(graph.edges.values())[0]

        # 7. WallSegment ID
        assert edge.wall_id == "custom_wall_99"
        # 8. length_px
        assert edge.length_px == 100.5
        # 9. angle_deg
        assert edge.angle_deg == 0.0
        # 10. confidence
        assert edge.confidence == 0.887
        # 11. source
        assert edge.source == ["skeleton", "ocr_verified"]
        # 12. thickness_px
        assert edge.thickness_px == 12.5
        # Metric endpoints
        assert edge.start_metric == (0.5, 1.0)
        assert edge.end_metric == (3.5, 1.0)
        # Reference to original segment
        assert edge.segment is seg


class TestDeterminism:
    """Verify deterministic generation of node and edge IDs."""

    def test_deterministic_node_and_edge_ids(self):
        """13-14. Node IDs and edge IDs are strictly deterministic."""
        segs = [
            _make_segment("w0", (0.0, 0.0), (50.0, 0.0)),
            _make_segment("w1", (50.0, 0.0), (100.0, 0.0)),
            _make_segment("w2", (100.0, 0.0), (100.0, 50.0)),
        ]

        graph1 = build_wall_graph(segs)
        graph2 = build_wall_graph(segs)

        assert list(graph1.nodes.keys()) == ["node_0", "node_1", "node_2", "node_3"]
        assert list(graph1.edges.keys()) == ["edge_0", "edge_1", "edge_2"]

        # Exact parity across runs
        assert list(graph1.nodes.keys()) == list(graph2.nodes.keys())
        assert list(graph1.edges.keys()) == list(graph2.edges.keys())
        for nid in graph1.nodes:
            assert graph1.nodes[nid].x == graph2.nodes[nid].x
            assert graph1.nodes[nid].y == graph2.nodes[nid].y
            assert graph1.nodes[nid].type == graph2.nodes[nid].type
