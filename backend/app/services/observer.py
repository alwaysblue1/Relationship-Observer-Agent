import json
from datetime import datetime
from uuid import uuid4
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.chat import (
    AnalysisSession, AnonymizedMessage, RelationshipEvent,
    ObserverAnalysis, Participant,
)
from app.services.llm import deepseek_client
from app.services.event_engine import RelationshipEventEngine
from app.services.bailian import bailian_image_service


class ObserverService:
    """Orchestrates the full observer analysis pipeline."""

    @staticmethod
    async def run_full_analysis(
        session_id: str,
        session: AnalysisSession,
        messages: list[dict],
        events: list[dict],
        db: AsyncSession,
    ) -> ObserverAnalysis:
        metrics = RelationshipEventEngine.compute_metrics(messages, events)
        metrics["session_title"] = session.title

        relationship_status = ObserverService._classify_status(metrics)

        report, scoring, suggestions, personality, spotify = None, None, None, None, None

        try:
            report = await deepseek_client.generate_observer_report(metrics)
        except Exception as e:
            report = {"error": str(e)}

        try:
            scoring = await deepseek_client.generate_scoring(metrics)
        except Exception as e:
            scoring = {"error": str(e)}

        try:
            suggestions = await deepseek_client.generate_suggestions(metrics)
        except Exception as e:
            suggestions = {"error": str(e)}

        try:
            personality = await deepseek_client.generate_personality(metrics)
        except Exception as e:
            personality = {"error": str(e)}

        try:
            spotify = await deepseek_client.generate_spotify_recommendation({
                **metrics, "relationship_status": relationship_status,
            })
        except Exception as e:
            spotify = {"error": str(e)}

        score_val = scoring.get("health_score", 50) if isinstance(scoring, dict) else 50
        trend_dir = scoring.get("trend_direction", "stable") if isinstance(scoring, dict) else "stable"
        trend_val = scoring.get("trend_value", 0) if isinstance(scoring, dict) else 0
        reasons = scoring.get("reasons", []) if isinstance(scoring, dict) else []

        analysis = ObserverAnalysis(
            id=str(uuid4()),
            session_id=session_id,
            analysis_type="full",

            relationship_trend=report.get("relationship_trend", "") if isinstance(report, dict) else "",
            communication_change=report.get("communication_change", "") if isinstance(report, dict) else "",
            emotional_rhythm=report.get("emotional_rhythm", "") if isinstance(report, dict) else "",
            observer_summary=report.get("observer_summary", "") if isinstance(report, dict) else "",

            health_score=score_val,
            score_trend=trend_dir,
            score_trend_value=trend_val,
            score_reasons=reasons,

            personality_label=personality.get("label", "") if isinstance(personality, dict) else "",
            personality_description=personality.get("description", "") if isinstance(personality, dict) else "",
            personality_traits=personality.get("traits", []) if isinstance(personality, dict) else [],
            personality_portrait_svg=await ObserverService._generate_portrait(personality if isinstance(personality, dict) else {}),

            suggestions=suggestions.get("suggestions", []) if isinstance(suggestions, dict) else [],

            spotify_mood_keywords=", ".join(spotify.get("mood_keywords", [])) if isinstance(spotify, dict) else "",
            spotify_playlist_name=spotify.get("playlist_name", "") if isinstance(spotify, dict) else "",
            spotify_recommendation=spotify if isinstance(spotify, dict) else {},

            raw_metrics=metrics,
        )

        db.add(analysis)
        await db.commit()
        await db.refresh(analysis)
        return analysis

    @staticmethod
    def _classify_status(metrics: dict) -> str:
        score = metrics.get("event_score_total", 0)
        if score >= 30:
            return "high_intimacy"
        if score >= 10:
            return "stable"
        if score >= -10:
            return "distancing"
        return "repairing"

    @staticmethod
    async def _generate_portrait(personality: dict) -> str:
        portrait_desc = personality.get("portrait_description", "抽象人格画像")
        label = personality.get("label", "Observer")

        image_url = await bailian_image_service.generate_image(portrait_desc)
        if image_url:
            return image_url

        return ObserverService._generate_portrait_svg(personality)

    @staticmethod
    def _generate_portrait_svg(personality: dict) -> str:
        label = personality.get("label", "Observer")
        traits = personality.get("traits", [])
        portrait = personality.get("portrait_description", "抽象人格画像")

        colors = ["#f43f5e", "#8b5cf6", "#3b82f6", "#10b981", "#f59e0b", "#ec4899"]
        color_idx = hash(label) % len(colors)
        color = colors[color_idx]

        trait_circles = ""
        for i, _ in enumerate(traits[:3]):
            cx = 60 + i * 60
            cy = 180
            r = 15 + i * 5
            trait_circles += f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{color}" stroke-width="1.5" opacity="0.6"/>'

        return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 240" width="200" height="240">
  <rect width="200" height="240" rx="16" fill="#0f172a"/>
  <circle cx="100" cy="70" r="35" fill="none" stroke="{color}" stroke-width="2" opacity="0.8"/>
  <circle cx="100" cy="70" r="18" fill="{color}" opacity="0.2"/>
  <text x="100" y="78" text-anchor="middle" fill="{color}" font-size="14" font-family="sans-serif" font-weight="bold">{label}</text>
  {trait_circles}
  <text x="100" y="215" text-anchor="middle" fill="#64748b" font-size="10" font-family="sans-serif">{portrait[:30]}</text>
</svg>'''
