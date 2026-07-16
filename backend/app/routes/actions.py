"""Routes for physical actions recorded after recommendations."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from app.dependencies import (
    TwinAPIException,
    call_store_or_raise,
    get_state_store,
)
from app.schemas import ActualActionCreateRequest, ActualActionResponse
from app.store_protocol import TwinStateStore


router = APIRouter(tags=["actual-actions"])


INVALID_ACTION_REQUEST_CODE = "INVALID_ACTION_REQUEST"


@router.post(
    "/sessions/{state_id}/actual-actions",
    response_model=ActualActionResponse,
)
def record_actual_action(
    state_id: str,
    request: ActualActionCreateRequest,
    store: TwinStateStore = Depends(get_state_store),
) -> ActualActionResponse:
    if not state_id.strip():
        raise TwinAPIException(
            status_code=422,
            code=INVALID_ACTION_REQUEST_CODE,
            message="Invalid actual-action request.",
            details={"reason": "Path state_id must contain a non-whitespace value."},
        )
    return call_store_or_raise(
        store.record_actual_action,
        state_id,
        request,
    )


@router.get(
    "/sessions/{state_id}/actual-actions",
    response_model=list[ActualActionResponse],
)
def list_actual_actions(
    state_id: str,
    limit: int = Query(50, ge=1, le=200),
    store: TwinStateStore = Depends(get_state_store),
) -> list[ActualActionResponse]:
    if not state_id.strip():
        raise TwinAPIException(
            status_code=422,
            code=INVALID_ACTION_REQUEST_CODE,
            message="Invalid actual-action request.",
            details={"reason": "Path state_id must contain a non-whitespace value."},
        )
    return call_store_or_raise(
        store.list_actual_actions,
        state_id,
        limit=limit,
    )
