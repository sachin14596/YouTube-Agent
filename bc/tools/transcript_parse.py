import time
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound

def get_transcript(video_id: str, lang="en", retries=3, delay=10):
    for attempt in range(retries):
        try:
            return YouTubeTranscriptApi.get_transcript(video_id, languages=[lang, "en-GB"])
        except (TranscriptsDisabled, NoTranscriptFound) as e:
            print(f"⚠️ No transcript for {video_id}: {e}")
            return None
        except Exception as e:
            print(f"⚠️ Attempt {attempt+1} failed for {video_id}: {e}")
            if attempt < retries - 1:
                time.sleep(delay)  # wait before retry
            else:
                return None

def get_first_60s_text(transcript):
    if not transcript:
        return None
    first_minute = [t["text"] for t in transcript if t["start"] <= 60]
    return " ".join(first_minute) if first_minute else None
