"""
arXiv Daily Paper Pusher - Entry point.

Usage:
    python main.py                  # Run once (default)
    python main.py --schedule 10:30 # Run daily at 10:30 (local time), stays alive
"""

import argparse
import time
import yaml
import schedule
from datetime import timedelta, timezone

from fetch_papers import fetch_papers_for_group, get_yesterday_range_utc
from rank_papers import rank_and_filter
from push_feishu import push_to_feishu, format_date_range


def load_config(path: str = "config.yaml") -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def run_once():
    """Execute one full fetch-rank-push cycle."""

    config = load_config()
    tz_offset = config.get("timezone_offset", 8)
    top_k = config.get("top_k", 6)
    webhook_url = config.get("feishu_webhook", "")

    local_tz = timezone(timedelta(hours=tz_offset))
    start_utc, end_utc = get_yesterday_range_utc(tz_offset)
    date_range = format_date_range(start_utc, end_utc, local_tz)

    print(f"🚀 arXiv Daily Pusher started for {date_range}")

    group_results = []

    for group in config.get("groups", []):
        name = group["name"]
        keywords = group["keywords"]

        print(f"⏳ Fetching: {name}")
        api_mode = config.get("api_mode", "auto")
        candidates = fetch_papers_for_group(
            keywords=keywords,
            tz_offset_hours=tz_offset,
            api_mode=api_mode,
        )
        print(f"   Candidates: {len(candidates)}")

        top_papers = rank_and_filter(papers=candidates, keywords=keywords, top_k=top_k)

        group_results.append({
            "group_name": name,
            "keywords": keywords,
            "papers": top_papers,
        })

    # Push to Feishu
    push_strategy = config.get("push_strategy", "per_group")
    print(f"\n📤 Pushing to Feishu (strategy: {push_strategy})...")
    push_to_feishu(webhook_url, group_results, date_range, push_strategy)

    print("\n✅ Done.")


def main():
    parser = argparse.ArgumentParser(
        description="arXiv Daily Paper Pusher — fetch, rank, push to Feishu"
    )
    parser.add_argument(
        "--schedule",
        type=str,
        default=None,
        metavar="HH:MM",
        help="Run daily at the specified local time (e.g. 10:30). "
             "The process stays alive and repeats every day. "
             "Omit to run once and exit.",
    )
    args = parser.parse_args()

    if args.schedule is None:
        # Single run mode
        run_once()
    else:
        # Scheduled mode — validate time format
        try:
            parts = args.schedule.split(":")
            h, m = int(parts[0]), int(parts[1])
            if not (0 <= h <= 23 and 0 <= m <= 59):
                raise ValueError
            time_str = f"{h:02d}:{m:02d}"
        except (ValueError, IndexError):
            print(f"❌ Invalid time format: '{args.schedule}'. Use HH:MM (e.g. 10:30)")
            return

        print(f"⏰ Scheduled mode: will run daily at {time_str}")
        print(f"   Press Ctrl+C to stop.\n")

        # Run immediately on first start, then schedule
        print("▶ Running initial execution...")
        try:
            run_once()
        except Exception as e:
            print(f"⚠ Initial run failed: {e}")

        # Set up daily schedule
        schedule.every().day.at(time_str).do(run_once)

        print(f"\n⏳ Next run scheduled at {time_str}. Waiting...")
        try:
            while True:
                schedule.run_pending()
                time.sleep(30)
        except KeyboardInterrupt:
            print("\n👋 Scheduler stopped.")


if __name__ == "__main__":
    main()
