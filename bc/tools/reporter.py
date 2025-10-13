"""
Reporter Tool
-------------
Phase 3 – Final Step: Compiles all outputs (hook rewrite, title ideas, policy notes)
into a single Markdown and JSON report for each video.

Future Scope:
- Add nicer Markdown templates with emoji & layout.
- Integrate auto-eval metrics & supervisor summaries.
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

    # === Generate reports ===
    for v in videos:
        vid = v["video_id"]
        title = v["title"]

        rewrite = rewrites.get(vid, {})
        title_info = titles.get(vid, {})
        policy_info = policies.get(vid, {})

        markdown = f"""# 🎥 {title}

**Video ID:** {vid}  
**Generated:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}  

---

## 🧠 Hook Rewrite

---

## 🪶 Title & Thumbnail Ideas
{title_info.get("ideas", "No title/thumb ideas generated.")}

---

## 🚦 Policy Check
**Safe:** {policy_info.get("safe", True)}  
**Flagged Terms:** {", ".join(policy_info.get("flagged_terms", [])) or "None"}  

---

✅ End of Report
"""

        # Save individual report
        md_path = REPORTS_DIR / f"{vid}.md"
        json_path = BASE_ARTIFACTS / f"{vid}.json"

        with open(md_path, "w", encoding="utf-8") as f:
            f.write(markdown)

        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "video_id": vid,
                    "title": title,
                    "rewrite": rewrite,
                    "titles": title_info,
                    "policy": policy_info,
                },
                f,
                indent=2,
            )

        summary.append({
            "video_id": vid,
            "title": title,
            "safe": policy_info.get("safe", True),
            "report_file": str(md_path)
        })

        print(f"✅ Report created for → {title}")

    # === Save summary index ===
    summary_path = REPORTS_DIR / "_summary.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print(f"\n💾 All reports saved → {REPORTS_DIR}")
    print("✅ Reporter complete.\n")


# === CLI entrypoint ===
if __name__ == "__main__":
    reporter()
