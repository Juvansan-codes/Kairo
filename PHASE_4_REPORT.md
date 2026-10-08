# PHASE 4 REPORT: Dimension Parser & Unit Normalization

## Overview
Phase 4 successfully implemented the **Dimension Parser and Unit Normalization** subsystem. This module conceptually sits between the raw OCR text regions (Phase 3) and the geometric wall/room association system (Phase 5).

## Parser Subsystem Definition
The subsystem was constructed purely conceptually around dimension mathematics and structural heuristics, deliberately avoiding any geometry association.
Files created:
* `backend/app/dimensions/models.py`: Defines `DimensionCandidate` and `DimensionParseResult` mapping.
* `backend/app/dimensions/units.py`: Provides `parse_dimension_string()` to extract list of numeric metric values from strings.
* `backend/app/dimensions/classifier.py`: Implements heuristic `classify_dimension()` to categorize textual content.
* `backend/app/dimensions/parser.py`: The `parse_dimensions(text_regions)` orchestration entrypoint.

## Supported Formats & Unit Normalization
The parser seamlessly converts multiple imperial and metric textual variants into a strict mathematical standard (millimeters).

### Metric (normalized to `mm`):
* `4200` $\rightarrow$ `4200.0 mm`
* `4200 mm` $\rightarrow$ `4200.0 mm`
* `3.5 m` $\rightarrow$ `3500.0 mm`
* `350 cm` $\rightarrow$ `3500.0 mm`

### Imperial (normalized to `mm` via $1' = 304.8\text{mm}$, $1" = 25.4\text{mm}$):
* `12'-6"` $\rightarrow$ `3810.0 mm`
* `12' 6"` $\rightarrow$ `3810.0 mm`
* `12'6"` $\rightarrow$ `3810.0 mm`

### Compound & Chained Dimensions
Strings containing multiple geometric representations are split and preserved independently without assuming target objects:
* `"12' x 10'"` $\rightarrow$ `ROOM_DIMENSION` $\rightarrow$ `[3657.6, 3048.0]`
* `"1200 2500 1800"` $\rightarrow$ `ROOM_DIMENSION` $\rightarrow$ `[1200.0, 2500.0, 1800.0]`

## Classification Rules
The `classify_dimension` module relies strictly on formatting, regex context, and explicit units to sort candidates.
* **DIMENSION**: Value with strong unit indicator (`mm`, `'`, `"`) or likely wall-length numbers.
* **ROOM_DIMENSION**: Contains multiple parsed values inside the same string (via `x`, `*`, or spaces).
* **NUMERIC_ANNOTATION**: Numbers that denote drawing numbers, very small identifiers (`A-102`), years (`2026`), or generic labels.
* **TEXT**: Standard alphabetic words (`BEDROOM`, `LIVING`, etc.)

## Tests
### Unit-Test Results
A highly comprehensive unit-test suite (`backend/test_dimensions.py`) verified every imperial, metric, compound, chained, and ambiguous format requested.
**Results:** All formats parsed perfectly into correct standard metric scales with accurately calculated confidence levels. 

### Real-Floorplan Results
Tested against the actual `PaddleOCREngine` output from images `F1`, `F2`, and `F3`.
The module cleanly processed and filtered all textual layout artifacts:
* `"BuildingCV floor plan + 3"` $\rightarrow$ Ignored as `NUMERIC_ANNOTATION`.
* `"Architectural"`, `"Compact"`, `"Long house"` $\rightarrow$ Ignored as `TEXT`.

## Known Limitations
* **Highly Ambiguous Numbers**: Without geometry context, parsing a bare `"2.5"` is extremely tricky (is it $2.5\text{m}$ or a room identifier?). We rely heavily on the context heuristics or fall back to returning lower parse confidences. 
* **OCR Quality**: The parsing algorithm relies on OCR maintaining spaces or exact quotes `"`/`'`. Low resolution OCR artifacts could cause failure.

## Handoff to Phase 5
Phase 5 (Geometry & 3D Reconstruction) will invoke `parse_dimensions()` on OCR arrays. 
It will consume the resulting `DimensionParseResult` object containing `dimensions` (List of `DimensionCandidate`). Phase 5 will then analyze the `values_mm`, `polygon`, and `orientation` coordinates provided natively inside each candidate to project and lock walls to these metric targets.

**PHASE 4 IS COMPLETE.**
