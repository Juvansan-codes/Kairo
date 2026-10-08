import pytest
from pydantic import ValidationError

from app.geometry.schema import (
    DimensionEvidenceSchema,
    MGRResultSchema,
    OpeningSchema,
    RoomPolygonSchema,
    WallSegmentSchema,
)
from app.geometry.types import (
    DimensionEvidence,
    MGRResult,
    Opening,
    RoomPolygon,
    WallSegment,
)


def test_wall_segment_schema():
    wall = WallSegmentSchema(
        id="wall-1",
        start=(0.0, 0.0),
        end=(100.0, 0.0),
        length_px=100.0,
        angle_deg=0.0,
        confidence=0.95,
        source=["skeleton"],
    )

    assert wall.id == "wall-1"
    assert wall.start == (0.0, 0.0)
    assert wall.confidence == 0.95


def test_opening_schema_accepts_door_and_window():
    door = OpeningSchema(
        id="door-1",
        type="door",
        start=(20.0, 0.0),
        end=(40.0, 0.0),
        wall_id="wall-1",
        confidence=0.9,
    )
    window = OpeningSchema(
        id="window-1",
        type="window",
        start=(60.0, 0.0),
        end=(80.0, 0.0),
        wall_id="wall-1",
        confidence=0.85,
    )

    assert door.type == "door"
    assert window.type == "window"


def test_opening_schema_rejects_invalid_type():
    with pytest.raises(ValidationError):
        OpeningSchema(
            id="opening-1",
            type="opening",
            start=(0.0, 0.0),
            end=(10.0, 0.0),
        )


def test_room_polygon_schema():
    room = RoomPolygonSchema(
        id="room-1",
        polygon=[
            (0.0, 0.0),
            (100.0, 0.0),
            (100.0, 100.0),
            (0.0, 100.0),
        ],
        area_px2=10000.0,
        area_m2=4.0,
        label="Living Room",
        confidence=0.92,
        source=["polygonization"],
    )

    assert len(room.polygon) == 4
    assert room.area_px2 == 10000.0
    assert room.area_m2 == 4.0


def test_dimension_evidence_schema():
    dimension = DimensionEvidenceSchema(
        id="dim-1",
        value_mm=2000.0,
        start_px=(0.0, 0.0),
        end_px=(100.0, 0.0),
        confidence=0.98,
        source=["dimension_annotation"],
    )

    assert dimension.value_mm == 2000.0
    assert dimension.start_px == (0.0, 0.0)


def test_confidence_must_be_between_zero_and_one():
    with pytest.raises(ValidationError):
        WallSegmentSchema(
            id="wall-1",
            start=(0.0, 0.0),
            end=(10.0, 0.0),
            confidence=1.5,
        )

    with pytest.raises(ValidationError):
        RoomPolygonSchema(
            id="room-1",
            polygon=[(0.0, 0.0), (10.0, 0.0)],
            confidence=-0.1,
        )


def test_mgr_result_schema_defaults():
    result = MGRResultSchema()

    assert result.walls == []
    assert result.rooms == []
    assert result.doors == []
    assert result.windows == []
    assert result.scale_mm_per_px is None
    assert result.confidence == {}
    assert result.provenance == {}
    assert result.assumptions == []


def test_mgr_result_schema_serializes_nested_geometry():
    result = MGRResultSchema(
        walls=[
            WallSegmentSchema(
                id="wall-1",
                start=(0.0, 0.0),
                end=(100.0, 0.0),
                confidence=0.9,
            )
        ],
        rooms=[
            RoomPolygonSchema(
                id="room-1",
                polygon=[
                    (0.0, 0.0),
                    (100.0, 0.0),
                    (100.0, 100.0),
                    (0.0, 100.0),
                ],
                area_px2=10000.0,
                area_m2=4.0,
                confidence=0.95,
            )
        ],
        doors=[
            OpeningSchema(
                id="door-1",
                type="door",
                start=(20.0, 0.0),
                end=(40.0, 0.0),
                wall_id="wall-1",
            )
        ],
        windows=[
            OpeningSchema(
                id="window-1",
                type="window",
                start=(60.0, 0.0),
                end=(80.0, 0.0),
                wall_id="wall-1",
            )
        ],
        scale_mm_per_px=20.0,
        confidence={
            "overall": 0.93,
            "geometry": 0.95,
            "scale": 0.9,
            "topology_valid": True,
        },
        provenance={
            "source": "MGR",
            "method": "deterministic_geometric_reconciliation",
        },
        assumptions=["metric calibration derived from dimension evidence"],
    )

    payload = result.model_dump(mode="json")

    assert payload["walls"][0]["id"] == "wall-1"
    assert payload["rooms"][0]["area_m2"] == 4.0
    assert payload["doors"][0]["type"] == "door"
    assert payload["windows"][0]["type"] == "window"
    assert payload["scale_mm_per_px"] == 20.0
    assert payload["confidence"]["overall"] == 0.93
    assert payload["provenance"]["source"] == "MGR"


def test_mgr_result_schema_from_domain():
    domain_result = MGRResult(
        walls=[
            WallSegment(
                id="wall-1",
                start=(0.0, 0.0),
                end=(100.0, 0.0),
                length_px=100.0,
                confidence=0.9,
            )
        ],
        rooms=[
            RoomPolygon(
                id="room-1",
                polygon=[
                    (0.0, 0.0),
                    (100.0, 0.0),
                    (100.0, 100.0),
                    (0.0, 100.0),
                ],
                area_px2=10000.0,
                area_m2=4.0,
                confidence=0.95,
            )
        ],
        doors=[
            Opening(
                id="door-1",
                type="door",
                start=(20.0, 0.0),
                end=(40.0, 0.0),
                wall_id="wall-1",
            )
        ],
        windows=[],
        scale_mm_per_px=20.0,
        confidence={"overall": 0.93},
        provenance={"source": "MGR"},
        assumptions=["calibrated"],
    )

    schema_result = MGRResultSchema.from_domain(domain_result)

    assert schema_result.walls[0].id == "wall-1"
    assert schema_result.rooms[0].area_m2 == 4.0
    assert schema_result.doors[0].wall_id == "wall-1"
    assert schema_result.scale_mm_per_px == 20.0
    assert schema_result.confidence["overall"] == 0.93
    assert schema_result.provenance["source"] == "MGR"


def test_schema_rejects_unknown_fields():
    with pytest.raises(ValidationError):
        WallSegmentSchema(
            id="wall-1",
            start=(0.0, 0.0),
            end=(10.0, 0.0),
            unexpected_field="not-allowed",
        )


def test_schema_json_schema_is_generated():
    schema = MGRResultSchema.model_json_schema()

    assert schema["title"] == "MGRResultSchema"
    assert "properties" in schema
    assert "walls" in schema["properties"]
    assert "rooms" in schema["properties"]
    assert "doors" in schema["properties"]
    assert "windows" in schema["properties"]
    assert "scale_mm_per_px" in schema["properties"]
    assert "confidence" in schema["properties"]
    assert "provenance" in schema["properties"]
    assert "assumptions" in schema["properties"]
