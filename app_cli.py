import argparse
import json
import os
import shutil
from pathlib import Path

from bc.tools import youtube_ingest, transcript_parse, candidate_selector
import sys, io
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


BASE_OUT = Path("bc/outputs")
ARTIFACTS_DIR = BASE_OUT / "artifacts"
SUGGESTIONS_DIR = BASE_OUT / "suggestions"
REPORTS_DIR = BASE_OUT / "reports"


def _safe_clear_dir(dir_path: Path):
    """Delete all files inside a directory (not the directory itself)."""
    if not dir_path.exists():
        return
    for p in dir_path.glob("*"):
        try:
            if p.is_file():
                p.unlink()
            elif p.is_dir():
                shutil.rmtree(p)
        except Exception as e:
            print(f"⚠️ Could not remove {p}: {e}")


def main():
    parser = argparse.ArgumentParser(description="🎬 Back-Catalog Uplift Agent CLI")

    parser.add_argument("command", choices=["ingest"], help="Command to run")

    parser.add_argument("--channel", required=True, help="YouTube channel ID or URL")
    parser.add_argument("--limit", type=int, default=5, help="Number of videos to process")
    parser.add_argument("--age-days", type=int, default=180, help="Minimum video age in days")

    # ✅ granular cleaning flags (cross-platform, safe)
    parser.add_argument("--clean-artifacts", action="store_true", help="Clean bc/outputs/artifacts before run")
    parser.add_argument("--clean-reports",   action="store_true", help="Clean bc/outputs/reports before run")
    parser.add_argument("--clean-suggestions", action="store_true",
                        help="Clean bc/outputs/suggestions before run (ONLY if you’ll regenerate them)")

    # (legacy) keep --clean but make it equivalent to artifacts+reports
    parser.add_argument("--clean", action="store_true",
                        help="(Legacy) Clean artifacts and reports before run (does NOT clear suggestions)")
    args = parser.parse_args()

    # --- Ensure base folders exist
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    SUGGESTIONS_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    # --- Resolve final cleaning intents
    clean_artifacts = args.clean_artifacts or args.clean
    clean_reports = args.clean_reports or args.clean
    clean_suggestions = args.clean_suggestions  # never implied by legacy --clean

    # --- Perform requested cleanups (safe, selective)
    if clean_artifacts:
        print("🧹 Cleaning artifacts...")
        _safe_clear_dir(ARTIFACTS_DIR)
    if clean_reports:
        print("🧹 Cleaning reports...")
        _safe_clear_dir(REPORTS_DIR)
    if clean_suggestions:
        print("🧹 Cleaning suggestions (make sure you will regenerate rewrites/titles)...")
        _safe_clear_dir(SUGGESTIONS_DIR)

    if args.command == "ingest":
        print(f"\n🧠 Selecting top {args.limit} videos older than {args.age_days} days...\n")

        candidates = candidate_selector.select_backcatalog_candidates(
            channel_id=args.channel,
            age_days_min=args.age_days,
            pool_size=100,
            limit=args.limit
        )

        print(f"✅ Selected {len(candidates)} candidates.")
        print(json.dumps(candidates, indent=2))

        artifacts_path = ARTIFACTS_DIR / "videos.json"
        with open(artifacts_path, "w", encoding="utf-8") as f:
            json.dump(candidates, f, indent=2)
        print(f"💾 Saved selected videos → {artifacts_path}")

        print("\n🎧 Starting transcript extraction via Whisper fallback...\n")
        for v in candidates:
            vid = v["video_id"]
            try:
                print(f"▶ Processing: {v['title']} ({vid})")
                transcript = transcript_parse.get_transcript_text(vid)
                v["first60_text"] = transcript[:1000] if transcript else None
            except Exception as e:
                print(f"⚠️ Failed for {vid}: {e}")

        with open(artifacts_path, "w", encoding="utf-8") as f:
            json.dump(candidates, f, indent=2)

        print("\n✅ Phase 2 complete → Transcripts updated in videos.json")


if __name__ == "__main__":
    main()
