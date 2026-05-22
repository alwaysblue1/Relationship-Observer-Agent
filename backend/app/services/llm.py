import json
import asyncio
from typing import Optional, AsyncGenerator

from openai import AsyncOpenAI

from app.config import settings
from app.prompts.templates import PROMPTS


class DeepSeekClient:
    """Client for DeepSeek API with Observer prompt templates."""

    def __init__(self):
        self._client: Optional[AsyncOpenAI] = None

    @property
    def client(self) -> AsyncOpenAI:
        if self._client is None:
            api_key = settings.deepseek_api_key
            base_url = settings.deepseek_base_url
            if not api_key:
                self._client = AsyncOpenAI(
                    api_key="sk-placeholder",
                    base_url=base_url or "https://api.deepseek.com",
                )
            else:
                self._client = AsyncOpenAI(
                    api_key=api_key,
                    base_url=base_url or "https://api.deepseek.com",
                )
        return self._client

    @property
    def is_available(self) -> bool:
        return bool(settings.deepseek_api_key)

    async def generate_observer_report(self, metrics: dict) -> dict:
        if not self.is_available:
            return self._mock_observer_report(metrics)
        prompt = PROMPTS["observer_report"].format(
            metrics=json.dumps(metrics, ensure_ascii=False, indent=2)
        )
        return await self._call_json(prompt)

    async def generate_scoring(self, metrics: dict) -> dict:
        if not self.is_available:
            return self._mock_scoring(metrics)
        prompt = PROMPTS["scoring"].format(
            metrics=json.dumps(metrics, ensure_ascii=False, indent=2)
        )
        return await self._call_json(prompt)

    async def generate_suggestions(self, metrics: dict) -> dict:
        if not self.is_available:
            return self._mock_suggestions(metrics)
        prompt = PROMPTS["suggestion"].format(
            metrics=json.dumps(metrics, ensure_ascii=False, indent=2)
        )
        return await self._call_json(prompt)

    async def generate_personality(self, metrics: dict) -> dict:
        if not self.is_available:
            return self._mock_personality(metrics)
        prompt = PROMPTS["personality"].format(
            metrics=json.dumps(metrics, ensure_ascii=False, indent=2)
        )
        return await self._call_json(prompt)

    async def generate_spotify_recommendation(self, metrics: dict) -> dict:
        if not self.is_available:
            return self._mock_spotify(metrics)
        prompt = PROMPTS["spotify"].format(
            metrics=json.dumps(metrics, ensure_ascii=False, indent=2)
        )
        return await self._call_json(prompt)

    async def _call_json(self, user_prompt: str) -> dict:
        try:
            response = await self.client.chat.completions.create(
                model=settings.deepseek_model,
                messages=[
                    {"role": "system", "content": PROMPTS["system"]},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.7,
                max_tokens=2000,
                response_format={"type": "json_object"},
            )
            content = response.choices[0].message.content
            return json.loads(content)
        except json.JSONDecodeError:
            return {"raw": content, "error": "Failed to parse JSON"}
        except Exception as e:
            return {"error": str(e)}

    async def get_embedding(self, text: str) -> list[float]:
        try:
            response = await self.client.embeddings.create(
                model="deepseek-embedding",
                input=text,
            )
            return response.data[0].embedding
        except Exception:
            return [0.0] * settings.embedding_dim

    # ---- Mock responses for when API key is not configured ----

    def _mock_observer_report(self, metrics: dict) -> dict:
        event_score = metrics.get("event_score_total", 0)
        if event_score > 20:
            trend = "近期双方互动保持较高频率，主动开启话题和深度交流仍然是这段关系的常态。"
            comm = "沟通模式以事务性和情感分享并重，双方都表现出了稳定的参与意愿。"
            rhythm = "晚间互动依然是主要的情感连接时段，周末的互动密度高于工作日。"
            summary = "互动模式总体平稳，继续关注深度交流的变化趋势会有助于更好地理解彼此的节奏。"
        elif event_score > 0:
            trend = "互动频率基本稳定，但主动性和深度交流的占比相较之前略有变化。"
            comm = "沟通更偏向日常事务协调，情感分享的频次有所减少。"
            rhythm = "互动时间分布较为均匀，深夜互动的比例维持在正常范围。"
            summary = "关系整体平稳，但可以留意沟通深度的微妙变化。这些小变化累积起来可能值得关注。"
        else:
            trend = "近期互动频率有所下降，双方主动发起对话的次数减少。"
            comm = "沟通内容更偏向简短的事务性交流，深度对话的占比降低。"
            rhythm = "晚间互动模式发生了一些变化，回复间隔有所增加。"
            summary = "这些变化值得温和地关注。模式变化不一定是负面的，但保持觉察总是有益的。"

        return {
            "relationship_trend": trend,
            "communication_change": comm,
            "emotional_rhythm": rhythm,
            "observer_summary": summary,
        }

    def _mock_scoring(self, metrics: dict) -> dict:
        event_score = metrics.get("event_score_total", 0)
        score = max(20, min(90, 55 + event_score))
        return {
            "health_score": int(score),
            "trend_direction": "down" if event_score < 5 else "up",
            "trend_value": abs(event_score) * 1.5,
            "reasons": [
                "深度交流频率变化",
                "主动互动比例调整",
                "回复时间模式变化",
            ],
        }

    def _mock_suggestions(self, metrics: dict) -> dict:
        return {
            "suggestions": [
                "也许可以尝试一次不围绕事务的聊天，分享一件最近让你感到有趣的小事。",
                "关注那些'额外'的互动瞬间——它们往往比日常对话承载了更多的情感信息。",
                "保持你自己的节奏。关系的节律像潮汐，有涨有落是自然的。",
            ],
            "mood_note": "你似乎在观察和思考这段关系的变化——这种觉察本身就是一种珍贵的品质。",
        }

    def _mock_personality(self, metrics: dict) -> dict:
        event_score = metrics.get("event_score_total", 0)
        night_ratio = metrics.get("night_interaction_ratio", 0)
        messages_per_day = metrics.get("messages_per_day", 10)

        if night_ratio > 0.2:
            label = "深夜emo怪"
            desc = "凌晨三点的人生哲学家，黑暗中灵感迸发的情感诗人。"
            traits = ["深夜活跃", "情绪敏感", "深度思考者"]
            portrait = "一个在月光下静坐的剪影，手中握着一杯永远喝不完的温咖啡。"
        elif event_score < 0:
            label = "冷战艺术家"
            desc = "沉默是你的画布，克制是你的画笔。"
            traits = ["克制表达", "独立性强", "观察者视角"]
            portrait = "一个站在落地窗前的轮廓，玻璃上倒映着城市夜景和模糊的自己。"
        elif event_score > 30:
            label = "修复师"
            desc = "关系的维护者，用耐心修复每一次微小的裂痕。"
            traits = ["主动修复", "高共情", "稳定输出"]
            portrait = "一双手在光源下拼接碎片，每个碎片都反射出不同的颜色。"
        elif messages_per_day > 30:
            label = "话痨星人"
            desc = "聊天框就是你的第二居所，文字是你的氧气。"
            traits = ["高互动", "表达欲强", "能量充沛"]
            portrait = "一个被对话框气泡包围的小星球，每颗卫星都在发光。"
        else:
            label = "观察者"
            desc = "你站在关系的边缘，敏锐地记录每一个变化。"
            traits = ["敏锐观察", "理性克制", "不轻易下判断"]
            portrait = "一只安静坐在窗台上的猫，眼神平视着房间里的光影变化。"

        return {
            "label": label,
            "description": desc,
            "traits": traits,
            "portrait_description": portrait,
        }

    def _mock_spotify(self, metrics: dict) -> dict:
        event_score = metrics.get("event_score_total", 0)
        if event_score > 20:
            return {
                "mood_keywords": ["温暖", "轻快"],
                "playlist_name": "温暖时刻 · Observer Mix",
                "recommendation_reason": "这段时间的互动频率给人温暖的感觉，这些音乐或许能陪伴你度过此刻。",
                "suggested_genres": ["city pop", "upbeat", "indie pop"],
            }
        elif event_score > 0:
            return {
                "mood_keywords": ["平静", "反思"],
                "playlist_name": "静默潮汐 · Observer Mix",
                "recommendation_reason": "关系像平静的海面，偶尔的微风吹过也会泛起涟漪。",
                "suggested_genres": ["acoustic", "indie", "ambient"],
            }
        else:
            return {
                "mood_keywords": ["沉静", "独处"],
                "playlist_name": "深夜独白 · Observer Mix",
                "recommendation_reason": "有些情绪需要时间来沉淀，音乐是最好的陪伴者。",
                "suggested_genres": ["emo", "indie", "midnight jazz"],
            }



deepseek_client = DeepSeekClient()
