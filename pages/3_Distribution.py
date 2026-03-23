import streamlit as st
import plotly.express as px
from utils.gbif_loader import load_both, load_observations, COLORS

st.set_page_config(page_title="Q5 — Urban vs Rural", page_icon="🏙️", layout="wide")
st.title("Q5 — Is the Asian hornet synanthropic?")
st.warning(
    "⚠️ **Bias warning:** Urban areas have more citizen science observers, "
    "which inflates detection probability regardless of actual population density."
)

country = st.sidebar.selectbox("Country", ["DE", "FR", "BE", "NL"], index=0)
limit   = st.sidebar.slider("Max records", 100, 1000, 300, step=100)

if st.secrets.get("DEBUG", False):
    # ── Діагностика ───────────────────────────────────────
    with st.expander("🔍 Debug info", expanded=True):
        df_all = load_both(country=country, limit=limit)
        st.write(f"Total records loaded: {len(df_all)}")
        st.write(f"Species in data: {df_all['species_label'].unique().tolist()}")

        df_as_raw, total_as = load_observations("Vespa velutina", country, limit)
        st.write(f"Asian hornet total in GBIF for {country}: {total_as}")
        st.write(f"Asian hornet records loaded: {len(df_as_raw)}")

        if not df_as_raw.empty:
            st.write("Sample:", df_as_raw.head(3))
        else:
            st.error(f"No Asian hornet records found for country={country}")
            st.info("Try switching to FR (France) — Asian hornet was first found there in 2004")

# ── Main content ──────────────────────────────────────
df = load_both(country=country, limit=limit)
df_as = df[df["species_label"] == "Asian hornet"]

st.metric("Asian hornet records", len(df_as))
st.metric("European hornet records",
          len(df[df["species_label"] == "European hornet"]))

if df_as.empty:
    st.warning(
        f"No Asian hornet sightings loaded for **{country}**. "
        "Try **FR** or **BE** where Asian hornet is more established."
    )
else:
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
            x="stateProvince", y="count",
            color_discrete_sequence=[COLORS["Asian hornet"]],
            title=f"Asian hornet sightings by region ({country})",
            labels={"stateProvince": "Region", "count": "Observations"},
        )
        fig.update_xaxes(tickangle=45)
        st.plotly_chart(fig, use_container_width=True)

st.subheader("Raw data")
if not df_as.empty:
    st.dataframe(
        df_as[["year", "stateProvince", "decimalLatitude",
               "decimalLongitude", "basisOfRecord"]].head(50),
        use_container_width=True,
    )
else:
    st.dataframe(df[["species_label", "year", "stateProvince",
                      "decimalLatitude", "decimalLongitude"]].head(20),
                 use_container_width=True)
