import os
import time
import random
import subprocess
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound

# Output directories
TRANSCRIPT_DIR = "bc/outputs/transcripts"
os.makedirs(TRANSCRIPT_DIR, exist_ok=True)


def get_transcript_text(video_id, max_retries=3):
    """
    🔹 Try to fetch transcript using YouTubeTranscriptApi.
    🔹 If it fails (no captions, or Too Many Requests), fallback to Whisper ASR.
    🔹 Returns transcript text (first 60s or 90s).
    """

    # Helper for retries
    def _fetch_with_retries(video_id):
        for i in range(max_retries):
            try:
                # --- Try fetching transcript via YouTubeTranscriptApi ---
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

    # Primary attempt: YouTube transcript
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
    except Exception as e:
        print(f"❌ YouTube transcript unavailable → switching to Whisper fallback for {video_id}")

    # --- Fallback: Whisper transcription of first 90 seconds ---
    try:
        print(f"🎧 Downloading audio for Whisper fallback ({video_id})...")
        audio_file = f"{video_id}.mp3"

        # Download 90 seconds audio using yt-dlp
        subprocess.run([
            "yt-dlp", "-x", "--audio-format", "mp3",
            "--max-filesize", "50M",
            "--postprocessor-args", "-ss 0 -t 90",
            "-o", audio_file,
            f"https://www.youtube.com/watch?v={video_id}"
        ], check=True)

        print(f"🎙️ Transcribing via Whisper (this may take a few minutes)...")

        # Use whisper CLI (if installed) to transcribe audio
        whisper_cmd = ["whisper", audio_file, "--language", "en", "--model", "base", "--output_dir", TRANSCRIPT_DIR]
        subprocess.run(whisper_cmd, check=True)

        # Get Whisper output
        whisper_out = os.path.join(TRANSCRIPT_DIR, f"{video_id}.txt")
        if os.path.exists(whisper_out):
            with open(whisper_out, "r", encoding="utf-8") as f:
                whisper_text = f.read().strip()
            print(f"✅ Whisper transcript saved: {whisper_out}")
            return whisper_text[:1000]  # Limit to ~60–90s worth of text
        else:
            print(f"⚠️ Whisper output not found for {video_id}")
            return None

    except subprocess.CalledProcessError as e:
        print(f"⚠️ Whisper fallback failed: {e}")
        return None
    except Exception as e:
        print(f"⚠️ Whisper unexpected error: {e}")
        return None
