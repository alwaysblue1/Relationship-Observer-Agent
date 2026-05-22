import httpx
import json
from typing import Optional

from app.config import settings


class SpotifyMCPService:
    """Integration with Spotify MCP for music recommendations."""

    def __init__(self):
        self.base_url = settings.spotify_mcp_url

    async def search_tracks(self, query: str, limit: int = 5) -> list[dict]:
        if not self.base_url:
            return self._mock_tracks(query, limit)

        async with httpx.AsyncClient() as client:
            try:
                resp = await client.get(
                    f"{self.base_url}/search",
                    params={"q": query, "type": "track", "limit": limit},
                    timeout=10,
                )
                if resp.status_code == 200:
                    data = resp.json()
                    return data.get("tracks", {}).get("items", [])
            except Exception:
                pass
        return self._mock_tracks(query, limit)

    async def create_playlist(self, name: str, track_uris: list[str]) -> Optional[dict]:
        if not self.base_url:
            return {"id": "mock_playlist", "name": name, "uri": "spotify:playlist:mock", "tracks": track_uris}

        async with httpx.AsyncClient() as client:
            try:
                resp = await client.post(
                    f"{self.base_url}/playlists",
                    json={"name": name, "track_uris": track_uris},
                    timeout=10,
                )
                if resp.status_code == 200:
                    return resp.json()
            except Exception:
                pass
        return None

    async def get_recommendations(self, genres: list[str], mood_keywords: list[str]) -> list[dict]:
        if not self.base_url:
            return []

        async with httpx.AsyncClient() as client:
            try:
                resp = await client.post(
                    f"{self.base_url}/recommendations",
                    json={"genres": genres, "mood": mood_keywords},
                    timeout=10,
                )
                if resp.status_code == 200:
                    return resp.json().get("tracks", [])
            except Exception:
                pass
        return []

    @staticmethod
    def _mock_tracks(query: str, limit: int) -> list[dict]:
        mock_library = {
            "emo": [
                {"name": "Welcome to the Black Parade", "artist": "My Chemical Romance", "uri": "spotify:track:mock1"},
                {"name": "Numb", "artist": "Linkin Park", "uri": "spotify:track:mock2"},
                {"name": "Helena", "artist": "My Chemical Romance", "uri": "spotify:track:mock3"},
            ],
            "indie": [
                {"name": "Skinny Love", "artist": "Bon Iver", "uri": "spotify:track:mock4"},
                {"name": "Holocene", "artist": "Bon Iver", "uri": "spotify:track:mock5"},
            ],
            "acoustic": [
                {"name": "Fix You", "artist": "Coldplay", "uri": "spotify:track:mock6"},
                {"name": "Let Her Go", "artist": "Passenger", "uri": "spotify:track:mock7"},
            ],
            "upbeat": [
                {"name": "Plastic Love", "artist": "Mariya Takeuchi", "uri": "spotify:track:mock8"},
                {"name": "Stay With Me", "artist": "Miki Matsubara", "uri": "spotify:track:mock9"},
            ],
        }
        for key, tracks in mock_library.items():
            if key in query.lower():
                return tracks[:limit]
        return [
            {"name": "Sample Track", "artist": "Sample Artist", "uri": "spotify:track:mock0"}
        ][:limit]


spotify_service = SpotifyMCPService()
