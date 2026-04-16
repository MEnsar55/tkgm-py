"""Async TKGM API client (uses httpx)."""
# Asenkron TKGM API istemcisi (httpx kütüphanesini kullanır).

from __future__ import annotations

import asyncio
from functools import cached_property
from typing import Any

import httpx

from .exceptions import (
    TKGMAuthError,
    TKGMError,
    TKGMHTTPError,
    TKGMNotFoundError,
    TKGMParseError,
    TKGMRateLimitError,
)
from .models import District, Neighborhood, Parcel, Province

_BASE = "https://cbsapi.tkgm.gov.tr/megsiswebapi.v3.1/api"
_DEFAULT_TIMEOUT = 20.0
_DEFAULT_HEADERS = {
    "User-Agent": "tkgm-py/1.0 (https://github.com/MEnsar55/tkgm-py)",
    "Accept": "application/json",
    "Referer": "https://parselsorgu.tkgm.gov.tr/",
    "Origin": "https://parselsorgu.tkgm.gov.tr",
}


def _raise_for(resp: httpx.Response) -> dict:
    if resp.status_code == 401:
        raise TKGMAuthError("Authentication required. Provide a valid bearer token.")
    if resp.status_code == 429:
        raise TKGMRateLimitError("Rate limit exceeded.")
    if resp.is_error:
        raise TKGMHTTPError(resp.status_code, resp.text[:200])

    try:
        data = resp.json()
    except Exception as exc:
        raise TKGMParseError(f"Cannot parse response: {resp.text[:200]}") from exc

    if isinstance(data, dict) and "Message" in data:
        msg = data["Message"]
        if "Bulunamadı" in msg or "No HTTP resource" in msg:
            raise TKGMNotFoundError(msg)
        raise TKGMError(msg)

    return data


class AsyncTKGMClient:
    """
    Async TKGM client — drop-in async alternative to TKGMClient.

    Usage::

        async with AsyncTKGMClient() as client:
            provinces = await client.get_provinces()
            ankara = await client.find_province("Ankara")
            districts = await client.get_districts(ankara.id)

    With authentication::

        async with AsyncTKGMClient(token="...") as client:
            parcel = await client.get_parcel(55797, 14, 3)
            parcel = await client.get_parcel_by_coordinate(40.9839, 37.8764)
    """
    # Asenkron TKGM istemcisi — TKGMClient'ın async alternatifi.
    # Kullanım: async with AsyncTKGMClient() as client: provinces = await client.get_provinces()
    # Kimlik doğrulamalı: async with AsyncTKGMClient(token="...") as client: parcel = await client.get_parcel(...)

    def __init__(
        self,
        token: str | None = None,
        timeout: float = _DEFAULT_TIMEOUT,
        rate_limit_delay: float = 0.2,
    ) -> None:
        self._token = token
        self._timeout = timeout
        self._rate_limit_delay = rate_limit_delay
        self._last_request_at: float = 0.0
        self._province_cache: list[Province] | None = None
        self._lock = asyncio.Lock()

        headers = {**_DEFAULT_HEADERS}
        if token:
            headers["Authorization"] = f"Bearer {token}"

        transport = httpx.AsyncHTTPTransport(retries=3)
        self._client = httpx.AsyncClient(
            base_url=_BASE,
            headers=headers,
            timeout=timeout,
            transport=transport,
        )

    async def _get(self, path: str) -> dict:
        async with self._lock:
            now = asyncio.get_event_loop().time()
            elapsed = now - self._last_request_at
            if elapsed < self._rate_limit_delay:
                await asyncio.sleep(self._rate_limit_delay - elapsed)
            resp = await self._client.get(path)
            self._last_request_at = asyncio.get_event_loop().time()
        return _raise_for(resp)

    # ── Public endpoints ──────────────────────────────────────────────────────
    # ── Herkese açık uç noktalar ─────────────────────────────────────────────

    async def get_provinces(self) -> list[Province]:
        """Return all provinces. Cached after first call."""
        # Tüm illeri döndürür. İlk çağrıdan sonra önbelleğe alınır.
        if self._province_cache is None:
            data = await self._get("/idariYapi/ilListe")
            self._province_cache = [Province.from_feature(f) for f in data.get("features", [])]
        return self._province_cache

    async def get_districts(self, province_id: int) -> list[District]:
        data = await self._get(f"/idariYapi/ilceListe/{province_id}")
        return [District.from_feature(f, province_id=province_id) for f in data.get("features", [])]

    async def get_neighborhoods(self, district_id: int) -> list[Neighborhood]:
        data = await self._get(f"/idariYapi/mahalleListe/{district_id}")
        return [Neighborhood.from_feature(f, district_id=district_id) for f in data.get("features", [])]

    # ── Convenience finders ───────────────────────────────────────────────────
    # ── Pratik arama yardımcıları ─────────────────────────────────────────────

    async def find_province(self, name: str) -> Province:
        name_lower = name.lower()
        for p in await self.get_provinces():
            if name_lower in p.name.lower():
                return p
        raise TKGMNotFoundError(f"Province not found: {name!r}")

    async def find_district(self, province_id: int, name: str) -> District:
        name_lower = name.lower()
        for d in await self.get_districts(province_id):
            if name_lower in d.name.lower():
                return d
        raise TKGMNotFoundError(f"District not found: {name!r}")

    async def find_neighborhood(self, district_id: int, name: str) -> Neighborhood:
        name_lower = name.lower()
        for n in await self.get_neighborhoods(district_id):
            if name_lower in n.name.lower():
                return n
        raise TKGMNotFoundError(f"Neighborhood not found: {name!r}")

    # ── Authenticated endpoints ───────────────────────────────────────────────
    # ── Kimlik doğrulama gerektiren uç noktalar ───────────────────────────────

    async def get_parcel(
        self,
        neighborhood_id: int,
        block: int,
        parcel: int,
    ) -> Parcel:
        """Look up a parcel by administrative address. Requires auth."""
        # Parseli idari adresine göre sorgular. Kimlik doğrulama gerektirir.
        if not self._token:
            raise TKGMAuthError("get_parcel() requires authentication.")
        data = await self._get(f"/parsel/{neighborhood_id}/{block}/{parcel}")
        return Parcel.from_response(data, neighborhood_id, block, parcel)

    async def get_parcel_by_coordinate(self, lat: float, lon: float) -> Parcel:
        """Look up a parcel by GPS coordinates. Requires auth."""
        # GPS koordinatlarına göre parsel sorgular. Kimlik doğrulama gerektirir.
        if not self._token:
            raise TKGMAuthError("get_parcel_by_coordinate() requires authentication.")
        data = await self._get(f"/parsel/cografi/{lat:.6f}/{lon:.6f}")
        return Parcel.from_response(data, neighborhood_id=0, block=0, parcel=0)

    async def close(self) -> None:
        await self._client.aclose()

    async def __aenter__(self) -> "AsyncTKGMClient":
        return self

    async def __aexit__(self, *_) -> None:
        await self.close()
