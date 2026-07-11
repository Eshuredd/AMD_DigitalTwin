from __future__ import annotations

import sys
from datetime import date, datetime, time, timezone
from pathlib import Path
from typing import Any, Callable

import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from frontend.api_client import (
    DEFAULT_API_BASE_URL,
    DISEASE_MODEL_VERSION,
    CropTwinAPIClient,
    CropTwinAPIError,
)
from frontend.ui_helpers import (
    ACTION_OPTIONS,
    SOIL_TEXTURE_OPTIONS,
    encode_image_bytes_to_base64,
    format_percent,
    humanize_disease_label,
    keys_to_clear_after,
    top_class_probabilities,
)


SESSION_KEYS = {
    "api_base_url": DEFAULT_API_BASE_URL,
    "active_state_id": "",
    "session_response": None,
    "disease_response": None,
    "water_response": None,
    "twin_response": None,
    "simulation_response": None,
    "recommendation_response": None,
    "narration_response": None,
    "history_response": None,
    "session_state_response": None,
    "health_response": None,
    "system_info_response": None,
}


def main() -> None:
    st.set_page_config(
        page_title="CropTwin",
        page_icon="🍅",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    _init_session_state()
    _render_styles()

    st.title("CropTwin Tomato Digital Twin")
    st.caption(
        "A Streamlit workflow client for the FastAPI tomato irrigation and disease evidence API."
    )

    client = CropTwinAPIClient(st.session_state.api_base_url)
    try:
        _render_sidebar(client)

        session_tab, disease_tab, water_tab, decision_tab, records_tab = st.tabs(
            [
                "Session",
                "Disease Evidence",
                "Water And Twin",
                "Simulation And Recommendation",
                "Narration And Records",
            ]
        )

        with session_tab:
            _render_session_tab(client)
        with disease_tab:
            _render_disease_tab(client)
        with water_tab:
            _render_water_tab(client)
        with decision_tab:
            _render_decision_tab(client)
        with records_tab:
            _render_records_tab(client)
    finally:
        client.close()


def _init_session_state() -> None:
    for key, value in SESSION_KEYS.items():
        st.session_state.setdefault(key, value)


def _render_styles() -> None:
    st.markdown(
        """
        <style>
        .block-container { padding-top: 2rem; }
        .small-muted { color: #667085; font-size: 0.9rem; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _render_sidebar(client: CropTwinAPIClient) -> None:
    with st.sidebar:
        st.header("Connection")
        new_base_url = st.text_input("API base URL", value=st.session_state.api_base_url)
        if new_base_url != st.session_state.api_base_url:
            st.session_state.api_base_url = new_base_url.strip() or DEFAULT_API_BASE_URL
            st.rerun()

        if st.button("Check health", use_container_width=True):
            _call_api("Health check", lambda: client.health(), store_as="health_response")
        if st.session_state.health_response:
            st.success(st.session_state.health_response.get("status", "ok"))

        if st.button("Load system info", use_container_width=True):
            _call_api("System info", lambda: client.system_info(), store_as="system_info_response")
        if st.session_state.system_info_response:
            with st.expander("System info", expanded=False):
                st.json(st.session_state.system_info_response)

        st.divider()
        st.header("Active Session")
        state_id = st.text_input("State ID", value=st.session_state.active_state_id)
        if state_id != st.session_state.active_state_id:
            st.session_state.active_state_id = state_id.strip()

        col_load, col_clear = st.columns(2)
        with col_load:
            if st.button("Load", disabled=not _has_state_id(), use_container_width=True):
                _call_api(
                    "Load session",
                    lambda: client.get_session(st.session_state.active_state_id),
                    store_as="session_state_response",
                )
        with col_clear:
            if st.button("Reset UI", use_container_width=True):
                for key, value in SESSION_KEYS.items():
                    st.session_state[key] = DEFAULT_API_BASE_URL if key == "api_base_url" else value
                st.rerun()

        _render_progress()


def _render_progress() -> None:
    st.divider()
    st.header("Workflow")
    steps = [
        ("Session", bool(st.session_state.active_state_id)),
        ("Disease", bool(st.session_state.disease_response)),
        ("Water", bool(st.session_state.water_response)),
        ("Twin state", bool(st.session_state.twin_response)),
        ("Simulation", bool(st.session_state.simulation_response)),
        ("Recommendation", bool(st.session_state.recommendation_response)),
        ("Narration", bool(st.session_state.narration_response)),
    ]
    for label, complete in steps:
        st.checkbox(label, value=complete, disabled=True)


def _render_session_tab(client: CropTwinAPIClient) -> None:
    st.subheader("Create Session")
    with st.form("create_session_form"):
        col_a, col_b = st.columns(2)
        with col_a:
            planting_date = st.date_input("Planting date", value=date.today())
            soil_texture = st.selectbox("Soil texture", SOIL_TEXTURE_OPTIONS, index=1)
            location_name = st.text_input("Location name", value="Hyderabad Farm")
        with col_b:
            latitude = st.number_input("Latitude", value=17.3850, format="%.6f")
            longitude = st.number_input("Longitude", value=78.4867, format="%.6f")
            elevation_m = st.number_input("Elevation m", value=542.0, format="%.1f")

        submitted = st.form_submit_button("Create session")
        if submitted:
            payload = {
                "crop_type": "tomato",
                "planting_date": planting_date.isoformat(),
                "location": {
                    "name": location_name,
                    "latitude": latitude,
                    "longitude": longitude,
                    "elevation_m": elevation_m,
                },
                "soil_texture": soil_texture,
            }
            result = _call_api("Create session", lambda: client.create_session(payload))
            if result:
                _clear_downstream("session")
                st.session_state.session_response = result
                st.session_state.active_state_id = result["state_id"]

    _show_response("Session response", st.session_state.session_response)


def _render_disease_tab(client: CropTwinAPIClient) -> None:
    st.subheader("Disease Evidence")
    if not _has_state_id():
        st.info("Create or load a session first.")
        return

    uploaded = st.file_uploader("Tomato leaf image", type=["jpg", "jpeg", "png"])
    if uploaded:
        image_bytes = uploaded.getvalue()
        st.image(image_bytes, caption=uploaded.name, use_container_width=True)
        st.caption(f"{len(image_bytes):,} bytes")

    if st.button("Predict disease", disabled=uploaded is None):
        try:
            image_base64 = encode_image_bytes_to_base64(uploaded.getvalue())
        except ValueError as exc:
            st.error(str(exc))
        else:
            result = _call_api(
                "Predict disease",
                lambda: client.predict_disease(
                    st.session_state.active_state_id,
                    image_base64,
                    model_version=DISEASE_MODEL_VERSION,
                ),
            )
            if result:
                _clear_downstream("disease")
                st.session_state.disease_response = result

    response = st.session_state.disease_response
    if response:
        col_a, col_b, col_c = st.columns(3)
        col_a.metric("Prediction", humanize_disease_label(response["predicted_label"]))
        col_b.metric("Confidence", format_percent(response["confidence_calibrated"]))
        col_c.metric("Uncertainty", response["uncertainty_band"])
        with st.expander("Top class probabilities", expanded=True):
            for label, probability in top_class_probabilities(response.get("class_probs", {}), limit=5):
                st.write(f"{humanize_disease_label(label)}: {format_percent(probability)}")
    _show_response("Disease response", response)


def _render_water_tab(client: CropTwinAPIClient) -> None:
    st.subheader("Water State")
    if not _has_state_id():
        st.info("Create or load a session first.")
        return

    with st.form("water_form"):
        current_date = st.date_input("Current date", value=date.today())
        col_a, col_b, col_c = st.columns(3)
        with col_a:
            tmin_c = st.number_input("Tmin C", value=22.0, format="%.1f")
            tmax_c = st.number_input("Tmax C", value=32.0, format="%.1f")
            humidity_pct = st.number_input("Humidity %", min_value=0.0, max_value=100.0, value=65.0)
        with col_b:
            wind_speed_mps = st.number_input("Wind m/s", min_value=0.0, value=2.0)
            rainfall_mm = st.number_input("Rainfall mm", min_value=0.0, value=0.0)
            shortwave = st.number_input("Shortwave MJ/m2", min_value=0.0, value=18.0)
        with col_c:
            eto_feed = st.number_input("Reference ETo mm", min_value=0.0, value=0.0)
            include_irrigation = st.checkbox("Include last irrigation")
            irrigation_amount = st.number_input("Irrigation mm", min_value=0.0, value=8.0)
            irrigation_date = st.date_input("Irrigation date", value=date.today())
            irrigation_time = st.time_input("Irrigation time", value=time(6, 0))

        submitted = st.form_submit_button("Compute water state")
        if submitted:
            payload: dict[str, Any] = {
                "current_date": current_date.isoformat(),
                "weather": {
                    "tmin_c": tmin_c,
                    "tmax_c": tmax_c,
                    "humidity_pct": humidity_pct,
                    "wind_speed_mps": wind_speed_mps,
                    "shortwave_radiation_sum_mj_m2": shortwave,
                    "rainfall_mm": rainfall_mm,
                    "eto_reference_feed": eto_feed or None,
                },
            }
            if include_irrigation:
                timestamp = datetime.combine(irrigation_date, irrigation_time, tzinfo=timezone.utc)
                payload["last_irrigation_event"] = {
                    "timestamp": timestamp.isoformat().replace("+00:00", "Z"),
                    "amount_mm": irrigation_amount,
                }
            result = _call_api(
                "Compute water state",
                lambda: client.compute_water_state(st.session_state.active_state_id, payload),
            )
            if result:
                _clear_downstream("water")
                st.session_state.water_response = result

    _render_water_summary(st.session_state.water_response)

    st.subheader("Canonical Twin State")
    can_update = bool(st.session_state.disease_response and st.session_state.water_response)
    if st.button("Update twin state", disabled=not can_update):
        result = _call_api(
            "Update twin state",
            lambda: client.update_twin_state(st.session_state.active_state_id),
        )
        if result:
            _clear_downstream("twin")
            st.session_state.twin_response = result
    if not can_update:
        st.caption("Disease evidence and water state are required before the twin state can be updated.")

    _show_response("Water response", st.session_state.water_response)
    _show_response("Twin response", st.session_state.twin_response)


def _render_water_summary(response: dict[str, Any] | None) -> None:
    if not response:
        return
    col_a, col_b, col_c, col_d = st.columns(4)
    col_a.metric("Growth stage", response["growth_stage"])
    col_b.metric("ETo", f"{response['eto_computed']:.2f} mm")
    col_c.metric("Root depletion", f"{response['root_zone_depletion']:.2f} mm")
    col_d.metric("Stress", response["stress_band"])


def _render_decision_tab(client: CropTwinAPIClient) -> None:
    st.subheader("Simulate Actions")
    if not _has_state_id():
        st.info("Create or load a session first.")
        return

    actions = st.multiselect("Candidate actions", ACTION_OPTIONS, default=ACTION_OPTIONS)
    if st.button("Simulate actions", disabled=not st.session_state.twin_response or not actions):
        result = _call_api(
            "Simulate actions",
            lambda: client.simulate_actions(st.session_state.active_state_id, actions),
        )
        if result:
            _clear_downstream("simulation")
            st.session_state.simulation_response = result

    if st.session_state.simulation_response:
        rows = st.session_state.simulation_response.get("simulations", [])
        st.dataframe(rows, use_container_width=True, hide_index=True)

    st.subheader("Recommendation")
    if st.button("Generate recommendation", disabled=not st.session_state.simulation_response):
        result = _call_api(
            "Generate recommendation",
            lambda: client.recommend(st.session_state.active_state_id),
        )
        if result:
            _clear_downstream("recommendation")
            st.session_state.recommendation_response = result

    recommendation = st.session_state.recommendation_response
    if recommendation:
        col_a, col_b, col_c = st.columns(3)
        col_a.metric("Chosen action", recommendation["chosen_action"])
        col_b.metric("Constraint", recommendation["irrigation_constraint"])
        col_c.metric("Inspection", "Yes" if recommendation["inspection_advisory"] else "No")
        st.write("Reason codes:", ", ".join(recommendation.get("decision_reason_codes", [])))

    _show_response("Simulation response", st.session_state.simulation_response)
    _show_response("Recommendation response", recommendation)


def _render_records_tab(client: CropTwinAPIClient) -> None:
    st.subheader("Narration")
    if not _has_state_id():
        st.info("Create or load a session first.")
        return

    if st.button("Generate narration", disabled=not st.session_state.recommendation_response):
        result = _call_api(
            "Generate narration",
            lambda: client.narrate(st.session_state.active_state_id),
        )
        if result:
            st.session_state.narration_response = result

    narration = st.session_state.narration_response
    if narration:
        st.markdown(f"### {narration['headline']}")
        st.write(narration["rationale"])
        if narration.get("caution"):
            st.warning(narration["caution"])

    st.subheader("State And History")
    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("Refresh current state", use_container_width=True):
            _call_api(
                "Refresh current state",
                lambda: client.get_session(st.session_state.active_state_id),
                store_as="session_state_response",
            )
    with col_b:
        if st.button("Refresh history", use_container_width=True):
            _call_api(
                "Refresh history",
                lambda: client.get_history(st.session_state.active_state_id),
                store_as="history_response",
            )

    _show_response("Narration response", narration)
    _show_response("Current state response", st.session_state.session_state_response)
    _show_response("History response", st.session_state.history_response)


def _call_api(
    label: str,
    func: Callable[[], dict[str, Any]],
    *,
    store_as: str | None = None,
) -> dict[str, Any] | None:
    with st.spinner(label):
        try:
            result = func()
        except CropTwinAPIError as exc:
            st.error(f"{exc.code}: {exc.message}")
            if exc.status_code:
                st.caption(f"HTTP {exc.status_code}")
            if exc.details:
                with st.expander("Error details", expanded=False):
                    st.json(exc.details)
            return None
        except Exception as exc:
            st.error(f"Unexpected frontend error: {exc}")
            return None
    st.success(f"{label} completed.")
    if store_as:
        st.session_state[store_as] = result
    return result


def _show_response(label: str, response: dict[str, Any] | None) -> None:
    if response is None:
        return
    with st.expander(label, expanded=False):
        st.json(response)


def _clear_downstream(step: str) -> None:
    for key in keys_to_clear_after(step):
        st.session_state[key] = None


def _has_state_id() -> bool:
    return bool(st.session_state.active_state_id)


if __name__ == "__main__":
    main()
