"""Example: look up a parcel by its administrative address (requires auth)."""

import os
from tkgm import TKGMClient, TKGMAuthError, TKGMNotFoundError

# Token obtained after logging in via e-Devlet at:
# https://online.tkgm.gov.tr/giris
# Then extract the Authorization: Bearer <token> from browser devtools.
TOKEN = os.getenv("TKGM_TOKEN")

if not TOKEN:
    print(
        "Set TKGM_TOKEN environment variable to your bearer token.\n"
        "Login at: https://online.tkgm.gov.tr/giris\n"
        "Then check browser devtools > Network > any /api/ request > Authorization header."
    )
    raise SystemExit(1)

with TKGMClient(token=TOKEN) as client:
    # Step 1: resolve neighborhood ID
    ordu = client.find_province("Ordu")
    altinordu = client.find_district(ordu.id, "Altınordu")
    akcatepe = client.find_neighborhood(altinordu.id, "Akçatepe")
    print(f"Neighborhood: {akcatepe}")

    # Step 2: query parcel (replace block/parcel with real values)
    try:
        parcel = client.get_parcel(
            neighborhood_id=akcatepe.id,
            block=14,    # ada numarası
            parcel=3,    # parsel numarası
        )
        print(f"Parcel: {parcel}")
        if parcel.geometry:
            lon, lat = parcel.geometry.centroid()
            print(f"Centroid: lat={lat:.6f}, lon={lon:.6f}")
        print("GeoJSON:", parcel.to_geojson())

    except TKGMNotFoundError as e:
        print(f"Parcel not found: {e}")

    # Step 3: coordinate-based lookup
    try:
        parcel = client.get_parcel_by_coordinate(lat=40.9839, lon=37.8764)
        print(f"Parcel at coordinate: {parcel}")
    except TKGMNotFoundError as e:
        print(f"No parcel at coordinate: {e}")
