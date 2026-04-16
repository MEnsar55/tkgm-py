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
  Turkey's official land registry and cadastre service.<br>
  <em>Türkiye'nin resmi tapu ve kadastro servisi için Python istemcisi.</em>
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
>
> *[burakaktna/tkgmservice](https://github.com/burakaktna/tkgmservice) (PHP) projesinden ilham alınarak
> async desteği, tip güvenliği, önbellekleme ve yeniden deneme mekanizmasıyla sıfırdan Python'a yazıldı.*

## Features / Özellikler

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

*Senkron (`TKGMClient`) ve asenkron (`AsyncTKGMClient`) istemci, tam tip desteği, LRU önbellekleme,
otomatik yeniden deneme, GeoJSON yardımcıları ve İngilizce + Türkçe ikidilli dokümantasyon.*

## Installation / Kurulum

```bash
git clone https://github.com/MEnsar55/tkgm-py.git
cd tkgm-py
pip install -e .
```

**Requirements:** Python ≥ 3.10, `requests`, `httpx`, `urllib3`

*Python ≥ 3.10, `requests`, `httpx` ve `urllib3` gerektirir.*

## Quick Start / Hızlı Başlangıç

```python
from tkgm import TKGMClient

with TKGMClient() as client:
    # List all 81 provinces
    provinces = client.get_provinces()
    print(f"Total provinces: {len(provinces)}")   # 81

    # Find a province by name (case-insensitive, partial match)
    ordu = client.find_province("Ordu")
    print(ordu)   # Province(id=52, name='ORDU')

    # Get districts
    districts = client.get_districts(ordu.id)
    altinordu = client.find_district(ordu.id, "Altınordu")

    # Get neighborhoods
    neighborhoods = client.get_neighborhoods(altinordu.id)
    akcatepe = client.find_neighborhood(altinordu.id, "Akçatepe")
    print(akcatepe)   # Neighborhood(id=..., name='AKÇATEPE')
```

*Tüm 81 ili listeler, isme göre il/ilçe/mahalle arar (büyük/küçük harf duyarsız, kısmi eşleşme).*

## Authenticated Endpoints / Kimlik Doğrulama Gerektiren Uç Noktalar

Parcel lookup requires an **e-Devlet bearer token**.

*Parsel sorguları **e-Devlet bearer token** gerektirir.*

### How to get a token / Token nasıl alınır

The token is a JWT obtained after logging into the TKGM portal via e-Devlet.
The exact login URL may vary — look for a TKGM service on [turkiye.gov.tr](https://www.turkiye.gov.tr)
or check the Network tab of your browser while using any official TKGM web tool.

Once logged in, open **DevTools → Network** → click any `/api/` request →
copy the `Authorization: Bearer <token>` header value.

> **Note:** Some TKGM URLs require specific redirect parameters and cannot be opened directly.
> Always navigate through the official portal or an official TKGM application.

*Token, e-Devlet üzerinden TKGM portalına giriş yapıldıktan sonra alınan bir JWT'dir.
Giriş URL'si değişkenlik gösterebilir — [turkiye.gov.tr](https://www.turkiye.gov.tr) üzerinden
TKGM hizmetini arayın ya da resmi bir TKGM aracını kullanırken tarayıcının Network sekmesini inceleyin.*

*Giriş sonrası: **F12 → Network** → herhangi bir `/api/` isteği → `Authorization: Bearer <token>` başlığını kopyalayın.*

*Not: Bazı TKGM URL'leri yönlendirme parametresi gerektirdiğinden doğrudan açılamaz.
Her zaman resmi portal veya resmi bir TKGM uygulaması üzerinden erişin.*

```python
import os
from tkgm import TKGMClient

with TKGMClient(token=os.environ["TKGM_TOKEN"]) as client:
    ordu = client.find_province("Ordu")
    altinordu = client.find_district(ordu.id, "Altınordu")
    akcatepe = client.find_neighborhood(altinordu.id, "Akçatepe")

    # Look up by ada + parsel number
    parcel = client.get_parcel(
        neighborhood_id=akcatepe.id,
        block=14,    # ada numarası
        parcel=3,    # parsel numarası
    )
    lon, lat = parcel.geometry.centroid()
    print(f"Centroid: lat={lat:.6f}, lon={lon:.6f}")
    print(parcel.to_geojson())   # GeoJSON Feature dict

    # Look up by GPS coordinate
    parcel = client.get_parcel_by_coordinate(lat=40.9839, lon=37.8764)
```

## Async Usage / Asenkron Kullanım

```python
import asyncio
from tkgm import AsyncTKGMClient

async def main():
    async with AsyncTKGMClient() as client:
        provinces = await client.get_provinces()
        ordu = await client.find_province("Ordu")

        # Fetch multiple provinces in parallel
        cities = ["Ankara", "İstanbul", "İzmir", "Trabzon"]
        objs = await asyncio.gather(*[client.find_province(c) for c in cities])
        district_lists = await asyncio.gather(*[client.get_districts(p.id) for p in objs])
        for p, ds in zip(objs, district_lists):
            print(f"{p.name}: {len(ds)} districts")

asyncio.run(main())
```

*Birden fazla ili paralel olarak sorgular. `AsyncTKGMClient`, `TKGMClient` ile birebir aynı arayüze sahiptir; tüm metodlar `await` ile çağrılır.*

## API Reference / API Referansı

### Base URL / Temel URL

```
https://cbsapi.tkgm.gov.tr/megsiswebapi.v3.1/api
```

### Public Endpoints — no auth required

*Herkese açık uç noktalar — kimlik doğrulama gerekmez*

| Method | Endpoint | Client method |
|--------|----------|---------------|
| `GET` | `/idariYapi/ilListe` | `get_provinces()` |
| `GET` | `/idariYapi/ilceListe/{il_id}` | `get_districts(province_id)` |
| `GET` | `/idariYapi/mahalleListe/{ilce_id}` | `get_neighborhoods(district_id)` |

### Authenticated Endpoints — e-Devlet token required

*Kimlik doğrulama gerektiren uç noktalar — e-Devlet token zorunlu*

| Method | Endpoint | Client method |
|--------|----------|---------------|
| `GET` | `/parsel/{mahalle_id}/{ada}/{parsel}` | `get_parcel(neighborhood_id, block, parcel)` |
| `GET` | `/parsel/cografi/{lat}/{lon}` | `get_parcel_by_coordinate(lat, lon)` |

### Convenience Methods / Pratik Arama Yardımcıları

| Method | Description |
|--------|-------------|
| `find_province(name)` | Case-insensitive partial name search / *Büyük/küçük harf duyarsız kısmi eşleşme* |
| `find_district(province_id, name)` | Case-insensitive partial name search / *Büyük/küçük harf duyarsız kısmi eşleşme* |
| `find_neighborhood(district_id, name)` | Case-insensitive partial name search / *Büyük/küçük harf duyarsız kısmi eşleşme* |

### Models / Modeller

```python
Province(id, name, geometry)
District(id, name, province_id, geometry)
Neighborhood(id, name, district_id, geometry)
Parcel(neighborhood_id, block, parcel, geometry, properties)

# Helpers
parcel.to_geojson()           # → GeoJSON Feature dict
parcel.geometry.centroid()    # → (lon, lat) tuple
```

### Constructor Options / Yapıcı Parametreleri

```python
TKGMClient(
    token=None,          # e-Devlet bearer token (optional for public endpoints)
    timeout=20,          # HTTP timeout in seconds
    retries=3,           # Auto-retries on 429 / 5xx
    backoff=0.5,         # Exponential backoff factor
    rate_limit_delay=0.2 # Minimum seconds between requests
)
```

*token: herkese açık uç noktalar için opsiyonel · timeout: saniye cinsinden · retries: 429/5xx'te otomatik yeniden deneme · rate_limit_delay: istekler arası minimum bekleme*

### Exception Hierarchy / Hata Sınıfları

```
TKGMError
├── TKGMHTTPError        HTTP 4xx / 5xx
├── TKGMNotFoundError    Resource does not exist
├── TKGMAuthError        Authentication required
├── TKGMRateLimitError   Too many requests (429)
└── TKGMParseError       Unexpected / non-JSON response
```

*TKGMNotFoundError: kaynak bulunamadı · TKGMAuthError: kimlik doğrulama gerekli · TKGMRateLimitError: çok fazla istek · TKGMParseError: beklenmeyen yanıt formatı*

## Examples / Örnekler

See the [`examples/`](examples/) directory:

*[`examples/`](examples/) klasörüne bakın:*

| File | Description |
|------|-------------|
| [`01_provinces.py`](examples/01_provinces.py) | List all provinces, districts, and neighborhoods / *Tüm il, ilçe ve mahalleleri listele* |
| [`02_parcel_lookup.py`](examples/02_parcel_lookup.py) | Parcel lookup by address and GPS (requires auth) / *Adres ve GPS ile parsel sorgulama (token gerekli)* |
| [`03_async.py`](examples/03_async.py) | Async parallel requests / *Asenkron paralel istekler* |

```bash
python examples/01_provinces.py
TKGM_TOKEN=eyJ... python examples/02_parcel_lookup.py
python examples/03_async.py
```

## Contributing / Katkıda Bulunma

Contributions are welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) before opening a PR.

*Katkılarınızı bekliyoruz! PR açmadan önce lütfen [CONTRIBUTING.md](CONTRIBUTING.md) dosyasını okuyun.*

```bash
git clone https://github.com/MEnsar55/tkgm-py.git
cd tkgm-py
pip install -e ".[dev]"
pytest
```

## License / Lisans

[MIT](LICENSE) © [MEnsar55](https://github.com/MEnsar55)
