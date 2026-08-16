"""Consistent FastAPI error translation for service/database operations."""

from functools import wraps
import logging

from fastapi import HTTPException

logger = logging.getLogger(__name__)


def handle_supabase_errors(operation_name: str):
    """Translate unexpected endpoint errors without swallowing HTTP exceptions."""

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except HTTPException:
                raise
            except Exception as error:
                logger.error("Error during %s: %s", operation_name, error)
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to complete {operation_name}: {str(error)}",
                ) from error

        return wrapper

    return decorator
