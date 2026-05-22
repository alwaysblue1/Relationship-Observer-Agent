from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.dependencies import require_user
from app.models.chat import AnalysisSession, ObserverAnalysis
from app.models.user import User

router = APIRouter(prefix="/api/analysis", tags=["analysis"])


@router.get("/sessions")
async def list_sessions(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_user),
):
    result = await db.execute(
        select(AnalysisSession)
        .where(AnalysisSession.user_id == current_user.id)
        .order_by(AnalysisSession.created_at.desc())
    )
    sessions = result.scalars().all()
    return [
        {
            "id": s.id,
            "title": s.title,
            "platform": s.platform,
            "total_messages": s.total_messages,
            "date_range_start": s.date_range_start.isoformat() if s.date_range_start else None,
            "date_range_end": s.date_range_end.isoformat() if s.date_range_end else None,
            "created_at": s.created_at.isoformat(),
        }
        for s in sessions
    ]


@router.get("/sessions/{session_id}")
async def get_session(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_user),
):
    result = await db.execute(
        select(AnalysisSession)
        .options(selectinload(AnalysisSession.analyses))
        .where(AnalysisSession.id == session_id)
        .where(AnalysisSession.user_id == current_user.id)
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(404, "Session not found")

    analysis = session.analyses[0] if session.analyses else None

    return {
        "id": session.id,
        "title": session.title,
        "platform": session.platform,
        "total_messages": session.total_messages,
        "date_range_start": session.date_range_start.isoformat() if session.date_range_start else None,
        "date_range_end": session.date_range_end.isoformat() if session.date_range_end else None,
        "created_at": session.created_at.isoformat(),
        "analysis": {
            "id": analysis.id,
            "relationship_trend": analysis.relationship_trend,
            "communication_change": analysis.communication_change,
            "emotional_rhythm": analysis.emotional_rhythm,
            "observer_summary": analysis.observer_summary,
            "health_score": analysis.health_score,
            "score_trend": analysis.score_trend,
            "score_trend_value": analysis.score_trend_value,
            "score_reasons": analysis.score_reasons,
            "personality_label": analysis.personality_label,
            "personality_description": analysis.personality_description,
            "personality_traits": analysis.personality_traits,
            "personality_portrait_svg": analysis.personality_portrait_svg,
            "suggestions": analysis.suggestions,
            "spotify_mood_keywords": analysis.spotify_mood_keywords,
            "spotify_playlist_name": analysis.spotify_playlist_name,
            "spotify_recommendation": analysis.spotify_recommendation,
            "raw_metrics": analysis.raw_metrics,
            "created_at": analysis.created_at.isoformat(),
        } if analysis else None,
    }


@router.get("/report/{session_id}")
async def get_observer_report(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_user),
):
    result = await db.execute(
        select(ObserverAnalysis)
        .join(AnalysisSession)
        .where(ObserverAnalysis.session_id == session_id)
        .where(AnalysisSession.user_id == current_user.id)
        .order_by(ObserverAnalysis.created_at.desc())
    )
    analysis = result.scalars().first()
    if not analysis:
        raise HTTPException(404, "No analysis found for this session")

    return {
        "id": analysis.id,
        "session_id": analysis.session_id,
        "relationship_trend": analysis.relationship_trend,
        "communication_change": analysis.communication_change,
        "emotional_rhythm": analysis.emotional_rhythm,
        "observer_summary": analysis.observer_summary,
        "created_at": analysis.created_at.isoformat(),
    }


@router.get("/scoring/{session_id}")
async def get_scoring(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_user),
):
    result = await db.execute(
        select(ObserverAnalysis)
        .join(AnalysisSession)
        .where(ObserverAnalysis.session_id == session_id)
        .where(AnalysisSession.user_id == current_user.id)
        .order_by(ObserverAnalysis.created_at.desc())
    )
    analysis = result.scalars().first()
    if not analysis:
        raise HTTPException(404, "No analysis found")

    return {
        "health_score": analysis.health_score,
        "trend": analysis.score_trend,
        "trend_value": analysis.score_trend_value,
        "reasons": analysis.score_reasons,
        "disclaimer": "评分仅代表沟通模式趋势，不代表真实情感。",
    }


@router.get("/personality/{session_id}")
async def get_personality(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_user),
):
    result = await db.execute(
        select(ObserverAnalysis)
        .join(AnalysisSession)
        .where(ObserverAnalysis.session_id == session_id)
        .where(AnalysisSession.user_id == current_user.id)
        .order_by(ObserverAnalysis.created_at.desc())
    )
    analysis = result.scalars().first()
    if not analysis:
        raise HTTPException(404, "No analysis found")

    return {
        "label": analysis.personality_label,
        "description": analysis.personality_description,
        "traits": analysis.personality_traits,
        "portrait_svg": analysis.personality_portrait_svg,
    }


@router.get("/suggestions/{session_id}")
async def get_suggestions(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_user),
):
    result = await db.execute(
        select(ObserverAnalysis)
        .join(AnalysisSession)
        .where(ObserverAnalysis.session_id == session_id)
        .where(AnalysisSession.user_id == current_user.id)
        .order_by(ObserverAnalysis.created_at.desc())
    )
    analysis = result.scalars().first()
    if not analysis:
        raise HTTPException(404, "No analysis found")

    return {
        "suggestions": analysis.suggestions,
    }


@router.get("/metrics/{session_id}")
async def get_metrics(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_user),
):
    result = await db.execute(
        select(ObserverAnalysis)
        .join(AnalysisSession)
        .where(ObserverAnalysis.session_id == session_id)
        .where(AnalysisSession.user_id == current_user.id)
        .order_by(ObserverAnalysis.created_at.desc())
    )
    analysis = result.scalars().first()
    if not analysis:
        raise HTTPException(404, "No analysis found")

    return analysis.raw_metrics or {}


@router.delete("/sessions/{session_id}")
async def delete_session(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_user),
):
    result = await db.execute(
        select(AnalysisSession)
        .where(AnalysisSession.id == session_id)
        .where(AnalysisSession.user_id == current_user.id)
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(404, "Session not found")

    await db.delete(session)
    await db.commit()
    return {"ok": True}
