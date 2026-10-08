from .ours import OurMethod
from .stub import StubBaseline, UnavailableBaseline

METHODS = {
    "baseline": OurMethod(
        name="B0_Baseline",
        enable_geometric_reconciliation=False,
        enable_metric_calibration=False,
        enable_topology_validation=False
    ),
    "geometry_reconciled": OurMethod(
        name="B1_GeometryReconciled",
        enable_geometric_reconciliation=True,
        enable_metric_calibration=False,
        enable_topology_validation=False
    ),
    "metric_calibrated": OurMethod(
        name="B2_MetricCalibrated",
        enable_geometric_reconciliation=True,
        enable_metric_calibration=True,
        enable_topology_validation=False
    ),
    "topology_validated": OurMethod(
        name="B3_TopologyValidated",
        enable_geometric_reconciliation=True,
        enable_metric_calibration=True,
        enable_topology_validation=True
    ),
    "full_mgr": OurMethod("OURS_v1"),
    "ours": OurMethod("OURS_v1"),
    "raster2seq": UnavailableBaseline("Raster2Seq")
}

def get_method(name: str):
    if name not in METHODS:
        raise ValueError(f"Unknown method {name}")
    return METHODS[name]
