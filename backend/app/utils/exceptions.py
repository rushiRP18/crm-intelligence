"""
Custom exceptions and FastAPI exception handlers.
"""
from fastapi import Request
from fastapi.responses import JSONResponse


class CRMException(Exception):
    def __init__(
        self,
        error_code: str,
        message: str,
        status_code: int = 400,
        details: dict | None = None,
    ):
        self.error_code = error_code
        self.message = message
        self.status_code = status_code
        self.details = details
        super().__init__(message)


class EmailNotFound(CRMException):
    def __init__(self, email_id):
        super().__init__(
            "EMAIL_NOT_FOUND",
            f"Email with id '{email_id}' does not exist",
            404,
            {"id": email_id},
        )


class DuplicateMessageId(CRMException):
    def __init__(self, message_id: str):
        super().__init__(
            "DUPLICATE_MESSAGE_ID",
            f"Email with message_id '{message_id}' already exists",
            409,
            {"message_id": message_id},
        )


class ThreadNotFound(CRMException):
    def __init__(self, thread_id):
        super().__init__(
            "THREAD_NOT_FOUND",
            f"Thread '{thread_id}' does not exist",
            404,
            {"thread_id": thread_id},
        )


class ContactNotFound(CRMException):
    def __init__(self, email: str):
        super().__init__(
            "CONTACT_NOT_FOUND",
            f"Contact '{email}' does not exist",
            404,
            {"email": email},
        )


class DraftNotFound(CRMException):
    def __init__(self, draft_id):
        super().__init__(
            "DRAFT_NOT_FOUND",
            f"Draft '{draft_id}' does not exist",
            404,
            {"id": draft_id},
        )


async def crm_exception_handler(request: Request, exc: CRMException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error_code": exc.error_code,
            "message": exc.message,
            "details": exc.details,
        },
    )


async def generic_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={
            "error_code": "INTERNAL_ERROR",
            "message": str(exc),
            "details": None,
        },
    )
