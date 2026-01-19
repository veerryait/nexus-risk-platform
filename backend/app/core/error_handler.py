"""
Secure Error Handling Module

This module provides:
1. Sanitized error responses for users (vague, no internal details)
2. Private logging of full error details for debugging
3. Exception handlers that prevent information leakage
"""

import logging
import traceback
import uuid
import os
from pathlib import Path
from datetime import datetime
from typing import Optional
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

# Configure private logger (server-side only, never exposed to clients)
logger = logging.getLogger("nexus.security")
logger.setLevel(logging.ERROR)

# Try to create file handler, fallback to console if logs directory can't be created
try:
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    file_handler = logging.FileHandler(logs_dir / "error_private.log")
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(levelname)s - [%(error_id)s] - %(message)s'
    ))
    logger.addHandler(file_handler)
except Exception:
    # Fallback to console logging in production/Docker environments
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s'
    ))
    logger.addHandler(console_handler)


class SecureErrorMiddleware(BaseHTTPMiddleware):
    """
    Middleware that catches all unhandled exceptions and returns
    sanitized error responses without internal details.
    """
    
    async def dispatch(self, request: Request, call_next):
        try:
            response = await call_next(request)
            return response
        except Exception as exc:
            return await self.handle_exception(request, exc)
    
    async def handle_exception(self, request: Request, exc: Exception) -> JSONResponse:
        # Generate unique error ID for correlation
        error_id = str(uuid.uuid4())[:8].upper()
        
        # Log full details privately
        self._log_private(error_id, request, exc)
        
        # Return sanitized response
        return JSONResponse(
            status_code=500,
            content={
                "error": "An internal error occurred",
                "error_id": error_id,
                "message": "Please contact support with this error ID if the issue persists"
            }
        )
    
    def _log_private(self, error_id: str, request: Request, exc: Exception):
        """Log full error details privately - never exposed to clients"""
        extra = {"error_id": error_id}
        logger.error(
            f"Path: {request.url.path} | Method: {request.method} | "
            f"Error: {type(exc).__name__}: {str(exc)}\n"
            f"Traceback:\n{traceback.format_exc()}",
            extra=extra
        )


# User-facing error messages (intentionally vague)
USER_MESSAGES = {
    "db_error": "A database error occurred. Please try again later.",
    "auth_error": "Authentication failed. Please check your credentials.",
    "not_found": "The requested resource was not found.",
    "validation_error": "Invalid input. Please check your data.",
    "rate_limit": "Too many requests. Please wait and try again.",
    "service_unavailable": "Service temporarily unavailable.",
    "permission_denied": "You don't have permission to perform this action.",
    "generic_error": "An error occurred. Please try again.",
}


class SecureHTTPException(HTTPException):
    """
    Custom exception that separates user-facing messages from internal details.
    """
    
    def __init__(
        self,
        status_code: int,
        user_message: str = None,
        internal_message: str = None,
        error_type: str = "generic_error"
    ):
        # User sees this (vague)
        self.user_message = user_message or USER_MESSAGES.get(error_type, USER_MESSAGES["generic_error"])
        
        # Logged privately (detailed)
        self.internal_message = internal_message
        
        super().__init__(status_code=status_code, detail=self.user_message)


def sanitize_error_response(exc: Exception, include_error_id: bool = True) -> dict:
    """
    Create a sanitized error response that doesn't leak internal details.
    """
    error_id = str(uuid.uuid4())[:8].upper() if include_error_id else None
    
    # Log the actual error privately
    logger.error(
        f"Error: {type(exc).__name__}: {str(exc)}\n{traceback.format_exc()}",
        extra={"error_id": error_id or "N/A"}
    )
    
    # Determine user-facing message based on exception type
    if isinstance(exc, SecureHTTPException):
        message = exc.user_message
    elif "database" in str(exc).lower() or "postgres" in str(exc).lower():
        message = USER_MESSAGES["db_error"]
    elif "unauthorized" in str(exc).lower() or "authentication" in str(exc).lower():
        message = USER_MESSAGES["auth_error"]
    elif "permission" in str(exc).lower() or "forbidden" in str(exc).lower():
        message = USER_MESSAGES["permission_denied"]
    else:
        message = USER_MESSAGES["generic_error"]
    
    response = {"error": message}
    if error_id:
        response["error_id"] = error_id
        response["support_message"] = "Reference this ID when contacting support"
    
    return response


def setup_exception_handlers(app):
    """
    Configure FastAPI exception handlers to prevent information leakage.
    """
    
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        """Catch-all handler for unhandled exceptions"""
        error_response = sanitize_error_response(exc)
        return JSONResponse(
            status_code=500,
            content=error_response
        )
    
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        """Handle HTTP exceptions without leaking details"""
        error_id = str(uuid.uuid4())[:8].upper()
        
        # For HTTP exceptions, we can show the detail but sanitize it
        if isinstance(exc, SecureHTTPException):
            message = exc.user_message
        else:
            # Sanitize common framework messages
            detail = str(exc.detail)
            if any(keyword in detail.lower() for keyword in ["sql", "database", "postgres", "connection"]):
                message = USER_MESSAGES["db_error"]
            elif exc.status_code == 401:
                message = USER_MESSAGES["auth_error"]
            elif exc.status_code == 403:
                message = USER_MESSAGES["permission_denied"]
            elif exc.status_code == 404:
                message = USER_MESSAGES["not_found"]
            elif exc.status_code == 422:
                message = USER_MESSAGES["validation_error"]
            elif exc.status_code == 429:
                message = USER_MESSAGES["rate_limit"]
            else:
                message = exc.detail  # Use original detail for known safe messages
        
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": message,
                "error_id": error_id
            }
        )
    
    return app


# Utility function for services to log errors without exposing them
def log_error_privately(
    error: Exception,
    context: str = "",
    request_data: Optional[dict] = None
) -> str:
    """
    Log an error with full details privately and return an error ID.
    Use this in catch blocks to log but not expose error details.
    
    Returns: error_id for user reference
    """
    error_id = str(uuid.uuid4())[:8].upper()
    
    log_message = f"Context: {context} | Error: {type(error).__name__}: {str(error)}"
    if request_data:
        # Sanitize request data (remove potential secrets)
        safe_data = {k: v for k, v in request_data.items() 
                     if not any(secret in k.lower() for secret in ["password", "token", "key", "secret"])}
        log_message += f" | Request: {safe_data}"
    log_message += f"\nTraceback:\n{traceback.format_exc()}"
    
    logger.error(log_message, extra={"error_id": error_id})
    
    return error_id
