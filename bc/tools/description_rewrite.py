"""
Tool: description_rewrite.py
Purpose: Rewrites YouTube descriptions for SEO and clarity.
"""

from pathlib import Path
import json
import re
from bc.tools.shared_bedrock import generate_bedrock_response


BASE_DIR = Path(__file__).resolve().parent.parent
ARTIFACTS = BASE_DIR / "outputs" / "artifacts"
SUGGESTIONS = BASE_DIR / "outputs" / "suggestions"
SUGGESTIONS.mkdir(parents=True, exist_ok=True)

for file in SUGGESTIONS.glob("description_*.json"):
    try:
        file.unlink()
    except Exception:
        pass


def clean_text(txt: str) -> str:
    txt = txt.replace("```json", "").replace("```", "")
    txt = re.sub(r"<[^>]+>", "", txt)
    txt = re.sub(r"\s+", " ", txt)
    return txt.strip()


def extract_json_segment(text: str) -> str:
    """Extract JSON object even if model surrounds it with text."""
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        return match.group(0)
    return text


def description_rewrite():
    videos_file = ARTIFACTS / "videos.json"
    if not videos_file.exists():
        print(f"❌ No videos.json found at {videos_file}")
        return

    with open(videos_file, "r", encoding="utf-8") as f:
        videos = json.load(f)

    results = []
    print("✍️ Starting description rewrite process...")

    for vid in videos:
        title = vid.get("title", "")
        description = vid.get("description", "")
        transcript = vid.get("first60_text", "")
        if not description:
            print(f"⚠️ Skipping {title} (no description found in metadata)")
            continue

        prompt = f"""
You are a YouTube SEO strategist and copywriter.

Task: Rewrite the following video description to improve discoverability,
engagement, and conversions while keeping the tone natural and factual.

Guidelines:
- The first 2 lines should hook the viewer (for CTR in search previews).
- Include relevant keywords naturally.
- Keep under 180 words total.
- Maintain brand voice; avoid clickbait.
- Add 1 call-to-action (subscribe / link / next video) if missing.

Input:
Title: {title}
Transcript (context snippet): {transcript}
Current Description: {description}

Respond ONLY in valid JSON:
{{
  "improved_description": "Rewritten SEO-optimized description (≤180 words)",
  "improvement_notes": [
    "Note 1",
    "Note 2",
    "Note 3"
  ]
}}
Ensure JSON validity, no markdown, no commentary.
        """

        raw_output = generate_bedrock_response(prompt, max_tokens=400)
        cleaned = clean_text(raw_output)
        extracted = extract_json_segment(cleaned)

        try:
            parsed = json.loads(extracted)
        except json.JSONDecodeError:
            print(f"⚠️ JSON decode failed for {title}, saving raw text.")
            parsed = {
                "improved_description": cleaned,
                "improvement_notes": ["(Unstructured output)"],
            }

        results.append({
            "video_id": vid["video_id"],
            "title": title,
            "improved_description": parsed.get("improved_description", ""),
            "improvement_notes": parsed.get("improvement_notes", []),
            "model": "AWS Bedrock – meta.llama3-8b-instruct-v1:0"
        })

        print(f"✅ Rewritten description: {title}")

    out_file = SUGGESTIONS / "description_rewrites.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"💾 Saved → {out_file}")


if __name__ == "__main__":
    description_rewrite()
