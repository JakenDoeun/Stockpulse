"""StockPulse API entry point: `uvicorn app.main:app` from the backend/ directory."""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from . import db as database
from .config import get_settings
from .schemas import AppInfo, DatabaseHealth, ErrorResponse, FieldError, HealthResponse

log = logging.getLogger("uvicorn.error")  # uvicorn's general server log; a custom logger would have no handler

ERROR_CODES = {400: "BAD_REQUEST", 401: "UNAUTHORIZED", 403: "FORBIDDEN", 404: "NOT_FOUND", 405: "METHOD_NOT_ALLOWED",
               409: "CONFLICT", 413: "PAYLOAD_TOO_LARGE", 415: "UNSUPPORTED_MEDIA_TYPE", 422: "VALIDATION_FAILED",
               500: "INTERNAL_ERROR", 501: "NOT_IMPLEMENTED", 502: "BAD_GATEWAY", 503: "SERVICE_UNAVAILABLE"}


@asynccontextmanager
async def lifespan(app: FastAPI):
    s = get_settings()
    state = database.check_database()
    log.info("starting %s %s env=%s db=%s status=%s", s.app_name, s.app_version, s.app_env, state["backend"], state["status"])
    if state["status"] != "ok":  # keep serving so /health can report it; run `alembic upgrade head` if pending
        log.warning("database %s (%s); revision=%s expected=%s", state["status"], state["detail"], state["revision"],
                    state["expected_revision"])
    yield
    database.engine.dispose()
    log.info("stopped %s", s.app_name)


settings = get_settings()
app = FastAPI(title=settings.app_name, version=settings.app_version, lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origin_list, allow_methods=["*"], allow_headers=["*"])


def _error(status: int, detail: str, errors: list[FieldError] | None = None) -> JSONResponse:
    body = ErrorResponse(detail=detail, code=ERROR_CODES.get(status, "ERROR"), errors=errors or [])
    return JSONResponse(body.model_dump(), status_code=status)


@app.exception_handler(StarletteHTTPException)
async def _http_error(_req: Request, exc: StarletteHTTPException):
    return _error(exc.status_code, str(exc.detail))


@app.exception_handler(RequestValidationError)
async def _validation_error(_req: Request, exc: RequestValidationError):
    errors = [FieldError(loc=list(e["loc"]), message=e["msg"]) for e in exc.errors()]
    first = errors[0]
    where = ".".join(str(p) for p in first.loc if p != "body") or "request"
    more = f" (and {len(errors) - 1} more)" if len(errors) > 1 else ""
    return _error(422, f"Invalid {where}: {first.message}{more}", errors)


@app.exception_handler(Exception)
async def _unexpected(_req: Request, exc: Exception):
    log.exception("unhandled error")
    return _error(500, "Internal server error.")


@app.get("/health", response_model=HealthResponse, responses={503: {"model": HealthResponse}})
def health(response: Response) -> HealthResponse:
    s = get_settings()
    db_state = database.check_database()
    ok = db_state["status"] == "ok"
    if not ok:
        response.status_code = 503
    return HealthResponse(status="ok" if ok else "degraded",
                          app=AppInfo(name=s.app_name, version=s.app_version, environment=s.app_env),
                          database=DatabaseHealth(**db_state))
