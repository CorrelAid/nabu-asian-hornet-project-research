import streamlit as st
import pandas as pd
from pygbif import species, occurrences as occ

SPECIES = {
    "European hornet": "Vespa crabro",
    "Asian hornet":    "Vespa velutina",
}

COLORS = {
    "European hornet": "#f5a623",
    "Asian hornet":    "#d0021b",
}

@st.cache_data(ttl=3600, show_spinner="Loading GBIF data...")
def get_species_key(name: str) -> int:
    result = species.name_suggest(q=name)[0]
    return result["key"]

@st.cache_data(ttl=3600, show_spinner="Fetching observations...")
def load_observations(
    species_name: str,
    country: str = "DE",
    limit: int = 300,
) -> tuple[pd.DataFrame, int]:
    key = get_species_key(species_name)

    # Завантажуємо по 50 записів на рік для рівномірного покриття
    records_per_year = max(10, limit // 25)
    years = range(2000, 2026)
    all_results = []

    for year in years:
        res = occ.search(
            taxonKey=key,
            country=country,
            year=year,
            limit=records_per_year,
        )
        if res["results"]:
            all_results.extend(res["results"])

    total_res = occ.search(taxonKey=key, country=country, limit=1)
    total = total_res["count"]

    if not all_results:
        return pd.DataFrame(), total

    df = pd.DataFrame(all_results)
    df["eventDate"] = pd.to_datetime(df["eventDate"], errors="coerce")
    df["year"] = df["eventDate"].dt.year
    df["year"] = pd.to_numeric(df["year"], errors="coerce").astype("Int64")

    label = next(
        (k for k, v in SPECIES.items() if v == species_name),
        species_name
    )
    df["species_label"] = label
    df["color"] = COLORS.get(label, "#999")

    keep = [
        "species", "species_label", "color",
        "decimalLatitude", "decimalLongitude",
        "eventDate", "year",
        "stateProvince", "basisOfRecord",
        "gbifID",
    ]
    cols = [c for c in keep if c in df.columns]
    return df[cols], total

@st.cache_data(ttl=3600, show_spinner="Loading both species...")
def load_both(country: str = "DE", limit: int = 300) -> pd.DataFrame:
    frames = []
    for label, name in SPECIES.items():
        df, _ = load_observations(name, country, limit)
        if not df.empty:
            frames.append(df)
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
