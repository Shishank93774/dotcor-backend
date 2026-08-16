from typing import Optional

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse


class DomainException(Exception):
    """Base class for all domain-specific exceptions."""

    def __init__(self, message: str, detail: Optional[dict] = None):
        self.message = message
        self.detail = detail
        super().__init__(self.message)


class ResourceConflictError(DomainException):
    """Raised when a resource conflict occurs (HTTP 409)."""

    pass


class InvalidInputError(DomainException):
    """Raised when input validation fails (HTTP 422)."""

    pass


class ResourceNotFoundError(DomainException):
    """Raised when a requested resource is not found (HTTP 404)."""

    pass


class InvalidTokenError(DomainException):
    """Raised when an invalid token is provided (HTTP 401)."""

    pass


class UnauthorizedError(DomainException):
    """Raised when a user is not authorized to access a resource (HTTP 403)."""

    pass


class ServiceError(DomainException):
    """Raised when an unexpected internal service error occurs (HTTP 500)."""

    pass


def setup_exception_handlers(app: FastAPI):
    @app.exception_handler(ResourceConflictError)
    async def conflict_exception_handler(request: Request, exc: ResourceConflictError):
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={"detail": exc.message},
        )

    @app.exception_handler(InvalidInputError)
    async def invalid_input_exception_handler(request: Request, exc: InvalidInputError):
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            content={"detail": exc.message},
        )

    @app.exception_handler(ResourceNotFoundError)
    async def not_found_exception_handler(request: Request, exc: ResourceNotFoundError):
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"detail": exc.message},
        )

    @app.exception_handler(InvalidTokenError)
    async def invalid_token_exception_handler(request: Request, exc: InvalidTokenError):
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"detail": exc.message},
        )

    @app.exception_handler(ServiceError)
    async def service_error_exception_handler(request: Request, exc: ServiceError):
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": exc.message},
        )

    @app.exception_handler(DomainException)
    async def domain_exception_handler(request: Request, exc: DomainException):
        return JSONResponse(
            status_code=400,
            content={"detail": exc.message},
        )
