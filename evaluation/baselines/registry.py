from .ours import OurMethod
from .stub import StubBaseline, UnavailableBaseline

METHODS = {
    "baseline": StubBaseline("B0_Baseline"),
    "geometry_reconciled": StubBaseline("B1_GeometryReconciled"),
    "metric_calibrated": StubBaseline("B2_MetricCalibrated"),
    "topology_validated": StubBaseline("B3_TopologyValidated"),
    "full_mgr": OurMethod(),
    "ours": OurMethod(),
    "raster2seq": UnavailableBaseline("Raster2Seq")
}

def get_method(name: str):
    if name not in METHODS:
        raise ValueError(f"Unknown method {name}")
    return METHODS[name]
