"""Example: async usage — fetch multiple districts in parallel."""

import asyncio
from tkgm import AsyncTKGMClient


async def main():
    async with AsyncTKGMClient() as client:
        # Fetch all provinces
        provinces = await client.get_provinces()
        print(f"Total provinces: {len(provinces)}")

        # Fetch districts for multiple provinces in parallel
        target_provinces = ["Ankara", "İstanbul", "İzmir", "Ordu", "Trabzon"]
        province_objs = await asyncio.gather(
            *[client.find_province(name) for name in target_provinces]
        )

        district_lists = await asyncio.gather(
            *[client.get_districts(p.id) for p in province_objs]
        )

        for province, districts in zip(province_objs, district_lists):
            print(f"{province.name}: {len(districts)} districts")


asyncio.run(main())
