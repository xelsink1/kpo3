from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class Work(Base):
    __tablename__ = "works"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(String, index=True)
    assignment_id = Column(String, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    file_path = Column(String)
    hash_value = Column(String, index=True)
