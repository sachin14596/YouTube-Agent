import os
import time
import random
import subprocess
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound

# Output directories
TRANSCRIPT_DIR = "bc/outputs/transcripts"
os.makedirs(TRANSCRIPT_DIR, exist_ok=True)


# === Helper: robust audio downloader with fallbacks ===
def download_audio_with_fallback(video_id):
    """
    Attempts to download the first 90 seconds of audio using yt-dlp.
    Retries with different user agents and optional cookies if needed.
    """
    url = f"https://www.youtube.com/watch?v={video_id}"
    output = f"{video_id}.mp3"

    user_agents = [
        # desktop
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
        # android mobile
        "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0 Mobile Safari/537.36",
        # ios safari
        "Mozilla/5.0 (iPhone; CPU iPhone OS 16_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.2 Mobile Safari/604.1",
    ]

    for ua in user_agents:
        try:
            print(f"🎧 Trying download with UA: {ua.split('(')[0].strip()}...")
            cmd = [
                "yt-dlp",
                "--no-warnings",
                "-x", "--audio-format", "mp3",
                "--max-filesize", "50M",
                "--postprocessor-args", "-ss 0 -t 90",
                "--user-agent", ua,
                "-o", output,
                url,
            ]

            # If user has cookies.txt file, use it
            if os.path.exists("cookies.txt"):
                cmd[1:1] = ["--cookies", "cookies.txt"]

            subprocess.run(cmd, check=True)

            if os.path.exists(output):
                print(f"✅ Download succeeded with {ua[:25]}...")
                return output

        except subprocess.CalledProcessError as e:
            print(f"⚠️ Attempt failed with user-agent: {ua[:40]}... ({e})")

    print("❌ All user-agents failed; YouTube may require login or region cookies.")
    return None


def get_transcript_text(video_id, max_retries=3):
    """
    🔹 Try to fetch transcript using YouTubeTranscriptApi.
    🔹 If it fails, fallback to Whisper ASR via yt-dlp audio.
    🔹 Returns transcript text (first 60–90 seconds).
    """

    def _fetch_with_retries(video_id):
        for i in range(max_retries):
            try:
                transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=["en"])
                lines = [seg["text"].strip() for seg in transcript if seg.get("text")]
                return " ".join(lines)
            except (TranscriptsDisabled, NoTranscriptFound):
                raise
            except Exception as e:
                wait = (2 ** i) + random.uniform(0, 1)
                print(f"⚠️ Attempt {i+1} failed ({e}) — retrying in {wait:.1f}s")
                time.sleep(wait)
        return None

    # --- Primary: YouTube captions ---
    try:
        transcript_text = _fetch_with_retries(video_id)
        if transcript_text:
            save_path = os.path.join(TRANSCRIPT_DIR, f"{video_id}.txt")
            with open(save_path, "w", encoding="utf-8") as f:
                f.write(transcript_text)
            print(f"✅ YouTube transcript saved: {save_path}")
            return transcript_text
        else:
            print(f"❌ YouTube transcript unavailable → switching to Whisper fallback for {video_id}")
    except Exception:
        print(f"❌ YouTube transcript unavailable → switching to Whisper fallback for {video_id}")

    # --- Fallback: Whisper ASR ---
    try:
        print(f"🎧 Downloading audio for Whisper fallback ({video_id})...")
        audio_file = download_audio_with_fallback(video_id)
        if not audio_file:
            print(f"⚠️ Audio download failed for {video_id}.")
            return None

        print(f"🎙️ Transcribing via Whisper (this may take a few minutes)...")
        whisper_cmd = [
            "whisper", audio_file,
            "--language", "en",
            "--model", "base",
            "--output_dir", TRANSCRIPT_DIR
        ]
        subprocess.run(whisper_cmd, check=True)

        whisper_out = os.path.join(TRANSCRIPT_DIR, f"{video_id}.txt")
        if os.path.exists(whisper_out):
            with open(whisper_out, "r", encoding="utf-8") as f:
                whisper_text = f.read().strip()
            print(f"✅ Whisper transcript saved: {whisper_out}")
            return whisper_text[:1000]
        else:
            print(f"⚠️ Whisper output not found for {video_id}")
            return None

    except subprocess.CalledProcessError as e:
        print(f"⚠️ Whisper fallback failed: {e}")
        return None
    except Exception as e:
        print(f"⚠️ Whisper unexpected error: {e}")
        return None
