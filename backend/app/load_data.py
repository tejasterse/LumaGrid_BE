"""
Loads a streetlights CSV into the database. Works for both the dummy data
and, later, your real Week 1 field survey export — same columns, same script.

Usage:
    python -m app.load_data ../data/dummy_streetlights.csv
"""
import csv
import sys
from datetime import datetime

from .database import SessionLocal, Base, engine
from . import models


def load_csv(path: str):
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    added, skipped = 0, 0
    try:
        with open(path, newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                exists = db.query(models.Streetlight).filter(models.Streetlight.id == row["id"]).first()
                if exists:
                    skipped += 1
                    continue
                install_date = None
                if row.get("install_date"):
                    install_date = datetime.strptime(row["install_date"], "%Y-%m-%d").date()
                light = models.Streetlight(
                    id=row["id"],
                    latitude=float(row["latitude"]),
                    longitude=float(row["longitude"]),
                    location_note=row.get("location_note") or None,
                    pole_type=row.get("pole_type") or None,
                    fixture_type=row.get("fixture_type") or None,
                    installed_by=row.get("installed_by") or None,
                    install_date=install_date,
                    current_status=row.get("current_status") or "unknown",
                )
                db.add(light)
                added += 1
        db.commit()
        print(f"Loaded {added} streetlights, skipped {skipped} already present.")
    finally:
        db.close()


if __name__ == "__main__":
    csv_path = sys.argv[1] if len(sys.argv) > 1 else "../data/dummy_streetlights.csv"
    load_csv(csv_path)
