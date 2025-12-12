from fastapi import FastAPI, UploadFile, Form, File, HTTPException, Depends
from fastapi.responses import FileResponse
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError
from models import Base, Work
from pydantic import BaseModel
import os
import hashlib
import uuid
from datetime import datetime
from typing import List, Dict, Any
from pathlib import Path

app = FastAPI()

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/works")
def create_work(
    student_id: str = Form(...),
    assignment_id: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    content = file.file.read()
    file_hash = hashlib.sha256(content).hexdigest()
    timestamp = datetime.utcnow()
    if not file.filename:
        filename = f"{uuid.uuid4()}.txt"
    else:
        ext = file.filename.split(".")[-1] if "." in file.filename else "txt"
        filename = f"{uuid.uuid4()}.{ext}"
    file_path = f"/app/files/{filename}"
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, "wb") as f:
        f.write(content)

    work = Work(
        student_id=student_id,
        assignment_id=assignment_id,
        timestamp=timestamp,
        file_path=file_path,
        hash_value=file_hash
    )
    db.add(work)
    db.commit()
    db.refresh(work)
    return {
        "work_id": work.id,
        "hash": file_hash,
        "timestamp": timestamp.isoformat()
    }

@app.get("/previous_works")
def get_previous_works(before: str = None, db: Session = Depends(get_db)) -> Dict[str, List[Dict[str, Any]]]:
    query = db.query(Work.id, Work.hash_value)
    if before:
        try:
            bt = datetime.fromisoformat(before)
            query = query.filter(Work.timestamp < bt)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid before timestamp")
    previous = [
        {"id": row.id, "hash": row.hash_value}
        for row in query.all()
    ]
    return {"previous_works": previous}

@app.get("/works/{work_id}/file")
def get_work_file(work_id: int, db: Session = Depends(get_db)):
    work = db.query(Work).filter(Work.id == work_id).first()
    if not work:
        raise HTTPException(status_code=404, detail="Work not found")
    if not os.path.exists(work.file_path):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(path=Path(work.file_path), filename=Path(work.file_path).name)
