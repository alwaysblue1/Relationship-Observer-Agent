import json

from openai import AsyncOpenAI

from app.config import settings
from app.prompts.templates import PROMPTS


class DeepSeekClient:
    """Client for DeepSeek API with Observer prompt templates."""

    def __init__(self):
        self._client = AsyncOpenAI(
            api_key=settings.deepseek_api_key,
            base_url=settings.deepseek_base_url or "https://api.deepseek.com",
        )

    @property
    def client(self) -> AsyncOpenAI:
        return self._client

    @staticmethod
    def _format_patterns(patterns: list[dict] | None) -> str:
        if not patterns:
            return "暂无相似模式参考。"
        lines = []
        for i, p in enumerate(patterns):
            lines.append(f"{i+1}. {p['description']}")
            if p.get("observer_style_output"):
                for out in p["observer_style_output"]:
                    lines.append(f"   观察视角：{out}")
        return "\n".join(lines)

    async def generate_observer_report(self, metrics: dict, patterns: list[dict] | None = None) -> dict:
        prompt = PROMPTS["observer_report"].format(
            metrics=json.dumps(metrics, ensure_ascii=False, indent=2),
            retrieved_patterns=self._format_patterns(patterns),
        )
        return await self._call_json(prompt)

    async def generate_scoring(self, metrics: dict, patterns: list[dict] | None = None) -> dict:
        prompt = PROMPTS["scoring"].format(
            metrics=json.dumps(metrics, ensure_ascii=False, indent=2),
            retrieved_patterns=self._format_patterns(patterns),
        )
        return await self._call_json(prompt)

    async def generate_suggestions(self, metrics: dict, patterns: list[dict] | None = None) -> dict:
        prompt = PROMPTS["suggestion"].format(
            metrics=json.dumps(metrics, ensure_ascii=False, indent=2),
            retrieved_patterns=self._format_patterns(patterns),
        )
        return await self._call_json(prompt)

    async def generate_personality(self, metrics: dict, patterns: list[dict] | None = None) -> dict:
        prompt = PROMPTS["personality"].format(
            metrics=json.dumps(metrics, ensure_ascii=False, indent=2),
            retrieved_patterns=self._format_patterns(patterns),
        )
        return await self._call_json(prompt)

    async def generate_spotify_recommendation(self, metrics: dict, patterns: list[dict] | None = None) -> dict:
        variation_angle = metrics.pop("variation_angle", "深夜")
        variation_style = metrics.pop("variation_style", "indie")
        prompt = PROMPTS["spotify"].format(
            metrics=json.dumps(metrics, ensure_ascii=False, indent=2),
            retrieved_patterns=self._format_patterns(patterns),
            variation_angle=variation_angle,
            variation_style=variation_style,
        )
        return await self._call_json(prompt, temperature=1.0)

    async def _call_json(self, user_prompt: str, temperature: float = 0.7) -> dict:
        response = await self.client.chat.completions.create(
            model=settings.deepseek_model,
            messages=[
                {"role": "system", "content": PROMPTS["system"]},
                {"role": "user", "content": user_prompt},
            ],
            temperature=temperature,
            max_tokens=2000,
            response_format={"type": "json_object"},
        )
        content = response.choices[0].message.content
        return json.loads(content)


deepseek_client = DeepSeekClient()
