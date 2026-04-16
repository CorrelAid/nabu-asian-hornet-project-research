import streamlit as st
import plotly.express as px
from utils.gbif_loader import load_both, COLORS

st.set_page_config(page_title="Q1 — Displacement", page_icon="⚔️", layout="wide")

st.title("Q1 — Is the European hornet being displaced?")
st.markdown(
    "Comparing overlap zones of both species. "
    "Areas with high Asian hornet presence — do they show fewer European sightings?"
)

# ── Sidebar filters ───────────────────────────────────
# Country selection drives the GBIF query; limit controls sample size per species
country = st.sidebar.selectbox("Country", ["DE", "FR", "BE", "NL"], index=0)
limit   = st.sidebar.slider("Max records", 100, 1000, 300, step=100)

# ── Data loading ──────────────────────────────────────
# load_both() returns a combined DataFrame with a 'species_label' column
# that distinguishes European and Asian hornets across all visualizations
df = load_both(country=country, limit=limit)

# Drop rows without coordinates — required for map rendering
df_map = df.dropna(subset=["decimalLatitude", "decimalLongitude"])

# ── Overlap map ───────────────────────────────────────
# Scatter map showing co-occurrence of both species at the same geographic scale.
# Visual overlap (or absence) is the first indicator of potential displacement.
st.subheader("Overlap map")
fig = px.scatter_mapbox(
    df_map,
    lat="decimalLatitude",
    lon="decimalLongitude",
    color="species_label",
    color_discrete_map=COLORS,
    hover_data=["year", "stateProvince"],  # shown in tooltip on hover
    mapbox_style="carto-positron",
    zoom=5,
    height=500,
)
st.plotly_chart(fig, use_container_width=True)

# ── Regional breakdown ────────────────────────────────
# Aggregates sightings by Bundesland to identify regions where one species
# dominates — a potential signal of competitive exclusion
st.subheader("By region (Bundesland)")

if "stateProvince" in df.columns:

    # Pivot table: rows = Bundesland, columns = species, values = sighting count
    # fill_value=0 ensures states with zero sightings for a species are included
    pivot = (
        df.groupby(["stateProvince", "species_label"])
        .size()
        .unstack(fill_value=0)
        .reset_index()
    )
    st.dataframe(pivot, use_container_width=True)

    # Grouped bar chart for the same data — easier to compare species side by side
    # per region than reading the raw pivot table
    fig2 = px.bar(
        df.groupby(["stateProvince", "species_label"])
           .size().reset_index(name="count"),
        x="stateProvince",
        y="count",
        color="species_label",
        color_discrete_map=COLORS,
        barmode="group",  # side-by-side bars, not stacked
        title="Observations per Bundesland",
    )
    st.plotly_chart(fig2, use_container_width=True)
