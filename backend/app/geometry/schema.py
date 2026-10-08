from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


PointSchema = tuple[float, float]


class WallSegmentSchema(BaseModel):
    """Serializable schema for a reconciled wall segment."""

    model_config = ConfigDict(extra="forbid")

    id: str
    start: PointSchema
    end: PointSchema
    length_px: float = 0.0
    angle_deg: float = 0.0
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    source: list[str] = Field(default_factory=list)
    thickness_px: float | None = None
    start_metric: PointSchema | None = None
    end_metric: PointSchema | None = None


class OpeningSchema(BaseModel):
    """Serializable schema for a door or window opening."""

    model_config = ConfigDict(extra="forbid")

    id: str
    type: Literal["door", "window"]
    start: PointSchema
    end: PointSchema
    wall_id: str | None = None
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    source: list[str] = Field(default_factory=list)


class RoomPolygonSchema(BaseModel):
    """Serializable schema for a reconstructed room polygon."""

    model_config = ConfigDict(extra="forbid")

    id: str
    polygon: list[PointSchema]
    area_px2: float = 0.0
    area_m2: float | None = None
    label: str | None = None
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    source: list[str] = Field(default_factory=list)


class DimensionEvidenceSchema(BaseModel):
    """Serializable schema for metric dimension evidence."""

    model_config = ConfigDict(extra="forbid")

    id: str
    value_mm: float
    start_px: PointSchema
    end_px: PointSchema
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    source: list[str] = Field(default_factory=list)


class MGRResultSchema(BaseModel):
    """Canonical serializable output schema for the MGR pipeline."""

    model_config = ConfigDict(extra="forbid")

    walls: list[WallSegmentSchema] = Field(default_factory=list)
    rooms: list[RoomPolygonSchema] = Field(default_factory=list)
    doors: list[OpeningSchema] = Field(default_factory=list)
    windows: list[OpeningSchema] = Field(default_factory=list)
    scale_mm_per_px: float | None = None
    confidence: dict[str, Any] = Field(default_factory=dict)
    provenance: dict[str, Any] = Field(default_factory=dict)
    assumptions: list[str] = Field(default_factory=list)

    @classmethod
    def from_domain(cls, result: Any) -> "MGRResultSchema":
        """Convert a domain MGRResult dataclass into the public schema."""
        return cls(
            walls=[
                WallSegmentSchema.model_validate(wall.__dict__)
                for wall in result.walls
            ],
            rooms=[
                RoomPolygonSchema.model_validate(room.__dict__)
                for room in result.rooms
            ],
            doors=[
                OpeningSchema.model_validate(door.__dict__)
                for door in result.doors
            ],
            windows=[
                OpeningSchema.model_validate(window.__dict__)
                for window in result.windows
            ],
            scale_mm_per_px=result.scale_mm_per_px,
            confidence=result.confidence,
            provenance=result.provenance,
            assumptions=result.assumptions,
        )
