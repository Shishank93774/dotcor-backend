from typing import Optional
from fastapi import FastAPI, Request
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

class ServiceError(DomainException):
    """Raised when an unexpected internal service error occurs (HTTP 500)."""
    pass

def setup_exception_handlers(app: FastAPI):
    @app.exception_handler(ResourceConflictError)
    async def conflict_exception_handler(request: Request, exc: ResourceConflictError):
        return JSONResponse(
            status_code=409,
            content={"detail": exc.message},
        )

    @app.exception_handler(InvalidInputError)
    async def invalid_input_exception_handler(request: Request, exc: InvalidInputError):
        return JSONResponse(
            status_code=422,
            content={"detail": exc.message},
        )

    @app.exception_handler(ResourceNotFoundError)
    async def not_found_exception_handler(request: Request, exc: ResourceNotFoundError):
        return JSONResponse(
            status_code=404,
            content={"detail": exc.message},
        )

    @app.exception_handler(ServiceError)
    async def service_error_exception_handler(request: Request, exc: ServiceError):
        return JSONResponse(
            status_code=500,
            content={"detail": exc.message},
        )

    @app.exception_handler(DomainException)
    async def domain_exception_handler(request: Request, exc: DomainException):
        return JSONResponse(
            status_code=400,
            content={"detail": exc.message},
        )
