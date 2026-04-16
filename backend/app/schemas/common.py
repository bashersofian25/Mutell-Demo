from pydantic import BaseModel


class SuccessResponse(BaseModel):
    success: bool = True
    data: dict | list | None = None
    message: str | None = None


class ErrorResponse(BaseModel):
    success: bool = False
    error: str
    message: str
    details: dict | None = None


class PaginatedMeta(BaseModel):
    page: int
    per_page: int
    total: int


class PaginatedResponse(BaseModel):
    success: bool = True
    data: list = []
    meta: PaginatedMeta
