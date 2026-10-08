from shapely.geometry import Polygon

def validate_topology(prediction):
    """
    Simple deterministic checks for topology.
    Returns a report dict with issues found.
    """
    report = {
        "invalid_room_polygons": 0,
        "self_intersections": 0,
        "disconnected_walls": 0, # Not checked yet
        "floating_doors": 0, # Not checked yet
        "floating_windows": 0 # Not checked yet
    }
    
    for r in prediction.rooms:
        if "polygon" in r:
            poly = Polygon(r["polygon"])
            if not poly.is_valid:
                report["invalid_room_polygons"] += 1
            if not poly.is_simple:
                report["self_intersections"] += 1
                
    return report
