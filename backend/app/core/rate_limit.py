"""Rate-limiting configuration for authentication endpoints."""

from fastapi import APIRouter
from fastapi.routing import APIRoute
from slowapi import Limiter
from slowapi.util import get_remote_address

from .config import settings

limiter = Limiter(key_func=get_remote_address)


def limit_login_router(router: APIRouter) -> APIRouter:
    """Apply the configured request limit to the generated cookie-login route."""
    for route in router.routes:
        if isinstance(route, APIRoute) and route.path == "/login":
            limited_endpoint = limiter.limit(settings.login_rate_limit)(route.endpoint)
            route.endpoint = limited_endpoint
            route.dependant.call = limited_endpoint
            break
    return router
