"""
Models matching SPEC.md's data model exactly. Do not add fields here that
aren't in the spec (no observation/confidence-score columns — that's v2).
"""
from sqlalchemy import Column, String, Float, Date, DateTime, ForeignKey, Integer
from sqlalchemy.orm import relationship
from .database import Base


class Streetlight(Base):
    __tablename__ = "streetlights"

    id = Column(String, primary_key=True)  # e.g. "SL-AJG-001"
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    location_note = Column(String, nullable=True)
    pole_type = Column(String, nullable=True)       # concrete / metal / wood
    fixture_type = Column(String, nullable=True)     # LED / CFL / solar
    installed_by = Column(String, nullable=True)
    install_date = Column(Date, nullable=True)
    current_status = Column(String, default="unknown")  # working / not_working / reported / unknown

    reports = relationship("Report", back_populates="streetlight")
    sensitive_zones = relationship("NearSensitiveZone", back_populates="streetlight")


class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, autoincrement=True)
    streetlight_id = Column(String, ForeignKey("streetlights.id"), nullable=False)
    reporter_phone = Column(String, nullable=True)
    reported_latitude = Column(Float, nullable=True)
    reported_longitude = Column(Float, nullable=True)
    issue_type = Column(String, nullable=False)  # not_working / broken_pole / flickering / obstructed / wiring / other
    photo_url = Column(String, nullable=True)
    notes = Column(String, nullable=True)
    timestamp = Column(DateTime, nullable=False)
    status = Column(String, default="new")  # new / verified / assigned / in_progress / resolved

    streetlight = relationship("Streetlight", back_populates="reports")
    maintenance = relationship("Maintenance", back_populates="report", uselist=False)


class Maintenance(Base):
    __tablename__ = "maintenance"

    id = Column(Integer, primary_key=True, autoincrement=True)
    report_id = Column(Integer, ForeignKey("reports.id"), nullable=False)
    assigned_to = Column(String, nullable=True)
    status = Column(String, default="pending")
    repair_photo_url = Column(String, nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    resolution_time_hours = Column(Float, nullable=True)

    report = relationship("Report", back_populates="maintenance")


class NearSensitiveZone(Base):
    __tablename__ = "near_sensitive_zones"

    id = Column(Integer, primary_key=True, autoincrement=True)
    streetlight_id = Column(String, ForeignKey("streetlights.id"), nullable=False)
    zone_type = Column(String, nullable=False)  # school / hospital / bus_stop / market / junction
    distance_m = Column(Float, nullable=False)

    streetlight = relationship("Streetlight", back_populates="sensitive_zones")
