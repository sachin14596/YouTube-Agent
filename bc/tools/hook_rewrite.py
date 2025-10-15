"""
Tool: hook_rewrite.py
Purpose: Rewrites the hook zone (first 60–90s transcript) using a shared global LLM model.
"""

from pathlib import Path
import json
import re
from bc.tools.shared_model import model, tokenizer, device, MODEL_NAME


# === PATHS ===
BASE_DIR = Path(__file__).resolve().parent.parent
ARTIFACTS = BASE_DIR / "outputs" / "artifacts"
OUT_PATH = BASE_DIR / "outputs" / "suggestions"
OUT_PATH.mkdir(parents=True, exist_ok=True)


# --- Helper: cleanup function ---
def clean_text(txt: str) -> str:
    txt = re.sub(r"<[^>]+>", "", txt)  # remove HTML tags
    txt = re.sub(r"(?i)(transcript|rewrite|title|output).*?:", "", txt)  # remove prompt headers
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

        prompt = (
            f"Rewrite the following YouTube intro to make it more engaging, clear, and curiosity-driven.\n\n"
            f"Title: {title}\n\n"
            f"Transcript:\n{transcript}\n\n"
            f"---\nOutput only the improved rewritten version — do not include any instructions or explanations."
        )

        inputs = tokenizer(prompt, return_tensors="pt").to(device)
        outputs = model.generate(**inputs, max_new_tokens=300)
        rewritten_text = tokenizer.decode(outputs[0], skip_special_tokens=True)

        cleaned = clean_text(rewritten_text)

        rewrites.append({
            "video_id": vid["video_id"],
            "title": title,
            "rewritten_script": cleaned,
            "model": MODEL_NAME
        })

        print(f"✅ Rewritten: {title}")

    out_file = OUT_PATH / "hook_rewrites.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(rewrites, f, indent=2, ensure_ascii=False)

    print(f"💾 Saved rewrites → {out_file}")


if __name__ == "__main__":
    hook_rewrite()
