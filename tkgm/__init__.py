"""
tkgm-py — Python client for the Turkish Land Registry (TKGM) API.

Public API::

    from tkgm import TKGMClient, AsyncTKGMClient
    from tkgm.models import Province, District, Neighborhood, Parcel
    from tkgm.exceptions import TKGMNotFoundError, TKGMAuthError

Quick start::

    with TKGMClient() as client:
        provinces = client.get_provinces()
        ankara = client.find_province("Ankara")
        districts = client.get_districts(ankara.id)
        cankaya = client.find_district(ankara.id, "Çankaya")
        neighborhoods = client.get_neighborhoods(cankaya.id)

API base URL: https://cbsapi.tkgm.gov.tr/megsiswebapi.v3.1/api
"""
# tkgm-py — Türkiye Tapu ve Kadastro (TKGM) API'si için Python istemcisi.
# Hızlı başlangıç: TKGMClient veya AsyncTKGMClient ile il/ilçe/mahalle/parsel sorgulayın.

from .async_client import AsyncTKGMClient
from .client import TKGMClient
from .exceptions import (
    TKGMAuthError,
    TKGMError,
    TKGMHTTPError,
    TKGMNotFoundError,
    TKGMParseError,
    TKGMRateLimitError,
)
from .models import District, Geometry, Neighborhood, Parcel, Province

__version__ = "1.0.0"
__all__ = [
    "TKGMClient",
    "AsyncTKGMClient",
    "Province",
    "District",
    "Neighborhood",
    "Parcel",
    "Geometry",
    "TKGMError",
    "TKGMHTTPError",
    "TKGMNotFoundError",
    "TKGMAuthError",
    "TKGMParseError",
    "TKGMRateLimitError",
]
