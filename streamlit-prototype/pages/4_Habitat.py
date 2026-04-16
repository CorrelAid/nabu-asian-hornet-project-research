import streamlit as st
import plotly.express as px
import pandas as pd
from utils.gbif_loader import load_both, COLORS

st.set_page_config(
    page_title="Q3 — Habitat Types",
    page_icon="🌿",
    layout="wide"
)

st.title("Q3 — Habitat types and hornet distribution")
st.markdown(
    "Germany has **93 recognised habitat types** — forests, meadows, moors etc. "
    "Where do hornets occur most frequently, and where are they absent?"
)

# ── Sidebar filters ───────────────────────────────────
# Species multiselect allows isolating one species for habitat comparison,
# or viewing both together to spot differences in habitat preference
country = st.sidebar.selectbox("Country", ["DE", "FR", "BE", "NL"], index=0)
limit   = st.sidebar.slider("Max records", 100, 1000, 300, step=100)
species_filter = st.sidebar.multiselect(
    "Species",
    ["European hornet", "Asian hornet"],
    default=["European hornet", "Asian hornet"]
)

# ── Data loading ──────────────────────────────────────
df = load_both(country=country, limit=limit)

if df.empty:
    st.error("No data loaded.")
    st.stop()

# Apply species filter — supports single-species or combined view
df = df[df["species_label"].isin(species_filter)]

# ── Habitat keyword classification ────────────────────
# GBIF does not provide a standardised habitat field.
# Instead, we infer habitat type from free-text locality descriptions
# using a curated keyword dictionary (German + English terms).
# This is a proxy approach — for production use, spatial joins with
# official habitat polygon layers (e.g., Corine Land Cover) are recommended.
st.subheader("🌍 Habitat keywords from locality field")
st.caption(
    "GBIF locality field often contains habitat descriptions "
    "like 'Feldflur', 'Waldstück', 'Garten' etc."
)

# Keyword dictionary: habitat label → list of German/English trigger words.
# First match wins — order within the dict matters for ambiguous localities.
HABITAT_KEYWORDS = {
    "Forest / Wald":    ["wald", "forst", "forest", "gehölz", "baum"],
    "Field / Feld":     ["feld", "flur", "wiese", "meadow", "field"],
    "Garden / Garten":  ["garten", "garden", "park", "grün"],
    "Settlement":       ["stadt", "dorf", "ortschaft", "siedlung", "urban"],
    "Water / Wasser":   ["bach", "fluss", "see", "teich", "wasser", "river"],
    "Moor / Sumpf":     ["moor", "sumpf", "feucht", "wetland"],
    "Vineyard":         ["weinberg", "reben", "vineyard"],
}

if "locality" in df.columns:

    def classify_habitat(locality: str) -> str:
        """
        Assign a habitat category to a locality string via keyword matching.

        Returns "Unknown" for missing values, "Other" if no keyword matches.
        Matching is case-insensitive and uses substring search (not whole words),
        so short keywords like "see" may produce false positives in edge cases.
        """
        if not isinstance(locality, str):
            return "Unknown"
        loc = locality.lower()
        for habitat, keywords in HABITAT_KEYWORDS.items():
            if any(kw in loc for kw in keywords):
                return habitat
        return "Other"

    # Apply classification — result stored in new column for grouping and display
    df["habitat_type"] = df["locality"].apply(classify_habitat)

    col1, col2 = st.columns(2)

    with col1:
        # Grouped bar chart: compare habitat preference between species.
        # Sorted descending so the most common habitats appear on the left.
        habitat_counts = (
            df.groupby(["habitat_type", "species_label"])
            .size()
            .reset_index(name="count")
            .sort_values("count", ascending=False)
        )
        fig = px.bar(
            habitat_counts,
            x="habitat_type",
            y="count",
            color="species_label",
            color_discrete_map=COLORS,
            barmode="group",        # side-by-side to make species comparison easier
            title="Observations by habitat type",
            labels={"habitat_type": "Habitat", "count": "Observations"},
        )
        fig.update_xaxes(tickangle=30)  # angled labels prevent overlap on x-axis
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        # Pie chart: overall habitat share across both species combined.
        # Complements the bar chart by showing proportional breakdown at a glance.
        # Uses the "Safe" qualitative palette for colorblind-friendly distinction.
        total_by_habitat = (
            df.groupby("habitat_type")
            .size()
            .reset_index(name="count")
            .sort_values("count", ascending=False)
        )
        fig2 = px.pie(
            total_by_habitat,
            names="habitat_type",
            values="count",
            title="Habitat distribution (both species)",
            color_discrete_sequence=px.colors.qualitative.Safe,
        )
        st.plotly_chart(fig2, use_container_width=True)

    # ── Sample locality descriptions ──────────────────
    # Shows raw locality strings alongside their assigned habitat label.
    # Useful for manually validating keyword classification quality —
    # drop_duplicates("locality") avoids showing the same location multiple times
    st.subheader("📋 Sample locality descriptions")
    sample = (
        df[df["locality"].notna()][["species_label", "locality", "habitat_type", "year"]]
        .drop_duplicates("locality")
        .head(20)
    )
    st.dataframe(sample, use_container_width=True)

else:
    # locality column is absent in some GBIF API responses depending on country/dataset;
    # habitat classification cannot proceed without it
    st.warning("Locality field not available in current dataset.")

# ── Seasonal activity pattern ─────────────────────────
# Monthly aggregation shows peak activity periods for each species.
# For habitat analysis this adds context: e.g., forest sightings may peak
# in summer when hornets are most active and observers are most present.
st.subheader("📅 Seasonal activity pattern")

if "month" in df.columns:
    monthly = (
        df.groupby(["month", "species_label"])
        .size()
        .reset_index(name="count")
    )

    # Integer month → abbreviated name mapping for readable x-axis labels
    month_names = {
        1:"Jan", 2:"Feb", 3:"Mar", 4:"Apr", 5:"May", 6:"Jun",
        7:"Jul", 8:"Aug", 9:"Sep", 10:"Oct", 11:"Nov", 12:"Dec"
    }
    monthly["month_name"] = monthly["month"].map(month_names)

    fig3 = px.bar(
        monthly,
        x="month",
        y="count",
        color="species_label",
        color_discrete_map=COLORS,
        barmode="group",
        title="Monthly observation pattern",
        labels={"month": "Month", "count": "Observations"},
    )
    # Override default numeric tick labels with month abbreviations
    fig3.update_xaxes(
        tickvals=list(month_names.keys()),
        ticktext=list(month_names.values())
    )
    st.plotly_chart(fig3, use_container_width=True)
