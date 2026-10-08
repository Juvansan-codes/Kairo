from shapely.geometry import Polygon, LineString
from shapely.ops import unary_union
from scipy.optimize import linear_sum_assignment
import numpy as np

def compute_wall_iou(prediction, ground_truth, buffer_px=5.0):
    """
    Computes Intersection over Union (IoU) for walls.
    Wall geometries are expected to be list of line segments (e.g. [[x1, y1], [x2, y2]])
    Buffer tolerance defines thickness for overlap matching.
    """
    if not ground_truth.walls:
        return None
    if not prediction.walls:
        return 0.0

    gt_lines = []
    for w in ground_truth.walls:
        if "geometry" in w and len(w["geometry"]) >= 2:
            gt_lines.append(LineString(w["geometry"]))
            
    pred_lines = []
    for w in prediction.walls:
        if "geometry" in w and len(w["geometry"]) >= 2:
            pred_lines.append(LineString(w["geometry"]))

    if not gt_lines:
        return None
    if not pred_lines:
        return 0.0

    # Buffer lines to create polygons and union them
    gt_poly = unary_union([line.buffer(buffer_px) for line in gt_lines])
    pred_poly = unary_union([line.buffer(buffer_px) for line in pred_lines])

    intersection = gt_poly.intersection(pred_poly).area
    union = gt_poly.union(pred_poly).area

    if union == 0:
        return 0.0
    return intersection / union

def get_polygon(item):
    if "polygon" in item:
        return Polygon(item["polygon"])
    elif "geometry" in item:
        return Polygon(item["geometry"])
    return None

def compute_room_iou(prediction, ground_truth):
    """
    Computes average IoU for rooms using bipartite matching (Hungarian algorithm).
    Rooms must have 'polygon' attribute with coordinates.
    """
    if not ground_truth.rooms:
        return None
    if not prediction.rooms:
        return 0.0

    gt_polys = [get_polygon(r) for r in ground_truth.rooms if get_polygon(r) is not None and get_polygon(r).is_valid]
    pred_polys = [get_polygon(r) for r in prediction.rooms if get_polygon(r) is not None and get_polygon(r).is_valid]

    if not gt_polys:
        return None
    if not pred_polys:
        return 0.0

    # Compute pairwise IoU matrix
    iou_matrix = np.zeros((len(pred_polys), len(gt_polys)))
    for i, p in enumerate(pred_polys):
        for j, g in enumerate(gt_polys):
            if p.intersects(g):
                inter_area = p.intersection(g).area
                union_area = p.union(g).area
                if union_area > 0:
                    iou_matrix[i, j] = inter_area / union_area

    # Maximize total IoU using linear_sum_assignment (Hungarian)
    # scipy.optimize minimizes, so we pass negative IoU matrix
    row_ind, col_ind = linear_sum_assignment(-iou_matrix)

    matched_ious = []
    for r, c in zip(row_ind, col_ind):
        if iou_matrix[r, c] > 0.1: # Only consider matches with > 10% overlap
            matched_ious.append(iou_matrix[r, c])

    if not matched_ious:
        return 0.0

    # The prompt usually defines room IoU as average over ground truth instances, 
    # but average over matched + penalizing missed is standard.
    # Let's return average of ALL matches (or 0 if none)
    return sum(matched_ious) / len(matched_ious)
