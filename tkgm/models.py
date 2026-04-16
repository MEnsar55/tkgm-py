"""Dataclass models for TKGM API responses."""
# TKGM API yanıtları için veri modelleri (dataclass).

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


# ── GeoJSON helpers ──────────────────────────────────────────────────────────
# ── GeoJSON yardımcı sınıfları ───────────────────────────────────────────────

@dataclass
class Geometry:
    type: str
    coordinates: Any  # list[list[list[float]]] for Polygon
                      # Polygon için: liste içinde liste içinde float listesi

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "Geometry":
        return cls(type=d["type"], coordinates=d["coordinates"])

    def centroid(self) -> tuple[float, float]:
        """Return (lon, lat) centroid of the first ring."""
        # İlk halkadaki koordinatların (lon, lat) ağırlık merkezini döndürür.
        ring = self.coordinates[0] if self.type == "Polygon" else self.coordinates
        lons = [pt[0] for pt in ring]
        lats = [pt[1] for pt in ring]
        return sum(lons) / len(lons), sum(lats) / len(lats)


@dataclass
class Feature:
    """A GeoJSON Feature with typed properties."""
    # Tiplendirilmiş özelliklerle bir GeoJSON Feature nesnesi.
    geometry: Geometry | None
    properties: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "Feature":
        return cls(
            geometry=Geometry.from_dict(d["geometry"]) if d.get("geometry") else None,
            properties=d.get("properties", {}),
        )


# ── Administrative models ─────────────────────────────────────────────────────
# ── İdari yapı modelleri (il / ilçe / mahalle) ───────────────────────────────

@dataclass
class Province:
    """Turkish province (il)."""
    # Türkiye ili.
    id: int
    name: str
    geometry: Geometry | None = None

    @classmethod
    def from_feature(cls, feature: dict[str, Any]) -> "Province":
        props = feature.get("properties", {})
        geo = feature.get("geometry")
        return cls(
            id=props["id"],
            name=props["text"],
            geometry=Geometry.from_dict(geo) if geo else None,
        )

    def __repr__(self) -> str:
        return f"Province(id={self.id}, name={self.name!r})"


@dataclass
class District:
    """Turkish district (ilçe)."""
    # Türkiye ilçesi.
    id: int
    name: str
    province_id: int | None = None
    geometry: Geometry | None = None

    @classmethod
    def from_feature(cls, feature: dict[str, Any], province_id: int | None = None) -> "District":
        props = feature.get("properties", {})
        geo = feature.get("geometry")
        return cls(
            id=props["id"],
            name=props["text"],
            province_id=province_id,
            geometry=Geometry.from_dict(geo) if geo else None,
        )

    def __repr__(self) -> str:
        return f"District(id={self.id}, name={self.name!r})"


@dataclass
class Neighborhood:
    """Turkish neighborhood / village (mahalle / köy)."""
    # Türkiye mahallesi veya köyü.
    id: int
    name: str
    district_id: int | None = None
    geometry: Geometry | None = None

    @classmethod
    def from_feature(cls, feature: dict[str, Any], district_id: int | None = None) -> "Neighborhood":
        props = feature.get("properties", {})
        geo = feature.get("geometry")
        return cls(
            id=props["id"],
            name=props["text"],
            district_id=district_id,
            geometry=Geometry.from_dict(geo) if geo else None,
        )

    def __repr__(self) -> str:
        return f"Neighborhood(id={self.id}, name={self.name!r})"


# ── Parcel model ──────────────────────────────────────────────────────────────
# ── Parsel modeli ─────────────────────────────────────────────────────────────

@dataclass
class Parcel:
    """A cadastral parcel (tapu parseli)."""
    # Tapu parseli (kadastro birimi).
    neighborhood_id: int
    block: int           # ada
    parcel: int          # parsel
    geometry: Geometry | None = None
    properties: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_response(
        cls,
        data: dict[str, Any],
        neighborhood_id: int,
        block: int,
        parcel: int,
    ) -> "Parcel":
        # The API may return a FeatureCollection or a Feature
        # API yanıtı FeatureCollection veya tek bir Feature olabilir
        if data.get("features"):
            feature = data["features"][0]
        elif data.get("type") == "Feature":
            feature = data
        else:
            feature = {}

        geo = feature.get("geometry")
        props = feature.get("properties", {})
        return cls(
            neighborhood_id=neighborhood_id,
            block=block,
            parcel=parcel,
            geometry=Geometry.from_dict(geo) if geo else None,
            properties=props,
        )

    def to_geojson(self) -> dict[str, Any]:
        """Return a GeoJSON Feature dict."""
        # Parseli GeoJSON Feature sözlüğü olarak döndürür.
        return {
            "type": "Feature",
            "geometry": {
                "type": self.geometry.type,
                "coordinates": self.geometry.coordinates,
            } if self.geometry else None,
            "properties": {
                **self.properties,
                "neighborhood_id": self.neighborhood_id,
                "block": self.block,
                "parcel": self.parcel,
            },
        }

    def __repr__(self) -> str:
        return (
            f"Parcel(neighborhood_id={self.neighborhood_id}, "
            f"block={self.block}, parcel={self.parcel})"
        )
