"""
LightWatch MVP backend. Endpoints match SPEC.md's "Backend (FastAPI)" section.
The WhatsApp webhook and risk-summary weighting are left as clearly marked
stubs — see SPEC.md stage 3 before building those out for real.
"""
import os
import math
from twilio.rest import Client
from dotenv import load_dotenv

load_dotenv()
from datetime import datetime
from typing import Optional
from fastapi import FastAPI, Depends, HTTPException, Form, Response
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import func

from . import models, schemas
from .database import Base, engine, get_db

Base.metadata.create_all(bind=engine)

app = FastAPI(title="LightWatch MVP")

# Tighten CORS allow_origins for production deployment
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://luma-grid-fe.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

WHATSAPP_SESSIONS = {}

def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371000  # Earth radius in meters
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    a = math.sin(delta_phi / 2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


@app.get("/streetlights", response_model=list[schemas.StreetlightOut])
def list_streetlights(db: Session = Depends(get_db)):
    return db.query(models.Streetlight).all()


@app.get("/streetlights/{streetlight_id}")
def get_streetlight(streetlight_id: str, db: Session = Depends(get_db)):
    light = db.query(models.Streetlight).filter(models.Streetlight.id == streetlight_id).first()
    if not light:
        raise HTTPException(status_code=404, detail="Streetlight not found")
    reports = db.query(models.Report).filter(models.Report.streetlight_id == streetlight_id).all()
    return {
        "streetlight": schemas.StreetlightOut.model_validate(light),
        "reports": [schemas.ReportOut.model_validate(r) for r in reports],
    }


@app.post("/streetlights", response_model=schemas.StreetlightOut)
def create_streetlight(payload: schemas.StreetlightCreate, db: Session = Depends(get_db)):
    existing = db.query(models.Streetlight).filter(models.Streetlight.id == payload.id).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"{payload.id} already exists")
    light = models.Streetlight(**payload.model_dump())
    db.add(light)
    db.commit()
    db.refresh(light)
    return light


@app.post("/reports", response_model=schemas.ReportOut)
def create_report(payload: schemas.ReportCreate, db: Session = Depends(get_db)):
    light = db.query(models.Streetlight).filter(models.Streetlight.id == payload.streetlight_id).first()
    if not light:
        raise HTTPException(status_code=404, detail="Unknown streetlight_id — match against nearest light before calling this")
    report = models.Report(timestamp=datetime.utcnow(), status="new", **payload.model_dump())
    db.add(report)
    # A new report is a reasonable signal to flip the light to "reported" if it
    # wasn't already known to be down — keep this simple, don't over-infer.
    if light.current_status == "working" or light.current_status == "unknown":
        light.current_status = "reported"
    db.commit()
    db.refresh(report)
    return report


@app.get("/reports", response_model=list[schemas.ReportOut])
def list_reports(status: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(models.Report)
    if status:
        query = query.filter(models.Report.status == status)
    return query.order_by(models.Report.timestamp.asc()).all()


@app.patch("/reports/{report_id}", response_model=schemas.ReportOut)
def update_report_status(report_id: int, payload: schemas.ReportStatusUpdate, db: Session = Depends(get_db)):
    report = db.query(models.Report).filter(models.Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    report.status = payload.status
    if payload.status == "resolved":
        light = db.query(models.Streetlight).filter(models.Streetlight.id == report.streetlight_id).first()
        if light:
            light.current_status = "working"
        if report.reporter_phone:
            try:
                to_phone = report.reporter_phone
                if not to_phone.startswith("whatsapp:"):
                    to_phone = f"whatsapp:{to_phone if to_phone.startswith('+') else '+' + to_phone}"
                
                client = Client(os.environ["TWILIO_ACCOUNT_SID"], os.environ["TWILIO_AUTH_TOKEN"])
                
                # Note: If your Twilio trial account blocks free-form text, this will throw the
                # "ContentSid Required" error we saw earlier, which will be caught gracefully here!
                client.messages.create(
                    from_=os.environ["TWILIO_WHATSAPP_NUMBER"],
                    to=to_phone,
                    body=f"Ticket #{report.id} has been marked as resolved! The streetlight at {light.id} should now be working."
                )
                print(f"[WhatsApp] Resolution confirmation sent to {to_phone}")
            except Exception as e:
                print(f"[WhatsApp Error] Failed to send resolution confirmation to {report.reporter_phone}: {e}")
    db.commit()
    db.refresh(report)
    return report


@app.get("/risk-summary")
def risk_summary(db: Session = Depends(get_db)):
    """
    Simple weighted formula, not a model: (# not_working / total lights) * sensitivity_weight.
    Grouped loosely by location_note prefix for now — replace with a real "stretch/zone"
    grouping once the field survey defines actual road segments. Don't dress this up as AI.
    """
    ZONE_WEIGHTS = {"school": 3, "hospital": 3, "bus_stop": 2, "market": 1.5, "junction": 1.5}

    lights = db.query(models.Streetlight).all()
    total = len(lights)
    if total == 0:
        return {"total_lights": 0, "not_working": 0, "risk_score": 0}

    not_working = sum(1 for l in lights if l.current_status == "not_working")
    zones = db.query(models.NearSensitiveZone).all()
    max_weight = max([ZONE_WEIGHTS.get(z.zone_type, 1) for z in zones], default=1)

    score = round((not_working / total) * max_weight * 100, 1)
    return {
        "total_lights": total,
        "not_working": not_working,
        "risk_score": score,
        "note": "formula-based, not machine-learned",
    }


@app.post("/webhook/whatsapp")
def whatsapp_webhook(
    From: str = Form(...),
    Body: str = Form(""),
    Latitude: Optional[float] = Form(None),
    Longitude: Optional[float] = Form(None),
    NumMedia: str = Form("0"),
    MediaUrl0: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    phone = From
    
    # Send messages via client.messages.create()
    client = Client(os.environ["TWILIO_ACCOUNT_SID"], os.environ["TWILIO_AUTH_TOKEN"])
    
    def send_reply(msg: str):
        try:
            client.messages.create(
                from_=os.environ["TWILIO_WHATSAPP_NUMBER"],
                to=phone,
                body=msg
            )
            print(f"[WhatsApp] Reply sent to {phone}")
        except Exception as e:
            print(f"[WhatsApp Error] Failed to send webhook reply to {phone}: {e}")

    # If this is a new report containing location
    if Latitude is not None and Longitude is not None:
        WHATSAPP_SESSIONS[phone] = {
            "lat": Latitude,
            "lon": Longitude,
            "photo_url": MediaUrl0
        }
        send_reply("Please reply with issue type: 1) not working 2) broken pole 3) flickering 4) other")
        return Response(status_code=200)
        
    # If this is a reply to an existing session
    if phone in WHATSAPP_SESSIONS and Body:
        session = WHATSAPP_SESSIONS[phone]
        issue_mapping = {"1": "not_working", "2": "broken_pole", "3": "flickering", "4": "other"}
        issue_type = issue_mapping.get(Body.strip(), "other")
        
        lights = db.query(models.Streetlight).all()
        nearest_light = None
        min_dist = float('inf')
        for light in lights:
            if light.latitude is not None and light.longitude is not None:
                dist = calculate_distance(session["lat"], session["lon"], light.latitude, light.longitude)
                if dist < min_dist:
                    min_dist = dist
                    nearest_light = light
                    
        if nearest_light and min_dist <= 30:
            streetlight_id = nearest_light.id
        else:
            unmatched = db.query(models.Streetlight).filter(models.Streetlight.id == "unmatched").first()
            if not unmatched:
                unmatched = models.Streetlight(
                    id="unmatched",
                    latitude=session["lat"],
                    longitude=session["lon"],
                    location_note="Placeholder for unmatched reports",
                    current_status="reported"
                )
                db.add(unmatched)
                db.commit()
            streetlight_id = "unmatched"
            
        report_data = schemas.ReportCreate(
            streetlight_id=streetlight_id,
            reporter_phone=phone,
            reported_latitude=session["lat"],
            reported_longitude=session["lon"],
            issue_type=issue_type,
            photo_url=session.get("photo_url")
        )
        report = create_report(report_data, db)
        
        del WHATSAPP_SESSIONS[phone]
        send_reply(f"Ticket #{report.id} created successfully!")
        return Response(status_code=200)
        
    send_reply("Send a location pin to start a report.")
    return Response(status_code=200)


@app.get("/")
def root():
    return {"status": "ok", "service": "LightWatch MVP backend"}
