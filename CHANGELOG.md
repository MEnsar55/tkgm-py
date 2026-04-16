# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [1.0.0] - 2025-04-16

### Added
- `TKGMClient` — synchronous client via `requests`
- `AsyncTKGMClient` — async client via `httpx`
- Dataclass models: `Province`, `District`, `Neighborhood`, `Parcel`, `Geometry`
- Exception hierarchy: `TKGMError`, `TKGMHTTPError`, `TKGMNotFoundError`, `TKGMAuthError`, `TKGMRateLimitError`, `TKGMParseError`
- LRU caching for province lists
- Automatic retry with exponential backoff (urllib3 `Retry`)
- Rate limiting between consecutive requests
- `Parcel.to_geojson()` — GeoJSON Feature export
- `Geometry.centroid()` — (lon, lat) centroid calculation
- Convenience finders: `find_province`, `find_district`, `find_neighborhood`
- Bilingual comments (English + Turkish) across all source files
- Examples: provinces, parcel lookup, async parallel requests
- GitHub Actions CI workflow
