"""
Core data structures for Metric-Aware Geometric Reconciliation (MGR).

This module contains geometry representations only.
Algorithm implementations belong in separate modules.
"""

from dataclasses import dataclass, field
from typing import Any, Literal


Point = tuple[float, float]


@dataclass
class WallSegment:
    """A geometrically reconstructed wall segment."""

    id: str
    start: Point
    end: Point

    length_px: float = 0.0
    angle_deg: float = 0.0

    confidence: float = 0.0
    source: list[str] = field(default_factory=list)

    thickness_px: float | None = None

    start_metric: Point | None = None
    end_metric: Point | None = None


@dataclass
class Opening:
    """A door or window associated with a wall."""

    id: str
    type: Literal["door", "window"]

    start: Point
    end: Point

    wall_id: str | None = None

    confidence: float = 0.0
    source: list[str] = field(default_factory=list)


@dataclass
class RoomPolygon:
    """A closed room region derived from the wall graph."""

    id: str
    polygon: list[Point]

    area_px2: float = 0.0
    area_m2: float | None = None

    label: str | None = None
    confidence: float = 0.0

    source: list[str] = field(default_factory=list)


@dataclass
class DimensionEvidence:
    """A dimension measurement supplied by OCR or another source."""

    id: str

    value_mm: float

    start_px: Point
    end_px: Point

    confidence: float = 0.0
    source: list[str] = field(default_factory=list)


@dataclass
class MGRResult:
    """Final structured output produced by the MGR pipeline."""

    walls: list[WallSegment] = field(default_factory=list)
    rooms: list[RoomPolygon] = field(default_factory=list)

    doors: list[Opening] = field(default_factory=list)
    windows: list[Opening] = field(default_factory=list)

    scale_mm_per_px: float | None = None

    confidence: dict[str, Any] = field(default_factory=dict)
    provenance: dict[str, Any] = field(default_factory=dict)

    assumptions: list[str] = field(default_factory=list)