from fastapi import FastAPI, UploadFile, Form, File, HTTPException, Depends
from pydantic import BaseModel
from typing import Any
import httpx
import os
from datetime import datetime

app = FastAPI()

STORING_URL = os.getenv("STORING_URL")
ANALYSIS_URL = os.getenv("ANALYSIS_URL")

class AnalyzeRequest(BaseModel):
    file_hash: str
    upload_time: str

@app.post("/upload")
async def upload_work(
    student_id: str = Form(...),
    assignment_id: str = Form(...),
    file: UploadFile = File(...)
):
    content = await file.read()
    async with httpx.AsyncClient() as client:
        files = {"file": (file.filename, content, "application/octet-stream")}
        data = {
            "student_id": student_id,
            "assignment_id": assignment_id
        }
        resp_storing = await client.post(f"{STORING_URL}/works", data=data, files=files)
        if resp_storing.status_code != 200:
            raise HTTPException(status_code=500, detail="Failed to store file")
        work_info: dict[str, Any] = resp_storing.json()
        work_id = work_info["work_id"]
        file_hash = work_info["hash"]
        upload_time = work_info["timestamp"]

        analyze_resp = await client.post(
            f"{ANALYSIS_URL}/analyze/{work_id}",
            json={"file_hash": file_hash, "upload_time": upload_time}
        )
        if analyze_resp.status_code != 200:
            raise HTTPException(status_code=500, detail="Failed to analyze")
        report_info = analyze_resp.json()

    return {
        "work_id": work_id,
        "report_id": report_info["report_id"],
        "plagiarism": report_info["plagiarism"]
    }

@app.get("/works/{work_id}/reports")
async def get_reports(work_id: int):
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{ANALYSIS_URL}/reports/{work_id}")
        if resp.status_code != 200:
            raise HTTPException(status_code=404, detail="Reports not found")
        return resp.json()
