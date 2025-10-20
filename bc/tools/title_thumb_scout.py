"""
Tool: title_thumb_scout.py
Purpose: Suggests new titles and thumbnail ideas for each video using AWS Bedrock.
Structured output enforced (JSON schema) for cleaner downstream reports.
"""

from pathlib import Path
import json
import re
from bc.tools.shared_bedrock import generate_bedrock_response


# === PATHS ===
BASE_DIR = Path(__file__).resolve().parent.parent
ARTIFACTS = BASE_DIR / "outputs" / "artifacts"
SUGGESTIONS = BASE_DIR / "outputs" / "suggestions"
SUGGESTIONS.mkdir(parents=True, exist_ok=True)

# --- Clean only previous output for this tool (not full folder) ---
out_file = SUGGESTIONS / "titlethumb.json"
if out_file.exists():
    try:
        out_file.unlink()
        print("🧹 Cleaned old titlethumb.json")
    except Exception as e:
        print(f"⚠️ Could not remove old titlethumb.json: {e}")


# --- Helper: cleanup ---
def clean_text(txt: str) -> str:
    """Remove stray tags or markdown if model adds any."""
    txt = re.sub(r"<[^>]+>", "", txt)
    txt = txt.replace("```json", "").replace("```", "")
    txt = re.sub(r"\s+", " ", txt)
    return txt.strip()


# --- Core function ---
def title_thumb_scout():
    videos_file = ARTIFACTS / "videos.json"
    if not videos_file.exists():
        print(f"❌ No videos.json found at {videos_file}")
        return

    with open(videos_file, "r", encoding="utf-8") as f:
        videos = json.load(f)

    results = []

    for vid in videos:
        title = vid.get("title", "")
        transcript = vid.get("first60_text", "")
        if not transcript:
            print(f"⚠️ Skipping {title} (no transcript)")
            continue

        # ---------- Strict JSON Prompt ----------
        prompt = f"""
You are a professional YouTube strategist.

Analyze the following video snippet and propose optimized content ideas.

Video Title: {title}
Transcript Snippet: {transcript}

Respond ONLY in the following JSON structure:
{{
  "titles": [
    "Title 1",
    "Title 2",
    "Title 3"
  ],
  "thumbnails": [
    {{
      "concept": "Brief visual composition",
      "emotion": "Main emotion evoked",
      "contrast": "Key visual contrast or focal point"
    }},
    {{
      "concept": "...",
      "emotion": "...",
      "contrast": "..."
    }},
    {{
      "concept": "...",
      "emotion": "...",
      "contrast": "..."
    }}
  ]
}}
Ensure valid JSON — no explanations or markdown.
        """

        # ---------- Model Inference ----------
        raw_output = generate_bedrock_response(prompt, max_tokens=300)
        cleaned = clean_text(raw_output)

        # ---------- Parse JSON ----------
        try:
            ideas_json = json.loads(cleaned)
        except json.JSONDecodeError:
            print(f"⚠️ JSON decode failed for {title}, storing raw text.")
            ideas_json = {"titles": [], "thumbnails": [], "raw": cleaned}

        results.append({
            "video_id": vid["video_id"],
            "title": title,
            "ideas": ideas_json,
            "model": "AWS Bedrock – meta.llama3-8b-instruct-v1:0"
        })

        print(f"✅ Generated ideas for: {title}")

    # ---------- Save Output ----------
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"💾 Saved → {out_file}")


if __name__ == "__main__":
    title_thumb_scout()
