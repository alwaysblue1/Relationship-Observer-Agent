import httpx
import random
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
                {"name": "I Miss You", "artist": "Blink-182", "uri": "spotify:track:mock10"},
                {"name": "Ohio Is for Lovers", "artist": "Hawthorne Heights", "uri": "spotify:track:mock11"},
            ],
            "indie": [
                {"name": "Skinny Love", "artist": "Bon Iver", "uri": "spotify:track:mock4"},
                {"name": "Holocene", "artist": "Bon Iver", "uri": "spotify:track:mock5"},
                {"name": "Chicago", "artist": "Sufjan Stevens", "uri": "spotify:track:mock12"},
                {"name": "Two Weeks", "artist": "Grizzly Bear", "uri": "spotify:track:mock13"},
                {"name": "1904", "artist": "The Tallest Man on Earth", "uri": "spotify:track:mock14"},
            ],
            "acoustic": [
                {"name": "Fix You", "artist": "Coldplay", "uri": "spotify:track:mock6"},
                {"name": "Let Her Go", "artist": "Passenger", "uri": "spotify:track:mock7"},
                {"name": "Banana Pancakes", "artist": "Jack Johnson", "uri": "spotify:track:mock15"},
                {"name": "Better Together", "artist": "Jack Johnson", "uri": "spotify:track:mock16"},
            ],
            "upbeat": [
                {"name": "Plastic Love", "artist": "Mariya Takeuchi", "uri": "spotify:track:mock8"},
                {"name": "Stay With Me", "artist": "Miki Matsubara", "uri": "spotify:track:mock9"},
                {"name": "Dance the Night", "artist": "Dua Lipa", "uri": "spotify:track:mock17"},
                {"name": "Levitating", "artist": "Dua Lipa", "uri": "spotify:track:mock18"},
            ],
            "city pop": [
                {"name": "Plastic Love", "artist": "Mariya Takeuchi", "uri": "spotify:track:mock8"},
                {"name": "Stay With Me", "artist": "Miki Matsubara", "uri": "spotify:track:mock9"},
                {"name": "4:00 AM", "artist": "Taeko Onuki", "uri": "spotify:track:mock19"},
            ],
            "ambient": [
                {"name": "Weightless", "artist": "Marconi Union", "uri": "spotify:track:mock20"},
                {"name": "An Ending", "artist": "Brian Eno", "uri": "spotify:track:mock21"},
            ],
            "jazz": [
                {"name": "My Funny Valentine", "artist": "Chet Baker", "uri": "spotify:track:mock22"},
                {"name": "Misty", "artist": "Erroll Garner", "uri": "spotify:track:mock23"},
            ],
            "dance": [
                {"name": "Blinding Lights", "artist": "The Weeknd", "uri": "spotify:track:mock24"},
                {"name": "Get Lucky", "artist": "Daft Punk", "uri": "spotify:track:mock25"},
            ],
            "pop": [
                {"name": "Flowers", "artist": "Miley Cyrus", "uri": "spotify:track:mock26"},
                {"name": "Shape of You", "artist": "Ed Sheeran", "uri": "spotify:track:mock27"},
                {"name": "Good 4 U", "artist": "Olivia Rodrigo", "uri": "spotify:track:mock28"},
            ],
            "folk": [
                {"name": "The Night We Met", "artist": "Lord Huron", "uri": "spotify:track:mock29"},
                {"name": "Rivers and Roads", "artist": "The Head and the Heart", "uri": "spotify:track:mock30"},
            ],
        }
        for key, tracks in mock_library.items():
            if key in query.lower():
                return random.sample(tracks, min(limit, len(tracks)))
        all_tracks = [t for tracks in mock_library.values() for t in tracks]
        return random.sample(all_tracks, min(limit, len(all_tracks)))


spotify_service = SpotifyMCPService()
