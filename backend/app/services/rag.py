"""Relationship Semantic RAG Pipeline.

Core idea: don't embed raw chat messages. Instead:
1. Compute 5 semantic metrics from event-engine statistical output
2. Build a Chinese natural-language state description
3. Embed that description via Aliyun text-embedding-v4
4. Retrieve top-k matching Pattern Cards from pgvector via cosine search
5. Inject retrieved patterns into Observer LLM prompts
"""

import math

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.services.bailian import bailian_embedding_service


class CoreMetricsCalculator:
    """Derive 5 relationship-semantic metrics (0–100) from event-engine stats."""

    @staticmethod
    def compute(events: list[dict], base_metrics: dict) -> dict[str, float]:
        total = max(base_metrics.get("total_messages", 0), 1)
        event_counts = base_metrics.get("event_counts", {})

        # initiative: topic_start + question_asked weighted / total, normalized to 0-100
        topic_starts = event_counts.get("start_new_topic", 0)
        questions = event_counts.get("question_asked", 0)
        initiative_raw = (topic_starts * 5 + questions * 3) / total
        initiative = min(100, round(initiative_raw * 20))

        # reply_energy: speed component (0-50) + quality component (0-50) - cold penalty
        avg_resp = base_metrics.get("avg_response_minutes", 30)
        speed_score = max(0, 50 - avg_resp * 1.2)  # faster = higher, 0min -> 50, ~40min -> 0
        avg_len = base_metrics.get("avg_message_length", 20)
        quality_score = min(50, avg_len * 1.5)  # longer = more engaged
        cold_count = event_counts.get("cold_replies", 0)
        cold_penalty = min(30, cold_count / max(total, 1) * 100)
        reply_energy = max(0, min(100, round(speed_score + quality_score - cold_penalty)))

        # intimacy: weighted intimacy events / total, normalized
        late_night = event_counts.get("late_night_interaction", 0)
        video = event_counts.get("video_call", 0)
        long_conv = event_counts.get("long_conversation", 0)
        long_text = event_counts.get("long_text", 0)
        goodnight = event_counts.get("goodnight", 0)
        morning = event_counts.get("morning_greeting", 0)
        image = event_counts.get("image_share", 0)
        intimacy_raw = (late_night * 6 + video * 8 + long_conv * 5 + long_text * 4
                        + goodnight * 3 + morning * 3 + image * 3) / total
        intimacy = min(100, round(intimacy_raw * 20))

        # stability: weekly variance penalty + night_ratio deviation from moderate
        weekly_trend = base_metrics.get("weekly_trend", [])
        if len(weekly_trend) >= 2:
            counts = [w["message_count"] for w in weekly_trend]
            mean_count = sum(counts) / len(counts)
            variance = sum((c - mean_count) ** 2 for c in counts) / len(counts)
            cv = math.sqrt(variance) / max(mean_count, 1)  # coefficient of variation
            variance_score = max(0, 100 - cv * 120)
        else:
            variance_score = 60

        night_ratio = base_metrics.get("night_interaction_ratio", 0)
        night_deviation = abs(night_ratio - 0.10)  # moderate baseline ~10%
        night_score = max(0, 100 - night_deviation * 300)
        stability = round(variance_score * 0.7 + night_score * 0.3)

        # repair_signal: explicit repair events + resilience (positive / negative ratio)
        cold_start_fail = event_counts.get("cold_start_fail", 0)
        read_no_reply = event_counts.get("read_but_no_reply_long", 0)
        repaired = event_counts.get("repaired_after_conflict", 0)
        cold_replies = event_counts.get("cold_replies", 0)

        positive_weight = (
            topic_starts * 5 + questions * 3 + long_text * 4 + long_conv * 5
            + goodnight * 2 + morning * 2 + image * 3
        )
        negative_weight = (
            cold_start_fail * 8 + read_no_reply * 6 + cold_replies * 4
        )
        resilience = positive_weight / max(negative_weight, 1)
        repair_base = repaired * 15 + min(resilience * 10, 40)
        repair_signal = min(100, round(repair_base))

        return {
            "initiative": initiative,
            "reply_energy": reply_energy,
            "intimacy": intimacy,
            "stability": stability,
            "repair_signal": repair_signal,
        }


class StateDescriptionBuilder:
    """Convert 5 core metrics + base stats into a 200-400 char Chinese state description."""

    # Narrative lookup tables for each metric level
    INITIATIVE_NARRATIVE = {
        (0, 20): "主动性较低，话题开启几乎完全由对方主导。互动处于被动接受状态。",
        (20, 45): "主动性偏弱，偶尔会开启新的对话，但多数时候等待对方发起。",
        (45, 65): "主动性处于健康的中等水平，双方交替发起话题。",
        (65, 85): "主动性较高，经常主动开启新的话题和提问，是对话的主要驱动者。",
        (85, 101): "主动性极高，几乎所有的对话都由一方发起和维持，可能造成关系不平衡。",
    }

    REPLY_ENERGY_NARRATIVE = {
        (0, 20): "回复投入度很低，回复简短、延迟较长，互动的能量明显不足。",
        (20, 45): "回复投入度偏低，回复质量和速度有提升空间，互动的热忱在减弱。",
        (45, 65): "回复投入度适中，能保持基本的有来有往，但缺乏持续的深度投入。",
        (65, 85): "回复投入度较高，回复及时且内容充实，展现出积极的互动意愿。",
        (85, 101): "回复投入度非常高，几乎是全情投入的互动状态。",
    }

    INTIMACY_NARRATIVE = {
        (0, 20): "亲密度较低，互动停留在表面层次，缺乏深层的情感连接。",
        (20, 45): "亲密度偏弱，有一定的情感交流但深度有限，尚未进入真正的亲密阶段。",
        (45, 65): "亲密度适中，存在稳定的情感连接，深夜互动和深度分享偶有发生。",
        (65, 85): "亲密感较强，频繁的情感交流和深度互动，关系有较为紧密的情感纽带。",
        (85, 101): "亲密感非常强烈，互动充满深度情感连接，双方共享高度的信任和暴露。",
    }

    STABILITY_NARRATIVE = {
        (0, 20): "互动节奏很不稳定，忽冷忽热的变化明显，缺乏可预测的互动模式。",
        (20, 45): "互动节奏偏不稳定，存在一定程度的波动，关系尚未找到稳定的基线。",
        (45, 65): "互动节奏相对稳定，有一定的规律性和可预测性，偶尔出现合理波动。",
        (65, 85): "互动节奏较为稳定，形成了较为固定的互动习惯和时间窗口。",
        (85, 101): "互动节奏非常稳定，每日互动模式高度一致，是可靠的情感锚点。",
    }

    REPAIR_SIGNAL_NARRATIVE = {
        (0, 20): "修复信号较弱，关系中缺乏主动的修复行为，冲突后难以自然恢复。",
        (20, 45): "修复信号偏弱，偶尔出现修复尝试但不够系统，冲突的消化较为缓慢。",
        (45, 65): "修复信号适中，具备基本的冲突修复能力，关系有一定的韧性。",
        (65, 85): "修复信号较强，有积极的修复意愿和能力，冲突后能较快恢复甚至深化关系。",
        (85, 101): "修复信号非常强，双方都展现出卓越的修复能力和意愿，关系具有很强的韧性。",
    }

    @classmethod
    def build(cls, core_metrics: dict[str, float], base_metrics: dict) -> str:
        def _pick(table: dict, value: float) -> str:
            for (lo, hi), text in table.items():
                if lo <= value < hi:
                    return text
            return ""

        initiative = core_metrics["initiative"]
        reply_energy = core_metrics["reply_energy"]
        intimacy = core_metrics["intimacy"]
        stability = core_metrics["stability"]
        repair_signal = core_metrics["repair_signal"]

        msgs_per_day = base_metrics.get("messages_per_day", 0)
        avg_resp = base_metrics.get("avg_response_minutes", 0)
        total = base_metrics.get("total_messages", 0)
        days = base_metrics.get("date_range_days", 0)

        parts = [
            f"当前关系互动特征：",
            f"主动性水平为{initiative}/100。{_pick(cls.INITIATIVE_NARRATIVE, initiative)}",
            f"回复投入度为{reply_energy}/100。{_pick(cls.REPLY_ENERGY_NARRATIVE, reply_energy)}",
            f"亲密度指标为{intimacy}/100。{_pick(cls.INTIMACY_NARRATIVE, intimacy)}",
            f"互动稳定性为{stability}/100。{_pick(cls.STABILITY_NARRATIVE, stability)}",
            f"修复信号强度为{repair_signal}/100。{_pick(cls.REPAIR_SIGNAL_NARRATIVE, repair_signal)}",
            f"整体特征：{days}天内共{total}条消息，日均{msgs_per_day}条，平均回复间隔{avg_resp}分钟。",
        ]
        return "".join(parts)


class PatternRetriever:
    """Semantic search over pattern_cards via pgvector cosine distance."""

    @staticmethod
    async def retrieve(
        query_vec: list[float],
        db: AsyncSession,
        top_k: int | None = None,
        threshold: float | None = None,
    ) -> list[dict]:
        if top_k is None:
            top_k = settings.rag_top_k
        if threshold is None:
            threshold = settings.rag_similarity_threshold

        query = text("""
            SELECT
                pattern_name,
                category,
                description,
                signals,
                metrics,
                observer_style_output,
                1 - (embedding <=> :query_vec) AS similarity
            FROM pattern_cards
            WHERE embedding IS NOT NULL
            ORDER BY embedding <=> :query_vec
            LIMIT :top_k
        """)

        try:
            result = await db.execute(query, {
                "query_vec": str(query_vec),
                "top_k": top_k,
            })
            rows = result.fetchall()
        except Exception:
            return []

        patterns = []
        for row in rows:
            sim = float(row.similarity)
            if sim < threshold:
                continue
            patterns.append({
                "pattern_name": row.pattern_name,
                "category": row.category,
                "description": row.description,
                "signals": row.signals,
                "metrics": row.metrics,
                "observer_style_output": row.observer_style_output,
                "similarity": round(sim, 4),
            })
        return patterns


class RAGPipeline:
    """Orchestrates the full RAG pipeline: metrics → description → embed → retrieve."""

    @staticmethod
    async def run(
        messages: list[dict],
        events: list[dict],
        base_metrics: dict,
        db: AsyncSession,
    ) -> dict:
        try:
            core_metrics = CoreMetricsCalculator.compute(events, base_metrics)
        except Exception:
            core_metrics = {
                "initiative": 50, "reply_energy": 50,
                "intimacy": 50, "stability": 50, "repair_signal": 50,
            }

        try:
            state_desc = StateDescriptionBuilder.build(core_metrics, base_metrics)
        except Exception:
            state_desc = "关系互动状态描述暂时无法生成。"

        patterns = []
        try:
            query_vec = await bailian_embedding_service.embed(state_desc)
            if query_vec:
                patterns = await PatternRetriever.retrieve(query_vec, db)
        except Exception:
            pass

        return {
            "patterns": patterns,
            "core_metrics": core_metrics,
            "state_description": state_desc,
        }
