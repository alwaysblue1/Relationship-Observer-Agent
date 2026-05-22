import json
import random
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
from app.services.rag import RAGPipeline


class ObserverService:
    """Orchestrates the full observer analysis pipeline."""

    @staticmethod
    def _sample_messages(messages: list[dict], max_chars: int = 4000) -> str:
        """Extract representative message samples across the full timeline.

        Divides messages into 4 temporal segments and picks content-rich
        messages from each, so the LLM can reference actual conversation
        topics, emotional tone, and content evolution — not just statistics.
        """
        if not messages:
            return "暂无消息样本。"

        sorted_msgs = sorted(messages, key=lambda m: m.get("timestamp", ""))
        n = len(sorted_msgs)
        segment_size = max(n // 4, 1)

        samples = []
        total_chars = 0

        for seg_idx in range(4):
            start = seg_idx * segment_size
            end = start + segment_size if seg_idx < 3 else n
            segment = sorted_msgs[start:end]
            if not segment:
                continue

            longest = max(segment, key=lambda m: len(m.get("anonymized_content", "")))
            mid = segment[len(segment) // 2]

            for msg in (longest, mid):
                content = msg.get("anonymized_content", "").strip()
                if len(content) < 6:
                    continue
                ts = msg.get("timestamp", "")[:10]
                sender = msg.get("anon_sender", "?")
                entry = f"[{ts}] {sender}: {content[:300]}"
                if total_chars + len(entry) > max_chars:
                    break
                if samples and entry == samples[-1]:
                    continue
                samples.append(entry)
                total_chars += len(entry)
            if total_chars > max_chars:
                break

        return "\n".join(samples)

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
        metrics["message_samples"] = ObserverService._sample_messages(messages)

        relationship_status = ObserverService._classify_status(metrics)

        rag_result = await RAGPipeline.run(messages, events, metrics, db)
        patterns = rag_result.get("patterns", [])

        report, scoring, suggestions, personality, spotify = None, None, None, None, None

        try:
            report = await deepseek_client.generate_observer_report(metrics, patterns=patterns)
        except Exception as e:
            report = {"error": str(e)}

        try:
            scoring = await deepseek_client.generate_scoring(metrics, patterns=patterns)
        except Exception as e:
            scoring = {"error": str(e)}

        try:
            suggestions = await deepseek_client.generate_suggestions(metrics, patterns=patterns)
        except Exception as e:
            suggestions = {"error": str(e)}

        try:
            personality = await deepseek_client.generate_personality(metrics, patterns=patterns)
        except Exception as e:
            personality = {"error": str(e)}

        try:
            variation_angle = random.choice(["清晨", "黄昏", "深夜", "雨天", "晴天", "旅途中", "独处时", "相聚时"])
            variation_style = random.choice(["华语独立", "日系city pop", "韩式R&B", "欧美indie", "后摇", "爵士嘻哈", "lofi", "古典跨界"])
            spotify = await deepseek_client.generate_spotify_recommendation({
                **metrics, "relationship_status": relationship_status,
                "variation_angle": variation_angle,
                "variation_style": variation_style,
            }, patterns=patterns)
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

            raw_metrics={**metrics, "rag": {"core_metrics": rag_result.get("core_metrics"), "retrieved_patterns": patterns, "state_description": rag_result.get("state_description")}},
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
        portrait = personality.get("portrait_description", "一只安静的小动物")

        colors = ["#f43f5e", "#8b5cf6", "#3b82f6", "#10b981", "#f59e0b", "#ec4899"]
        color_idx = hash(label) % len(colors)
        color = colors[color_idx]

        # Pick animal based on label hash
        animals = ["cat", "fox", "owl", "bear", "rabbit"]
        animal = animals[hash(label + "animal") % len(animals)]

        def _animal_svg(animal_type: str, color: str) -> str:
            if animal_type == "cat":
                return f'''<g transform="translate(100,75)">
  <ellipse cx="0" cy="5" rx="30" ry="22" fill="{color}" opacity="0.15" stroke="{color}" stroke-width="1.5"/>
  <polygon points="-22,-12 -14,-22 -6,-12" fill="{color}" opacity="0.5"/>
  <polygon points="6,-12 14,-22 22,-12" fill="{color}" opacity="0.5"/>
  <circle cx="-10" cy="2" r="4" fill="{color}" opacity="0.7"/>
  <circle cx="10" cy="2" r="4" fill="{color}" opacity="0.7"/>
  <ellipse cx="-10" cy="3" rx="2" ry="3" fill="#0f172a"/>
  <ellipse cx="10" cy="3" rx="2" ry="3" fill="#0f172a"/>
  <path d="M-3,8 Q0,12 3,8" fill="none" stroke="{color}" stroke-width="1" opacity="0.5"/>
  <line x1="0" y1="14" x2="0" y2="18" stroke="{color}" stroke-width="0.8" opacity="0.3"/>
</g>'''
            elif animal_type == "fox":
                return f'''<g transform="translate(100,75)">
  <ellipse cx="0" cy="5" rx="26" ry="20" fill="{color}" opacity="0.15" stroke="{color}" stroke-width="1.5"/>
  <polygon points="-18,-14 -24,-28 -8,-12" fill="{color}" opacity="0.5"/>
  <polygon points="18,-14 24,-28 8,-12" fill="{color}" opacity="0.5"/>
  <circle cx="-9" cy="2" r="3.5" fill="{color}" opacity="0.7"/>
  <circle cx="9" cy="2" r="3.5" fill="{color}" opacity="0.7"/>
  <ellipse cx="-9" cy="3" rx="1.8" ry="2.5" fill="#0f172a"/>
  <ellipse cx="9" cy="3" rx="1.8" ry="2.5" fill="#0f172a"/>
  <ellipse cx="0" cy="12" rx="4" ry="2.5" fill="{color}" opacity="0.3"/>
  <path d="M-2,10 Q0,14 2,10" fill="none" stroke="{color}" stroke-width="0.8" opacity="0.4"/>
</g>'''
            elif animal_type == "owl":
                return f'''<g transform="translate(100,75)">
  <ellipse cx="0" cy="5" rx="28" ry="24" fill="{color}" opacity="0.15" stroke="{color}" stroke-width="1.5"/>
  <circle cx="-12" cy="-2" r="10" fill="none" stroke="{color}" stroke-width="1.5" opacity="0.6"/>
  <circle cx="12" cy="-2" r="10" fill="none" stroke="{color}" stroke-width="1.5" opacity="0.6"/>
  <circle cx="-12" cy="-2" r="4" fill="{color}" opacity="0.7"/>
  <circle cx="12" cy="-2" r="4" fill="{color}" opacity="0.7"/>
  <circle cx="-12" cy="-2" r="2" fill="#0f172a"/>
  <circle cx="12" cy="-2" r="2" fill="#0f172a"/>
  <polygon points="-3,5 0,10 3,5" fill="{color}" opacity="0.5"/>
  <line x1="-15" y1="18" x2="-10" y2="12" stroke="{color}" stroke-width="1.2" opacity="0.3"/>
  <line x1="15" y1="18" x2="10" y2="12" stroke="{color}" stroke-width="1.2" opacity="0.3"/>
</g>'''
            elif animal_type == "bear":
                return f'''<g transform="translate(100,75)">
  <ellipse cx="0" cy="8" rx="32" ry="26" fill="{color}" opacity="0.15" stroke="{color}" stroke-width="1.5"/>
  <circle cx="-18" cy="-6" r="10" fill="{color}" opacity="0.2" stroke="{color}" stroke-width="1.2"/>
  <circle cx="18" cy="-6" r="10" fill="{color}" opacity="0.2" stroke="{color}" stroke-width="1.2"/>
  <circle cx="-10" cy="5" r="3" fill="{color}" opacity="0.7"/>
  <circle cx="10" cy="5" r="3" fill="{color}" opacity="0.7"/>
  <ellipse cx="-10" cy="6" rx="1.8" ry="2.5" fill="#0f172a"/>
  <ellipse cx="10" cy="6" rx="1.8" ry="2.5" fill="#0f172a"/>
  <ellipse cx="0" cy="16" rx="5" ry="3" fill="{color}" opacity="0.3"/>
  <path d="M-3,14 Q0,18 3,14" fill="none" stroke="{color}" stroke-width="0.8" opacity="0.4"/>
</g>'''
            else:  # rabbit
                return f'''<g transform="translate(100,75)">
  <ellipse cx="0" cy="5" rx="22" ry="24" fill="{color}" opacity="0.15" stroke="{color}" stroke-width="1.5"/>
  <ellipse cx="-8" cy="-24" rx="5" ry="14" fill="{color}" opacity="0.2" stroke="{color}" stroke-width="1"/>
  <ellipse cx="8" cy="-24" rx="5" ry="14" fill="{color}" opacity="0.2" stroke="{color}" stroke-width="1"/>
  <circle cx="-8" cy="2" r="3.5" fill="{color}" opacity="0.7"/>
  <circle cx="8" cy="2" r="3.5" fill="{color}" opacity="0.7"/>
  <ellipse cx="-8" cy="3" rx="1.8" ry="2.5" fill="#0f172a"/>
  <ellipse cx="8" cy="3" rx="1.8" ry="2.5" fill="#0f172a"/>
  <ellipse cx="0" cy="10" rx="3" ry="2" fill="{color}" opacity="0.4"/>
  <path d="M-1,9 Q2,12 5,9" fill="none" stroke="{color}" stroke-width="0.6" opacity="0.3"/>
  <path d="M-5,9 Q-3,12 -1,9" fill="none" stroke="{color}" stroke-width="0.6" opacity="0.3"/>
</g>'''

        svg_body = _animal_svg(animal, color)
        return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 240" width="200" height="240">
  <rect width="200" height="240" rx="16" fill="#0f172a"/>
  {svg_body}
  <text x="100" y="140" text-anchor="middle" fill="{color}" font-size="13" font-family="sans-serif" font-weight="bold">{label}</text>
  <text x="100" y="220" text-anchor="middle" fill="#64748b" font-size="10" font-family="sans-serif">{portrait[:28]}</text>
</svg>'''
