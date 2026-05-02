# tkgm-py

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white" alt="Python 3.10+">
  <img src="https://img.shields.io/badge/license-MIT-green" alt="License: MIT">
  <img src="https://img.shields.io/badge/sync-requests-orange" alt="sync (requests)">
  <img src="https://img.shields.io/badge/async-httpx-blueviolet" alt="async (httpx)">
  <img src="https://img.shields.io/badge/version-1.0.0-informational" alt="version 1.0.0">
  <img src="https://github.com/MEnsar55/tkgm-py/actions/workflows/ci.yml/badge.svg" alt="CI">
</p>

<p align="center">
  <b>Türkiye Tapu ve Kadastro Genel Müdürlüğü (TKGM) için resmi olmayan Python istemcisi.</b><br>
  Herhangi bir GPS koordinatından <b>token gerekmeden</b> gerçek kadastro parsel verisi çeker;
  81 il, 973 ilçe ve tüm mahallelerin idari yapısını sorgular.<br><br>
  <em>Unofficial Python client for Turkey's land-registry (TKGM) API. Looks up real cadastral
  parcels from any GPS coordinate <b>without authentication</b>, and resolves the full
  province / district / neighborhood hierarchy.</em>
</p>

<p align="center">
  <a href="#%C3%B6zellikler">Özellikler</a> ·
  <a href="#kurulum">Kurulum</a> ·
  <a href="#h%C4%B1zl%C4%B1-ba%C5%9Flang%C4%B1%C3%A7">Hızlı Başlangıç</a> ·
  <a href="#api">API</a> ·
  <a href="#ke%C5%9Fif">Keşif</a> ·
  <a href="#cli">CLI</a> ·
  <a href="#lisans">Lisans</a>
</p>

---

## Özellikler

- **Token-free koordinat sorgusu** — `lat,lon` → gerçek parsel (ada/parsel/nitelik/alan)
- **Tam idari yapı** — il (81) → ilçe (973) → mahalle/köy
- **Senkron + asenkron** — `TKGMClient` (requests) ve `AsyncTKGMClient` (httpx)
- **Tipli modeller** — `Province`, `District`, `Neighborhood`, `Parcel`, `Geometry` dataclass'ları
- **GeoJSON dönüşümü** — `parcel.to_geojson()` doğrudan haritaya basılabilir
- **Akıllı arama** — `find_province("Ankara")` büyük/küçük harf duyarsız, kısmi eşleşme
- **Otomatik retry** — 429/5xx için exponential backoff (`urllib3.Retry`)
- **Rate limit koruması** — istemci içinde minimum aralık (default 0.2s)
- **Önbellek** — il listesi `lru_cache` ile bir kez çekilir
- **Açıklayıcı hatalar** — `TKGMNotFoundError`, `TKGMRateLimitError`, `TKGMHTTPError`, `TKGMParseError`
- **Tip ipuçları** — tüm public API tam tiplenmiş
- **Bağlam yöneticisi** — `with TKGMClient() as c:` veya `async with AsyncTKGMClient() as c:`

---

## Kurulum

```bash
pip install -e git+https://github.com/MEnsar55/tkgm-py.git#egg=tkgm-py
```

veya yerel klon:

```bash
git clone https://github.com/MEnsar55/tkgm-py.git
cd tkgm-py
pip install -e .
```

**Gereksinimler:** Python ≥ 3.10 · `requests` · `httpx` · `urllib3`

---

## Hızlı Başlangıç

### Koordinattan parsel (token gerekmez)

```python
from tkgm import TKGMClient

with TKGMClient() as client:
    parcel = client.get_parcel_by_coordinate(lat=40.9839, lon=37.8764)

    print(parcel.properties)
    # {'ilAd': 'Ordu', 'ilceAd': 'Altınordu', 'mahalleAd': 'Selimiye',
    #  'adaNo': '322', 'parselNo': '31', 'nitelik': 'Trafo Yeri',
    #  'alan': '52,52', 'ozet': 'Selimiye-322/31', ...}

    lon, lat = parcel.geometry.centroid()
    print(f"Merkez: lat={lat:.6f}, lon={lon:.6f}")

    print(parcel.to_geojson())   # GeoJSON Feature
```

### İdari yapı

```python
from tkgm import TKGMClient

with TKGMClient() as client:
    provinces = client.get_provinces()                 # 81 il
    ankara    = client.find_province("Ankara")
    cankaya   = client.find_district(ankara.id, "Çankaya")
    mahalle   = client.find_neighborhood(cankaya.id, "Kızılay")

    print(ankara, cankaya, mahalle)
    # Province(id=6, name='ANKARA') District(id=406, name='ÇANKAYA') Neighborhood(id=42893, name='KIZILAY')
```

### Bir ilçedeki mahalleleri sırala

`get_neighborhoods()` `list[Neighborhood]` döndürür; sıralamayı Python tarafında yaparsın.

```python
import locale
from tkgm import TKGMClient

with TKGMClient() as client:
    ankara  = client.find_province("Ankara")
    cankaya = client.find_district(ankara.id, "Çankaya")
    mahalleler = client.get_neighborhoods(cankaya.id)

    # Türkçe alfabetik sıralama (büyük/küçük harf duyarsız)
    locale.setlocale(locale.LC_COLLATE, "tr_TR.UTF-8")  # Windows: "Turkish_Turkey.1254"
    mahalleler.sort(key=lambda m: locale.strxfrm(m.name))

    for m in mahalleler:
        print(f"{m.id:>6}  {m.name}")
```

Diğer sıralama seçenekleri:

```python
sorted(mahalleler, key=lambda m: m.name.lower())   # basit alfabetik
sorted(mahalleler, key=lambda m: m.id)             # ID'ye göre
sorted(                                            # bir merkeze yakınlığa göre
    mahalleler,
    key=lambda m: (m.geometry.centroid()[1] - 39.92) ** 2
                + (m.geometry.centroid()[0] - 32.85) ** 2
    if m.geometry else float("inf"),
)
```

### Asenkron (httpx)

```python
import asyncio
from tkgm import AsyncTKGMClient

async def main():
    async with AsyncTKGMClient() as client:
        # Birden fazla şehri paralel sorgula
        cities = ["Ankara", "İstanbul", "İzmir", "Trabzon", "Ordu"]
        provinces = await asyncio.gather(*[client.find_province(c) for c in cities])
        for p in provinces:
            print(p)

        # Koordinat sorgusu
        parcel = await client.get_parcel_by_coordinate(40.9839, 37.8764)
        print(parcel.properties["ozet"])

asyncio.run(main())
```

---

## API

### Base URL

```
https://cbsapi.tkgm.gov.tr/megsiswebapi.v3.1/api
```

### Uç noktalar

| HTTP Endpoint | İstemci metodu | Auth |
|---|---|---|
| `GET /idariYapi/ilListe` | `get_provinces()` | — |
| `GET /idariYapi/ilceListe/{il_id}` | `get_districts(province_id)` | — |
| `GET /idariYapi/mahalleListe/{ilce_id}` | `get_neighborhoods(district_id)` | — |
| `GET /parsel/{lat}/{lon}/` | `get_parcel_by_coordinate(lat, lon)` | — |
| `GET /parsel/{mahalle_id}/{ada}/{parsel}` | `get_parcel(neighborhood_id, block, parcel)` | e-Devlet |

> Yollar, nehirler ve bazı kamu alanları TKGM'de ayrı bir parsel olarak kayıtlı değildir; bu
> koordinatlarda `TKGMNotFoundError` fırlatılır. Bu, kütüphane hatası değil, TKGM verisinin
> eksikliğidir.

### `TKGMClient` / `AsyncTKGMClient`

```python
TKGMClient(
    token: str | None = None,    # yalnızca ada/parsel ID sorgusu için (e-Devlet bearer)
    timeout: int = 20,
    retries: int = 3,
    backoff: float = 0.5,
    rate_limit_delay: float = 0.2,
)

AsyncTKGMClient(
    token: str | None = None,
    timeout: float = 20.0,
    rate_limit_delay: float = 0.2,
)
```

**Metodlar (her iki istemcide de aynı imza, async sürümü `await` gerektirir):**

| Metod | Döndürür |
|---|---|
| `get_provinces()` | `list[Province]` (önbelleğe alınır) |
| `get_districts(province_id)` | `list[District]` |
| `get_neighborhoods(district_id)` | `list[Neighborhood]` |
| `find_province(name)` | `Province` (kısmi eşleşme, case-insensitive) |
| `find_district(province_id, name)` | `District` |
| `find_neighborhood(district_id, name)` | `Neighborhood` |
| `get_parcel_by_coordinate(lat, lon)` | `Parcel` |
| `get_parcel(neighborhood_id, block, parcel)` | `Parcel` (e-Devlet token'ı gerektirir) |
| `close()` | `None` |

### Modeller

```python
@dataclass
class Geometry:
    type: str                 # "Polygon", "MultiPolygon", ...
    coordinates: Any
    def centroid() -> tuple[float, float]   # (lon, lat)

@dataclass
class Province:        id: int; name: str; geometry: Geometry | None
@dataclass
class District:        id: int; name: str; province_id: int | None; geometry: Geometry | None
@dataclass
class Neighborhood:    id: int; name: str; district_id: int | None; geometry: Geometry | None

@dataclass
class Parcel:
    neighborhood_id: int
    block: int                # ada
    parcel: int               # parsel
    geometry: Geometry | None
    properties: dict[str, Any]
    def to_geojson() -> dict
```

### Parsel `properties` alanları

Koordinat sorgusundan dönen tipik alanlar:

| Alan | Açıklama |
|---|---|
| `ilAd` | İl adı |
| `ilceAd` | İlçe adı |
| `mahalleAd` | Mahalle / köy adı |
| `mahalleId` | Mahalle ID |
| `adaNo` | Ada numarası |
| `parselNo` | Parsel numarası |
| `nitelik` | Arazi niteliği (Tarla, Arsa, Bina, Trafo Yeri, ...) |
| `alan` | Yüzölçümü (m²) |
| `pafta` | Pafta numarası |
| `ozet` | "Mahalle-Ada/Parsel" özet metni |

### Hata sınıfları

```
TKGMError                       # taban sınıf
├── TKGMHTTPError               # HTTP 4xx/5xx (status_code attribute)
├── TKGMNotFoundError           # parsel/il/ilçe/mahalle bulunamadı
├── TKGMRateLimitError          # HTTP 429
├── TKGMAuthError               # ada/parsel ID için token gerekli
└── TKGMParseError              # geçersiz JSON yanıt
```

---

## CLI

`examples/` klasöründe çalıştırılabilir örnekler:

```bash
python examples/01_provinces.py        # 81 ili listeler
python examples/02_parcel_lookup.py    # ada/parsel ID sorgusu (TKGM_TOKEN env gerekir)
python examples/03_async.py            # paralel asenkron sorgular
```

---

## Keşif

`parselsorgu.tkgm.gov.tr`'nin minified JavaScript bundle'ı (`constants.min.js` ve XHR trafiği)
analiz edilerek aşağıdakiler tespit edildi:

- **Base URL:** `https://cbsapi.tkgm.gov.tr/megsiswebapi.v3.1/api`
- **Token-free uç nokta:** `GET /parsel/{lat}/{lon}/`
- **Gerekli istek başlıkları:** `Referer: https://parselsorgu.tkgm.gov.tr/` ve `Origin: https://parselsorgu.tkgm.gov.tr` — bu başlıklar olmadan API 403 döner. İstemci bu başlıkları otomatik gönderir.

> *Discovered via reverse engineering of the public TKGM web client. The Referer / Origin
> headers are mandatory; the library injects them automatically.*

---

## Geliştirme

```bash
git clone https://github.com/MEnsar55/tkgm-py.git
cd tkgm-py
pip install -e ".[dev]"
pytest
```

Katkı kuralları için [CONTRIBUTING.md](CONTRIBUTING.md), sürüm notları için [CHANGELOG.md](CHANGELOG.md).

---

## Yasal Uyarı

Bu proje **resmi değildir** ve TKGM ile bağlantısı yoktur. Tüm veriler TKGM'nin herkese açık
web istemcisinden elde edilen aynı uç noktalardan çekilir. Telif hakları ve veri kullanım
şartları için [TKGM Parsel Sorgulama](https://parselsorgu.tkgm.gov.tr/) sitesine bakın.

---

## Lisans

[MIT](LICENSE) © [MEnsar55](https://github.com/MEnsar55)
