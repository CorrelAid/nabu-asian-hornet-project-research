import streamlit as st
import plotly.express as px
from utils.gbif_loader import load_observations, COLORS

st.set_page_config(page_title="Q2 — Distribution", page_icon="🗺️", layout="wide")
st.title("Q2 — How widespread is the European hornet in Germany?")
st.markdown("North–south gradient, geographic patterns, trade routes hypothesis.")

country = st.sidebar.selectbox("Country", ["DE", "FR", "BE", "NL"], index=0)
limit   = st.sidebar.slider("Max records", 100, 1000, 300, step=100)

df_eu, total = load_observations("Vespa crabro", country, limit)
st.metric("Total European hornet records in GBIF", f"{total:,}")

df_valid = df_eu.dropna(subset=["decimalLatitude", "decimalLongitude"])

col1, col2 = st.columns(2)

with col1:
    st.subheader("North–South gradient")
    fig = px.histogram(
        df_valid,
        x="decimalLatitude",
        nbins=30,
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
        nbins=30,
        color_discrete_sequence=[COLORS["European hornet"]],
        title="Longitude distribution",
        labels={"decimalLongitude": "Longitude (East →)"},
    )
    st.plotly_chart(fig2, use_container_width=True)

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