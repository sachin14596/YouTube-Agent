"""
Tool: policy_guard.py
Purpose: Basic content safety & advertiser-friendliness check using shared global LLM.
"""

from pathlib import Path
import json
from bc.tools.shared_model import model, tokenizer, device, MODEL_NAME


# === PATHS ===
BASE_DIR = Path(__file__).resolve().parent.parent
SUGGESTIONS = BASE_DIR / "outputs" / "suggestions"
SUGGESTIONS.mkdir(parents=True, exist_ok=True)

# === BASIC RISKY WORD LIST ===
RISKY_WORDS = [
    "violence", "blood", "drugs", "weapon", "hate", "suicide",
    "terror", "sex", "nude", "gambling", "death", "kill", "gun"
]


def policy_guard():
    rewrites_file = SUGGESTIONS / "hook_rewrites.json"
    if not rewrites_file.exists():
        print(f"❌ No rewrites found at {rewrites_file}")
        return

    with open(rewrites_file, "r", encoding="utf-8") as f:
        rewrites = json.load(f)

    checks = []
    for item in rewrites:
        title = item.get("title", "")
        text = item.get("rewritten_script", "")
        flags = [w for w in RISKY_WORDS if w.lower() in text.lower()]

        if flags:
            prompt = (
                f"Text flagged for potential advertiser-unsafe content:\n\n{text}\n\n"
                f"Flagged words: {', '.join(flags)}\n\n"
                f"Rewrite this text to keep the same meaning but make it advertiser-friendly."
            )
            inputs = tokenizer(prompt, return_tensors="pt").to(device)
            outputs = model.generate(**inputs, max_new_tokens=200)
            safe_version = tokenizer.decode(outputs[0], skip_special_tokens=True)
        else:
            safe_version = text

        checks.append({
            "video_id": item["video_id"],
            "title": title,
            "flagged_words": flags,
            "safe_text": safe_version,
            "model": MODEL_NAME
        })

        if flags:
            print(f"⚠️ Policy risk in {title} ({', '.join(flags)}) → rewritten safely")
        else:
            print(f"✅ Policy safe: {title}")

    out_file = SUGGESTIONS / "policy_notes.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(checks, f, indent=2, ensure_ascii=False)

    print(f"💾 Saved policy notes → {out_file}")


if __name__ == "__main__":
    policy_guard()
