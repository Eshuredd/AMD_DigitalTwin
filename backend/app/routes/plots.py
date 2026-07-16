"""Plot and plot-backed crop-cycle routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.dependencies import call_store_or_raise, get_state_store
from app.schemas import (
    CreateCropCycleRequest,
    PlotCreateRequest,
    PlotResponse,
    SessionResponse,
)
from app.store_protocol import TwinStateStore


router = APIRouter(tags=["plots"])


@router.post("/farms/{farm_id}/plots", response_model=PlotResponse)
def create_plot(
    farm_id: str,
    request: PlotCreateRequest,
    store: TwinStateStore = Depends(get_state_store),
) -> PlotResponse:
    return call_store_or_raise(store.create_plot, farm_id, request)


@router.get("/farms/{farm_id}/plots", response_model=list[PlotResponse])
def list_plots(
    farm_id: str,
    store: TwinStateStore = Depends(get_state_store),
) -> list[PlotResponse]:
    return call_store_or_raise(store.list_plots, farm_id)


@router.get("/plots/{plot_id}", response_model=PlotResponse)
def get_plot(
    plot_id: str,
    store: TwinStateStore = Depends(get_state_store),
) -> PlotResponse:
    return call_store_or_raise(store.get_plot, plot_id)


@router.post("/plots/{plot_id}/crop-cycles", response_model=SessionResponse)
def create_crop_cycle_for_plot(
    plot_id: str,
    request: CreateCropCycleRequest,
    store: TwinStateStore = Depends(get_state_store),
) -> SessionResponse:
    return call_store_or_raise(
        store.create_crop_cycle_for_plot,
        plot_id,
        request,
    )
