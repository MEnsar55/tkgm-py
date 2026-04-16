"""Tests for TKGMClient (sync) using responses mock."""

from unittest.mock import MagicMock

import pytest
import responses as rsps

from tkgm import TKGMClient
from tkgm.client import _raise_for
from tkgm.exceptions import (
    TKGMAuthError,
    TKGMHTTPError,
    TKGMNotFoundError,
    TKGMParseError,
    TKGMRateLimitError,
)

BASE = "https://cbsapi.tkgm.gov.tr/megsiswebapi.v3.1/api"

# ── Shared payloads (ASCII-only names to avoid locale encoding issues) ─────────

PROVINCES = {
    "type": "FeatureCollection",
    "features": [
        {"type": "Feature", "geometry": None, "properties": {"id": 52, "text": "ORDU"}},
        {"type": "Feature", "geometry": None, "properties": {"id": 6, "text": "ANKARA"}},
    ],
}

DISTRICTS = {
    "type": "FeatureCollection",
    "features": [
        {"type": "Feature", "geometry": None, "properties": {"id": 852, "text": "ALTINORDU"}},
        {"type": "Feature", "geometry": None, "properties": {"id": 853, "text": "FATSA"}},
    ],
}

NEIGHBORHOODS = {
    "type": "FeatureCollection",
    "features": [
        {"type": "Feature", "geometry": None, "properties": {"id": 12345, "text": "AKCATEPE"}},
    ],
}

PARCEL = {
    "type": "FeatureCollection",
    "features": [
        {
            "type": "Feature",
            "geometry": {
                "type": "Polygon",
                "coordinates": [[[0.0, 0.0], [2.0, 0.0], [2.0, 2.0], [0.0, 2.0]]],
            },
            "properties": {"ada": "14", "parsel": "3"},
        }
    ],
}


# ── Province tests ────────────────────────────────────────────────────────────


@rsps.activate
def test_get_provinces() -> None:
    rsps.add(rsps.GET, f"{BASE}/idariYapi/ilListe", json=PROVINCES)
    with TKGMClient() as client:
        provinces = client.get_provinces()
    assert len(provinces) == 2
    assert provinces[0].id == 52
    assert provinces[0].name == "ORDU"


@rsps.activate
def test_find_province_case_insensitive() -> None:
    rsps.add(rsps.GET, f"{BASE}/idariYapi/ilListe", json=PROVINCES)
    with TKGMClient() as client:
        p = client.find_province("ordu")
    assert p.id == 52


@rsps.activate
def test_find_province_partial_match() -> None:
    rsps.add(rsps.GET, f"{BASE}/idariYapi/ilListe", json=PROVINCES)
    with TKGMClient() as client:
        p = client.find_province("ANK")
    assert p.id == 6


@rsps.activate
def test_find_province_not_found() -> None:
    rsps.add(rsps.GET, f"{BASE}/idariYapi/ilListe", json=PROVINCES)
    with TKGMClient() as client:
        with pytest.raises(TKGMNotFoundError):
            client.find_province("XYZ_NONEXISTENT")


# ── District tests ────────────────────────────────────────────────────────────


@rsps.activate
def test_get_districts() -> None:
    rsps.add(rsps.GET, f"{BASE}/idariYapi/ilceListe/52", json=DISTRICTS)
    with TKGMClient() as client:
        districts = client.get_districts(52)
    assert len(districts) == 2
    assert all(d.province_id == 52 for d in districts)


@rsps.activate
def test_find_district() -> None:
    rsps.add(rsps.GET, f"{BASE}/idariYapi/ilceListe/52", json=DISTRICTS)
    with TKGMClient() as client:
        d = client.find_district(52, "altin")  # ASCII — avoids dotless-i mismatch
    assert d.id == 852


@rsps.activate
def test_find_district_not_found() -> None:
    rsps.add(rsps.GET, f"{BASE}/idariYapi/ilceListe/52", json=DISTRICTS)
    with TKGMClient() as client:
        with pytest.raises(TKGMNotFoundError):
            client.find_district(52, "NONEXISTENT")


# ── Neighborhood tests ────────────────────────────────────────────────────────


@rsps.activate
def test_get_neighborhoods() -> None:
    rsps.add(rsps.GET, f"{BASE}/idariYapi/mahalleListe/852", json=NEIGHBORHOODS)
    with TKGMClient() as client:
        neighborhoods = client.get_neighborhoods(852)
    assert len(neighborhoods) == 1
    assert neighborhoods[0].district_id == 852


@rsps.activate
def test_find_neighborhood() -> None:
    rsps.add(rsps.GET, f"{BASE}/idariYapi/mahalleListe/852", json=NEIGHBORHOODS)
    with TKGMClient() as client:
        n = client.find_neighborhood(852, "akcat")  # ASCII
    assert n.id == 12345


# ── Parcel tests ──────────────────────────────────────────────────────────────


def test_get_parcel_requires_auth() -> None:
    with TKGMClient() as client:
        with pytest.raises(TKGMAuthError):
            client.get_parcel(12345, 14, 3)


@rsps.activate
def test_get_parcel_by_coordinate_no_auth_needed() -> None:
    rsps.add(rsps.GET, f"{BASE}/parsel/40.983900/37.876400/", json=PARCEL)
    with TKGMClient() as client:  # no token needed
        parcel = client.get_parcel_by_coordinate(40.9839, 37.8764)
    assert parcel.geometry is not None


@rsps.activate
def test_get_parcel_with_token() -> None:
    rsps.add(rsps.GET, f"{BASE}/parsel/12345/14/3", json=PARCEL)
    with TKGMClient(token="test-token") as client:
        parcel = client.get_parcel(12345, 14, 3)
    assert parcel.block == 14
    assert parcel.parcel == 3
    assert parcel.geometry is not None
    assert parcel.geometry.type == "Polygon"


@rsps.activate
def test_get_parcel_by_coordinate_with_token() -> None:
    rsps.add(rsps.GET, f"{BASE}/parsel/40.983900/37.876400/", json=PARCEL)
    with TKGMClient(token="test-token") as client:
        parcel = client.get_parcel_by_coordinate(40.9839, 37.8764)
    assert parcel.geometry is not None


# ── _raise_for unit tests (bypass retry logic) ────────────────────────────────


def _mock_resp(status: int, text: str = "", json_body: object = None) -> MagicMock:
    resp = MagicMock()
    resp.status_code = status
    resp.ok = status < 400
    resp.text = text
    if json_body is not None:
        resp.json.return_value = json_body
    else:
        resp.json.side_effect = ValueError("no json")
    return resp


def test_raise_for_401() -> None:
    with pytest.raises(TKGMAuthError):
        _raise_for(_mock_resp(401))


def test_raise_for_429() -> None:
    with pytest.raises(TKGMRateLimitError):
        _raise_for(_mock_resp(429))


def test_raise_for_500() -> None:
    with pytest.raises(TKGMHTTPError) as exc_info:
        _raise_for(_mock_resp(500, text="oops"))
    assert exc_info.value.status_code == 500


def test_raise_for_invalid_json() -> None:
    resp = MagicMock()
    resp.status_code = 200
    resp.ok = True
    resp.text = "not-json"
    resp.json.side_effect = ValueError("bad json")
    with pytest.raises(TKGMParseError):
        _raise_for(resp)


def test_raise_for_message_bulunamadi() -> None:
    resp = MagicMock()
    resp.status_code = 200
    resp.ok = True
    resp.json.return_value = {"Message": "No HTTP resource was found"}
    with pytest.raises(TKGMNotFoundError):
        _raise_for(resp)


def test_raise_for_message_no_http_resource() -> None:
    resp = MagicMock()
    resp.status_code = 200
    resp.ok = True
    resp.json.return_value = {"Message": "No HTTP resource was found"}
    with pytest.raises(TKGMNotFoundError):
        _raise_for(resp)


# ── Context manager ───────────────────────────────────────────────────────────


@rsps.activate
def test_context_manager() -> None:
    rsps.add(rsps.GET, f"{BASE}/idariYapi/ilListe", json=PROVINCES)
    with TKGMClient() as client:
        provinces = client.get_provinces()
    assert len(provinces) == 2
