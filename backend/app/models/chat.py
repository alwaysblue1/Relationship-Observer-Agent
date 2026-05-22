from datetime import datetime
from uuid import uuid4

from sqlalchemy import String, DateTime, Integer, Float, Text, JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from pgvector.sqlalchemy import Vector
import enum

from app.database import Base


class MessageType(str, enum.Enum):
    TEXT = "text"
    EMOJI = "emoji"
    IMAGE = "image"
    VOICE_CALL = "voice_call"
    VIDEO_CALL = "video_call"
    SYSTEM_EVENT = "system_event"


class Platform(str, enum.Enum):
    WECHAT = "wechat"
    QQ = "qq"


class RelationshipStatus(str, enum.Enum):
    HIGH_INTIMACY = "high_intimacy"
    STABLE = "stable"
    DISTANCING = "distancing"
    REPAIRING = "repairing"


class AnalysisSession(Base):
    __tablename__ = "analysis_sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    title: Mapped[str] = mapped_column(String(255), nullable=False, default="未命名分析")
    platform: Mapped[str] = mapped_column(String(20), nullable=False)
    date_range_start: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    date_range_end: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    total_messages: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=True, index=True)

    participants: Mapped[list["Participant"]] = relationship(back_populates="session", cascade="all, delete-orphan")
    messages: Mapped[list["AnonymizedMessage"]] = relationship(back_populates="session", cascade="all, delete-orphan")
    events: Mapped[list["RelationshipEvent"]] = relationship(back_populates="session", cascade="all, delete-orphan")
    analyses: Mapped[list["ObserverAnalysis"]] = relationship(back_populates="session", cascade="all, delete-orphan")
    user: Mapped["User"] = relationship(back_populates="sessions")


class Participant(Base):
    __tablename__ = "participants"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    session_id: Mapped[str] = mapped_column(String(36), ForeignKey("analysis_sessions.id"), nullable=False)
    anonymous_id: Mapped[str] = mapped_column(String(50), nullable=False)
    is_self: Mapped[bool] = mapped_column(default=False)
    original_name: Mapped[str] = mapped_column(String(100), nullable=True)

    session: Mapped["AnalysisSession"] = relationship(back_populates="participants")


class AnonymizedMessage(Base):
    __tablename__ = "anonymized_messages"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    session_id: Mapped[str] = mapped_column(String(36), ForeignKey("analysis_sessions.id"), nullable=False)
    sender_anon_id: Mapped[str] = mapped_column(String(50), nullable=False)
    message_type: Mapped[str] = mapped_column(String(20), nullable=False, default=MessageType.TEXT.value)
    anonymized_content: Mapped[str] = mapped_column(Text, nullable=True)
    original_timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    embedding: Mapped[list[float]] = mapped_column(Vector(1536), nullable=True)
    extra_data: Mapped[dict] = mapped_column(JSON, nullable=True)

    session: Mapped["AnalysisSession"] = relationship(back_populates="messages")


class RelationshipEvent(Base):
    __tablename__ = "relationship_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    session_id: Mapped[str] = mapped_column(String(36), ForeignKey("analysis_sessions.id"), nullable=False)
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    weight: Mapped[int] = mapped_column(Integer, default=0)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    occurred_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    extra_data: Mapped[dict] = mapped_column(JSON, nullable=True)

    session: Mapped["AnalysisSession"] = relationship(back_populates="events")


class ObserverAnalysis(Base):
    __tablename__ = "observer_analyses"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    session_id: Mapped[str] = mapped_column(String(36), ForeignKey("analysis_sessions.id"), nullable=False)
    analysis_type: Mapped[str] = mapped_column(String(50), nullable=False)

    relationship_trend: Mapped[str] = mapped_column(Text, nullable=True)
    communication_change: Mapped[str] = mapped_column(Text, nullable=True)
    emotional_rhythm: Mapped[str] = mapped_column(Text, nullable=True)
    observer_summary: Mapped[str] = mapped_column(Text, nullable=True)

    health_score: Mapped[int] = mapped_column(Integer, nullable=True)
    score_trend: Mapped[str] = mapped_column(String(50), nullable=True)
    score_trend_value: Mapped[float] = mapped_column(Float, nullable=True)
    score_reasons: Mapped[dict] = mapped_column(JSON, nullable=True)

    personality_label: Mapped[str] = mapped_column(String(100), nullable=True)
    personality_description: Mapped[str] = mapped_column(Text, nullable=True)
    personality_traits: Mapped[dict] = mapped_column(JSON, nullable=True)
    personality_portrait_svg: Mapped[str] = mapped_column(Text, nullable=True)

    suggestions: Mapped[dict] = mapped_column(JSON, nullable=True)

    spotify_mood_keywords: Mapped[str] = mapped_column(Text, nullable=True)
    spotify_playlist_name: Mapped[str] = mapped_column(String(255), nullable=True)
    spotify_recommendation: Mapped[dict] = mapped_column(JSON, nullable=True)

    raw_metrics: Mapped[dict] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    session: Mapped["AnalysisSession"] = relationship(back_populates="analyses")
