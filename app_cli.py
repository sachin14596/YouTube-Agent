import argparse
from bc.tools import youtube_ingest, transcript_parse

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["ingest"])
    parser.add_argument("--channel", required=True, help="YouTube Channel ID")
    parser.add_argument("--limit", type=int, default=5)
    args = parser.parse_args()

    if args.command == "ingest":
        videos = youtube_ingest.get_channel_videos(args.channel, args.limit)

        for v in videos:
            transcript = transcript_parse.get_transcript(v["video_id"])
            v["first60_text"] = transcript_parse.get_first_60s_text(transcript)

        youtube_ingest.save_videos(videos)

if __name__ == "__main__":
    main()
