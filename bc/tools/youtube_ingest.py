import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("YT_API_KEY")

YOUTUBE_API_BASE = "https://www.googleapis.com/youtube/v3"

def get_channel_videos(channel_id: str, max_results: int = 10):
    """Fetches public videos from a channel using API key (no OAuth)."""

    # Step 1: Get uploads playlist ID
    channel_url = f"{YOUTUBE_API_BASE}/channels"
    channel_params = {
        "part": "contentDetails",
        "id": channel_id,
        "key": API_KEY
    }
    channel_resp = requests.get(channel_url, params=channel_params).json()
    if not channel_resp.get("items"):
        raise ValueError("Invalid channel ID or API error")

    uploads_playlist_id = channel_resp["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]

    # Step 2: Fetch videos from uploads playlist
    playlist_url = f"{YOUTUBE_API_BASE}/playlistItems"
    playlist_params = {
        "part": "snippet,contentDetails",
        "playlistId": uploads_playlist_id,
        "maxResults": max_results,
        "key": API_KEY
    }
    playlist_resp = requests.get(playlist_url, params=playlist_params).json()

    videos = []
    for item in playlist_resp.get("items", []):
        video_id = item["contentDetails"]["videoId"]
        title = item["snippet"]["title"]
        published_at = item["contentDetails"]["videoPublishedAt"]
        videos.append({
            "video_id": video_id,
            "title": title,
            "publishedAt": published_at
        })

    return videos


def save_videos(videos, out_path="bc/outputs/artifacts/videos.json"):
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(videos, f, indent=2)
    print(f"✅ Saved {len(videos)} videos → {out_path}")


if __name__ == "__main__":
    test_channel = "UCX6OQ3DkcsbYNE6H8uQQuVA"  # MrBeast example
    vids = get_channel_videos(test_channel, max_results=5)
    save_videos(vids)
