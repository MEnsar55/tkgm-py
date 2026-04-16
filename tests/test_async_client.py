"""Tests for AsyncTKGMClient using respx mock."""

import httpx
import pytest
import respx

from tkgm import AsyncTKGMClient
from tkgm.async_client import _raise_for
from tkgm.exceptions import TKGMAuthError, TKGMHTTPError, TKGMNotFoundError, TKGMParseError

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
            "properties": {},
        }
    ],
}


# ── Province tests ────────────────────────────────────────────────────────────


@respx.mock
async def test_get_provinces() -> None:
    respx.get(f"{BASE}/idariYapi/ilListe").mock(
        return_value=httpx.Response(200, json=PROVINCES)
    )
    async with AsyncTKGMClient() as client:
        provinces = await client.get_provinces()
    assert len(provinces) == 2
    assert provinces[0].name == "ORDU"


@respx.mock
async def test_provinces_are_cached() -> None:
    respx.get(f"{BASE}/idariYapi/ilListe").mock(
        return_value=httpx.Response(200, json=PROVINCES)
    )
    async with AsyncTKGMClient() as client:
        p1 = await client.get_provinces()
        p2 = await client.get_provinces()
    assert p1 is p2  # same list object — cache hit


@respx.mock
async def test_find_province() -> None:
    respx.get(f"{BASE}/idariYapi/ilListe").mock(
        return_value=httpx.Response(200, json=PROVINCES)
    )
    async with AsyncTKGMClient() as client:
        p = await client.find_province("ordu")
    assert p.id == 52


@respx.mock
async def test_find_province_not_found() -> None:
    respx.get(f"{BASE}/idariYapi/ilListe").mock(
        return_value=httpx.Response(200, json=PROVINCES)
    )
    async with AsyncTKGMClient() as client:
        with pytest.raises(TKGMNotFoundError):
            await client.find_province("NONEXISTENT")


# ── District tests ────────────────────────────────────────────────────────────


@respx.mock
async def test_get_districts() -> None:
    respx.get(f"{BASE}/idariYapi/ilceListe/52").mock(
        return_value=httpx.Response(200, json=DISTRICTS)
    )
    async with AsyncTKGMClient() as client:
        districts = await client.get_districts(52)
    assert len(districts) == 1
    assert districts[0].province_id == 52


@respx.mock
async def test_find_district() -> None:
    respx.get(f"{BASE}/idariYapi/ilceListe/52").mock(
        return_value=httpx.Response(200, json=DISTRICTS)
    )
    async with AsyncTKGMClient() as client:
        d = await client.find_district(52, "altin")  # ASCII — avoids dotless-i mismatch
    assert d.id == 852


@respx.mock
async def test_find_district_not_found() -> None:
    respx.get(f"{BASE}/idariYapi/ilceListe/52").mock(
        return_value=httpx.Response(200, json=DISTRICTS)
    )
    async with AsyncTKGMClient() as client:
        with pytest.raises(TKGMNotFoundError):
            await client.find_district(52, "NONEXISTENT")


# ── Neighborhood tests ────────────────────────────────────────────────────────


@respx.mock
async def test_get_neighborhoods() -> None:
    respx.get(f"{BASE}/idariYapi/mahalleListe/852").mock(
        return_value=httpx.Response(200, json=NEIGHBORHOODS)
    )
    async with AsyncTKGMClient() as client:
        neighborhoods = await client.get_neighborhoods(852)
    assert len(neighborhoods) == 1
    assert neighborhoods[0].district_id == 852


@respx.mock
async def test_find_neighborhood() -> None:
    respx.get(f"{BASE}/idariYapi/mahalleListe/852").mock(
        return_value=httpx.Response(200, json=NEIGHBORHOODS)
    )
    async with AsyncTKGMClient() as client:
        n = await client.find_neighborhood(852, "akcat")  # ASCII
    assert n.id == 12345


# ── Parcel tests ──────────────────────────────────────────────────────────────


async def test_get_parcel_requires_auth() -> None:
    async with AsyncTKGMClient() as client:
        with pytest.raises(TKGMAuthError):
            await client.get_parcel(12345, 14, 3)


async def test_get_parcel_by_coordinate_requires_auth() -> None:
    async with AsyncTKGMClient() as client:
        with pytest.raises(TKGMAuthError):
            await client.get_parcel_by_coordinate(40.9839, 37.8764)


@respx.mock
async def test_get_parcel_with_token() -> None:
    respx.get(f"{BASE}/parsel/12345/14/3").mock(
        return_value=httpx.Response(200, json=PARCEL)
    )
    async with AsyncTKGMClient(token="test-token") as client:
        parcel = await client.get_parcel(12345, 14, 3)
    assert parcel.geometry is not None
    assert parcel.geometry.type == "Polygon"


@respx.mock
async def test_get_parcel_by_coordinate_with_token() -> None:
    respx.get(f"{BASE}/parsel/cografi/40.983900/37.876400").mock(
        return_value=httpx.Response(200, json=PARCEL)
    )
    async with AsyncTKGMClient(token="test-token") as client:
        parcel = await client.get_parcel_by_coordinate(40.9839, 37.8764)
    assert parcel.geometry is not None


# ── _raise_for unit tests ─────────────────────────────────────────────────────


def test_raise_for_401() -> None:
    resp = httpx.Response(401)
    with pytest.raises(TKGMAuthError):
        _raise_for(resp)


def test_raise_for_429() -> None:
    resp = httpx.Response(429)
    with pytest.raises(Exception):  # TKGMRateLimitError
        _raise_for(resp)


def test_raise_for_500() -> None:
    resp = httpx.Response(500, text="oops")
    with pytest.raises(TKGMHTTPError) as exc_info:
        _raise_for(resp)
    assert exc_info.value.status_code == 500


def test_raise_for_invalid_json() -> None:
    resp = httpx.Response(200, content=b"not-json-at-all!!!")
    with pytest.raises(TKGMParseError):
        _raise_for(resp)


def test_raise_for_message_bulunamadi() -> None:
    resp = httpx.Response(200, json={"Message": "No HTTP resource was found"})
    with pytest.raises(TKGMNotFoundError):
        _raise_for(resp)


# ── Context manager ───────────────────────────────────────────────────────────


@respx.mock
async def test_context_manager() -> None:
    respx.get(f"{BASE}/idariYapi/ilListe").mock(
        return_value=httpx.Response(200, json=PROVINCES)
    )
    async with AsyncTKGMClient() as client:
        provinces = await client.get_provinces()
    assert len(provinces) == 2
