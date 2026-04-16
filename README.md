# tkgm-py

Python client for the **TKGM (Tapu ve Kadastro Genel Müdürlüğü)** API — Turkey's official land registry and cadastre service.

> **Inspired by** [burakaktna/tkgmservice](https://github.com/burakaktna/tkgmservice) (PHP) — rewritten from scratch in Python with async support, caching, retries, and type safety.

## Features

- Full type hints and dataclass models (`Province`, `District`, `Neighborhood`, `Parcel`)
- **Sync** client (`TKGMClient`) via `requests`
- **Async** client (`AsyncTKGMClient`) via `httpx`
- LRU caching for province/district/neighborhood lists
- Automatic retry with exponential backoff
- Rate limiting between requests
- Proper exception hierarchy

## Installation

```bash
pip install requests httpx
# Clone the repo (not yet on PyPI)
git clone https://github.com/yourusername/tkgm-py
cd tkgm-py
pip install -e .
```

## Quick Start

```python
from tkgm import TKGMClient

with TKGMClient() as client:
    # List all 81 provinces
    provinces = client.get_provinces()

    # Find a province by name
    ordu = client.find_province("Ordu")         # Province(id=74, name='Ordu')

    # List districts
    districts = client.get_districts(ordu.id)

    # Find a district
    altinordu = client.find_district(ordu.id, "Altınordu")

    # List neighborhoods
    neighborhoods = client.get_neighborhoods(altinordu.id)

    # Find a neighborhood
    akcatepe = client.find_neighborhood(altinordu.id, "Akçatepe")
```

## Authenticated Endpoints

Parcel lookup (by address or GPS coordinate) requires an **e-Devlet bearer token**.

### How to get a token

1. Go to [https://online.tkgm.gov.tr/giris](https://online.tkgm.gov.tr/giris)
2. Log in with e-Devlet credentials
3. Open browser DevTools → Network → any `/api/` request → copy the `Authorization: Bearer <token>` header

```python
from tkgm import TKGMClient

with TKGMClient(token="eyJhbGci...") as client:
    # Lookup by neighborhood ID + ada + parsel
    parcel = client.get_parcel(
        neighborhood_id=akcatepe.id,
        block=14,    # ada numarası
        parcel=3,    # parsel numarası
    )
    print(parcel.geometry.centroid())   # (lon, lat)
    print(parcel.to_geojson())          # GeoJSON Feature dict

    # Lookup by GPS coordinate
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
        districts = await client.get_districts(ordu.id)

asyncio.run(main())
```

## API Reference

### Base URL

```
https://cbsapi.tkgm.gov.tr/megsiswebapi.v3.1/api
```

### Public Endpoints (no auth)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/idariYapi/ilListe` | All provinces |
| `GET` | `/idariYapi/ilceListe/{il_id}` | Districts of a province |
| `GET` | `/idariYapi/mahalleListe/{ilce_id}` | Neighborhoods of a district |

### Authenticated Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/parsel/{mahalle_id}/{ada}/{parsel}` | Parcel by address |
| `GET` | `/parsel/cografi/{lat}/{lon}` | Parcel by GPS coordinate |

## Exception Hierarchy

```
TKGMError
├── TKGMHTTPError       HTTP 4xx/5xx
├── TKGMNotFoundError   Resource does not exist
├── TKGMAuthError       Authentication required
├── TKGMRateLimitError  Too many requests
└── TKGMParseError      Unexpected response format
```

## License

MIT
