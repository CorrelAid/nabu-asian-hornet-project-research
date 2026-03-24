from pygbif import species, occurrences as occ
import pandas as pd
import os

os.makedirs("data", exist_ok=True)

SPECIES_MAP = {
    "European hornet": "Vespa crabro",
    "Asian hornet": "Vespa velutina",
}

MAX_PER_YEAR = 20000  # максимум записів на рік

for label, name in SPECIES_MAP.items():
    result = species.name_suggest(q=name)[0]
    key = result["key"]
    print(f"\nLoading {label}, key={key}")
    all_records = []

    for year in range(2000, 2026):
        res = occ.search(taxonKey=key, country="DE", year=year, limit=1)
        total = res["count"]

        if total == 0:
            print(f"  {year}: 0 total [skip]")
            continue

        # Пагінація через offset
        year_records = []
        offset = 0
        limit = 300

        while offset < min(total, MAX_PER_YEAR):
            res = occ.search(
                taxonKey=key,
                country="DE",
                year=year,
                limit=limit,
                offset=offset
            )
            batch = res["results"]
            if not batch:
                break
            year_records.extend(batch)
            offset += len(batch)

        all_records.extend(year_records)
        flag = "TRUNCATED" if total > MAX_PER_YEAR else "ok"
        print(f"  {year}: {total} total, loaded {len(year_records)} [{flag}]")

    df = pd.DataFrame(all_records)
    fname = f"data/{label.lower().replace(' ', '_')}_DE.csv"
    df.to_csv(fname, index=False)
    print(f"Saved {len(df)} to {fname}")

print("\nDone!")