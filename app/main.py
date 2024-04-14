from fastapi import FastAPI
from PyViCare.PyViCareUtils import (
    PyViCareBrowserOAuthTimeoutReachedError,
    PyViCareCommandError,
    PyViCareInternalServerError,
    PyViCareInvalidConfigurationError,
    PyViCareInvalidCredentialsError,
    PyViCareInvalidDataError,
    PyViCareNotSupportedFeatureError,
    PyViCareRateLimitError,
)
from starlette import status
from starlette.responses import PlainTextResponse

from app.api import circuit, dhw, health, heatpump, loxone, ventilation

app = FastAPI()
app.include_router(circuit.router)
app.include_router(dhw.router)
app.include_router(health.router)
app.include_router(heatpump.router)
app.include_router(loxone.router)
app.include_router(ventilation.router)


@app.exception_handler(PyViCareRateLimitError)
def rate_limit_exception_handler(request, exc):
    return PlainTextResponse(exc.message, status.HTTP_429_TOO_MANY_REQUESTS)


@app.exception_handler(PyViCareInvalidConfigurationError)
def invalid_config_exception_handler(request, exc):
    return PlainTextResponse(exc.message, status.HTTP_424_FAILED_DEPENDENCY)


@app.exception_handler(PyViCareNotSupportedFeatureError)
@app.exception_handler(PyViCareInvalidDataError)
@app.exception_handler(PyViCareCommandError)
def not_supported_exception_handler(request, exc):
    return PlainTextResponse(str(exc), status.HTTP_405_METHOD_NOT_ALLOWED)


@app.exception_handler(PyViCareInvalidCredentialsError)
@app.exception_handler(PyViCareBrowserOAuthTimeoutReachedError)
def auth_exception_handler(request, exc):
    return PlainTextResponse(str(exc), status.HTTP_401_UNAUTHORIZED)


@app.exception_handler(PyViCareInternalServerError)
def internal_server_exception_handler(request, exc):
    return PlainTextResponse(exc.message, status.HTTP_500_INTERNAL_SERVER_ERROR)
