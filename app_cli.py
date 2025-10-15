import argparse, json, os
from bc.tools import youtube_ingest, transcript_parse, candidate_selector

def main():
    parser = argparse.ArgumentParser(description="🎬 Back-Catalog Uplift Agent CLI")
    parser.add_argument("command", choices=["ingest"], help="Command to run")
    parser.add_argument("--channel", required=True, help="YouTube channel ID")
    parser.add_argument("--limit", type=int, default=5, help="How many videos to process")
    parser.add_argument("--age", type=int, default=180, help="Minimum age (days) for back-catalog filter")
    parser.add_argument("--clean", action="store_true", help="Clean old outputs before running")  # ✅ new flag
    args = parser.parse_args()

    if args.command == "ingest":
        print(f"\n🧠 Selecting top {args.limit} videos older than {args.age} days...\n")
        candidates = candidate_selector.select_backcatalog_candidates(
            channel_id=args.channel,
            age_days_min=args.age,
            pool_size=100,
            limit=args.limit
        )

        print(f"✅ Selected {len(candidates)} candidates.")
        print(json.dumps(candidates, indent=2))

        os.makedirs("bc/outputs/artifacts", exist_ok=True)
        artifacts_path = "bc/outputs/artifacts/videos.json"
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
