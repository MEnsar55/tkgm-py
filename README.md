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
  <br>
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
> **İlham kaynağı:** [burakaktna/tkgmservice](https://github.com/burakaktna/tkgmservice) (PHP) —
> async desteği, tip güvenliği, önbellekleme ve yeniden deneme mekanizmasıyla sıfırdan Python'a yeniden yazıldı.

## Features / Özellikler

| Feature / Özellik | Detail / Detay |
|---|---|
| **Sync client / Senkron istemci** | `TKGMClient` — powered by `requests` |
| **Async client / Asenkron istemci** | `AsyncTKGMClient` — powered by `httpx` |
| **Type safety / Tip güvenliği** | Full type hints + dataclass models (`Province`, `District`, `Neighborhood`, `Parcel`) |
| **Caching / Önbellekleme** | LRU cache for province / district / neighborhood lists |
| **Retries / Yeniden deneme** | Automatic exponential backoff on transient errors (429, 5xx) |
| **Rate limiting / İstek sınırlama** | Configurable minimum delay between requests |
| **GeoJSON** | `Parcel.to_geojson()` and `Geometry.centroid()` helpers |
| **Bilingual docs / İkidilli dokümantasyon** | Every docstring and comment is in English + Turkish |

## Installation / Kurulum

```bash
git clone https://github.com/MEnsar55/tkgm-py.git
cd tkgm-py
pip install -e .
```

**Requirements / Gereksinimler:** Python ≥ 3.10, `requests`, `httpx`, `urllib3`

## Quick Start / Hızlı Başlangıç

```python
from tkgm import TKGMClient

with TKGMClient() as client:
    # List all 81 provinces / Tüm 81 ili listele
    provinces = client.get_provinces()
    print(f"Total provinces: {len(provinces)}")   # 81

    # Find a province by name (case-insensitive, partial match)
    # İsme göre il bul (büyük/küçük harf duyarsız, kısmi eşleşme)
    ordu = client.find_province("Ordu")
    print(ordu)   # Province(id=52, name='ORDU')

    # Get districts / İlçeleri getir
    districts = client.get_districts(ordu.id)
    altinordu = client.find_district(ordu.id, "Altınordu")

    # Get neighborhoods / Mahalleleri getir
    neighborhoods = client.get_neighborhoods(altinordu.id)
    akcatepe = client.find_neighborhood(altinordu.id, "Akçatepe")
    print(akcatepe)   # Neighborhood(id=..., name='AKÇATEPE')
```

## Authenticated Endpoints / Kimlik Doğrulama Gerektiren Uç Noktalar

Parcel lookup requires an **e-Devlet bearer token**.

Parsel sorguları **e-Devlet bearer token** gerektirir.

### How to get a token / Token nasıl alınır

1. Go to **[https://parselsorgu.tkgm.gov.tr](https://parselsorgu.tkgm.gov.tr)**
   — **[https://parselsorgu.tkgm.gov.tr](https://parselsorgu.tkgm.gov.tr)** adresine git

2. Click **Giriş Yap** in the top right → log in with your **e-Devlet** credentials
   — Sağ üstten **Giriş Yap**'a tıkla → **e-Devlet** kimlik bilgilerinle giriş yap

3. Search for any parcel to trigger API calls
   — Herhangi bir parsel sorgula (API çağrısı tetiklemek için)

4. Open browser **DevTools → Network** tab → click any `/api/` request → copy the `Authorization: Bearer <token>` header value
   — Tarayıcıda **F12 → Network** sekmesi → herhangi bir `/api/` isteğine tıkla → `Authorization: Bearer <token>` başlık değerini kopyala

> **Note / Not:** Visiting `online.tkgm.gov.tr/giris` directly will fail with "Gerekli parametreler bulunamadı".
> Always start from `parselsorgu.tkgm.gov.tr`.
>
> `online.tkgm.gov.tr/giris` adresine doğrudan gidildiğinde "Gerekli parametreler bulunamadı" hatası alınır.
> Her zaman `parselsorgu.tkgm.gov.tr` üzerinden başlayın.

```python
import os
from tkgm import TKGMClient

with TKGMClient(token=os.environ["TKGM_TOKEN"]) as client:
    ordu = client.find_province("Ordu")
    altinordu = client.find_district(ordu.id, "Altınordu")
    akcatepe = client.find_neighborhood(altinordu.id, "Akçatepe")

    # Look up by ada + parsel number / Ada + parsel numarasıyla sorgula
    parcel = client.get_parcel(
        neighborhood_id=akcatepe.id,
        block=14,    # ada numarası
        parcel=3,    # parsel numarası
    )
    lon, lat = parcel.geometry.centroid()
    print(f"Centroid: lat={lat:.6f}, lon={lon:.6f}")
    print(parcel.to_geojson())   # GeoJSON Feature dict

    # Look up by GPS coordinate / GPS koordinatıyla sorgula
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

        # Fetch multiple provinces in parallel / Birden fazla ili paralel olarak sorgula
        cities = ["Ankara", "İstanbul", "İzmir", "Trabzon"]
        objs = await asyncio.gather(*[client.find_province(c) for c in cities])
        district_lists = await asyncio.gather(*[client.get_districts(p.id) for p in objs])
        for p, ds in zip(objs, district_lists):
            print(f"{p.name}: {len(ds)} districts")

asyncio.run(main())
```

## API Reference / API Referansı

### Base URL / Temel URL

```
https://cbsapi.tkgm.gov.tr/megsiswebapi.v3.1/api
```

### Public Endpoints — no auth required / Herkese açık uç noktalar — kimlik doğrulama gerekmez

| Method | Endpoint | Client method |
|--------|----------|---------------|
| `GET` | `/idariYapi/ilListe` | `get_provinces()` |
| `GET` | `/idariYapi/ilceListe/{il_id}` | `get_districts(province_id)` |
| `GET` | `/idariYapi/mahalleListe/{ilce_id}` | `get_neighborhoods(district_id)` |

### Authenticated Endpoints — e-Devlet token required / Kimlik doğrulama gerektiren uç noktalar

| Method | Endpoint | Client method |
|--------|----------|---------------|
| `GET` | `/parsel/{mahalle_id}/{ada}/{parsel}` | `get_parcel(neighborhood_id, block, parcel)` |
| `GET` | `/parsel/cografi/{lat}/{lon}` | `get_parcel_by_coordinate(lat, lon)` |

### Convenience Methods / Pratik Arama Yardımcıları

| Method | Description / Açıklama |
|--------|------------------------|
| `find_province(name)` | Case-insensitive partial name search / Büyük/küçük harf duyarsız kısmi eşleşme |
| `find_district(province_id, name)` | Case-insensitive partial name search / Büyük/küçük harf duyarsız kısmi eşleşme |
| `find_neighborhood(district_id, name)` | Case-insensitive partial name search / Büyük/küçük harf duyarsız kısmi eşleşme |

### Models / Modeller

```python
Province(id, name, geometry)
District(id, name, province_id, geometry)
Neighborhood(id, name, district_id, geometry)
Parcel(neighborhood_id, block, parcel, geometry, properties)

# Helpers / Yardımcılar
parcel.to_geojson()           # → GeoJSON Feature dict
parcel.geometry.centroid()    # → (lon, lat) tuple
```

### Constructor Options / Yapıcı Parametreleri

```python
TKGMClient(
    token=None,          # e-Devlet bearer token (optional for public endpoints / herkese açık uç noktalar için opsiyonel)
    timeout=20,          # HTTP timeout in seconds / Saniye cinsinden zaman aşımı
    retries=3,           # Auto-retries on 429 / 5xx / Otomatik yeniden deneme sayısı
    backoff=0.5,         # Exponential backoff factor / Üstel bekleme çarpanı
    rate_limit_delay=0.2 # Minimum seconds between requests / İstekler arası minimum bekleme (saniye)
)
```

### Exception Hierarchy / Hata Sınıfları

```
TKGMError
├── TKGMHTTPError        HTTP 4xx / 5xx
├── TKGMNotFoundError    Resource does not exist / Kaynak bulunamadı
├── TKGMAuthError        Authentication required / Kimlik doğrulama gerekli
├── TKGMRateLimitError   Too many requests (429) / Çok fazla istek
└── TKGMParseError       Unexpected / non-JSON response / Beklenmeyen yanıt formatı
```

## Examples / Örnekler

See the [`examples/`](examples/) directory:

[`examples/`](examples/) klasörüne bakın:

| File / Dosya | Description / Açıklama |
|------|-------------|
| [`01_provinces.py`](examples/01_provinces.py) | List all provinces, districts, and neighborhoods / Tüm il, ilçe ve mahalleleri listele |
| [`02_parcel_lookup.py`](examples/02_parcel_lookup.py) | Parcel lookup by address and GPS (requires auth) / Adres ve GPS ile parsel sorgulama (token gerekli) |
| [`03_async.py`](examples/03_async.py) | Async parallel requests / Asenkron paralel istekler |

```bash
python examples/01_provinces.py
TKGM_TOKEN=eyJ... python examples/02_parcel_lookup.py
python examples/03_async.py
```

## Contributing / Katkıda Bulunma

Contributions are welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) before opening a PR.

Katkılarınızı bekliyoruz! PR açmadan önce lütfen [CONTRIBUTING.md](CONTRIBUTING.md) dosyasını okuyun.

```bash
git clone https://github.com/MEnsar55/tkgm-py.git
cd tkgm-py
pip install -e ".[dev]"
pytest
```

## License / Lisans

[MIT](LICENSE) © [MEnsar55](https://github.com/MEnsar55)
