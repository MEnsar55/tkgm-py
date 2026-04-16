# tkgm-py

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white" alt="Python 3.10+">
  <img src="https://img.shields.io/badge/License-MIT-green" alt="License: MIT">
  <img src="https://img.shields.io/badge/async-httpx-blueviolet" alt="async">
  <img src="https://img.shields.io/badge/sync-requests-orange" alt="sync">
  <img src="https://github.com/MEnsar55/tkgm-py/actions/workflows/ci.yml/badge.svg" alt="CI">
</p>

<p align="center">
  Python client for the <strong>TKGM (Tapu ve Kadastro Genel Müdürlüğü)</strong> API —
  Turkey's official land registry and cadastre service.
</p>

<p align="center">
  <a href="#installation">Installation</a> ·
  <a href="#quick-start">Quick Start</a> ·
  <a href="#authenticated-endpoints">Authenticated</a> ·
  <a href="#async-usage">Async</a> ·
  <a href="#api-reference">API Reference</a> ·
  <a href="#contributing">Contributing</a>
</p>

---

> **Inspired by** [burakaktna/tkgmservice](https://github.com/burakaktna/tkgmservice) (PHP) —
> rewritten from scratch in Python with async support, type safety, caching, and retries.

## Features

| Feature | Detail |
|---|---|
| **Sync client** | `TKGMClient` — powered by `requests` |
| **Async client** | `AsyncTKGMClient` — powered by `httpx` |
| **Type safety** | Full type hints + dataclass models (`Province`, `District`, `Neighborhood`, `Parcel`) |
| **Caching** | LRU cache for province / district / neighborhood lists |
| **Retries** | Automatic exponential backoff on transient errors (429, 5xx) |
| **Rate limiting** | Configurable minimum delay between requests |
| **GeoJSON** | `Parcel.to_geojson()` and `Geometry.centroid()` helpers |
| **Bilingual docs** | Every docstring and comment is in English + Turkish |

## Installation

```bash
git clone https://github.com/MEnsar55/tkgm-py.git
cd tkgm-py
pip install -e .
```

**Requirements:** Python ≥ 3.10, `requests`, `httpx`, `urllib3`

## Quick Start

```python
from tkgm import TKGMClient

with TKGMClient() as client:
    # Tüm 81 ili listele
    provinces = client.get_provinces()
    print(f"Total provinces: {len(provinces)}")   # 81

    # İsme göre il bul (büyük/küçük harf duyarsız, kısmi eşleşme)
    ordu = client.find_province("Ordu")
    print(ordu)   # Province(id=52, name='ORDU')

    # İlçeleri getir
    districts = client.get_districts(ordu.id)
    altinordu = client.find_district(ordu.id, "Altınordu")

    # Mahalleleri getir
    neighborhoods = client.get_neighborhoods(altinordu.id)
    akcatepe = client.find_neighborhood(altinordu.id, "Akçatepe")
    print(akcatepe)   # Neighborhood(id=..., name='AKÇATEPE')
```

## Authenticated Endpoints

Parcel lookup requires an **e-Devlet bearer token**.

### How to get a token

1. Go to **[https://online.tkgm.gov.tr/giris](https://online.tkgm.gov.tr/giris)**
2. Log in with your **e-Devlet** credentials
3. Open browser **DevTools → Network** tab
4. Click any request to `/api/` → copy the `Authorization: Bearer <token>` header value

```python
import os
from tkgm import TKGMClient

with TKGMClient(token=os.environ["TKGM_TOKEN"]) as client:
    ordu = client.find_province("Ordu")
    altinordu = client.find_district(ordu.id, "Altınordu")
    akcatepe = client.find_neighborhood(altinordu.id, "Akçatepe")

    # Ada + parsel numarasıyla sorgula
    parcel = client.get_parcel(
        neighborhood_id=akcatepe.id,
        block=14,    # ada numarası
        parcel=3,    # parsel numarası
    )
    lon, lat = parcel.geometry.centroid()
    print(f"Centroid: lat={lat:.6f}, lon={lon:.6f}")
    print(parcel.to_geojson())   # GeoJSON Feature dict

    # GPS koordinatıyla sorgula
    parcel = client.get_parcel_by_coordinate(lat=40.9839, lon=37.8764)
```

## Async Usage

```python
import asyncio
from tkgm import AsyncTKGMClient

async def main():
    async with AsyncTKGMClient() as client:
        provinces = await client.get_provinces()
        ordu = await client.find_province("Ordu")

        # Birden fazla ili paralel olarak sorgula
        cities = ["Ankara", "İstanbul", "İzmir", "Trabzon"]
        objs = await asyncio.gather(*[client.find_province(c) for c in cities])
        district_lists = await asyncio.gather(*[client.get_districts(p.id) for p in objs])
        for p, ds in zip(objs, district_lists):
            print(f"{p.name}: {len(ds)} districts")

asyncio.run(main())
```

## API Reference

### Base URL

```
https://cbsapi.tkgm.gov.tr/megsiswebapi.v3.1/api
```

### Public Endpoints (no auth required)

| Method | Endpoint | Client method |
|--------|----------|---------------|
| `GET` | `/idariYapi/ilListe` | `get_provinces()` |
| `GET` | `/idariYapi/ilceListe/{il_id}` | `get_districts(province_id)` |
| `GET` | `/idariYapi/mahalleListe/{ilce_id}` | `get_neighborhoods(district_id)` |

### Authenticated Endpoints (e-Devlet token required)

| Method | Endpoint | Client method |
|--------|----------|---------------|
| `GET` | `/parsel/{mahalle_id}/{ada}/{parsel}` | `get_parcel(neighborhood_id, block, parcel)` |
| `GET` | `/parsel/cografi/{lat}/{lon}` | `get_parcel_by_coordinate(lat, lon)` |

### Convenience Methods

| Method | Description |
|--------|-------------|
| `find_province(name)` | Case-insensitive partial name search |
| `find_district(province_id, name)` | Case-insensitive partial name search |
| `find_neighborhood(district_id, name)` | Case-insensitive partial name search |

### Models

```python
Province(id, name, geometry)
District(id, name, province_id, geometry)
Neighborhood(id, name, district_id, geometry)
Parcel(neighborhood_id, block, parcel, geometry, properties)

# Helpers
parcel.to_geojson()           # → GeoJSON Feature dict
parcel.geometry.centroid()    # → (lon, lat) tuple
```

### Constructor Options

```python
TKGMClient(
    token=None,          # e-Devlet bearer token (optional for public endpoints)
    timeout=20,          # HTTP timeout in seconds
    retries=3,           # Auto-retries on 429 / 5xx
    backoff=0.5,         # Exponential backoff factor
    rate_limit_delay=0.2 # Minimum seconds between requests
)
```

### Exception Hierarchy

```
TKGMError
├── TKGMHTTPError        HTTP 4xx / 5xx
├── TKGMNotFoundError    Resource does not exist
├── TKGMAuthError        Authentication required
├── TKGMRateLimitError   Too many requests (429)
└── TKGMParseError       Unexpected / non-JSON response
```

## Examples

See the [`examples/`](examples/) directory:

| File | Description |
|------|-------------|
| [`01_provinces.py`](examples/01_provinces.py) | List all provinces, districts, and neighborhoods |
| [`02_parcel_lookup.py`](examples/02_parcel_lookup.py) | Parcel lookup by address and GPS (requires auth) |
| [`03_async.py`](examples/03_async.py) | Async parallel requests |

```bash
python examples/01_provinces.py
TKGM_TOKEN=eyJ... python examples/02_parcel_lookup.py
python examples/03_async.py
```

## Contributing

Contributions are welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) before opening a PR.

```bash
git clone https://github.com/MEnsar55/tkgm-py.git
cd tkgm-py
pip install -e ".[dev]"
pytest
```

## License

[MIT](LICENSE) © [MEnsar55](https://github.com/MEnsar55)
