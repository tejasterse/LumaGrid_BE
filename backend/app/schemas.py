from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel


class StreetlightCreate(BaseModel):
    id: str
    latitude: float
    longitude: float
    location_note: Optional[str] = None
    pole_type: Optional[str] = None
    fixture_type: Optional[str] = None
    installed_by: Optional[str] = None
    install_date: Optional[date] = None
    current_status: str = "unknown"


class StreetlightOut(StreetlightCreate):
    class Config:
        from_attributes = True


class ReportCreate(BaseModel):
    streetlight_id: str
    reporter_phone: Optional[str] = None
    reported_latitude: Optional[float] = None
    reported_longitude: Optional[float] = None
    issue_type: str
    photo_url: Optional[str] = None
    notes: Optional[str] = None


class ReportOut(BaseModel):
    id: int
    streetlight_id: str
    reporter_phone: Optional[str]
    reported_latitude: Optional[float]
    reported_longitude: Optional[float]
    issue_type: str
    photo_url: Optional[str]
    notes: Optional[str]
    timestamp: datetime
    status: str

    class Config:
        from_attributes = True


class ReportStatusUpdate(BaseModel):
    status: str


class WebhookPayload(BaseModel):
    phone: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    photo_url: Optional[str] = None
    body: Optional[str] = None
