import asyncio

import httpx

from app.config import settings


class BailianImageService:
    """Generate images via Alibaba Bailian (DashScope / wanx-v1)."""

    BASE_URL = "https://dashscope.aliyuncs.com/api/v1"

    async def generate_image(self, prompt: str) -> str | None:
        full_prompt = f"{prompt}，拟人化的小动物，风格简单，抽象，卡通"
        if not settings.bailian_api_key:
            return None

        async with httpx.AsyncClient(timeout=30) as client:
            try:
                resp = await client.post(
                    f"{self.BASE_URL}/services/aigc/text2image/image-synthesis",
                    headers={
                        "Authorization": f"Bearer {settings.bailian_api_key}",
                        "Content-Type": "application/json",
                        "X-DashScope-Async": "enable",
                    },
                    json={
                        "model": "wanx-v1",
                        "input": {"prompt": full_prompt},
                        "parameters": {
                            "n": 1,
                            "size": "1024*1024",
                        },
                    },
                )
                if resp.status_code != 200:
                    return None
                data = resp.json()
                task_id = data.get("output", {}).get("task_id")
                if not task_id:
                    return None
            except Exception:
                return None

            for _ in range(30):
                await asyncio.sleep(2)
                try:
                    resp = await client.get(
                        f"{self.BASE_URL}/tasks/{task_id}",
                        headers={"Authorization": f"Bearer {settings.bailian_api_key}"},
                    )
                    if resp.status_code != 200:
                        continue
                    data = resp.json()
                    status = data.get("output", {}).get("task_status")
                    if status == "SUCCEEDED":
                        results = data.get("output", {}).get("results", [])
                        if results:
                            return results[0].get("url")
                        return None
                    if status == "FAILED":
                        return None
                except Exception:
                    continue

            return None


class BailianEmbeddingService:
    """Text embeddings via Aliyun DashScope text-embedding-v4."""

    async def embed(self, text: str) -> list[float] | None:
        if not settings.bailian_api_key:
            return None

        async with httpx.AsyncClient(timeout=30) as client:
            try:
                resp = await client.post(
                    settings.aliyun_embedding_url,
                    headers={
                        "Authorization": f"Bearer {settings.bailian_api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": settings.aliyun_embedding_model,
                        "input": {"texts": [text]},
                    },
                )
                if resp.status_code != 200:
                    return None
                data = resp.json()
                embeddings = data.get("output", {}).get("embeddings", [])
                if embeddings:
                    return embeddings[0].get("embedding")
                return None
            except Exception:
                return None

    async def embed_batch(self, texts: list[str]) -> list[list[float] | None]:
        results = []
        for text in texts:
            results.append(await self.embed(text))
        return results


bailian_image_service = BailianImageService()
bailian_embedding_service = BailianEmbeddingService()
