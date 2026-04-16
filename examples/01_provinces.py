"""Example: list all provinces and find Ordu's districts."""

from tkgm import TKGMClient, TKGMNotFoundError

with TKGMClient() as client:
    # List all 81 provinces
    provinces = client.get_provinces()
    print(f"Total provinces: {len(provinces)}")
    for p in provinces[:5]:
        print(f"  {p}")

    # Find Ordu and list its districts
    ordu = client.find_province("Ordu")
    print(f"\nFound: {ordu}")

    districts = client.get_districts(ordu.id)
    print(f"Ordu districts ({len(districts)}):")
    for d in districts:
        print(f"  {d}")

    # Find Altınordu and list its neighborhoods
    altinordu = client.find_district(ordu.id, "Altınordu")
    neighborhoods = client.get_neighborhoods(altinordu.id)
    print(f"\nAltınordu neighborhoods ({len(neighborhoods)}):")
    for n in neighborhoods[:10]:
        print(f"  {n}")
