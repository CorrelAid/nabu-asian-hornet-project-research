import streamlit as st
import pandas as pd
import os
from pygbif import species, occurrences as occ

SPECIES = {
    "European hornet": "Vespa crabro",
    "Asian hornet":    "Vespa velutina",
}

COLORS = {
    "European hornet": "#f5a623",
    "Asian hornet":    "#d0021b",
}

# ── Google Drive FILE_IDs ─────────────────────────────
# Заміни на свої FILE_ID після завантаження на Drive
GDRIVE_IDS = {
    "European hornet": st.secrets.get("EU_HORNET_GDRIVE_ID", ""),
    "Asian hornet":    st.secrets.get("AS_HORNET_GDRIVE_ID", ""),
}

CSV_PATHS = {
    "European hornet": "/tmp/european_hornet_DE.csv",
    "Asian hornet":    "/tmp/asian_hornet_DE.csv",
}

@st.cache_data(ttl=86400, show_spinner="Downloading data from Google Drive...")
def download_from_gdrive(label: str) -> str:
    """Download CSV from Google Drive if not cached locally."""
    file_id = GDRIVE_IDS.get(label, "")
    path = CSV_PATHS.get(label, "")

    if not file_id:
        return ""

    if os.path.exists(path):
        return path

    try:
        import gdown
        url = f"https://drive.google.com/uc?id={file_id}&export=download"
        gdown.download(url, path, quiet=False)
        st.success(f"✅ Downloaded {label} data")
        return path
    except Exception as e:
        st.warning(f"⚠️ Could not download {label} from Drive: {e}")
        return ""

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

    label = next(
        (k for k, v in SPECIES.items() if v == species_name),
        species_name
    )

    # ── Спробуємо завантажити з Google Drive (тільки для DE) ──
    if country == "DE":
        path = download_from_gdrive(label)
        if path and os.path.exists(path):
            df = pd.read_csv(path)
            total = len(df)
            df = _process_df(df, label)
            return df, total

    # ── Fallback: GBIF API ────────────────────────────────────
    key = get_species_key(species_name)
    records_per_year = max(10, limit // 25)
    all_results = []
    for year in range(2000, 2026):
        res = occ.search(
            taxonKey=key,
            country=country,
            year=year,
            limit=records_per_year,
        )
        if res["results"]:
            all_results.extend(res["results"])

    total = len(all_results)
    df = pd.DataFrame(all_results) if all_results else pd.DataFrame()
    if df.empty:
        return pd.DataFrame(), 0

    df = _process_df(df, label)
    return df, total

def _process_df(df: pd.DataFrame, label: str) -> pd.DataFrame:
    """Process and clean dataframe."""
    df["eventDate"] = pd.to_datetime(df["eventDate"], errors="coerce")

    # Використовуємо year з CSV якщо є
    if "year" not in df.columns or df["year"].isna().sum() > len(df) * 0.3:
        df["year"] = df["eventDate"].dt.year.astype("Int64")
    else:
        df["year"] = pd.to_numeric(df["year"], errors="coerce").astype("Int64")

    df["month"] = df["eventDate"].dt.month.astype("Int64")

    # GADM поля
    if "gadm" in df.columns:
        def safe_gadm(x, level):
            try:
                if isinstance(x, dict):
                    return x.get(level, {}).get("name", "")
                import ast
                d = ast.literal_eval(str(x))
                return d.get(level, {}).get("name", "")
            except Exception:
                return ""
        df["bundesland"] = df["gadm"].apply(lambda x: safe_gadm(x, "level1"))
        df["landkreis"]  = df["gadm"].apply(lambda x: safe_gadm(x, "level2"))
    else:
        df["bundesland"] = df.get("stateProvince", "")
        df["landkreis"]  = ""

    df["species_label"] = label
    df["color"]         = COLORS.get(label, "#999")

    keep = [
        "species", "species_label", "color",
        "decimalLatitude", "decimalLongitude",
        "eventDate", "year", "month",
        "stateProvince", "bundesland", "landkreis",
        "locality", "basisOfRecord", "gbifID",
    ]
    cols = [c for c in keep if c in df.columns]
    return df[cols]

@st.cache_data(ttl=3600, show_spinner="Loading both species...")
def load_both(country: str = "DE", limit: int = 300) -> pd.DataFrame:
    frames = []
    for label, name in SPECIES.items():
        df, _ = load_observations(name, country, limit)
        if not df.empty:
            frames.append(df)
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()