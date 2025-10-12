import os
import datetime as dt
from dotenv import load_dotenv
from googleapiclient.discovery import build

load_dotenv()
API_KEY = os.getenv("YT_API_KEY")

# ---------- internal helpers ----------

def _youtube():
    if not API_KEY:
        raise RuntimeError("YOUTUBE_API_KEY missing in .env")
    return build("youtube", "v3", developerKey=API_KEY)

def _channel_uploads_playlist_id(channel_id: str) -> str:
    yt = _youtube()
    r = yt.channels().list(part="contentDetails", id=channel_id).execute()
    items = r.get("items", [])
    if not items:
        raise ValueError("Channel not found or contentDetails unavailable")
    return items[0]["contentDetails"]["relatedPlaylists"]["uploads"]

def _list_all_uploads(playlist_id: str, max_pages: int = 200):
    """Return list of {video_id, title, publishedAt} for *all* uploads (up to max_pages)."""
    yt = _youtube()
    token = None
    out = []
    pages = 0
    while True:
        r = yt.playlistItems().list(
            part="contentDetails,snippet",
            playlistId=playlist_id,
            maxResults=50,
            pageToken=token
        ).execute()
        for it in r.get("items", []):
            out.append({
                "video_id": it["contentDetails"]["videoId"],
                "title": it["snippet"]["title"],
                "publishedAt": it["contentDetails"]["videoPublishedAt"],
            })
        token = r.get("nextPageToken")
        pages += 1
        if not token or pages >= max_pages:
            break
    return out

def _iso_to_date(s: str) -> dt.date:
    try:
        return dt.datetime.fromisoformat(s.replace("Z", "+00:00")).date()
    except Exception:
        return dt.datetime.strptime(s[:10], "%Y-%m-%d").date()

def _chunk(ids, n=50):
    for i in range(0, len(ids), n):
        yield ids[i:i+n]

def _attach_stats(videos):
    """Add viewCount & commentCount to each video."""
    yt = _youtube()
    id_to_video = {v["video_id"]: v for v in videos}
    for chunk in _chunk(list(id_to_video.keys()), 50):
        r = yt.videos().list(part="statistics", id=",".join(chunk)).execute()
        for it in r.get("items", []):
            v = id_to_video.get(it["id"])
            stats = it.get("statistics", {})
            if v is not None:
                v["viewCount"] = int(stats.get("viewCount", 0))
                v["commentCount"] = int(stats.get("commentCount", 0))
    return list(id_to_video.values())

# ---------- public API ----------

def select_backcatalog_candidates(channel_id: str, age_days_min: int = 180, pool_size: int = 100, limit: int = 5):
    """
    Returns top 'limit' revival candidates (list of dicts):
    fields: video_id, title, publishedAt, age_days, views_per_day, comments_per_1k, selection_score
    """
    uploads_pl = _channel_uploads_playlist_id(channel_id)
    uploads = _list_all_uploads(uploads_pl, max_pages=200)

    today = dt.date.today()
    # filter by age
    aged = []
    for v in uploads:
        d = _iso_to_date(v["publishedAt"])
        age_days = max(1, (today - d).days)
        if age_days >= age_days_min:
            v = dict(v)  # copy
            v["age_days"] = age_days
            aged.append(v)

    if not aged:
        return []

    # keep only oldest 'pool_size'
    aged.sort(key=lambda x: x["age_days"], reverse=True)
    pool = aged[:pool_size]

    # attach stats
    pool = _attach_stats(pool)

    # compute signals
    vpd_vals = []
    for v in pool:
        views = v.get("viewCount", 0)
        comments = v.get("commentCount", 0)
        age_days = v["age_days"]
        v["views_per_day"] = views / age_days
        v["comments_per_1k"] = (comments / views * 1000) if views > 0 else 0.0
        if v["views_per_day"] > 0:
            vpd_vals.append(v["views_per_day"])

    # channel median velocity (from pool)
    vpd_vals.sort()
    median_vpd = vpd_vals[len(vpd_vals)//2] if vpd_vals else 0.0

    # scoring: older + under median velocity + decent comments density
    def score(v):
        age_score = min(1.0, v["age_days"] / 365.0)          # cap at 1 year
        under_vel = 1.0 if v["views_per_day"] < median_vpd else 0.3
        engagement = min(1.0, v["comments_per_1k"] / 2.0)    # 2 comments per 1k views ≈ good
        return 0.4*age_score + 0.4*under_vel + 0.2*engagement

    for v in pool:
        v["selection_score"] = round(score(v), 3)

    ranked = sorted(pool, key=lambda x: x["selection_score"], reverse=True)
    top = ranked[:limit]

    # drop heavy stats we don’t need beyond selection (optional)
    for v in top:
        v.pop("viewCount", None)
        v.pop("commentCount", None)

    return top
