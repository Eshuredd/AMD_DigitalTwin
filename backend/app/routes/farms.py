"""Farm routes for persistent CropTwin metadata."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.dependencies import call_store_or_raise, get_state_store
from app.schemas import FarmCreateRequest, FarmResponse
from app.store_protocol import TwinStateStore


router = APIRouter(tags=["farms"])


@router.post("/farms", response_model=FarmResponse)
def create_farm(
    request: FarmCreateRequest,
    store: TwinStateStore = Depends(get_state_store),
) -> FarmResponse:
    return call_store_or_raise(store.create_farm, request=request)


@router.get("/farms", response_model=list[FarmResponse])
def list_farms(
    store: TwinStateStore = Depends(get_state_store),
) -> list[FarmResponse]:
    return call_store_or_raise(store.list_farms)


@router.get("/farms/{farm_id}", response_model=FarmResponse)
def get_farm(
    farm_id: str,
    store: TwinStateStore = Depends(get_state_store),
) -> FarmResponse:
    return call_store_or_raise(store.get_farm, farm_id)
