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

# ── Sidebar filters ───────────────────────────────────
country = st.sidebar.selectbox("Country", ["DE", "FR", "BE", "NL"], index=0)
limit   = st.sidebar.slider("Max records", 100, 1000, 300, step=100)

# ── Data loading ──────────────────────────────────────
df = load_both(country=country, limit=limit)

if df.empty:
    st.error("No data loaded.")
    st.stop()

# ── Latitude-based climate zone classification ────────
# Germany spans roughly 47°N–55°N, covering meaningfully different
# thermal regimes. We use latitude thresholds as a simple proxy for
# climate zone — no external climate dataset required.
# Thresholds are approximate and based on general climatological zones
# for Central Europe, not official DWD or Köppen boundaries.
st.subheader("🌡️ Climate zones by latitude")

def lat_to_climate(lat: float) -> str:
    """
    Map a decimal latitude value to a descriptive climate zone label.

    Zones are defined by 2° latitude bands covering Germany (47°–55°N).
    Returns "Unknown" for null values to allow safe downstream filtering.
    """
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

# Drop records without latitude — copy() prevents SettingWithCopyWarning
# when assigning the new climate_zone column
df_valid = df.dropna(subset=["decimalLatitude"])
df_valid = df_valid.copy()
df_valid["climate_zone"] = df_valid["decimalLatitude"].apply(lat_to_climate)

col1, col2 = st.columns(2)

with col1:
    # Grouped bar chart sorted south-to-north (warm → cool) so the
    # x-axis reads as a geographic gradient from bottom to top of Germany.
    # category_orders enforces this custom sort regardless of data order.
    zone_counts = (
        df_valid.groupby(["climate_zone", "species_label"])
        .size()
        .reset_index(name="count")
    )
    zone_order = ["South (warm)", "South-Central", "Central",
                  "North-Central", "North (cool)"]
    fig = px.bar(
        zone_counts,
        x="climate_zone",
        y="count",
        color="species_label",
        color_discrete_map=COLORS,
        barmode="group",
        category_orders={"climate_zone": zone_order},  # south → north gradient
        title="Observations by climate zone",
        labels={"climate_zone": "Climate zone", "count": "Observations"},
    )
    st.plotly_chart(fig, use_container_width=True)

with col2:
    # Raw lat/lon scatter — complements the zone bar chart by showing
    # the continuous spatial distribution without discretisation into zones.
    # opacity=0.6 reduces overplotting where many records share similar coordinates.
    fig2 = px.scatter(
        df_valid,
        x="decimalLatitude",
        y="decimalLongitude",
        color="species_label",
        color_discrete_map=COLORS,
        title="Latitude vs Longitude distribution",
        labels={
            "decimalLatitude":  "Latitude (N↑ = colder)",
            "decimalLongitude": "Longitude"
        },
        opacity=0.6,
    )
    st.plotly_chart(fig2, use_container_width=True)

# ── Seasonal spread pattern ───────────────────────────
# Spring sightings (Mar–May) of Asian hornet are ecologically significant:
# they indicate that queens successfully overwintered and founded new colonies.
# A rising spring count year-over-year signals range expansion.
st.subheader("📅 Seasonal spread pattern")
st.caption(
    "Asian hornet spread is linked to winter survival. "
    "More sightings in spring = successful winter survival."
)

if "month" in df_valid.columns:
    df_as = df_valid[df_valid["species_label"] == "Asian hornet"]
    df_eu = df_valid[df_valid["species_label"] == "European hornet"]

    # Aggregate monthly counts per species separately, then merge on month.
    # outer join + fillna(0) ensures all 12 months appear even if one species
    # has zero sightings in a given month
    monthly_as = df_as.groupby("month").size().reset_index(name="Asian hornet")
    monthly_eu = df_eu.groupby("month").size().reset_index(name="European hornet")
    monthly = monthly_as.merge(monthly_eu, on="month", how="outer").fillna(0)

    # Integer month → abbreviated name for readable axis labels
    month_names = {
        1:"Jan", 2:"Feb", 3:"Mar", 4:"Apr", 5:"May", 6:"Jun",
        7:"Jul", 8:"Aug", 9:"Sep", 10:"Oct", 11:"Nov", 12:"Dec"
    }
    monthly["month_name"] = monthly["month"].map(month_names)

    # melt() converts the wide format (one column per species) to long format
    # required by px.line() for multi-series color grouping
    fig3 = px.line(
        monthly.melt(
            id_vars=["month", "month_name"],
            value_vars=["Asian hornet", "European hornet"],
            var_name="species_label",
            value_name="count"
        ),
        x="month",
        y="count",
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

    # Shaded vertical bands highlight the winter period (Dec + Jan–Feb)
    # to visually anchor the "winter survival" interpretation for the reader
    fig3.add_vrect(
        x0=11.5, x1=12.5,
        fillcolor="lightblue", opacity=0.2,
        annotation_text="Dec",
        annotation_position="top right"
    )
    fig3.add_vrect(
        x0=0.5, x1=2.5,
        fillcolor="lightblue", opacity=0.2,
        annotation_text="Winter",
        annotation_position="top left"
    )
    # Explicit tickmode="array" overrides Plotly's default numeric ticks
    # with month abbreviations for readability
    fig3.update_layout(
        xaxis=dict(
            tickmode="array",
            tickvals=list(range(1, 13)),
            ticktext=["Jan","Feb","Mar","Apr","May","Jun",
                      "Jul","Aug","Sep","Oct","Nov","Dec"]
        )
    )
    st.plotly_chart(fig3, use_container_width=True)

# ── Historical temperature data (Open-Meteo) ─────────
# Average January temperature is used as a proxy for winter severity —
# the primary climatic constraint on Asian hornet queen survival.
# Data is fetched from the Open-Meteo ERA5 reanalysis archive (2010–2023)
# for 6 representative German cities covering the main climate gradient.
st.subheader("🌡️ Historical temperature data (Open-Meteo)")
st.caption("Average January temperature by region — proxy for winter severity")

# Representative cities chosen to cover the full north–south temperature gradient.
# Freiburg is included as an outlier: warmest winter climate in Germany,
# consistent with earliest confirmed Asian hornet sightings.
CITIES = {
    "Hamburg (North)":       (53.55,  9.99),
    "Berlin (North-East)":   (52.52, 13.40),
    "Frankfurt (Central)":   (50.11,  8.68),
    "Stuttgart (SW)":        (48.78,  9.18),
    "München (South)":       (48.14, 11.58),
    "Freiburg (SW, warm)":   (47.99,  7.84),
}

@st.cache_data(ttl=86400)
def get_jan_temp(lat: float, lon: float) -> float:
    """
    Fetch mean January temperature (2010–2023) for a given location
    from the Open-Meteo ERA5 reanalysis archive.

    Filters daily temperature records to January entries (month == "01")
    and returns their mean, rounded to 1 decimal place.
    Cached for 24 hours to avoid redundant external API calls on reruns.

    Args:
        lat: Latitude of the location
        lon: Longitude of the location

    Returns:
        Mean January temperature in °C, or None if the request fails.
    """
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

        # Filter to January entries only; skip None values from missing days
        jan_temps = [
            t for d, t in zip(dates, temps)
            if d[5:7] == "01" and t is not None
        ]
        return round(sum(jan_temps) / len(jan_temps), 1) if jan_temps else None
    except Exception:
        return None

# Fetch temperatures for all cities — each call is individually cached
temp_data = []
for city, (lat, lon) in CITIES.items():
    temp = get_jan_temp(lat, lon)
    temp_data.append({"city": city, "avg_jan_temp": temp, "lat": lat})

# dropna() removes any city where the API call failed
temp_df = pd.DataFrame(temp_data).dropna()

if not temp_df.empty:
    # Sort ascending so the coldest city appears on the left —
    # reinforces the visual narrative of a cold-to-warm gradient.
    # RdYlBu_r color scale: red = warm, blue = cold (reversed to match intuition)
    fig4 = px.bar(
        temp_df.sort_values("avg_jan_temp"),
        x="city",
        y="avg_jan_temp",
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
