"""
Unit tests for Phase 10: Metric Calibration.
"""

import math
import pytest

from app.geometry.calibration import calibrate_wall_segments, estimate_scale_mm_per_px
from app.geometry.types import DimensionEvidence, WallSegment


def test_empty_dimensions_returns_none():
    """Empty dimensions list returns None without inventing scale."""
    assert estimate_scale_mm_per_px([]) is None


def test_single_valid_dimension():
    """Single valid dimension computes exact scale = value_mm / dist_px."""
    dim = DimensionEvidence(
        id="d1",
        value_mm=2000.0,
        start_px=(0.0, 0.0),
        end_px=(100.0, 0.0),  # dist = 100px
        confidence=0.9,
    )
    scale = estimate_scale_mm_per_px([dim])
    assert scale == 20.0  # 2000 / 100 = 20.0


def test_multiple_consistent_dimensions():
    """Multiple consistent dimensions produce the expected scale."""
    dims = [
        DimensionEvidence(id="d1", value_mm=2000.0, start_px=(0.0, 0.0), end_px=(100.0, 0.0), confidence=0.9),
        DimensionEvidence(id="d2", value_mm=4000.0, start_px=(0.0, 0.0), end_px=(200.0, 0.0), confidence=0.9),
        DimensionEvidence(id="d3", value_mm=1000.0, start_px=(0.0, 0.0), end_px=(50.0, 0.0), confidence=0.9),
    ]
    scale = estimate_scale_mm_per_px(dims)
    assert scale == 20.0


def test_noisy_measurements():
    """Noisy measurements within tolerance are combined into a robust estimate."""
    dims = [
        DimensionEvidence(id="d1", value_mm=2000.0, start_px=(0.0, 0.0), end_px=(100.0, 0.0), confidence=0.9),  # 20.0
        DimensionEvidence(id="d2", value_mm=2030.0, start_px=(0.0, 0.0), end_px=(100.0, 0.0), confidence=0.9),  # 20.3
        DimensionEvidence(id="d3", value_mm=1980.0, start_px=(0.0, 0.0), end_px=(100.0, 0.0), confidence=0.9),  # 19.8
        DimensionEvidence(id="d4", value_mm=2010.0, start_px=(0.0, 0.0), end_px=(100.0, 0.0), confidence=0.9),  # 20.1
    ]
    scale = estimate_scale_mm_per_px(dims, relative_tolerance=0.10)
    assert scale is not None
    assert abs(scale - 20.05) < 0.1


def test_outlier_measurement():
    """Extreme outlier does not corrupt the consistent consensus scale."""
    dims = [
        DimensionEvidence(id="d1", value_mm=2000.0, start_px=(0.0, 0.0), end_px=(100.0, 0.0), confidence=0.9),  # 20.0
        DimensionEvidence(id="d2", value_mm=2010.0, start_px=(0.0, 0.0), end_px=(100.0, 0.0), confidence=0.9),  # 20.1
        DimensionEvidence(id="d3", value_mm=1990.0, start_px=(0.0, 0.0), end_px=(100.0, 0.0), confidence=0.9),  # 19.9
        # Extreme OCR hallucination: 10000mm on 100px -> 100.0
        DimensionEvidence(id="d_outlier", value_mm=10000.0, start_px=(0.0, 0.0), end_px=(100.0, 0.0), confidence=0.9),
    ]
    scale = estimate_scale_mm_per_px(dims, relative_tolerance=0.10)
    assert scale is not None
    # Consensus should reject 100.0 and average around 20.0
    assert abs(scale - 20.0) < 0.1


def test_confidence_filtering():
    """Dimensions below min_confidence threshold are discarded."""
    dims = [
        DimensionEvidence(id="d_low", value_mm=5000.0, start_px=(0.0, 0.0), end_px=(100.0, 0.0), confidence=0.2),
        DimensionEvidence(id="d_high", value_mm=2000.0, start_px=(0.0, 0.0), end_px=(100.0, 0.0), confidence=0.8),
    ]
    scale = estimate_scale_mm_per_px(dims, min_confidence=0.5)
    assert scale == 20.0


def test_zero_length_evidence():
    """Zero-length dimension markers (dist=0) are safely ignored."""
    dims = [
        DimensionEvidence(id="d_zero", value_mm=2000.0, start_px=(50.0, 50.0), end_px=(50.0, 50.0), confidence=0.9),
        DimensionEvidence(id="d_valid", value_mm=2000.0, start_px=(0.0, 0.0), end_px=(100.0, 0.0), confidence=0.9),
    ]
    scale = estimate_scale_mm_per_px(dims)
    assert scale == 20.0


def test_tiny_pixel_distance():
    """Sub-pixel / tiny distances (<1e-4) do not trigger division by zero."""
    dims = [
        DimensionEvidence(id="d_tiny", value_mm=2000.0, start_px=(0.0, 0.0), end_px=(0.00001, 0.0), confidence=0.9),
    ]
    assert estimate_scale_mm_per_px(dims) is None


def test_invalid_zero_dimension_value():
    """Negative or zero value_mm measurements are rejected."""
    dims = [
        DimensionEvidence(id="d_zero_val", value_mm=0.0, start_px=(0.0, 0.0), end_px=(100.0, 0.0), confidence=0.9),
        DimensionEvidence(id="d_neg_val", value_mm=-1000.0, start_px=(0.0, 0.0), end_px=(100.0, 0.0), confidence=0.9),
    ]
    assert estimate_scale_mm_per_px(dims) is None


def test_all_invalid_evidence():
    """Collection containing only invalid evidence returns None."""
    dims = [
        DimensionEvidence(id="d1", value_mm=0.0, start_px=(0.0, 0.0), end_px=(100.0, 0.0), confidence=0.9),
        DimensionEvidence(id="d2", value_mm=2000.0, start_px=(10.0, 10.0), end_px=(10.0, 10.0), confidence=0.9),
    ]
    assert estimate_scale_mm_per_px(dims) is None


def test_deterministic_result():
    """Identical input in different permutations yields identical scale."""
    dims = [
        DimensionEvidence(id="d1", value_mm=2000.0, start_px=(0.0, 0.0), end_px=(100.0, 0.0), confidence=0.9),
        DimensionEvidence(id="d2", value_mm=2020.0, start_px=(0.0, 0.0), end_px=(100.0, 0.0), confidence=0.85),
        DimensionEvidence(id="d3", value_mm=1980.0, start_px=(0.0, 0.0), end_px=(100.0, 0.0), confidence=0.95),
    ]
    s1 = estimate_scale_mm_per_px(dims)
    s2 = estimate_scale_mm_per_px(list(reversed(dims)))
    assert s1 == s2


def test_relative_tolerance_behavior():
    """Tightening relative_tolerance rejects wider deviations; loosening accepts."""
    dims = [
        DimensionEvidence(id="d1", value_mm=2000.0, start_px=(0.0, 0.0), end_px=(100.0, 0.0), confidence=0.9),  # 20.0
        DimensionEvidence(id="d2", value_mm=2300.0, start_px=(0.0, 0.0), end_px=(100.0, 0.0), confidence=0.9),  # 23.0 (+15%)
    ]
    # With tight tolerance 5%, they disagree and fail consensus
    assert estimate_scale_mm_per_px(dims, relative_tolerance=0.05) is None
    # With wide tolerance 20%, they are accepted as inliers
    scale_wide = estimate_scale_mm_per_px(dims, relative_tolerance=0.20)
    assert scale_wide is not None
    assert abs(scale_wide - 21.5) < 0.1


def test_metric_wall_coordinate_conversion():
    """calibrate_wall_segments accurately converts pixel coordinates to metric mm."""
    wall = WallSegment(id="w1", start=(10.0, 20.0), end=(60.0, 20.0))
    calibrated = calibrate_wall_segments([wall], scale_mm_per_px=20.0)

    assert len(calibrated) == 1
    c = calibrated[0]
    assert c.start_metric == (200.0, 400.0)
    assert c.end_metric == (1200.0, 400.0)
    # Original pixel coordinates preserved
    assert c.start == (10.0, 20.0)
    assert c.end == (60.0, 20.0)


def test_horizontal_wall_calibration():
    """Horizontal wall metric endpoints maintain constant y metric coordinate."""
    wall = WallSegment(id="w_h", start=(0.0, 50.0), end=(100.0, 50.0))
    calibrated = calibrate_wall_segments([wall], scale_mm_per_px=15.0)[0]
    assert calibrated.start_metric == (0.0, 750.0)
    assert calibrated.end_metric == (1500.0, 750.0)


def test_vertical_wall_calibration():
    """Vertical wall metric endpoints maintain constant x metric coordinate."""
    wall = WallSegment(id="w_v", start=(50.0, 0.0), end=(50.0, 100.0))
    calibrated = calibrate_wall_segments([wall], scale_mm_per_px=15.0)[0]
    assert calibrated.start_metric == (750.0, 0.0)
    assert calibrated.end_metric == (750.0, 1500.0)


def test_diagonal_wall_calibration():
    """Diagonal wall coordinates scale proportionally in both axes."""
    wall = WallSegment(id="w_d", start=(10.0, 10.0), end=(50.0, 40.0))
    calibrated = calibrate_wall_segments([wall], scale_mm_per_px=10.0)[0]
    assert calibrated.start_metric == (100.0, 100.0)
    assert calibrated.end_metric == (500.0, 400.0)


def test_reversed_wall_endpoints():
    """Reversed wall endpoint ordering is preserved in metric endpoints."""
    wall = WallSegment(id="w_rev", start=(100.0, 50.0), end=(0.0, 50.0))
    calibrated = calibrate_wall_segments([wall], scale_mm_per_px=10.0)[0]
    assert calibrated.start_metric == (1000.0, 500.0)
    assert calibrated.end_metric == (0.0, 500.0)


def test_metric_coordinate_rounding():
    """Metric coordinates are rounded cleanly to 2 decimal places."""
    wall = WallSegment(id="w1", start=(3.333, 6.666), end=(13.333, 16.666))
    calibrated = calibrate_wall_segments([wall], scale_mm_per_px=10.0)[0]
    assert calibrated.start_metric == (33.33, 66.66)
    assert calibrated.end_metric == (133.33, 166.66)


def test_input_immutability():
    """Original WallSegment objects are not mutated."""
    wall = WallSegment(id="w1", start=(10.0, 20.0), end=(50.0, 20.0))
    calibrate_wall_segments([wall], scale_mm_per_px=20.0)
    assert wall.start_metric is None
    assert wall.end_metric is None


def test_returned_wall_segments_are_new_instances():
    """calibrate_wall_segments returns newly constructed objects."""
    wall = WallSegment(id="w1", start=(10.0, 20.0), end=(50.0, 20.0))
    res = calibrate_wall_segments([wall], scale_mm_per_px=20.0)
    assert res[0] is not wall


def test_metadata_preservation():
    """Wall metadata (id, length_px, angle_deg, confidence, thickness_px, source) is preserved."""
    wall = WallSegment(
        id="w_meta",
        start=(0.0, 0.0),
        end=(100.0, 0.0),
        length_px=100.0,
        angle_deg=0.0,
        confidence=0.87,
        source=["model", "heuristic"],
        thickness_px=4.5,
    )
    calibrated = calibrate_wall_segments([wall], scale_mm_per_px=10.0)[0]
    assert calibrated.id == "w_meta"
    assert calibrated.length_px == 100.0
    assert calibrated.angle_deg == 0.0
    assert calibrated.confidence == 0.87
    assert calibrated.source == ["model", "heuristic"]
    assert calibrated.thickness_px == 4.5
    # Source is copied
    assert calibrated.source is not wall.source


def test_no_scale_invented_when_evidence_unusable():
    """Returns None when evidence is completely unusable, without fallback guessing."""
    dims = [
        DimensionEvidence(id="d_bad1", value_mm=-50.0, start_px=(0.0, 0.0), end_px=(100.0, 0.0)),
        DimensionEvidence(id="d_bad2", value_mm=100.0, start_px=(0.0, 0.0), end_px=(0.0, 0.0)),
    ]
    assert estimate_scale_mm_per_px(dims) is None
