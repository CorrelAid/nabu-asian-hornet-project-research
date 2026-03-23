import streamlit as st
from utils.gbif_loader import load_both, SPECIES, COLORS
import plotly.express as px

st.set_page_config(
    page_title="NABU Hornet Dashboard",
    page_icon="🐝",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Sidebar ───────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🌿 NABU")
    st.title("🐝 Hornet Dashboard")
    st.markdown("**NABU × CorrelAid**")
    st.divider()

    country = st.selectbox(
        "Country", ["DE", "FR", "BE", "NL", "AT", "CH"],
        index=0
    )
    limit = st.slider(
        "Max records per species", 100, 1000, 300, step=100
    )
    year_min, year_max = st.slider(
        "Year range", 2000, 2025, (2010, 2025)
    )
    st.divider()
    st.caption("Data source: GBIF via pygbif")
    st.caption("© NABU × CorrelAid 2026")

# ── Data ─────────────────────────────────────────────
df = load_both(country=country, limit=limit)

if df.empty:
    st.error("No data loaded. Check GBIF connection.")
    st.stop()

# Year filter
if "year" in df.columns:
    df = df[df["year"].between(year_min, year_max)]

df_eu = df[df["species_label"] == "European hornet"]
df_as = df[df["species_label"] == "Asian hornet"]

# ── Header ────────────────────────────────────────────
st.title("🐝 European & Asian Hornet — NABU Dashboard")
st.markdown(
    "Interactive analysis of **Vespa crabro** (European) "
    "and **Vespa velutina** (Asian) hornet observations "
    f"in **{country}** ({year_min}–{year_max})."
)

# ── Metrics ───────────────────────────────────────────
col1, col2, col3, col4 = st.columns(4)
col1.metric("🟡 European hornet", f"{len(df_eu):,}", "sightings")
col2.metric("🔴 Asian hornet",    f"{len(df_as):,}", "sightings")
col3.metric("📅 Years", f"{year_min}–{year_max}")
col4.metric("🗺️ Total", f"{len(df):,}", "records")

st.divider()

# ── Timeline chart ────────────────────────────────────
st.subheader("📈 Observations over time")

yearly = (
    df.groupby(["year", "species_label"])
    .size()
    .reset_index(name="count")
)
fig = px.line(
    yearly,
    x="year", y="count",
    color="species_label",
    color_discrete_map=COLORS,
    markers=True,
    labels={"year": "Year", "count": "Observations",
            "species_label": "Species"},
    title=f"Annual observations in {country}",
)
st.plotly_chart(fig, use_container_width=True)

# ── Map preview ───────────────────────────────────────
st.subheader("🗺️ Observation map (preview)")

df_map = df.dropna(subset=["decimalLatitude", "decimalLongitude"])
fig_map = px.scatter_mapbox(
    df_map,
    lat="decimalLatitude",
    lon="decimalLongitude",
    color="species_label",
    color_discrete_map=COLORS,
    hover_data=["year", "stateProvince"],
    mapbox_style="carto-positron",
    zoom=5,
    height=450,
    title="Hornet sightings",
)
st.plotly_chart(fig_map, use_container_width=True)

st.caption(
    "Navigate to specific research questions using the sidebar pages."
)