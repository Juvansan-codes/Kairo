@'
# Backend — Metric-Aware Geometric Reconciliation (MGR)

This directory contains the backend implementation for the Kairo floor-plan reconstruction pipeline.

The core geometry system implements **Metric-Aware Geometric Reconciliation (MGR)**: a deterministic pipeline that converts extracted floor-plan geometry into a cleaned, topologically validated, and optionally metric-calibrated representation.

## MGR Status

Phases 1–14 of the geometry implementation are complete.

The MGR pipeline currently provides:

- wall extraction and morphological cleanup
- skeletonization
- wall segment extraction
- wall graph construction
- Manhattan snapping
- collinearity detection and segment merging
- intersection cleanup and splitting
- door/window reconciliation
- room polygonization
- metric calibration from dimension evidence
- topology validation
- deterministic end-to-end orchestration
- ablation support for evaluating individual processing stages
- a machine-readable Pydantic output schema
- backend documentation and regression tests

The geometry test suite currently contains **244 passing tests**.

---

## Architecture

The main geometry implementation lives in:

```text
backend/
├── app/
│   └── geometry/
│       ├── types.py
│       ├── solver.py
│       ├── graph.py
│       ├── snapping.py
│       ├── merging.py
│       ├── intersections.py
│       ├── openings.py
│       ├── room_polygonization.py
│       ├── calibration.py
│       ├── topology.py
│       ├── pipeline.py
│       ├── ablation.py
│       ├── schema.py
│       ├── test_*.py
│       └── ...
│
├── app/main.py
├── pyproject.toml
└── README.md