import streamlit as st
import plotly.express as px
from utils.gbif_loader import load_both, load_observations, COLORS

st.set_page_config(page_title="Q5 — Urban vs Rural", page_icon="🏙️", layout="wide")

st.title("Q5 — Is the Asian hornet synanthropic?")

# Citizen science bias warning — displayed prominently before any charts.
# Urban areas are over-represented in GBIF data because more people submit
# observations there, which can falsely suggest higher population density.
# Any urban/rural comparison must account for this observer effect.
st.warning(
    "⚠️ **Bias warning:** Urban areas have more citizen science observers, "
    "which inflates detection probability regardless of actual population density."
)

# ── Sidebar filters ───────────────────────────────────
# Asian hornet (Vespa velutina) is rare in DE — switching to FR or BE
# typically yields more records for meaningful analysis
country = st.sidebar.selectbox("Country", ["DE", "FR", "BE", "NL"], index=0)
limit   = st.sidebar.slider("Max records", 100, 1000, 300, step=100)

# ── Debug panel (dev only) ────────────────────────────
# Enabled via Streamlit secrets: set DEBUG = true in .streamlit/secrets.toml.
# Useful for diagnosing empty datasets — shows raw record counts and a data
# sample before any filtering is applied
if st.secrets.get("DEBUG", False):
    with st.expander("🔍 Debug info", expanded=True):
        df_all = load_both(country=country, limit=limit)
        st.write(f"Total records loaded: {len(df_all)}")
        st.write(f"Species in data: {df_all['species_label'].unique().tolist()}")

        # Load Asian hornet separately to get the unfiltered GBIF total count
        df_as_raw, total_as = load_observations("Vespa velutina", country, limit)
        st.write(f"Asian hornet total in GBIF for {country}: {total_as}")
        st.write(f"Asian hornet records loaded: {len(df_as_raw)}")

        if not df_as_raw.empty:
            st.write("Sample:", df_as_raw.head(3))
        else:
            # Guide the developer toward a country with confirmed Asian hornet presence
            st.error(f"No Asian hornet records found for country={country}")
            st.info("Try switching to FR (France) — Asian hornet was first found there in 2004")

# ── Main content ──────────────────────────────────────
# Load combined dataset and split by species for separate analysis
df    = load_both(country=country, limit=limit)
df_as = df[df["species_label"] == "Asian hornet"]

# Record count metrics give a quick sanity check on data availability
# before rendering charts — especially useful when Asian hornet count is 0
st.metric("Asian hornet records", len(df_as))
st.metric("European hornet records",
          len(df[df["species_label"] == "European hornet"]))

# ── Regional distribution chart ───────────────────────
if df_as.empty:
    # Asian hornet is not yet established in Germany (as of 2025),
    # so empty results for DE are expected — redirect user to FR/BE
    st.warning(
        f"No Asian hornet sightings loaded for **{country}**. "
        "Try **FR** or **BE** where Asian hornet is more established."
    )
else:
    # Aggregate sightings by region and sort descending to surface hotspots first.
    # dropna=True excludes records with unknown stateProvince from the groupby
    counts = (
        df_as
        .groupby("stateProvince", dropna=True)
        .size()
        .reset_index(name="count")
        .sort_values("count", ascending=False)
    )

    if not counts.empty:
        fig = px.bar(
            counts,
            x="stateProvince",
            y="count",
            color_discrete_sequence=[COLORS["Asian hornet"]],
            title=f"Asian hornet sightings by region ({country})",
            labels={"stateProvince": "Region", "count": "Observations"},
        )
        # Rotate labels to prevent overlap for long region names
        fig.update_xaxes(tickangle=45)
        st.plotly_chart(fig, use_container_width=True)

# ── Raw data table ────────────────────────────────────
# Shows Asian hornet records when available; falls back to the full combined
# dataset so the page is never completely empty for exploratory use.
# basisOfRecord is included to help assess observation quality
st.subheader("Raw data")

if not df_as.empty:
    st.dataframe(
        df_as[["year", "stateProvince", "decimalLatitude",
               "decimalLongitude", "basisOfRecord"]].head(50),
        use_container_width=True,
    )
else:
    # Fallback: show both species so the page remains informative
    # even when no Asian hornet records are available for the selected country
    st.dataframe(
        df[["species_label", "year", "stateProvince",
            "decimalLatitude", "decimalLongitude"]].head(20),
        use_container_width=True,
    )
