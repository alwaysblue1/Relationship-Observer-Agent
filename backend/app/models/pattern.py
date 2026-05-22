from datetime import datetime
from uuid import uuid4

from sqlalchemy import String, DateTime, JSON, Text
from sqlalchemy.orm import Mapped, mapped_column
from pgvector.sqlalchemy import Vector

from app.database import Base
from app.config import settings


class PatternCard(Base):
    __tablename__ = "pattern_cards"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    pattern_name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    category: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    signals: Mapped[dict] = mapped_column(JSON, nullable=False, default=list)
    metrics: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    observer_style_output: Mapped[dict] = mapped_column(JSON, nullable=False, default=list)
    embedding: Mapped[list[float]] = mapped_column(Vector(settings.aliyun_embedding_dim), nullable=True)
    source: Mapped[str] = mapped_column(String(50), default="manual")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
