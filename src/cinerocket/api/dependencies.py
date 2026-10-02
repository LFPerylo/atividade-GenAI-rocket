from typing import Annotated

from fastapi import Depends, Request

from cinerocket.application.service import AnalyticsService
from cinerocket.container import Container


def get_container(request: Request) -> Container:
    container: Container = request.app.state.container
    return container


def get_service(container: Annotated[Container, Depends(get_container)]) -> AnalyticsService:
    return container.service


ContainerDep = Annotated[Container, Depends(get_container)]
ServiceDep = Annotated[AnalyticsService, Depends(get_service)]
