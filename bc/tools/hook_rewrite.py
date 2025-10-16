"""
Tool: hook_rewrite.py
Purpose: Rewrites the hook zone (first 60–90s transcript) using AWS Bedrock.
Structured output enforced (JSON schema) for consistent downstream reporting.
"""

from pathlib import Path
import json
import re
from bc.tools.shared_bedrock import generate_bedrock_response


# === PATHS ===
BASE_DIR = Path(__file__).resolve().parent.parent
ARTIFACTS = BASE_DIR / "outputs" / "artifacts"
OUT_PATH = BASE_DIR / "outputs" / "suggestions"
OUT_PATH.mkdir(parents=True, exist_ok=True)

# --- Clean previous outputs ---
for file in OUT_PATH.glob("*"):  # or SUGGESTIONS.glob("*")
    try:
        file.unlink()
    except Exception:
        pass


# --- Helper: cleanup ---
def clean_text(txt: str) -> str:
    """Clean HTML or Markdown noise from model output."""
    txt = txt.replace("```json", "").replace("```", "")
    txt = re.sub(r"<[^>]+>", "", txt)
    txt = re.sub(r"\s+", " ", txt)
    return txt.strip()


# === HOOK REWRITE LOGIC ===
def hook_rewrite():
    videos_file = ARTIFACTS / "videos.json"
    if not videos_file.exists():
        print(f"❌ No videos.json found at {videos_file}")
        return

    with open(videos_file, "r", encoding="utf-8") as f:
        videos = json.load(f)

    rewrites = []
    print("✍️ Starting hook rewrite process...")

    for vid in videos:
        title = vid.get("title", "")
        transcript = vid.get("first60_text", "")
        if not transcript:
            print(f"⚠️ Skipping {title} (no transcript)")
            continue

        # ---------- Structured Prompt ----------
        prompt = f"""
You are a professional YouTube script editor specialized in audience retention.

Task:
Rewrite the first 60–90 seconds of a YouTube video (the "hook zone") to make it clearer, emotionally engaging, and curiosity-driven.

Guidelines:
- Keep the rewritten text conversational, natural, and hook-focused.
- Start with a punchy opener (a surprising fact, question, or bold statement).
- Maintain accuracy and avoid robotic tone.
- Keep length under 180 words.
- Return ONLY JSON — no explanations.

Video Title: {title}
Transcript: {transcript}

Respond ONLY in this JSON format:
{{
  "rewritten_script": "Your improved version only",
  "style_notes": [
    "Short note 1",
    "Short note 2"
  ]
}}
        """

        # ---------- Model Inference ----------
        raw_output = generate_bedrock_response(prompt, max_tokens=300)
        cleaned = clean_text(raw_output)

        # ---------- Parse JSON ----------
        try:
            parsed = json.loads(cleaned)
        except json.JSONDecodeError:
            print(f"⚠️ JSON decode failed for {title}, saving raw output.")
            parsed = {
                "rewritten_script": cleaned,
                "style_notes": ["(Unstructured output)"]
            }

        rewrites.append({
            "video_id": vid["video_id"],
            "title": title,
            "rewritten_script": parsed.get("rewritten_script", ""),
            "style_notes": parsed.get("style_notes", []),
            "model": "AWS Bedrock – meta.llama3-8b-instruct-v1:0"
        })

        print(f"✅ Rewritten: {title}")

    out_file = OUT_PATH / "hook_rewrites.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(rewrites, f, indent=2, ensure_ascii=False)

    print(f"💾 Saved rewrites → {out_file}")


if __name__ == "__main__":
    hook_rewrite()
