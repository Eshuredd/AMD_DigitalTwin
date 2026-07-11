# CropTwin Streamlit Frontend

This folder contains the optional Streamlit interface for the CropTwin FastAPI backend. The frontend is only an HTTP client: it does not recompute agronomy, disease confidence, simulation outcomes, recommendations, or narration.

## Design

The interface uses a light agriculture-and-technology dashboard style: warm off-white page background, white cards, a compact pale-sage sidebar, forest-green primary actions, and restrained terracotta accents for tomato or disease-related details.

The sidebar is intentionally small: it keeps connection status visible, provides load/reset controls, and moves infrastructure options into a collapsed **Settings** expander. The active session is shown in the main page as a read-only status bar above the workflow tabs, so the sidebar does not duplicate workflow navigation.

Palette:

| Role | Hex |
|---|---|
| Page background | `#F6F7F2` |
| Primary surface | `#FFFFFF` |
| Secondary surface | `#EDF2EA` |
| Sidebar background | `#E8EFE7` |
| Primary green | `#28634A` |
| Primary green hover | `#1F4E3A` |
| Sage accent | `#789274` |
| Soft sage highlight | `#DCE8D9` |
| Muted terracotta accent | `#BC6C55` |
| Primary text | `#1F2923` |
| Secondary text | `#667169` |
| Muted text | `#7D8880` |
| Border | `#D8E1D7` |
| Success | `#2F7A4A` |
| Warning | `#B7791F` |
| Error | `#B54747` |

## Install

```powershell
python -m pip install -r frontend/requirements.txt
```

## Run

Start the API from the repository root:

```powershell
uvicorn app.main:app --reload
```

Start the frontend in another terminal:

```powershell
streamlit run frontend/app.py
```

By default the frontend calls `http://127.0.0.1:8000`. Override it with:

```powershell
$env:CROPTWIN_API_BASE_URL="http://127.0.0.1:8000"
streamlit run frontend/app.py
```

The same base URL can also be edited in the Streamlit sidebar.

## Workflow

1. Create or load a CropTwin session.
2. Upload a tomato leaf image for disease evidence.
3. Enter weather and optional irrigation inputs to compute water state.
4. Update the canonical twin state.
5. Simulate candidate irrigation actions.
6. Generate the deterministic recommendation.
7. Generate narration and inspect session history.

The disease inference request uses a longer timeout because model loading and first inference can be slower than ordinary API calls.

Session creation fetches elevation automatically from Open-Meteo when the elevation override is disabled. The lookup uses the latitude and longitude entered in the form; the location name is stored as a label and is not geocoded.
