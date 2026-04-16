import streamlit as st
import pandas as pd
import os
from pygbif import species, occurrences as occ

# ── Species registry ──────────────────────────────────
# Maps human-readable labels to scientific names used in GBIF queries
SPECIES = {
    "European hornet": "Vespa crabro",
    "Asian hornet":    "Vespa velutina",
}

# Color palette for charts and maps (consistent across all pages)
COLORS = {
    "European hornet": "#f5a623",
    "Asian hornet":    "#d0021b",
}

# ── Google Drive file IDs ─────────────────────────────
# Pre-downloaded full GBIF datasets stored on Google Drive to avoid
# repeated API calls and rate limits during live demos.
# File IDs are injected via Streamlit secrets (never hardcoded).
# Replace with your own Drive file IDs after uploading the CSVs.
GDRIVE_IDS = {
    "European hornet": st.secrets.get("EU_HORNET_GDRIVE_ID", ""),
    "Asian hornet":    st.secrets.get("AS_HORNET_GDRIVE_ID", ""),
}

# Local temp paths where Drive CSVs are cached during the session
CSV_PATHS = {
    "European hornet": "/tmp/european_hornet_DE.csv",
    "Asian hornet":    "/tmp/asian_hornet_DE.csv",
}


@st.cache_data(ttl=86400, show_spinner="Downloading data from Google Drive...")
def download_from_gdrive(label: str) -> str:
    """
    Download a species CSV from Google Drive if not already cached locally.

    Uses gdown to fetch public Drive files by their file ID.
    The file is saved to /tmp and reused across reruns within 24 hours.

    Args:
        label: Species label ("European hornet" or "Asian hornet")

    Returns:
        Local file path if download succeeded, empty string otherwise.
    """
    file_id = GDRIVE_IDS.get(label, "")
    path = CSV_PATHS.get(label, "")

    # Skip if no Drive ID is configured in secrets
    if not file_id:
        return ""

    # Return cached file if already downloaded in this session
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
    """
    Resolve a scientific name to its GBIF taxon key.

    The taxon key is required for occurrence searches via pygbif.
    Result is cached for 1 hour to avoid redundant API lookups.

    Args:
        name: Scientific name (e.g. "Vespa crabro")

    Returns:
        Integer GBIF taxon key.
    """
    result = species.name_suggest(q=name)[0]
    return result["key"]


@st.cache_data(ttl=3600, show_spinner="Fetching observations...")
def load_observations(
    species_name: str,
    country: str = "DE",
    limit: int = 300,
) -> tuple[pd.DataFrame, int]:
    """
    Load occurrence records for a single species from GBIF.

    Data source priority:
      1. Google Drive CSV (only for DE) — full dataset, pre-downloaded
      2. Live GBIF API — sampled per year, used as fallback for other countries

    Args:
        species_name: Scientific name (e.g. "Vespa velutina")
        country:      ISO 3166-1 alpha-2 country code (default: "DE")
        limit:        Max total records when using live API (split across years)

    Returns:
        Tuple of (cleaned DataFrame, total record count).
        Returns (empty DataFrame, 0) if no data is available.
    """
    # Resolve scientific name back to human-readable label for downstream use
    label = next(
        (k for k, v in SPECIES.items() if v == species_name),
        species_name
    )

    # ── Primary source: Google Drive CSV (Germany only) ───
    # Full dataset with up to 20,000 records per year; preferred over API
    if country == "DE":
        path = download_from_gdrive(label)
        if path and os.path.exists(path):
            df = pd.read_csv(path)
            total = len(df)
            df = _process_df(df, label)
            return df, total

    # ── Fallback: Live GBIF API ───────────────────────────
    # Fetches a limited sample per year to stay within API rate limits.
    # records_per_year is distributed evenly across the 25-year range.
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
    """
    Clean and normalize a raw GBIF occurrence DataFrame.

    Steps performed:
      - Parse eventDate to datetime
      - Extract year and month (fallback to eventDate if column missing/sparse)
      - Parse GADM administrative levels into bundesland / landkreis columns
      - Attach species label and color for use in charts
      - Select and return only the relevant columns

    Args:
        df:    Raw DataFrame from CSV or GBIF API response
        label: Human-readable species label

    Returns:
        Cleaned DataFrame with a standardized column set.
    """
    df["eventDate"] = pd.to_datetime(df["eventDate"], errors="coerce")

    # Prefer the pre-existing year column from GBIF CSV if it's mostly populated;
    # otherwise derive it from eventDate to avoid data gaps
    if "year" not in df.columns or df["year"].isna().sum() > len(df) * 0.3:
        df["year"] = df["eventDate"].dt.year.astype("Int64")
    else:
        df["year"] = pd.to_numeric(df["year"], errors="coerce").astype("Int64")

    df["month"] = df["eventDate"].dt.month.astype("Int64")

    # ── Administrative boundaries (GADM) ─────────────────
    # GBIF API responses include a nested "gadm" dict with named levels.
    # CSVs may store it as a serialized string — ast.literal_eval handles that.
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
        # Fall back to flat stateProvince field if GADM is unavailable
        df["bundesland"] = df.get("stateProvince", "")
        df["landkreis"]  = ""

    # Attach display metadata used by charts across all pages
    df["species_label"] = label
    df["color"]         = COLORS.get(label, "#999")

    # Return only the columns needed downstream; ignore any extra GBIF fields
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
    """
    Load and combine occurrence records for both species into a single DataFrame.

    Convenience wrapper around load_observations() used by most dashboard pages.

    Args:
        country: ISO 3166-1 alpha-2 country code (default: "DE")
        limit:   Max records per species when using live API

    Returns:
        Concatenated DataFrame with a 'species_label' column for filtering.
        Returns an empty DataFrame if no data could be loaded for either species.
    """
    frames = []
    for label, name in SPECIES.items():
        df, _ = load_observations(name, country, limit)
        if not df.empty:
            frames.append(df)
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
