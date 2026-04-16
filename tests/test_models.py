"""Tests for tkgm.models — no network calls needed."""

import pytest
from tkgm.models import District, Feature, Geometry, Neighborhood, Parcel, Province

# ── Fixtures ──────────────────────────────────────────────────────────────────

PROVINCE_FEATURE: dict = {
    "type": "Feature",
    "geometry": {"type": "Point", "coordinates": [37.0, 41.0]},
    "properties": {"id": 52, "text": "ORDU"},
}

DISTRICT_FEATURE: dict = {
    "type": "Feature",
    "geometry": None,
    "properties": {"id": 852, "text": "ALTINORDU"},
}

NEIGHBORHOOD_FEATURE: dict = {
    "type": "Feature",
    "geometry": None,
    "properties": {"id": 12345, "text": "AKCATEPE"},
}

# 4-point square (no closing vertex) so average gives exact centroid
SQUARE_COORDS = [[[0.0, 0.0], [2.0, 0.0], [2.0, 2.0], [0.0, 2.0]]]

PARCEL_COLLECTION: dict = {
    "type": "FeatureCollection",
    "features": [
        {
            "type": "Feature",
            "geometry": {"type": "Polygon", "coordinates": SQUARE_COORDS},
            "properties": {"ada": "14", "parsel": "3"},
        }
    ],
}


# ── Geometry ──────────────────────────────────────────────────────────────────


class TestGeometry:
    def test_from_dict(self) -> None:
        geo = Geometry.from_dict({"type": "Point", "coordinates": [37.0, 41.0]})
        assert geo.type == "Point"
        assert geo.coordinates == [37.0, 41.0]

    def test_centroid_polygon(self) -> None:
        geo = Geometry(type="Polygon", coordinates=SQUARE_COORDS)
        lon, lat = geo.centroid()
        assert lon == pytest.approx(1.0)
        assert lat == pytest.approx(1.0)

    def test_centroid_non_polygon_uses_coords_directly(self) -> None:
        pts = [[0.0, 0.0], [4.0, 0.0], [4.0, 4.0], [0.0, 4.0]]
        geo = Geometry(type="LineString", coordinates=pts)
        lon, lat = geo.centroid()
        assert lon == pytest.approx(2.0)
        assert lat == pytest.approx(2.0)


# ── Province ──────────────────────────────────────────────────────────────────


class TestProvince:
    def test_from_feature(self) -> None:
        p = Province.from_feature(PROVINCE_FEATURE)
        assert p.id == 52
        assert p.name == "ORDU"
        assert p.geometry is not None
        assert p.geometry.type == "Point"

    def test_from_feature_no_geometry(self) -> None:
        feature = {**PROVINCE_FEATURE, "geometry": None}
        p = Province.from_feature(feature)
        assert p.geometry is None

    def test_repr(self) -> None:
        p = Province.from_feature(PROVINCE_FEATURE)
        assert "52" in repr(p)
        assert "ORDU" in repr(p)


# ── District ──────────────────────────────────────────────────────────────────


class TestDistrict:
    def test_from_feature(self) -> None:
        d = District.from_feature(DISTRICT_FEATURE, province_id=52)
        assert d.id == 852
        assert d.name == "ALTINORDU"
        assert d.province_id == 52
        assert d.geometry is None

    def test_from_feature_no_province(self) -> None:
        d = District.from_feature(DISTRICT_FEATURE)
        assert d.province_id is None

    def test_repr(self) -> None:
        d = District.from_feature(DISTRICT_FEATURE)
        assert "852" in repr(d)


# ── Neighborhood ──────────────────────────────────────────────────────────────


class TestNeighborhood:
    def test_from_feature(self) -> None:
        n = Neighborhood.from_feature(NEIGHBORHOOD_FEATURE, district_id=852)
        assert n.id == 12345
        assert n.name == "AKCATEPE"
        assert n.district_id == 852

    def test_repr(self) -> None:
        n = Neighborhood.from_feature(NEIGHBORHOOD_FEATURE)
        assert "12345" in repr(n)


# ── Parcel ────────────────────────────────────────────────────────────────────


class TestParcel:
    def test_from_response_feature_collection(self) -> None:
        parcel = Parcel.from_response(PARCEL_COLLECTION, neighborhood_id=12345, block=14, parcel=3)
        assert parcel.neighborhood_id == 12345
        assert parcel.block == 14
        assert parcel.parcel == 3
        assert parcel.geometry is not None
        assert parcel.geometry.type == "Polygon"

    def test_from_response_single_feature(self) -> None:
        feature = PARCEL_COLLECTION["features"][0]
        parcel = Parcel.from_response(feature, neighborhood_id=1, block=1, parcel=1)
        assert parcel.geometry is not None

    def test_from_response_empty_dict(self) -> None:
        parcel = Parcel.from_response({}, neighborhood_id=1, block=1, parcel=1)
        assert parcel.geometry is None

    def test_to_geojson_structure(self) -> None:
        parcel = Parcel.from_response(PARCEL_COLLECTION, neighborhood_id=12345, block=14, parcel=3)
        gj = parcel.to_geojson()
        assert gj["type"] == "Feature"
        assert gj["geometry"]["type"] == "Polygon"
        assert gj["properties"]["neighborhood_id"] == 12345
        assert gj["properties"]["block"] == 14
        assert gj["properties"]["parcel"] == 3

    def test_to_geojson_no_geometry(self) -> None:
        parcel = Parcel.from_response({}, neighborhood_id=1, block=1, parcel=1)
        gj = parcel.to_geojson()
        assert gj["geometry"] is None

    def test_centroid_via_geometry(self) -> None:
        parcel = Parcel.from_response(PARCEL_COLLECTION, neighborhood_id=1, block=1, parcel=1)
        assert parcel.geometry is not None
        lon, lat = parcel.geometry.centroid()
        assert lon == pytest.approx(1.0)
        assert lat == pytest.approx(1.0)

    def test_repr(self) -> None:
        parcel = Parcel.from_response(PARCEL_COLLECTION, neighborhood_id=12345, block=14, parcel=3)
        assert "12345" in repr(parcel)
        assert "14" in repr(parcel)


# ── Feature ───────────────────────────────────────────────────────────────────


class TestFeature:
    def test_from_dict_with_geometry(self) -> None:
        f = Feature.from_dict(
            {
                "geometry": {"type": "Point", "coordinates": [1.0, 2.0]},
                "properties": {"key": "value"},
            }
        )
        assert f.geometry is not None
        assert f.geometry.type == "Point"
        assert f.properties["key"] == "value"

    def test_from_dict_no_geometry(self) -> None:
        f = Feature.from_dict({"geometry": None, "properties": {}})
        assert f.geometry is None

    def test_from_dict_defaults(self) -> None:
        f = Feature.from_dict({})
        assert f.geometry is None
        assert f.properties == {}
