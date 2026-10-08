from shapely.geometry import Polygon, box
from scipy.optimize import linear_sum_assignment
import numpy as np

def get_bounds_or_poly(item):
    if "polygon" in item:
        poly = Polygon(item["polygon"])
        if poly.is_valid:
            return poly
    elif "geometry" in item:
        # Assuming geometry is bounding box [minx, miny, maxx, maxy] or line
        geom = item["geometry"]
        if len(geom) == 4 and isinstance(geom[0], (int, float)):
            return box(geom[0], geom[1], geom[2], geom[3])
        else:
            poly = Polygon(geom)
            if poly.is_valid:
                return poly
    return None

def compute_recall(pred_items, gt_items, iou_threshold=0.5):
    """
    Computes recall, precision, and matched counts.
    Returns: recall, matched_count, missed_count, false_positives
    """
    if not gt_items:
        return None, 0, 0, 0
    if not pred_items:
        return 0.0, 0, len(gt_items), 0

    gt_geoms = [get_bounds_or_poly(r) for r in gt_items if get_bounds_or_poly(r) is not None]
    pred_geoms = [get_bounds_or_poly(r) for r in pred_items if get_bounds_or_poly(r) is not None]

    if not gt_geoms:
        return None, 0, 0, 0
    if not pred_geoms:
        return 0.0, 0, len(gt_items), 0

    iou_matrix = np.zeros((len(pred_geoms), len(gt_geoms)))
    for i, p in enumerate(pred_geoms):
        for j, g in enumerate(gt_geoms):
            if p.intersects(g):
                inter = p.intersection(g).area
                union = p.union(g).area
                if union > 0:
                    iou_matrix[i, j] = inter / union

    row_ind, col_ind = linear_sum_assignment(-iou_matrix)

    matched_count = 0
    for r, c in zip(row_ind, col_ind):
        if iou_matrix[r, c] >= iou_threshold:
            matched_count += 1

    missed_count = len(gt_items) - matched_count
    false_positives = len(pred_items) - matched_count
    recall = matched_count / len(gt_items)

    return recall, matched_count, missed_count, false_positives

def compute_room_recall(prediction, ground_truth):
    return compute_recall(prediction.rooms, ground_truth.rooms, iou_threshold=0.5)

def compute_door_recall(prediction, ground_truth):
    return compute_recall(prediction.doors, ground_truth.doors, iou_threshold=0.1)

def compute_window_recall(prediction, ground_truth):
    return compute_recall(prediction.windows, ground_truth.windows, iou_threshold=0.1)
