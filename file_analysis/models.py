from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)
    work_id = Column(Integer, nullable=False)
    plagiarism = Column(Boolean, default=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    matched_work_id = Column(Integer, nullable=True)
