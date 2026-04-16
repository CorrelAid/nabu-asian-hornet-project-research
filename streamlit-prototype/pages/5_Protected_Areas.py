import streamlit as st
import plotly.express as px
import pandas as pd
from utils.gbif_loader import load_both, COLORS

st.set_page_config(
    page_title="Q4 — Protected Areas",
    page_icon="🏞️",
    layout="wide"
)

st.title("Q4 — Do Asian hornets occur more in protected areas?")
st.markdown(
    "Hypothesis: protected areas offer abundant insect prey. "
    "If confirmed, this could guide management strategies for nature reserves."
)

# ── Sidebar filters ───────────────────────────────────
country = st.sidebar.selectbox("Country", ["DE", "FR", "BE", "NL"], index=0)
limit   = st.sidebar.slider("Max records", 100, 1000, 300, step=100)

# ── Data loading ──────────────────────────────────────
df = load_both(country=country, limit=limit)

if df.empty:
    st.error("No data loaded.")
    st.stop()

# ── Protected area keyword classification ─────────────
# GBIF does not include a protected area flag in occurrence records.
# As a proxy, we scan the free-text locality field for official German/EU
# designation terms (Naturschutzgebiet, FFH, Natura 2000, etc.).
#
# Limitations of this approach:
#   - Only records with descriptive locality strings are classified correctly
#   - Records inside protected areas but with generic locality text are missed
#   - For production use, spatial intersection with WDPA or Natura 2000
#     polygon layers would give precise and complete classification
PROTECTED_KEYWORDS = [
    "naturschutz", "schutzgebiet", "nationalpark", "national park",
    "naturpark", "biosphäre", "biosphere", "reservat", "reserve",
    "vogelschutz", "ffh", "natura 2000", "naturreservat",
]

if "locality" in df.columns:

    def is_protected(locality: str) -> str:
        """
        Classify a locality string as protected or non-protected.

        Matching is case-insensitive substring search against PROTECTED_KEYWORDS.
        Returns "Unknown" for null/non-string values so they can be excluded
        from percentage calculations without distorting the results.
        """
        if not isinstance(locality, str):
            return "Unknown"
        loc = locality.lower()
        return "Protected area" if any(kw in loc for kw in PROTECTED_KEYWORDS) else "Non-protected"

    # Assign area type to every record — used as the grouping variable below
    df["area_type"] = df["locality"].apply(is_protected)

    col1, col2 = st.columns(2)

    with col1:
        # Grouped bar chart: absolute sighting counts per area type and species.
        # Shows raw magnitude — important context before looking at percentages.
        area_counts = (
            df.groupby(["area_type", "species_label"])
            .size()
            .reset_index(name="count")
        )
        fig = px.bar(
            area_counts,
            x="area_type",
            y="count",
            color="species_label",
            color_discrete_map=COLORS,
            barmode="group",    # side-by-side bars for direct species comparison
            title="Protected vs non-protected areas",
            labels={"area_type": "Area type", "count": "Observations"},
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        # Faceted pie chart: share of protected vs non-protected sightings
        # shown separately per species — reveals whether one species is
        # disproportionately represented in protected areas relative to the other.
        # "Unknown" rows are excluded to avoid distorting the percentages.
        protected_pct = (
            df.groupby(["species_label", "area_type"])
            .size()
            .reset_index(name="count")
        )
        fig2 = px.pie(
            protected_pct[protected_pct["area_type"] != "Unknown"],
            names="area_type",
            values="count",
            facet_col="species_label",  # one pie per species for direct comparison
            title="Share of protected area sightings",
            color_discrete_sequence=["#2ecc71", "#e74c3c"],  # green = protected, red = non-protected
        )
        st.plotly_chart(fig2, use_container_width=True)

    # Remind the reader about the keyword-based methodology and its limitations;
    # points toward WDPA as the recommended data source for a production version
    st.info(
        "⚠️ Note: This analysis is based on locality text keywords. "
        "For precise protected area boundaries, integration with "
        "WDPA (World Database on Protected Areas) is recommended."
    )

    # ── Protected area records ────────────────────────
    # Filter to confirmed protected area sightings for detailed inspection.
    # The metric gives a quick absolute count; the table lets the user
    # audit individual records and spot any obvious misclassifications
    protected_df = df[df["area_type"] == "Protected area"]

    st.metric("Sightings in protected areas", len(protected_df))
    st.dataframe(
        protected_df[["species_label", "locality", "bundesland", "year"]]
        .head(30),
        use_container_width=True,
    )

else:
    # locality column absent — keyword classification not possible.
    # This can happen with certain GBIF API responses or non-DE countries.
    st.warning("Locality field not available in current dataset.")
