import math
import numpy as np

def compute_dimension_error(prediction, ground_truth):
    """
    Computes Mean Absolute Error (MAE) and Mean Relative Error (MRE) 
    between predicted and ground truth dimensions.
    Returns (MAE, MRE)
    """
    gt_dims = ground_truth.dimensions
    pred_dims = prediction.dimensions
    
    if not gt_dims:
        return None, None
        
    if not pred_dims:
        return None, None
        
    # Simplify dimension matching by nearest value
    # True metric should use spatial distance between text regions, but for evaluation, 
    # we match numeric values via assignment
    gt_vals = [float(d["value_mm"]) for d in gt_dims if "value_mm" in d]
    pred_vals = [float(d["value_mm"]) for d in pred_dims if "value_mm" in d]
    
    if not gt_vals or not pred_vals:
        return None, None

    cost_matrix = np.zeros((len(pred_vals), len(gt_vals)))
    for i, p in enumerate(pred_vals):
        for j, g in enumerate(gt_vals):
            cost_matrix[i, j] = abs(p - g)

    from scipy.optimize import linear_sum_assignment
    row_ind, col_ind = linear_sum_assignment(cost_matrix)

    abs_errors = []
    rel_errors = []
    for r, c in zip(row_ind, col_ind):
        err = cost_matrix[r, c]
        abs_errors.append(err)
        if gt_vals[c] > 0:
            rel_errors.append(err / gt_vals[c])

    if not abs_errors:
        return None, None

    mae = sum(abs_errors) / len(abs_errors)
    mre = sum(rel_errors) / len(rel_errors) if rel_errors else None
    return mae, mre

def compute_scale_error(prediction, ground_truth):
    """
    Computes scale error (Absolute, Relative)
    """
    gt_scale = ground_truth.scale_mm_per_px
    pred_scale = prediction.scale_mm_per_px
    
    if gt_scale is None:
        return None, None
        
    if pred_scale is None:
        return None, None
        
    abs_err = abs(pred_scale - gt_scale)
    rel_err = abs_err / gt_scale if gt_scale > 0 else 0.0
    
    return abs_err, rel_err
