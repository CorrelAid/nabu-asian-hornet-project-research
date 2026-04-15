## NABU Hornet Dashboard — Streamlit Prototype

**Project:** CorrelAid × NABU (Naturschutzbund Deutschland)
**Purpose:** Exploratory prototype for analyzing the spread of *Vespa crabro* (European hornet) and *Vespa velutina* (Asian hornet) using GBIF occurrence data.

[![Open in Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://https://hornet-dashboard.streamlit.app//)


### Architecture Overview

The app is structured as a multi-page Streamlit application with a shared data loading utility:

```
streamlit_app.py          # Main dashboard / landing page
utils/gbif_loader.py      # Shared data loading & caching logic
pages/
  1_Overview.py           # Q1 — Species displacement & overlap map
  2_Displacement.py       # Q2 — European hornet geographic distribution
  3_Distribution.py       # Q5 — Synanthropic behavior (urban vs. rural)
  4_Habitat.py            # Q3 — Habitat type analysis
  4_Urban_Rural.py        # (empty / placeholder)
  5_Protected_Areas.py    # Q4 — Presence in protected areas
  6_Climate.py            # Q6 — Climate & weather influence
```

---

### Data Layer (`utils/gbif_loader.py`)

- Loads occurrence data for both species via **pygbif** (GBIF API)
- For Germany (`DE`), prioritizes **Google Drive CSV cache** (pre-downloaded via `download_gbif.py`) to avoid repeated API calls; falls back to live GBIF API for other countries
- All data is cached with `@st.cache_data` (TTL: 1h for API calls, 24h for Drive downloads)
- Cleans and normalizes fields: coordinates, `year`/`month` from `eventDate`, GADM administrative levels (`bundesland`, `landkreis`), species label and color
- Exposes `SPECIES`, `COLORS`, `load_both()`, and `load_observations()` to all pages

---

### Pages & Research Questions

| Page | Research Question | Key Visualizations |
|---|---|---|
| **Main** | Overview | Timeline (line chart), scatter map |
| **Q1 Overview** | Is the European hornet being displaced? | Overlap scatter map, bar chart by Bundesland |
| **Q2 Displacement** | European hornet distribution in Germany | Latitude/longitude histograms, density heatmap |
| **Q3 Habitat** | Habitat type correlation | Keyword-based locality classification, grouped bar + pie chart, monthly seasonality |
| **Q4 Protected Areas** | More sightings in Natura 2000 / national parks? | Keyword-based protected area flag, grouped bar + pie chart |
| **Q5 Distribution** | Is Asian hornet synanthropic? | Regional bar chart, raw data table, debug mode |
| **Q6 Climate** | Weather influence on spread | Latitude-based climate zones, seasonal line chart, Open-Meteo January temperature bar chart |

---

### Sidebar Controls

All pages share consistent sidebar filters:
- **Country** — `DE`, `FR`, `BE`, `NL`, `AT`, `CH`
- **Max records per species** — slider (100–1000)
- **Year range** — slider (2000–2025)

---

### Notable Design Decisions

- **Proxy-based habitat analysis** — both habitat type (`Q3`) and protected area status (`Q4`) are inferred from free-text `locality` field using keyword matching (e.g., `"wald"`, `"naturschutz"`). This is a pragmatic workaround pending proper spatial joins with Natura 2000 / WDPA polygon data.
- **Synanthropic bias warning** — `Q5` explicitly flags the citizen science detection bias (urban areas are over-represented due to more observers).
- **External climate data** — `Q6` fetches real historical temperature data from **Open-Meteo ERA5** API for 6 German cities to proxy winter severity.
- **Offline-first for Germany** — `download_gbif.py` pre-downloads full GBIF datasets per year (up to 20,000 records/year) to avoid rate limits during live demos.

---

### Known Limitations / Next Steps

- `pages/4_Urban_Rural.py` is currently empty — urban/rural analysis not yet implemented
- Habitat and protected area classification relies on locality text keywords, not actual spatial boundaries
- No statistical testing yet (correlation, significance)
- Designed as a **Streamlit prototype** — the production target is a **Django + HTMX** dashboard with PostgreSQL/PostGIS backend









### How to run it on your own machine

1. Install the requirements

   ```
   $ pip install -r requirements.txt
   ```

2. Run the app

   ```
   $ streamlit run streamlit_app.py
   ```



# 🐝 NABU Hornet Dashboard — Streamlit Prototype

**Project:** CorrelAid × NABU (Naturschutzbund Deutschland)
**Purpose:** Exploratory prototype for analyzing the spread of *Vespa crabro* (European hornet) and *Vespa velutina* (Asian hornet) using GBIF occurrence data.

[![Open in Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://hornet-dashboard.streamlit.app/)

---

## 📋 Table of Contents

- [Overview](#overview)
- [Tech Stack](#tech-stack)
- [Architecture](#architecture)
- [Research Questions](#research-questions)
- [Data Layer](#data-layer)
- [Design Decisions](#design-decisions)
- [Known Limitations](#known-limitations)
- [Getting Started](#getting-started)

---

## Overview

This dashboard is a **rapid prototype** built to explore and visualize hornet occurrence patterns across Central Europe. It covers six research questions relevant to NABU's conservation monitoring work, from species displacement and habitat preference to climate influence and protected area presence.

> ⚠️ This is a **Streamlit prototype**, not the final product. The production dashboard will be implemented in **Django + HTMX** with a PostgreSQL/PostGIS backend.

---

## 🛠️ Tech Stack

### Data & Analysis
| Library | Version | Purpose |
|---|---|---|
| `pandas` | 2.2.3 | Data manipulation and cleaning |
| `pygbif` | 0.6.4 | GBIF API client for occurrence data |
| `requests` | 2.32.5 | HTTP calls to Open-Meteo climate API |
| `gdown` | 5.2.0 | Downloading pre-built CSVs from Google Drive |

### Visualization
| Library | Version | Purpose |
|---|---|---|
| `plotly` | 5.24.0 | Interactive charts and maps |
| `folium` | 0.18.0 | Leaflet.js-based interactive maps |
| `streamlit-folium` | 0.24.0 | Folium map rendering inside Streamlit |

### App Framework
| Library | Version | Purpose |
|---|---|---|
| `streamlit` | 1.43.0 | Multi-page web app and UI components |

### External APIs
| API | Usage |
|---|---|
| [GBIF Occurrence API](https://www.gbif.org/developer/occurrence) | Species observation records |
| [Open-Meteo ERA5 Archive](https://open-meteo.com/en/docs/historical-weather-api) | Historical daily temperature data (2010–2023) |

### Infrastructure
| Tool | Purpose |
|---|---|
| Google Drive | Hosting pre-downloaded GBIF CSV datasets for Germany |
| Streamlit Community Cloud | App deployment and hosting |
| GitHub | Version control and team collaboration |

---

## 🏗️ Architecture

Multi-page Streamlit application with a shared data loading utility:

```
streamlit_app.py            # Main dashboard — overview metrics, timeline, map
utils/
  gbif_loader.py            # Shared data loading, caching, and cleaning logic
pages/
  1_Overview.py             # Q1 — Species displacement & overlap map
  2_Displacement.py         # Q2 — European hornet geographic distribution
  3_Distribution.py         # Q5 — Synanthropic behavior (urban vs. rural)
  4_Habitat.py              # Q3 — Habitat type analysis
  4_Urban_Rural.py          # (placeholder — not yet implemented)
  5_Protected_Areas.py      # Q4 — Presence in protected areas
  6_Climate.py              # Q6 — Climate & weather influence
download_gbif.py            # Standalone script: bulk-download GBIF data to CSV
data/                       # Local CSV cache (gitignored — large files)
```

---

## 🔬 Research Questions

| Page | Research Question | Key Visualizations |
|---|---|---|
| **Main** | Overview of both species | Timeline (line chart), scatter map |
| **Q1 — Overview** | Is the European hornet being displaced? | Overlap scatter map, bar chart by Bundesland |
| **Q2 — Displacement** | How widespread is the European hornet in Germany? | Latitude/longitude histograms, density heatmap |
| **Q3 — Habitat** | Which habitat types show highest hornet presence? | Keyword-classified bar + pie chart, monthly seasonality |
| **Q4 — Protected Areas** | Do Asian hornets occur more in Natura 2000 areas? | Protected area flag, grouped bar + pie chart |
| **Q5 — Distribution** | Is the Asian hornet synanthropic? | Regional bar chart, raw data table, debug mode |
| **Q6 — Climate** | How do weather conditions affect hornet spread? | Climate zones, seasonal line chart, January temperature chart |

### Sidebar Controls

All pages share consistent sidebar filters:

| Control | Options | Default |
|---|---|---|
| Country | `DE`, `FR`, `BE`, `NL`, `AT`, `CH` | `DE` |
| Max records per species | 100 – 1000 | 300 |
| Year range | 2000 – 2025 | 2010 – 2025 |

---

## 📦 Data Layer (`utils/gbif_loader.py`)

- Loads occurrence records for both species via **pygbif** (GBIF REST API)
- For Germany (`DE`), prioritizes a **Google Drive CSV cache** pre-built by `download_gbif.py` — up to 20,000 records per year, covering 2000–2025
- Falls back to the **live GBIF API** for all other countries (sampled, ~10–12 records/year)
- All results cached with `@st.cache_data` (TTL: 1 h for API, 24 h for Drive)
- Cleans and normalizes: coordinates, `year`/`month` from `eventDate`, GADM administrative levels (`bundesland`, `landkreis`), species label and color
- Exposes `SPECIES`, `COLORS`, `load_both()`, and `load_observations()` to all pages

---

## 🧠 Design Decisions

**Offline-first for Germany**
`download_gbif.py` pre-downloads full GBIF datasets and stores them as CSVs on Google Drive. This avoids API rate limits during live demos and enables full dataset analysis rather than sampled subsets.

**Proxy-based habitat and protected area analysis**
Both habitat type (Q3) and protected area status (Q4) are inferred from the free-text `locality` field using keyword matching (`"wald"`, `"naturschutz"`, `"ffh"`, etc.). This is a pragmatic workaround — the production version should use spatial joins with Corine Land Cover and WDPA / Natura 2000 polygon layers.

**Citizen science bias warning**
Q5 explicitly surfaces the observer effect: urban areas are over-represented in GBIF data because more people submit sightings there, which can falsely suggest higher population density in cities.

**Real climate data via Open-Meteo**
Q6 fetches ERA5 reanalysis data for 6 representative German cities to use average January temperature as a proxy for winter severity — the primary climatic constraint on Asian hornet queen survival and range expansion.

---

## ⚠️ Known Limitations

| Area | Limitation |
|---|---|
| Urban/rural analysis | `pages/4_Urban_Rural.py` is empty — not yet implemented |
| Habitat & protected areas | Classification uses locality text keywords, not actual spatial boundaries |
| Statistics | No formal testing yet (correlation coefficients, significance tests) |
| Germany focus | CSV cache only covers `DE`; other countries use a small live API sample |
| Production readiness | Prototype only — no authentication, persistent storage, or scheduled data updates |

**Production target:** Django + HTMX with PostgreSQL/PostGIS backend, Leaflet.js maps, and weekly automated GBIF sync via Celery.

---

## 🚀 Getting Started

### Prerequisites

- Python 3.11+
- A Google Drive file ID for each species CSV (optional — app falls back to live API without it)

### Installation

```bash
# Clone the repository
git clone https://github.com/your-org/nabu-hornet-dashboard.git
cd nabu-hornet-dashboard

# Install dependencies
pip install -r requirements.txt
```

### Configuration (optional)

To use the Google Drive CSV cache for Germany, create `.streamlit/secrets.toml`:

```toml
EU_HORNET_GDRIVE_ID = "your_google_drive_file_id_here"
AS_HORNET_GDRIVE_ID = "your_google_drive_file_id_here"
```

To enable the debug panel on Q5:

```toml
DEBUG = true
```

### Pre-download GBIF data (optional)

Run once to build the full Germany CSV dataset locally before uploading to Drive:

```bash
python download_gbif.py
```

### Run the app

```bash
streamlit run streamlit_app.py
```

The app will be available at `http://localhost:8501`.

---

## 📄 License

Apache License 2.0 — see [LICENSE](LICENSE) for details.

---

*NABU × CorrelAid 2026*
