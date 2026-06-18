from typing import Optional

from pydantic import BaseModel


class DetailResponse(BaseModel):
    detail: str


class TelemetryImportResponse(BaseModel):
    status: str
    message: str
    recordsProcessed: int
    relationsCreated: int


class RecalibrationResponse(BaseModel):
    status: str
    message: str


class TelemetryDateRangeResponse(BaseModel):
    minDate: Optional[str] = None
    maxDate: Optional[str] = None
