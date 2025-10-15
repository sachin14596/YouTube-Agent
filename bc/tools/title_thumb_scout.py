"""
Tool: title_thumb_scout.py
Purpose: Suggests new titles and thumbnail ideas for each video using shared global LLM.
"""

from pathlib import Path
import json
import re
from bc.tools.shared_model import model, tokenizer, device, MODEL_NAME


# === PATHS ===
BASE_DIR = Path(__file__).resolve().parent.parent
ARTIFACTS = BASE_DIR / "outputs" / "artifacts"
SUGGESTIONS = BASE_DIR / "outputs" / "suggestions"
SUGGESTIONS.mkdir(parents=True, exist_ok=True)


# --- Helper: cleanup function ---
def clean_text(txt: str) -> str:
    txt = re.sub(r"<[^>]+>", "", txt)  # remove HTML
    txt = re.sub(r"(?i)(video title|transcript|suggest|output).*?:", "", txt)
    txt = re.sub(r"\s+", " ", txt)
    return txt.strip()


# === TITLE + THUMBNAIL GENERATOR ===
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

        prompt = (
            f"You are an expert YouTube strategist.\n"
            f"Generate exactly 3 creative, high-performing video titles and 3 thumbnail ideas "
            f"for this video.\n\n"
            f"Title: {title}\n\n"
            f"Transcript snippet:\n{transcript}\n\n"
            f"Respond in clean structured text only (no instructions or explanations)."
        )

        inputs = tokenizer(prompt, return_tensors="pt").to(device)
        outputs = model.generate(**inputs, max_new_tokens=300)
        ideas = tokenizer.decode(outputs[0], skip_special_tokens=True)

        cleaned = clean_text(ideas)

        results.append({
            "video_id": vid["video_id"],
            "title": title,
            "ideas": cleaned,
            "model": MODEL_NAME
        })

        print(f"✅ Generated ideas for: {title}")

    out_file = SUGGESTIONS / "titlethumb.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"💾 Saved → {out_file}")


if __name__ == "__main__":
    title_thumb_scout()
