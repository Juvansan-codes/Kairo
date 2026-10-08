import trimesh
import numpy as np
import shapely.geometry
from typing import Dict, Any

def generate_scene(mgr_result, output_path: str) -> Dict[str, Any]:
    """
    Generates a 3D scene from MGRResult and exports it as a GLB.
    Handles metric scaling if available, otherwise generates in pixel space.
    Uses robust 1D segmentation to create wall cutouts for doors/windows without unstable booleans.
    """
    scene = trimesh.Scene()
    
    scale_mm = mgr_result.scale_mm_per_px
    use_metric = scale_mm is not None
    
    # Constants
    WALL_HEIGHT = 2.8 if use_metric else 100.0
    WALL_THICKNESS = 0.15 if use_metric else 5.0
    DOOR_HEIGHT = 2.1 if use_metric else 75.0
    WINDOW_BOTTOM = 0.9 if use_metric else 30.0
    WINDOW_TOP = 2.1 if use_metric else 75.0
    
    def to_coords(px_pt, metric_pt):
        if use_metric and metric_pt is not None:
            # Convert mm to meters for standard GLB representation
            return (metric_pt[0] / 1000.0, metric_pt[1] / 1000.0)
        else:
            return (px_pt[0], px_pt[1])

    def create_wall_box(start_p, end_p, w_start, w_dir, z_min, z_max, thickness, color):
        length = end_p - start_p
        if length < 1e-4: return None
        height = z_max - z_min
        if height < 1e-4: return None
        
        mid_p = (start_p + end_p) / 2.0
        mid_xy = w_start + w_dir * mid_p
        
        box = trimesh.creation.box(extents=[length, thickness, height])
        
        # Rotate around Z
        theta = np.arctan2(w_dir[1], w_dir[0])
        rot = trimesh.transformations.rotation_matrix(theta, [0, 0, 1])
        box.apply_transform(rot)
        
        # Translate to midpoint
        box.apply_translation([mid_xy[0], mid_xy[1], z_min + height / 2.0])
        
        # Apply color
        box.visual.face_colors = color
        return box

    # 1. Walls & Openings (Robust 1D Segments)
    for i, wall in enumerate(mgr_result.walls):
        w_start = np.array(to_coords(wall.start, wall.start_metric))
        w_end = np.array(to_coords(wall.end, wall.end_metric))
        w_vec = w_end - w_start
        w_len = np.linalg.norm(w_vec)
        
        if w_len < 1e-5:
            continue
            
        w_dir = w_vec / w_len
        
        # Find openings for this wall
        wall_openings = []
        for o in mgr_result.doors + mgr_result.windows:
            if o.wall_id == wall.id:
                if use_metric:
                    o_start_scaled = (o.start[0] * scale_mm / 1000.0, o.start[1] * scale_mm / 1000.0)
                    o_end_scaled = (o.end[0] * scale_mm / 1000.0, o.end[1] * scale_mm / 1000.0)
                else:
                    o_start_scaled = o.start
                    o_end_scaled = o.end
                
                p1 = np.dot(np.array(o_start_scaled) - w_start, w_dir)
                p2 = np.dot(np.array(o_end_scaled) - w_start, w_dir)
                o_min, o_max = min(p1, p2), max(p1, p2)
                wall_openings.append((o_min, o_max, o.type))
                
        # Sort openings along the wall
        wall_openings.sort(key=lambda x: x[0])
        
        current_p = 0.0
        for o_min, o_max, o_type in wall_openings:
            o_min = max(0.0, min(w_len, o_min))
            o_max = max(0.0, min(w_len, o_max))
            
            if o_min > current_p:
                box = create_wall_box(current_p, o_min, w_start, w_dir, 0.0, WALL_HEIGHT, WALL_THICKNESS, [100, 100, 100, 255])
                if box: scene.add_geometry(box, node_name=f"wall_{wall.id}_seg_{current_p}")
                
            if o_max > o_min:
                if o_type == "door":
                    # Lintel above door
                    if DOOR_HEIGHT < WALL_HEIGHT:
                        box = create_wall_box(o_min, o_max, w_start, w_dir, DOOR_HEIGHT, WALL_HEIGHT, WALL_THICKNESS, [100, 100, 100, 255])
                        if box: scene.add_geometry(box, node_name=f"wall_{wall.id}_lintel_{o_min}")
                    # Actual Door Panel
                    door_box = create_wall_box(o_min, o_max, w_start, w_dir, 0.0, DOOR_HEIGHT, WALL_THICKNESS * 0.2, [241, 90, 36, 255])
                    if door_box: scene.add_geometry(door_box, node_name=f"door_{wall.id}_{o_min}")
                elif o_type == "window":
                    # Sill below window
                    box_sill = create_wall_box(o_min, o_max, w_start, w_dir, 0.0, WINDOW_BOTTOM, WALL_THICKNESS, [100, 100, 100, 255])
                    if box_sill: scene.add_geometry(box_sill, node_name=f"wall_{wall.id}_sill_{o_min}")
                    
                    # Lintel above window
                    if WINDOW_TOP < WALL_HEIGHT:
                        box_lintel = create_wall_box(o_min, o_max, w_start, w_dir, WINDOW_TOP, WALL_HEIGHT, WALL_THICKNESS, [100, 100, 100, 255])
                        if box_lintel: scene.add_geometry(box_lintel, node_name=f"wall_{wall.id}_lintel_{o_min}")
                        
                    # Actual Window Glass
                    glass_box = create_wall_box(o_min, o_max, w_start, w_dir, WINDOW_BOTTOM, WINDOW_TOP, WALL_THICKNESS * 0.1, [100, 181, 246, 160])
                    if glass_box: scene.add_geometry(glass_box, node_name=f"win_{wall.id}_{o_min}")
                        
            current_p = max(current_p, o_max)
            
        if current_p < w_len:
            box = create_wall_box(current_p, w_len, w_start, w_dir, 0.0, WALL_HEIGHT, WALL_THICKNESS, [100, 100, 100, 255])
            if box: scene.add_geometry(box, node_name=f"wall_{wall.id}_seg_end")

    # 2. Rooms (Floors)
    for i, room in enumerate(mgr_result.rooms):
        if len(room.polygon) < 3:
            continue
            
        pts = []
        for p in room.polygon:
            if use_metric:
                pts.append((p[0] * scale_mm / 1000.0, p[1] * scale_mm / 1000.0))
            else:
                pts.append((p[0], p[1]))
                
        poly = shapely.geometry.Polygon(pts)
        try:
            # Thin floor slab
            slab_thickness = 0.1 if use_metric else 2.0
            mesh = trimesh.creation.extrude_polygon(poly, height=slab_thickness)
            mesh.apply_translation([0, 0, -slab_thickness])
            scene.add_geometry(mesh, node_name=f"room_{room.id}")
        except Exception as e:
            print(f"Failed to extrude room {room.id}: {e}")

    # Export to GLB
    scene.export(output_path, file_type="glb")
    
    # Return statistics
    stats = {
        "walls_generated": len(mgr_result.walls),
        "rooms_generated": len(mgr_result.rooms),
        "doors_generated": len(mgr_result.doors),
        "windows_generated": len(mgr_result.windows),
        "vertex_count": sum(len(g.vertices) for g in scene.geometry.values()) if scene.geometry else 0,
        "face_count": sum(len(g.faces) for g in scene.geometry.values()) if scene.geometry else 0,
        "coordinate_space": "metric (meters)" if use_metric else "pixel",
        "scale_status": "available" if use_metric else "unavailable",
        "topology_valid": mgr_result.confidence.get("topology_valid", False)
    }
    
    return stats
