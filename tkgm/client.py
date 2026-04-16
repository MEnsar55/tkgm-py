"""Synchronous TKGM API client (uses requests)."""
# Senkron TKGM API istemcisi (requests kütüphanesini kullanır).

from __future__ import annotations

import time
from functools import lru_cache
from typing import Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

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
_DEFAULT_TIMEOUT = 20  # seconds / saniye
_DEFAULT_HEADERS = {
    "User-Agent": "tkgm-py/1.0 (https://github.com/yourusername/tkgm-py)",
    "Accept": "application/json",
    "Referer": "https://parselsorgu.tkgm.gov.tr/",
    "Origin": "https://parselsorgu.tkgm.gov.tr",
}


def _build_session(
    retries: int = 3,
    backoff: float = 0.5,
    token: str | None = None,
) -> requests.Session:
    session = requests.Session()
    session.headers.update(_DEFAULT_HEADERS)
    if token:
        session.headers["Authorization"] = f"Bearer {token}"

    adapter = HTTPAdapter(
        max_retries=Retry(
            total=retries,
            backoff_factor=backoff,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET"],
        )
    )
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


def _raise_for(resp: requests.Response) -> dict:
    """Parse response or raise an appropriate exception."""
    # Yanıtı ayrıştır veya uygun bir hata fırlat.
    if resp.status_code == 401:
        raise TKGMAuthError("Authentication required. Provide a valid bearer token.")
    if resp.status_code == 429:
        raise TKGMRateLimitError("Rate limit exceeded. Slow down requests.")
    if not resp.ok:
        raise TKGMHTTPError(resp.status_code, resp.text[:200])

    try:
        data = resp.json()
    except Exception as exc:
        raise TKGMParseError(f"Cannot parse response: {resp.text[:200]}") from exc

    # API returns 200 with a Message field when the resource is not found
    # API kaynak bulunamadığında 200 döndürür, yanıtta Message alanı bulunur
    if isinstance(data, dict) and "Message" in data:
        msg = data["Message"]
        if "Bulunamadı" in msg or "No HTTP resource" in msg:
            raise TKGMNotFoundError(msg)
        raise TKGMError(msg)

    return data


class TKGMClient:
    """
    Synchronous client for the TKGM (Tapu ve Kadastro Genel Müdürlüğü) API.

    Public endpoints (no auth required):
        - get_provinces()
        - get_districts(province_id)
        - get_neighborhoods(district_id)

    Authenticated endpoints (requires e-Devlet / TKGM bearer token):
        - get_parcel(neighborhood_id, block, parcel)
        - get_parcel_by_coordinate(lat, lon)

    Example::

        client = TKGMClient()
        provinces = client.get_provinces()
        ankara = client.find_province("Ankara")
        districts = client.get_districts(ankara.id)
        cankaya = client.find_district(ankara.id, "Çankaya")
        neighborhoods = client.get_neighborhoods(cankaya.id)

    With authentication::

        client = TKGMClient(token="your_bearer_token")
        parcel = client.get_parcel(neighborhood_id=55797, block=14, parcel=3)
    """
    # TKGM (Tapu ve Kadastro Genel Müdürlüğü) API'si için senkron istemci.
    # Herkese açık uç noktalar (kimlik doğrulama gerekmez):
    #   - get_provinces(), get_districts(province_id), get_neighborhoods(district_id)
    # Kimlik doğrulama gerektiren uç noktalar (e-Devlet / TKGM bearer token gerekli):
    #   - get_parcel(neighborhood_id, block, parcel), get_parcel_by_coordinate(lat, lon)

    def __init__(
        self,
        token: str | None = None,
        timeout: int = _DEFAULT_TIMEOUT,
        retries: int = 3,
        backoff: float = 0.5,
        rate_limit_delay: float = 0.2,
    ) -> None:
        """
        Args:
            token:            Bearer token from e-Devlet / TKGM login (optional for public endpoints).
            timeout:          HTTP timeout in seconds.
            retries:          Number of automatic retries on transient errors.
            backoff:          Backoff factor between retries.
            rate_limit_delay: Minimum seconds between consecutive requests.
        """
        # token:            e-Devlet / TKGM girişinden alınan Bearer token (herkese açık uç noktalar için opsiyonel).
        # timeout:          Saniye cinsinden HTTP zaman aşımı.
        # retries:          Geçici hatalarda otomatik yeniden deneme sayısı.
        # backoff:          Yeniden denemeler arasındaki bekleme çarpanı.
        # rate_limit_delay: Ardışık istekler arasındaki minimum bekleme süresi (saniye).
        self._token = token
        self._timeout = timeout
        self._rate_limit_delay = rate_limit_delay
        self._last_request_at: float = 0.0
        self._session = _build_session(retries=retries, backoff=backoff, token=token)

    def _get(self, path: str) -> dict:
        """Throttled GET with retry/error handling."""
        # Hız sınırlı GET isteği; otomatik yeniden deneme ve hata yönetimi içerir.
        elapsed = time.monotonic() - self._last_request_at
        if elapsed < self._rate_limit_delay:
            time.sleep(self._rate_limit_delay - elapsed)

        url = f"{_BASE}/{path.lstrip('/')}"
        resp = self._session.get(url, timeout=self._timeout)
        self._last_request_at = time.monotonic()
        return _raise_for(resp)

    # ── Public endpoints ──────────────────────────────────────────────────────
    # ── Herkese açık uç noktalar ─────────────────────────────────────────────

    @lru_cache(maxsize=1)
    def get_provinces(self) -> list[Province]:
        """Return all Turkish provinces (iller).

        Results are cached for the lifetime of the client instance.
        """
        # Tüm Türkiye illerini döndürür. Sonuçlar istemci ömrü boyunca önbellekte tutulur.
        data = self._get("/idariYapi/ilListe")
        return [Province.from_feature(f) for f in data.get("features", [])]

    def get_districts(self, province_id: int) -> list[District]:
        """Return all districts (ilçeler) of a province.

        Args:
            province_id: The province ID returned by get_provinces().
        """
        # Bir ile ait tüm ilçeleri döndürür.
        # province_id: get_provinces() tarafından döndürülen il ID'si.
        data = self._get(f"/idariYapi/ilceListe/{province_id}")
        return [District.from_feature(f, province_id=province_id) for f in data.get("features", [])]

    def get_neighborhoods(self, district_id: int) -> list[Neighborhood]:
        """Return all neighborhoods (mahalleler/köyler) of a district.

        Args:
            district_id: The district ID returned by get_districts().
        """
        # Bir ilçeye ait tüm mahalleleri / köyleri döndürür.
        # district_id: get_districts() tarafından döndürülen ilçe ID'si.
        data = self._get(f"/idariYapi/mahalleListe/{district_id}")
        return [Neighborhood.from_feature(f, district_id=district_id) for f in data.get("features", [])]

    # ── Convenience finders ───────────────────────────────────────────────────
    # ── Pratik arama yardımcıları ─────────────────────────────────────────────

    def find_province(self, name: str) -> Province:
        """Find a province by name (case-insensitive, partial match).

        Raises TKGMNotFoundError if not found.
        """
        # İl adına göre arama yapar (büyük/küçük harf duyarsız, kısmi eşleşme).
        # Bulunamazsa TKGMNotFoundError fırlatır.
        name_lower = name.lower()
        for p in self.get_provinces():
            if name_lower in p.name.lower():
                return p
        raise TKGMNotFoundError(f"Province not found: {name!r}")

    def find_district(self, province_id: int, name: str) -> District:
        """Find a district within a province by name (case-insensitive, partial match)."""
        # İl içinde ilçe adına göre arama yapar (büyük/küçük harf duyarsız, kısmi eşleşme).
        name_lower = name.lower()
        for d in self.get_districts(province_id):
            if name_lower in d.name.lower():
                return d
        raise TKGMNotFoundError(f"District not found: {name!r} in province {province_id}")

    def find_neighborhood(self, district_id: int, name: str) -> Neighborhood:
        """Find a neighborhood within a district by name (case-insensitive, partial match)."""
        # İlçe içinde mahalle adına göre arama yapar (büyük/küçük harf duyarsız, kısmi eşleşme).
        name_lower = name.lower()
        for n in self.get_neighborhoods(district_id):
            if name_lower in n.name.lower():
                return n
        raise TKGMNotFoundError(f"Neighborhood not found: {name!r} in district {district_id}")

    # ── Authenticated endpoints ───────────────────────────────────────────────
    # ── Kimlik doğrulama gerektiren uç noktalar ───────────────────────────────

    def get_parcel(
        self,
        neighborhood_id: int,
        block: int,
        parcel: int,
    ) -> Parcel:
        """Look up a cadastral parcel by its administrative address.

        Requires authentication (set ``token`` in constructor).

        Args:
            neighborhood_id: Mahalle ID from get_neighborhoods().
            block:           Ada (block) number.
            parcel:          Parsel (parcel) number.

        Raises:
            TKGMNotFoundError: Parcel does not exist.
            TKGMAuthError:     Authentication token required.
        """
        # Kadastral parseli idari adresine göre sorgular.
        # Kimlik doğrulama gerektirir (constructor'da token parametresini ayarlayın).
        # neighborhood_id: get_neighborhoods() ile alınan mahalle ID'si.
        # block:           Ada numarası.
        # parcel:          Parsel numarası.
        # TKGMNotFoundError: Parsel mevcut değil.
        # TKGMAuthError:     Kimlik doğrulama token'ı gerekli.
        if not self._token:
            raise TKGMAuthError(
                "get_parcel() requires authentication. "
                "Pass token=<your_bearer_token> to TKGMClient()."
            )
        data = self._get(f"/parsel/{neighborhood_id}/{block}/{parcel}")
        return Parcel.from_response(data, neighborhood_id, block, parcel)

    def get_parcel_by_coordinate(self, lat: float, lon: float) -> Parcel:
        """Look up a parcel by GPS coordinates (WGS84).

        Requires authentication (set ``token`` in constructor).

        Args:
            lat: Latitude (e.g. 40.9839 for Ordu).
            lon: Longitude (e.g. 37.8764 for Ordu).

        Raises:
            TKGMNotFoundError: No parcel at these coordinates.
            TKGMAuthError:     Authentication token required.

        Note:
            Authentication is obtained via e-Devlet login at:
            https://online.tkgm.gov.tr/giris
            The bearer token can be extracted from the browser's
            Authorization header after login.
        """
        # GPS koordinatlarına göre parsel sorgular (WGS84).
        # Kimlik doğrulama gerektirir (constructor'da token parametresini ayarlayın).
        # lat: Enlem (örn. Ordu için 40.9839).
        # lon: Boylam (örn. Ordu için 37.8764).
        # TKGMNotFoundError: Bu koordinatlarda parsel bulunamadı.
        # TKGMAuthError:     Kimlik doğrulama token'ı gerekli.
        # Not: Kimlik doğrulama e-Devlet girişi üzerinden alınır:
        #      https://online.tkgm.gov.tr/giris
        #      Bearer token, giriş sonrası tarayıcının Authorization başlığından kopyalanabilir.
        if not self._token:
            raise TKGMAuthError(
                "get_parcel_by_coordinate() requires authentication. "
                "Pass token=<your_bearer_token> to TKGMClient()."
            )
        data = self._get(f"/parsel/cografi/{lat:.6f}/{lon:.6f}")
        return Parcel.from_response(data, neighborhood_id=0, block=0, parcel=0)

    def close(self) -> None:
        """Close the underlying HTTP session."""
        # Alttaki HTTP oturumunu kapat.
        self._session.close()

    def __enter__(self) -> "TKGMClient":
        return self

    def __exit__(self, *_) -> None:
        self.close()
