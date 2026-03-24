import streamlit as st
import plotly.express as px
import pandas as pd
import requests
from utils.gbif_loader import load_both, COLORS

st.set_page_config(
    page_title="Q6 — Climate & Weather",
    page_icon="🌤️",
    layout="wide"
)
st.title("Q6 — How do weather conditions affect hornet spread?")
st.markdown(
    "Which climate zones in Germany show the highest Asian hornet presence? "
    "How does winter severity affect population spread?"
)

country = st.sidebar.selectbox("Country", ["DE", "FR", "BE", "NL"], index=0)
limit   = st.sidebar.slider("Max records", 100, 1000, 300, step=100)

df = load_both(country=country, limit=limit)

if df.empty:
    st.error("No data loaded.")
    st.stop()

# ── Latitude climate zones ────────────────────────────
st.subheader("🌡️ Climate zones by latitude")

def lat_to_climate(lat: float) -> str:
    if pd.isna(lat):
        return "Unknown"
    if lat >= 54:
        return "North (cool)"
    elif lat >= 52:
        return "North-Central"
    elif lat >= 50:
        return "Central"
    elif lat >= 48:
        return "South-Central"
    else:
        return "South (warm)"

df_valid = df.dropna(subset=["decimalLatitude"])
df_valid = df_valid.copy()
df_valid["climate_zone"] = df_valid["decimalLatitude"].apply(lat_to_climate)

col1, col2 = st.columns(2)

with col1:
    zone_counts = (
        df_valid.groupby(["climate_zone", "species_label"])
        .size()
        .reset_index(name="count")
    )
    zone_order = ["South (warm)", "South-Central", "Central",
                  "North-Central", "North (cool)"]
    fig = px.bar(
        zone_counts,
        x="climate_zone", y="count",
        color="species_label",
        color_discrete_map=COLORS,
        barmode="group",
        category_orders={"climate_zone": zone_order},
        title="Observations by climate zone",
        labels={"climate_zone": "Climate zone", "count": "Observations"},
    )
    st.plotly_chart(fig, use_container_width=True)

with col2:
    fig2 = px.scatter(
        df_valid,
        x="decimalLatitude",
        y="decimalLongitude",
        color="species_label",
        color_discrete_map=COLORS,
        title="Latitude vs Longitude distribution",
        labels={
            "decimalLatitude": "Latitude (N↑ = colder)",
            "decimalLongitude": "Longitude"
        },
        opacity=0.6,
    )
    st.plotly_chart(fig2, use_container_width=True)

# ── Seasonal spread ───────────────────────────────────
st.subheader("📅 Seasonal spread pattern")
st.caption(
    "Asian hornet spread is linked to winter survival. "
    "More sightings in spring = successful winter survival."
)

if "month" in df_valid.columns:
    df_as = df_valid[df_valid["species_label"] == "Asian hornet"]
    df_eu = df_valid[df_valid["species_label"] == "European hornet"]

    monthly_as = (
        df_as.groupby("month").size().reset_index(name="Asian hornet")
    )
    monthly_eu = (
        df_eu.groupby("month").size().reset_index(name="European hornet")
    )
    monthly = monthly_as.merge(monthly_eu, on="month", how="outer").fillna(0)

    month_names = {
        1:"Jan", 2:"Feb", 3:"Mar", 4:"Apr", 5:"May", 6:"Jun",
        7:"Jul", 8:"Aug", 9:"Sep", 10:"Oct", 11:"Nov", 12:"Dec"
    }
    monthly["month_name"] = monthly["month"].map(month_names)

    fig3 = px.line(
        monthly.melt(id_vars=["month", "month_name"],
                     value_vars=["Asian hornet", "European hornet"],
                     var_name="species_label", value_name="count"),
        x="month", y="count",
        color="species_label",
        color_discrete_map=COLORS,
        markers=True,
        title="Monthly activity — winter survival indicator",
        labels={"month": "Month", "count": "Observations"},
    )
    fig3.update_xaxes(
        tickvals=list(month_names.keys()),
        ticktext=list(month_names.values())
    )
    fig3.add_vrect(
        x0=11.5, x1=12.5,
        fillcolor="lightblue", opacity=0.3,
        annotation_text="Dec",
        annotation_position="top left"
    )
    fig3.add_vrect(
        x0=0.5, x1=2.5,
        fillcolor="lightblue", opacity=0.3,
        annotation_text="Jan-Feb (winter)",
        annotation_position="top left"
    )
    st.plotly_chart(fig3, use_container_width=True)

# ── Open-Meteo climate data ───────────────────────────
st.subheader("🌡️ Historical temperature data (Open-Meteo)")
st.caption("Average January temperature by region — proxy for winter severity")

CITIES = {
    "Hamburg (North)":       (53.55, 9.99),
    "Berlin (North-East)":   (52.52, 13.40),
    "Frankfurt (Central)":   (50.11, 8.68),
    "Stuttgart (SW)":        (48.78, 9.18),
    "München (South)":       (48.14, 11.58),
    "Freiburg (SW, warm)":   (47.99, 7.84),
}

@st.cache_data(ttl=86400)
def get_jan_temp(lat: float, lon: float) -> float:
    url = (
        f"https://archive-api.open-meteo.com/v1/archive"
        f"?latitude={lat}&longitude={lon}"
        f"&start_date=2010-01-01&end_date=2023-12-31"
        f"&daily=temperature_2m_mean"
        f"&timezone=Europe%2FBerlin"
    )
    try:
        r = requests.get(url, timeout=15)
        data = r.json()
        dates = data.get("daily", {}).get("time", [])
        temps = data.get("daily", {}).get("temperature_2m_mean", [])
        jan_temps = [
            t for d, t in zip(dates, temps)
            if d[5:7] == "01" and t is not None
        ]
        return round(sum(jan_temps) / len(jan_temps), 1) if jan_temps else None
    except Exception:
        return None

temp_data = []
for city, (lat, lon) in CITIES.items():
    temp = get_jan_temp(lat, lon)
    temp_data.append({"city": city, "avg_jan_temp": temp, "lat": lat})

temp_df = pd.DataFrame(temp_data).dropna()

if not temp_df.empty:
    fig4 = px.bar(
        temp_df.sort_values("avg_jan_temp"),
        x="city", y="avg_jan_temp",
        color="avg_jan_temp",
        color_continuous_scale="RdYlBu_r",
        title="Average January temperature by city (2010–2023)",
        labels={"city": "City", "avg_jan_temp": "Avg Jan temp (°C)"},
    )
    fig4.update_xaxes(tickangle=30)
    st.plotly_chart(fig4, use_container_width=True)
    st.caption(
        "Warmer winters (SW Germany) correlate with higher Asian hornet spread. "
        "Source: Open-Meteo ERA5 reanalysis data."
    )
