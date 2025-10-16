"""
Reporter Tool (Phase 3 – Final Step)
------------------------------------
Compiles all outputs (hook rewrite, title ideas, policy notes)
into a single Markdown + JSON report for each analyzed video.

Future Scope:
- Add HTML export for web previews.
- Include supervisor route trace visualization.
"""

import json
from pathlib import Path
from datetime import datetime


def reporter():
    print("📝 Generating final Markdown + JSON reports...")

    # === Define folders ===
    BASE_ARTIFACTS = Path("bc/outputs/artifacts")
    BASE_SUGGESTIONS = Path("bc/outputs/suggestions")
    REPORTS_DIR = Path("bc/outputs/reports")
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    # --- Clean previous reports ---
    for file in REPORTS_DIR.glob("*"):
        try:
            file.unlink()
        except Exception:
            pass


    # === Input files ===
    videos_file = BASE_ARTIFACTS / "videos.json"
    hooks_file = BASE_SUGGESTIONS / "hook_rewrites.json"
    titles_file = BASE_SUGGESTIONS / "titlethumb.json"
    policy_file = BASE_SUGGESTIONS / "policy_notes.json"

    if not all(f.exists() for f in [videos_file, hooks_file, titles_file, policy_file]):
        print("⚠️ Missing one or more input files for report generation.")
        return

    # === Load data ===
    videos = json.load(open(videos_file, "r", encoding="utf-8"))
    rewrites = {x["video_id"]: x for x in json.load(open(hooks_file, "r", encoding="utf-8"))}
    titles = {x["video_id"]: x for x in json.load(open(titles_file, "r", encoding="utf-8"))}
    policies = {x["video_id"]: x for x in json.load(open(policy_file, "r", encoding="utf-8"))}

    summary = []

    # === Generate structured reports ===
    for v in videos:
        vid = v["video_id"]
        title = v["title"]

        rewrite_data = rewrites.get(vid, {})
        title_data = titles.get(vid, {})
        policy_data = policies.get(vid, {})

        # --- Extract info safely ---
        rewritten_text = rewrite_data.get("rewritten_script", "No rewrite available.")
        style_notes = rewrite_data.get("style_notes", [])

        ideas = title_data.get("ideas", {})
        title_list = ideas.get("titles", [])
        thumb_list = ideas.get("thumbnails", [])

        policy_safe = policy_data.get("safe", True)
        flagged_terms = policy_data.get("flagged_terms", [])
        policy_advice = policy_data.get("advice", [])

        # --- Build Markdown Section ---
        md_titles = "\n".join([f"- {t}" for t in title_list]) if title_list else "No title ideas generated."
        md_thumbs = ""
        for t in thumb_list:
            concept = t.get("concept", "")
            emotion = t.get("emotion", "")
            contrast = t.get("contrast", "")
            md_thumbs += f"\n🎨 **Concept:** {concept}\n💡 *Emotion:* {emotion}\n✨ *Contrast:* {contrast}\n"

        md_notes = "\n".join([f"- {n}" for n in style_notes]) if style_notes else "No style notes."
        md_policy_advice = "\n".join([f"- {p}" for p in policy_advice]) if policy_advice else "No specific advice."

        # --- Markdown template ---
        markdown = f"""# 🎥 {title}

**Video ID:** {vid}  
**Generated:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}  

---

## 🧠 Hook Rewrite
{rewritten_text}

### ✍️ Style Notes
{md_notes}

---

## 🪶 Title & Thumbnail Ideas

### 🎯 Suggested Titles
{md_titles}

### 🖼️ Thumbnail Concepts
{md_thumbs or 'No thumbnail ideas generated.'}

---

## 🚦 Policy Check
✅ **Safe for all audiences:** {policy_safe}  
**Flagged Terms:** {', '.join(flagged_terms) if flagged_terms else 'None'}  

### 🧩 Reviewer Advice
{md_policy_advice}

---

✅ *End of Report*
"""

        # --- Save individual report ---
        md_path = REPORTS_DIR / f"{vid}.md"
        json_path = BASE_ARTIFACTS / f"{vid}.json"

        with open(md_path, "w", encoding="utf-8") as f:
            f.write(markdown)

        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "video_id": vid,
                    "title": title,
                    "hook_rewrite": {
                        "rewritten_script": rewritten_text,
                        "style_notes": style_notes,
                    },
                    "title_thumb": ideas,
                    "policy": policy_data,
                },
                f,
                indent=2,
                ensure_ascii=False,
            )

        summary.append({
            "video_id": vid,
            "title": title,
            "safe": policy_safe,
            "report_file": str(md_path)
        })

        print(f"✅ Report created for → {title}")

    # --- Save summary index ---
    summary_path = REPORTS_DIR / "_summary.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    print(f"\n💾 All reports saved → {REPORTS_DIR}")
    print("✅ Reporter complete.\n")


if __name__ == "__main__":
    reporter()
