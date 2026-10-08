
from evaluation.schema import Prediction, GroundTruth
from evaluation.metrics.layout import compute_room_iou, compute_wall_iou
from evaluation.metrics.completeness import compute_room_recall
from evaluation.metrics.dimensions import compute_scale_error, compute_dimension_error

def test_exact_match():
    gt = GroundTruth(
        rooms=[{"polygon": [[0,0], [10,0], [10,10], [0,10]]}],
        scale_mm_per_px=20.0
    )
    pred = Prediction(
        rooms=[{"polygon": [[0,0], [10,0], [10,10], [0,10]]}],
        scale_mm_per_px=20.0
    )
    
    assert compute_room_iou(pred, gt) == 1.0
    assert compute_room_recall(pred, gt)[0] == 1.0
    assert compute_scale_error(pred, gt) == (0.0, 0.0)

def test_half_overlap():
    gt = GroundTruth(
        rooms=[{"polygon": [[0,0], [10,0], [10,10], [0,10]]}]
    )
    # Prediction is shifted by 5 units
    pred = Prediction(
        rooms=[{"polygon": [[5,0], [15,0], [15,10], [5,10]]}]
    )
    
    # Intersection is 5x10 = 50. Union is 15x10 = 150. IoU = 50/150 = 1/3
    iou = compute_room_iou(pred, gt)
    assert abs(iou - 0.3333) < 0.01
    
    # Recall fails if threshold is 0.5 (1/3 < 0.5)
    recall, matched, missed, fp = compute_room_recall(pred, gt)
    assert recall == 0.0
    assert matched == 0
    assert missed == 1
    assert fp == 1

def test_no_overlap():
    gt = GroundTruth(rooms=[{"polygon": [[0,0], [10,0], [10,10], [0,10]]}])
    pred = Prediction(rooms=[{"polygon": [[20,20], [30,20], [30,30], [20,30]]}])
    
    assert compute_room_iou(pred, gt) == 0.0
    assert compute_room_recall(pred, gt)[0] == 0.0

def test_missing_room():
    gt = GroundTruth(rooms=[
        {"polygon": [[0,0], [10,0], [10,10], [0,10]]},
        {"polygon": [[20,20], [30,20], [30,30], [20,30]]}
    ])
    pred = Prediction(rooms=[
        {"polygon": [[0,0], [10,0], [10,10], [0,10]]}
    ])
    
    # Average IoU of MATCHED pairs is 1.0
    assert compute_room_iou(pred, gt) == 1.0
    
    recall, matched, missed, fp = compute_room_recall(pred, gt)
    assert recall == 0.5
    assert missed == 1
    assert fp == 0

def test_extra_room():
    gt = GroundTruth(rooms=[
        {"polygon": [[0,0], [10,0], [10,10], [0,10]]}
    ])
    pred = Prediction(rooms=[
        {"polygon": [[0,0], [10,0], [10,10], [0,10]]},
        {"polygon": [[20,20], [30,20], [30,30], [20,30]]}
    ])
    
    assert compute_room_iou(pred, gt) == 1.0
    recall, matched, missed, fp = compute_room_recall(pred, gt)
    assert recall == 1.0
    assert missed == 0
    assert fp == 1

def test_scale_error():
    gt = GroundTruth(scale_mm_per_px=20.0)
    pred = Prediction(scale_mm_per_px=22.0)
    abs_err, rel_err = compute_scale_error(pred, gt)
    assert abs_err == 2.0
    assert rel_err == 0.1 # 10% error

if __name__ == "__main__":
    test_exact_match()
    test_half_overlap()
    test_no_overlap()
    test_missing_room()
    test_extra_room()
    test_scale_error()
    print("ALL SYNTHETIC TESTS PASSED!")
