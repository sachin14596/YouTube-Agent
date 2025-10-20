"""
Tool: reporter.py
Purpose: Generates unified Markdown & JSON reports summarizing
hook rewrites, description rewrites, title/thumbnail ideas, and policy checks.
"""

import json
from pathlib import Path
from datetime import datetime

# === PATHS ===
BASE_DIR = Path(__file__).resolve().parent.parent
OUT_SUGGESTIONS = BASE_DIR / "outputs" / "suggestions"
OUT_REPORTS = BASE_DIR / "outputs" / "reports"
OUT_ARTIFACTS = BASE_DIR / "outputs" / "artifacts"

OUT_REPORTS.mkdir(parents=True, exist_ok=True)


# === Helper: Safe JSON Load ===
def _load_json(path: Path):
    if path.exists():
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            print(f"⚠️ JSON parse error in {path.name}")
    else:
        print(f"⚠️ Missing file: {path}")
    return []


# === Main Reporter ===
def reporter():
    print("\n🧾 Generating Markdown reports...")

    # --- Load all suggestion files ---
    hooks = _load_json(OUT_SUGGESTIONS / "hook_rewrites.json")
    descs = _load_json(OUT_SUGGESTIONS / "description_rewrites.json")
    titles = _load_json(OUT_SUGGESTIONS / "titlethumb.json")
    policies = _load_json(OUT_SUGGESTIONS / "policy_notes.json")

    # Convert lists to dicts for quick lookup
    desc_map = {d["video_id"]: d for d in descs}
    title_map = {t["video_id"]: t for t in titles}
    policy_map = {p["video_id"]: p for p in policies}

    reports_summary = []

    for item in hooks:
        vid = item.get("video_id")
        title = item.get("title", "Untitled Video")
        rewritten = item.get("rewritten_script", "N/A")
        style_notes = item.get("style_notes", [])

        # Lookups
        desc_data = desc_map.get(vid)
        title_data = title_map.get(vid)
        policy_data = policy_map.get(vid)

        # --- Markdown Composition ---
        lines = []
        lines.append(f"# 🎥 {title}\n")
        lines.append(f"**Video ID:** `{vid}`  ")
        lines.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("\n---\n")

        # 🧠 Hook Rewrite
        lines.append("## 🧠 Hook Rewrite")
        lines.append(rewritten)
        if style_notes:
            lines.append("\n**Notes on Hook Improvement:**")
            for n in style_notes:
                lines.append(f"- {n}")
        lines.append("\n---\n")

        # 🪶 Improved Description
        if desc_data:
            desc_text = (
                desc_data.get("improved_description")
                or desc_data.get("rewritten_description")
                or ""
            )
            notes = desc_data.get("improvement_notes", [])
            if desc_text:
                lines.append("## Improved Description")
                lines.append(desc_text)
                if notes:
                    lines.append("\n**Notes on Improvement:**")
                    for n in notes:
                        lines.append(f"- {n}")
                lines.append("\n---\n")

        # 🎯 Titles & Thumbnails
        if title_data:
            ideas = title_data.get("ideas", {})
            titles_list = ideas.get("titles", [])
            thumbs = ideas.get("thumbnails", [])
            lines.append("## 🎯 Title & Thumbnail Ideas")

            if titles_list:
                lines.append("**Suggested Titles:**")
                for t in titles_list:
                    lines.append(f"- {t}")
            if thumbs:
                lines.append("\n**Thumbnail Concepts:**")
                for thumb in thumbs:
                    concept = thumb.get("concept", "")
                    emotion = thumb.get("emotion", "")
                    contrast = thumb.get("contrast", "")
                    lines.append(
                        f"- 🎨 *Concept:* {concept} | 💡 *Emotion:* {emotion} | ✨ *Contrast:* {contrast}"
                    )
            lines.append("\n---\n")

        # 🚦 Policy Guard
        if policy_data:
            safe = policy_data.get("safe", True)
            flagged = policy_data.get("flagged_terms", [])
            advice = policy_data.get("advice", [])
            lines.append("## 🚦 Policy Check")
            lines.append(f"✅ **Safe for all audiences:** {safe}")
            if flagged:
                lines.append(f"**Flagged Terms:** {', '.join(flagged)}")
            if advice:
                lines.append("\n**Reviewer Advice:**")
                for tip in advice:
                    lines.append(f"- {tip}")
            lines.append("\n---\n")

        # Compile Report Text
        report_text = "\n".join(lines)

        # Save Markdown
        out_path = OUT_REPORTS / f"{vid}.md"
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(report_text)

        reports_summary.append(
            {
                "video_id": vid,
                "title": title,
                "hook": rewritten[:120] + "...",
                "has_description": bool(desc_data),
                "safe": policy_data.get("safe", True) if policy_data else None,
            }
        )

        print(f"✅ Saved report → {out_path.name}")

    # --- Write Summary JSON ---
    summary_path = OUT_REPORTS / "_summary.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(reports_summary, f, indent=2, ensure_ascii=False)

    print(f"💾 Summary JSON written → {summary_path}")
    print("✅ All reports generated successfully!\n")


if __name__ == "__main__":
    reporter()
