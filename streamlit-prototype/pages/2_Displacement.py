import streamlit as st
import plotly.express as px
from utils.gbif_loader import load_observations, COLORS

st.set_page_config(page_title="Q2 — Distribution", page_icon="🗺️", layout="wide")

st.title("Q2 — How widespread is the European hornet in Germany?")
st.markdown("North–south gradient, geographic patterns, trade routes hypothesis.")

# ── Sidebar filters ───────────────────────────────────
# Country and limit are passed directly to load_observations();
# changing country switches between Google Drive cache (DE) and live API (others)
country = st.sidebar.selectbox("Country", ["DE", "FR", "BE", "NL"], index=0)
limit   = st.sidebar.slider("Max records", 100, 1000, 300, step=100)

# ── Data loading ──────────────────────────────────────
# Load European hornet only — this page focuses on Vespa crabro distribution.
# total reflects the full GBIF record count (before any limit is applied),
# used as a data coverage indicator in the metric below
df_eu, total = load_observations("Vespa crabro", country, limit)

st.metric("Total European hornet records in GBIF", f"{total:,}")

# Drop records missing coordinates — required for all spatial visualizations
df_valid = df_eu.dropna(subset=["decimalLatitude", "decimalLongitude"])

# ── Gradient histograms ───────────────────────────────
# Side-by-side histograms reveal whether sightings cluster in certain
# latitudinal or longitudinal bands — key for detecting the north–south
# gradient and testing the trade routes (east–west corridors) hypothesis
col1, col2 = st.columns(2)

with col1:
    st.subheader("North–South gradient")
    fig = px.histogram(
        df_valid,
        x="decimalLatitude",
        nbins=30,           # 30 bins gives sufficient resolution across ~10° range
        color_discrete_sequence=[COLORS["European hornet"]],
        title="Latitude distribution",
        labels={"decimalLatitude": "Latitude (North ↑)"},
    )
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.subheader("East–West gradient")
    fig2 = px.histogram(
        df_valid,
        x="decimalLongitude",
        nbins=30,           # same bin count for visual consistency with latitude plot
        color_discrete_sequence=[COLORS["European hornet"]],
        title="Longitude distribution",
        labels={"decimalLongitude": "Longitude (East →)"},
    )
    st.plotly_chart(fig2, use_container_width=True)

# ── Density heatmap ───────────────────────────────────
# Kernel density estimation on the map surface highlights hotspots
# and sparse regions more clearly than individual scatter points.
# radius=15 controls the blur kernel size in pixels at the given zoom level;
# YlOrRd scale (yellow → red) visually encodes increasing density
st.subheader("Density map")
fig3 = px.density_mapbox(
    df_valid,
    lat="decimalLatitude",
    lon="decimalLongitude",
    radius=15,
    mapbox_style="carto-positron",
    zoom=5,
    height=500,
    color_continuous_scale="YlOrRd",
    title="European hornet density heatmap",
)
st.plotly_chart(fig3, use_container_width=True)
