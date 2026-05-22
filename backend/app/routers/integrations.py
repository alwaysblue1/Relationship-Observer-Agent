import random

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.dependencies import require_user
from app.models.chat import ObserverAnalysis, AnalysisSession
from app.models.user import User
from app.services.spotify import spotify_service

router = APIRouter(prefix="/api/integrations", tags=["integrations"])


@router.get("/spotify/{session_id}")
async def get_spotify_recommendation(
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

    rec = analysis.spotify_recommendation or {}
    genres = rec.get("suggested_genres", ["indie", "acoustic"])
    keywords = rec.get("mood_keywords", [])

    # Randomize genre order and pick a random offset for variety
    shuffled_genres = random.sample(genres, len(genres)) if len(genres) > 1 else list(genres)
    tracks = await spotify_service.get_recommendations(shuffled_genres, keywords)
    if not tracks:
        # Try each genre with random priority
        for genre in shuffled_genres:
            tracks = await spotify_service.search_tracks(genre)
            if tracks:
                break
        if not tracks:
            tracks = await spotify_service.search_tracks("indie")

    return {
        "playlist_name": analysis.spotify_playlist_name or rec.get("playlist_name", "Observer Mix"),
        "mood_keywords": keywords or analysis.spotify_mood_keywords.split(", "),
        "recommendation_reason": rec.get("recommendation_reason", ""),
        "tracks": tracks,
        "spotify_open_url": "https://open.spotify.com",
    }


@router.post("/spotify/create-playlist/{session_id}")
async def create_spotify_playlist(
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

    rec = analysis.spotify_recommendation or {}
    genres = rec.get("suggested_genres", ["indie"])
    keywords = rec.get("mood_keywords", [])

    tracks = await spotify_service.get_recommendations(genres, keywords)
    if not tracks:
        tracks = await spotify_service.search_tracks(genres[0] if genres else "indie")

    uris = [t.get("uri", "") for t in tracks if t.get("uri")]
    playlist_name = analysis.spotify_playlist_name or "Observer Mix"

    result_playlist = await spotify_service.create_playlist(playlist_name, uris)

    return {
        "playlist": result_playlist,
        "spotify_open_url": "https://open.spotify.com",
    }
