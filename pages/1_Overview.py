import streamlit as st
import plotly.express as px
from utils.gbif_loader import load_both, COLORS

st.set_page_config(page_title="Q1 — Displacement", page_icon="⚔️", layout="wide")
st.title("Q1 — Is the European hornet being displaced?")
st.markdown(
    "Comparing overlap zones of both species. "
    "Areas with high Asian hornet presence — do they show fewer European sightings?"
)

country = st.sidebar.selectbox("Country", ["DE", "FR", "BE", "NL"], index=0)
limit   = st.sidebar.slider("Max records", 100, 1000, 300, step=100)

df = load_both(country=country, limit=limit)
df_map = df.dropna(subset=["decimalLatitude", "decimalLongitude"])

st.subheader("Overlap map")
fig = px.scatter_mapbox(
    df_map,
    lat="decimalLatitude",
    lon="decimalLongitude",
    color="species_label",
    color_discrete_map=COLORS,
    hover_data=["year", "stateProvince"],
    mapbox_style="carto-positron",
    zoom=5, height=500,
)
st.plotly_chart(fig, use_container_width=True)

st.subheader("By region (Bundesland)")
if "stateProvince" in df.columns:
    pivot = (
        df.groupby(["stateProvince", "species_label"])
        .size()
        .unstack(fill_value=0)
        .reset_index()
    )
    st.dataframe(pivot, use_container_width=True)

    fig2 = px.bar(
        df.groupby(["stateProvince", "species_label"])
           .size().reset_index(name="count"),
        x="stateProvince", y="count",
        color="species_label",
        color_discrete_map=COLORS,
        barmode="group",
        title="Observations per Bundesland",
    )
    st.plotly_chart(fig2, use_container_width=True)