from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from importlib.metadata import version

from fastapi import FastAPI

from cinerocket.api.errors import register_error_handlers
from cinerocket.api.routes import chat, health, metadata, sessions
from cinerocket.config import get_settings
from cinerocket.container import Container, build_container
from cinerocket.observability import configure_logging

API_PREFIX = "/api/v1"


def create_app(container: Container | None = None) -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        if container is None:
            settings = get_settings()
            configure_logging(settings.log_level)
            app.state.container = build_container(settings)
        else:
            app.state.container = container
        yield

    app = FastAPI(
        title="CineRocket Analytics API",
        description="Perguntas em linguagem natural sobre o catálogo de filmes da CineData (Text-to-SQL).",
        version=version("cinerocket"),
        lifespan=lifespan,
    )
    register_error_handlers(app)
    app.include_router(health.router)
    for router in (chat.router, sessions.router, metadata.router):
        app.include_router(router, prefix=API_PREFIX)
    return app
