from scipy.spatial.distance import cdist
import numpy as np

def compute_chamfer_distance(pred_points, gt_points):
    """
    Computes the symmetric Chamfer distance between two sets of points.
    Assumes points are in comparable coordinates (e.g., both converted to metric space).
    """
    if not gt_points or not pred_points:
        return None
        
    pts1 = np.array(pred_points)
    pts2 = np.array(gt_points)
    
    # Distance from each pred to nearest gt
    dist1 = cdist(pts1, pts2).min(axis=1).mean()
    
    # Distance from each gt to nearest pred
    dist2 = cdist(pts2, pts1).min(axis=1).mean()
    
    return dist1 + dist2
