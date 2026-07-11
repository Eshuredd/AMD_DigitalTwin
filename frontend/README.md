# CropTwin Streamlit Frontend

This folder contains the optional Streamlit user interface for the CropTwin FastAPI backend. It does not duplicate agronomic, recommendation, disease, simulation, or narration logic; all domain decisions come from the API.

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
