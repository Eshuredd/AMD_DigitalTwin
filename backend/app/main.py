"""FastAPI application wiring for the tomato digital twin API.

Route modules own domain orchestration. This entrypoint registers routers and
the project error handler without running domain computations or initializing
external services.
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.dependencies import (
    TwinAPIException,
    get_state_store,
    initialize_state_store,
    twin_api_exception_handler,
)
from app.routes import (
    actions,
    disease,
    farms,
    meta,
    narration,
    plots,
    recommend,
    sessions,
    simulation,
    water,
)


@asynccontextmanager
async def lifespan(fastapi_app: FastAPI):
    if get_state_store not in fastapi_app.dependency_overrides:
        initialize_state_store()
    yield


app = FastAPI(
    title="Tomato Irrigation Disease Digital Twin API",
    version=meta.API_VERSION,
    lifespan=lifespan,
)

app.add_exception_handler(
    TwinAPIException,
    twin_api_exception_handler,
)

app.include_router(meta.router)
app.include_router(farms.router)
app.include_router(plots.router)
app.include_router(sessions.router)
app.include_router(disease.router)
app.include_router(water.router)
app.include_router(simulation.router)
app.include_router(recommend.router)
app.include_router(narration.router)
app.include_router(actions.router)
