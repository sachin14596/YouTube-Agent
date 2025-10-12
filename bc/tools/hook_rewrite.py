# ============================================================
# 🎬 Hook Rewriter Tool | Llama-3.2-1B-Instruct Integration
# ============================================================

import os
import json
from pathlib import Path
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch
from dotenv import load_dotenv

# -------------------------------
# 🔹 Load environment variables
# -------------------------------
load_dotenv()
HF_TOKEN = os.getenv("HF_TOKEN")
MODEL_NAME = os.getenv("MODEL_NAME", "meta-llama/Llama-3.2-1B-Instruct")

BASE_DIR = Path(__file__).resolve().parents[2]
ARTIFACTS_PATH = BASE_DIR / "bc" / "outputs" / "artifacts" / "videos.json"
OUT_DIR = BASE_DIR / "bc" / "outputs" / "suggestions"
OUT_DIR.mkdir(parents=True, exist_ok=True)

print(f"🧠 Loading model: {MODEL_NAME} ...")

# -------------------------------
# 🔹 Load model and tokenizer
# -------------------------------
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, use_auth_token=HF_TOKEN)
model = AutoModelForCausalLM.from_pretrained(MODEL_NAME, use_auth_token=HF_TOKEN)

device = "cuda" if torch.cuda.is_available() else "cpu"
model = model.to(device)
print(f"Device set to use {device}")

# -------------------------------
# 🔹 Helper: Generate rewritten text
# -------------------------------
def generate_llama_response(prompt: str) -> str:
    """
    Sends a rewrite prompt to the Llama-3.2-1B-Instruct model and returns clean text.
    """
    messages = [{"role": "user", "content": prompt}]
    inputs = tokenizer.apply_chat_template(
        messages,
        add_generation_prompt=True,
        tokenize=True,
        return_dict=True,
        return_tensors="pt",
    ).to(device)

    outputs = model.generate(**inputs, max_new_tokens=350, temperature=0.8)
    response = tokenizer.decode(
        outputs[0][inputs["input_ids"].shape[-1]:],
        skip_special_tokens=True
    )
    return response.strip()

# -------------------------------
# 🔹 Main rewrite function
# -------------------------------
def hook_rewrite():
    """
    Loads shortlisted videos, rewrites hook intros with Llama model,
    and saves enhanced versions.
    """
    if not ARTIFACTS_PATH.exists():
        print(f"❌ No videos.json found at {ARTIFACTS_PATH}")
        return

    with open(ARTIFACTS_PATH, "r", encoding="utf-8") as f:
        videos = json.load(f)

    rewritten_data = []
    for video in videos:
        vid = video.get("video_id")
        title = video.get("title", "Untitled")
        first60_text = video.get("first60_text", "").strip()

        if not first60_text:
            print(f"⚠️ Skipping {title} — no transcript text.")
            continue

        print(f"✍️ Rewriting: {title}")

        # Prompt to guide model behaviour
        prompt = (
            "Rewrite the following YouTube video introduction to make it more engaging, "
            "curiosity-driven, and audience-retentive. Keep the tone natural and concise, "
            "suitable for the first 60 seconds of a video.\n\n"
            f"Original:\n{first60_text}\n\nRewritten:"
        )

        try:
            rewritten = generate_llama_response(prompt)
            print(f"✅ Rewritten: {title}")
        except Exception as e:
            print(f"⚠️ Failed to rewrite {title}: {e}")
            rewritten = ""

        rewritten_data.append({
            "video_id": vid,
            "title": title,
            "rewritten_script": rewritten,
            "model": MODEL_NAME
        })

    # Save all rewritten scripts
    out_path = OUT_DIR / "hook_rewrites.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(rewritten_data, f, indent=2, ensure_ascii=False)

    print(f"💾 Saved rewrites → {out_path}")

# -------------------------------
# 🔹 Entry point (for CLI runs)
# -------------------------------
if __name__ == "__main__":
    hook_rewrite()
