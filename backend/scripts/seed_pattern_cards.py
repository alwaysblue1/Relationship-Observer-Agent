"""Seed pattern_cards table from pattern_cards.json with embeddings.

Usage:
    cd backend
    python -m scripts.seed_pattern_cards

Modes:
    Online:  if BAILIAN_API_KEY is set, calls Aliyun DashScope text-embedding-v4 API.
    Offline: if BAILIAN_API_KEY is not set, loads precomputed embeddings from
             app/data/precomputed_embeddings.json (1024-dim vectors exported from
             a previously seeded database).

Idempotent: skips cards where pattern_name already exists with an embedding.
"""

import asyncio
import json
import sys
from pathlib import Path

import httpx
from sqlalchemy import text

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import settings
from app.database import async_session, engine
from app.models.pattern import PatternCard


async def get_embedding_online(client: httpx.AsyncClient, text: str) -> list[float] | None:
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
            print(f"  Embedding API returned {resp.status_code}: {resp.text[:200]}")
            return None
        data = resp.json()
        embeddings = data.get("output", {}).get("embeddings", [])
        if embeddings:
            return embeddings[0].get("embedding")
        return None
    except Exception as e:
        print(f"  Embedding request failed: {e}")
        return None


def load_precomputed_embeddings() -> dict[str, list[float]]:
    path = Path(__file__).resolve().parent.parent / "app" / "data" / "precomputed_embeddings.json"
    if not path.exists():
        print(f"  Precomputed embeddings not found at {path}")
        return {}
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    print(f"Loaded {len(data)} precomputed embeddings (offline mode)")
    return data


async def seed():
    cards_path = Path(__file__).resolve().parent.parent / "app" / "data" / "pattern_cards.json"
    with open(cards_path, "r", encoding="utf-8") as f:
        cards = json.load(f)

    print(f"Loaded {len(cards)} pattern cards from {cards_path}")

    # Determine mode
    use_api = bool(settings.bailian_api_key)
    if use_api:
        print(f"Mode: ONLINE (calling Aliyun embedding API)")
    else:
        print("Mode: OFFLINE (using precomputed embeddings)")

    precomputed = {} if use_api else load_precomputed_embeddings()
    if not use_api and not precomputed:
        print("No precomputed embeddings and no API key. Cannot seed. Aborting.")
        return

    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await conn.run_sync(PatternCard.metadata.create_all)

    client = httpx.AsyncClient(timeout=60) if use_api else None

    try:
        async with async_session() as db:
            inserted = 0
            skipped = 0
            failed = 0

            for i, card in enumerate(cards):
                name = card["pattern_name"]
                print(f"[{i+1}/{len(cards)}] {name} ...", end=" ", flush=True)

                # Check if already seeded
                existing = await db.execute(
                    text("SELECT 1 FROM pattern_cards WHERE pattern_name = :name AND embedding IS NOT NULL"),
                    {"name": name},
                )
                if existing.first():
                    print("skip (exists)")
                    skipped += 1
                    continue

                # Get embedding
                if use_api:
                    embedding = await get_embedding_online(client, card["description"])
                else:
                    embedding = precomputed.get(name)

                if embedding is None:
                    print("FAILED (no embedding)")
                    failed += 1
                    continue

                row = PatternCard(
                    pattern_name=name,
                    category=card["category"],
                    description=card["description"],
                    signals=card.get("signals", []),
                    metrics=card.get("metrics", {}),
                    observer_style_output=card.get("observer_style_output", []),
                    embedding=embedding,
                    source="seeded",
                )
                db.add(row)
                await db.commit()
                print(f"OK (dim={len(embedding)})")
                inserted += 1

        print(f"\nDone: {inserted} inserted, {skipped} skipped, {failed} failed")

        if inserted > 0 or skipped > 0:
            print("Creating IVFFlat index ...")
            async with engine.begin() as conn:
                await conn.execute(text(
                    "CREATE INDEX IF NOT EXISTS idx_pattern_embedding ON pattern_cards "
                    "USING ivfflat (embedding vector_cosine_ops) WITH (lists = 20)"
                ))
            print("Index ready.")

    finally:
        if client:
            await client.aclose()


if __name__ == "__main__":
    asyncio.run(seed())
