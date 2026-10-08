from evaluation.metrics.layout import compute_wall_iou, compute_room_iou
from evaluation.metrics.completeness import compute_door_recall
from evaluation.schema import Prediction, GroundTruth

print("--- WALL IOU TESTS ---")
gt_exact = GroundTruth(walls=[{"geometry": [[0, 0], [100, 0]]}])
pred_exact = Prediction(walls=[{"geometry": [[0, 0], [100, 0]]}])
print(f"Exact match IoU: {compute_wall_iou(pred_exact, gt_exact):.4f}")

pred_shifted = Prediction(walls=[{"geometry": [[0, 10], [100, 10]]}])
print(f"Shifted (10px) IoU: {compute_wall_iou(pred_shifted, gt_exact):.4f}")

pred_shifted_slightly = Prediction(walls=[{"geometry": [[0, 2], [100, 2]]}])
print(f"Shifted (2px) IoU: {compute_wall_iou(pred_shifted_slightly, gt_exact):.4f}")

pred_missing = Prediction(walls=[])
print(f"Missing wall IoU: {compute_wall_iou(pred_missing, gt_exact):.4f}")

pred_extra = Prediction(walls=[{"geometry": [[0, 0], [100, 0]]}, {"geometry": [[0, 50], [100, 50]]}])
print(f"Extra wall IoU: {compute_wall_iou(pred_extra, gt_exact):.4f}")

pred_perp = Prediction(walls=[{"geometry": [[50, -50], [50, 50]]}])
print(f"Perpendicular wall IoU: {compute_wall_iou(pred_perp, gt_exact):.4f}")

print("\n--- ROOM IOU TESTS ---")
gt_room = GroundTruth(rooms=[{"polygon": [[0, 0], [100, 0], [100, 100], [0, 100], [0, 0]]}])
pred_room = Prediction(rooms=[{"polygon": [[0, 0], [100, 0], [100, 100], [0, 100], [0, 0]]}])
print(f"Exact room IoU: {compute_room_iou(pred_room, gt_room):.4f}")

pred_room_shifted = Prediction(rooms=[{"polygon": [[10, 10], [110, 10], [110, 110], [10, 110], [10, 10]]}])
print(f"Shifted room IoU: {compute_room_iou(pred_room_shifted, gt_room):.4f}")

print("\n--- DOOR/WINDOW (OPENING) TESTS ---")
gt_door = GroundTruth(doors=[{"polygon": [[40, -5], [60, -5], [60, 5], [40, 5], [40, -5]]}])
# The prediction has been adapted to a bounding box: [minx-2, miny-2, maxx+2, maxy+2]
# original line was (40, 0) to (60, 0). Thus box is [38, -2, 62, 2]
pred_door = Prediction(doors=[{"geometry": [38, -2, 62, 2]}])
recall, matched, missed, fp = compute_door_recall(pred_door, gt_door)
print(f"Exact door recall: {recall:.4f}, Matched: {matched}, Missed: {missed}, FP: {fp}")

pred_door_shifted = Prediction(doors=[{"geometry": [38, 10, 62, 14]}])
recall_sh, matched_sh, missed_sh, fp_sh = compute_door_recall(pred_door_shifted, gt_door)
print(f"Shifted door recall: {recall_sh:.4f}, Matched: {matched_sh}, Missed: {missed_sh}, FP: {fp_sh}")

pred_door_missing = Prediction(doors=[])
recall_m, matched_m, missed_m, fp_m = compute_door_recall(pred_door_missing, gt_door)
print(f"Missing door recall: {recall_m:.4f}, Matched: {matched_m}, Missed: {missed_m}, FP: {fp_m}")

gt_door_multiple = GroundTruth(doors=[{"polygon": [[40, -5], [60, -5], [60, 5], [40, 5]]}])
pred_door_extra = Prediction(doors=[{"geometry": [38, -2, 62, 2]}, {"geometry": [100, 100, 120, 104]}])
recall_e, matched_e, missed_e, fp_e = compute_door_recall(pred_door_extra, gt_door_multiple)
print(f"Extra door recall: {recall_e:.4f}, Matched: {matched_e}, Missed: {missed_e}, FP: {fp_e}")
