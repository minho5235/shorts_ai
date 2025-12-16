from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.sql import func
from database import Base

class VideoRequest(Base):
    __tablename__ = "video_requests"

    id = Column(Integer, primary_key=True, index=True)
    topic = Column(String(255), nullable=False)  # 주제 (예: 오늘의 뉴스)
    status = Column(String(50), default="PENDING") # 상태 (PENDING, PROCESSING, COMPLETED)
    script = Column(Text, nullable=True) # AI가 쓴 대본
    video_url = Column(String(500), nullable=True) # 완성된 영상 경로
    created_at = Column(DateTime(timezone=True), server_default=func.now()) # 생성 시간