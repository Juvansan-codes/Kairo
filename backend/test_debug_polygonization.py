import numpy as np
from app.geometry.pipeline import run_mgr_pipeline
from app.services.analysis import PerceptionAnalysisService
from app.geometry.adapter import adapt_analysis_to_mgr
from app.geometry.graph import build_wall_graph
from shapely.ops import polygonize, unary_union
from shapely.geometry import LineString
import math

class DummyJob:
    stage = ""

# Test with real floor plan
img_path = r"d:\College Files\Kairo\evaluation\datasets\custom_real_v1\real_001.png"
perc = PerceptionAnalysisService().analyze(img_path, DummyJob())
inputs = adapt_analysis_to_mgr(perc)

# Run pipeline
res = run_mgr_pipeline(**inputs, node_tolerance_px=15.0)

print(f"=== WALL ANALYSIS ===")
print(f"Total walls: {len(res.walls)}")

# Build graph manually to debug
from app.geometry.room_polygonization import polygonize_rooms
walls = res.walls

print(f"\n=== DETAILED WALL INFO ===")
for i, w in enumerate(walls[:5]):  # First 5 walls
    print(f"Wall {i}: start={w.start}, end={w.end}, length={w.length_px:.2f}")

# Try room polygonization manually
print(f"\n=== MANUAL ROOM POLYGONIZATION DEBUG ===")
graph = build_wall_graph(walls, tolerance=15.0)
print(f"Graph nodes: {len(graph.nodes)}")
print(f"Graph edges: {len(graph.edges)}")

# Extract lines
lines = []
for edge in graph.edges.values():
    start_node = graph.get_node(edge.start_node_id)
    end_node = graph.get_node(edge.end_node_id)
    if start_node and end_node:
        p1 = (start_node.x, start_node.y)
        p2 = (end_node.x, end_node.y)
        dist = math.hypot(p2[0] - p1[0], p2[1] - p1[1])
        if dist >= 1e-4:
            lines.append(LineString([p1, p2]))

print(f"LineStrings created: {len(lines)}")

# Try polygonization
if lines:
    noded_network = unary_union(lines)
    print(f"Noded network type: {noded_network.geom_type}")
    raw_polygons = list(polygonize(noded_network))
    print(f"Raw polygons found: {len(raw_polygons)}")
    
    if raw_polygons:
        for i, poly in enumerate(raw_polygons[:3]):
            print(f"  Polygon {i}: area={poly.area:.2f}, valid={poly.is_valid}, type={poly.geom_type}")
    else:
        print("  No polygons found - walls may not form closed regions!")
        print(f"  Network length: {noded_network.length}")
        print(f"  Network is_ring: {hasattr(noded_network, 'is_ring')}")
        
        # Check if we have a MultiLineString
        if noded_network.geom_type == 'MultiLineString':
            print(f"  Number of line components: {len(noded_network.geoms)}")
            # Check for rings manually
            from shapely.geometry import LinearRing
            rings = [geom for geom in noded_network.geoms if geom.is_ring]
            print(f"  Rings found: {len(rings)}")
