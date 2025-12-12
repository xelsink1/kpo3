from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from models import Base, Report
from pydantic import BaseModel
import os
import httpx
from datetime import datetime
from typing import Dict, Any, List

app = FastAPI()

DATABASE_URL = os.getenv("DATABASE_URL")
STORING_URL = os.getenv("STORING_URL")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class AnalyzeRequest(BaseModel):
    file_hash: str
    upload_time: str

@app.post("/analyze/{work_id}")
async def analyze_work(
    work_id: int,
    request: AnalyzeRequest,
    db: Session = Depends(get_db)
):
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{STORING_URL}/previous_works?before={request.upload_time}")
        if resp.status_code != 200:
            raise HTTPException(status_code=500, detail="Failed to fetch previous works")
        previous_data: Dict[str, List[Dict[str, Any]]] = resp.json()
        previous_works = previous_data["previous_works"]

    plagiarism = False
    matched_work_id = None
    for prev in previous_works:
        if prev["hash"] == request.file_hash:
            plagiarism = True
            matched_work_id = prev["id"]
            break

    timestamp = datetime.utcnow()
    report = Report(
        work_id=work_id,
        plagiarism=plagiarism,
        timestamp=timestamp,
        matched_work_id=matched_work_id
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    return {
        "report_id": report.id,
        "plagiarism": plagiarism,
        "matched_work_id": matched_work_id
    }

@app.get("/reports/{work_id}")
def get_work_reports(work_id: int, db: Session = Depends(get_db)):
    report = db.query(Report).filter(Report.work_id == work_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return {
        "report_id": report.id,
        "work_id": report.work_id,
        "plagiarism": report.plagiarism,
        "timestamp": report.timestamp.isoformat(),
        "matched_work_id": report.matched_work_id
    }
