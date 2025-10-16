"""
Tool: policy_guard.py
Purpose: Checks content safety & advertiser-friendliness using AWS Bedrock.
Structured JSON output with clear safety fields for downstream reporting.
"""

from pathlib import Path
import json
import re
from bc.tools.shared_bedrock import generate_bedrock_response


# === PATHS ===
BASE_DIR = Path(__file__).resolve().parent.parent
SUGGESTIONS = BASE_DIR / "outputs" / "suggestions"
SUGGESTIONS.mkdir(parents=True, exist_ok=True)

# --- Clean previous outputs (fresh run) ---
for file in SUGGESTIONS.glob("*"):
    try:
        file.unlink()
    except Exception:
        pass


# === BASIC RISKY WORD LIST ===
RISKY_WORDS = [
    "violence", "blood", "drugs", "weapon", "hate", "suicide",
    "terror", "sex", "nude", "gambling", "death", "kill", "gun"
]


# --- Helper: cleanup ---
def clean_text(txt: str) -> str:
    txt = txt.replace("```json", "").replace("```", "")
    txt = re.sub(r"<[^>]+>", "", txt)
    txt = re.sub(r"\s+", " ", txt)
    return txt.strip()


# === POLICY CHECK LOGIC ===
def policy_guard():
    rewrites_file = SUGGESTIONS / "hook_rewrites.json"
    if not rewrites_file.exists():
        print(f"❌ No rewrites found at {rewrites_file}")
        return

    with open(rewrites_file, "r", encoding="utf-8") as f:
        rewrites = json.load(f)

    results = []

    for item in rewrites:
        title = item.get("title", "")
        text = item.get("rewritten_script", "")
        video_id = item.get("video_id", "")

        # --- Step 1: Keyword Scan ---
        flagged = [w for w in RISKY_WORDS if w.lower() in text.lower()]
        safe = len(flagged) == 0

        # --- Step 2: If flagged, rewrite safely ---
        advice = []
        safe_text = text

        if flagged:
            prompt = f"""
You are a YouTube policy compliance editor.

Task: Review and sanitize the following script to meet advertiser-friendly standards.

Flagged terms: {', '.join(flagged)}
Text: {text}

Respond ONLY in this JSON structure:
{{
  "safe_version": "Rewritten safe version of text",
  "advice": [
    "Short note 1",
    "Short note 2"
  ]
}}
Ensure valid JSON, no explanations.
            """

            raw_output = generate_bedrock_response(prompt, max_tokens=300)
            cleaned = clean_text(raw_output)

            try:
                parsed = json.loads(cleaned)
                safe_text = parsed.get("safe_version", text)
                advice = parsed.get("advice", [])
            except json.JSONDecodeError:
                print(f"⚠️ JSON decode failed for {title}, using fallback safe version.")
                advice = [f"Manual review needed for terms: {', '.join(flagged)}"]

            print(f"⚠️ Policy risk in {title} ({', '.join(flagged)}) → rewritten safely")
        else:
            print(f"✅ Policy safe: {title}")

        results.append({
            "video_id": video_id,
            "title": title,
            "safe": safe,
            "flagged_terms": flagged,
            "safe_text": safe_text,
            "advice": advice,
            "model": "AWS Bedrock – meta.llama3-8b-instruct-v1:0"
        })

    out_file = SUGGESTIONS / "policy_notes.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"💾 Saved policy notes → {out_file}")


if __name__ == "__main__":
    policy_guard()
