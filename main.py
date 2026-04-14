"""
Phase 2 entry point: Scheduled skill that pushes to Feishu.
"""

import yaml
from datetime import timedelta, timezone

from fetch_papers import fetch_papers_for_group, get_yesterday_range_utc
from rank_papers import rank_and_filter
from push_feishu import push_to_feishu, format_date_range


def load_config(path: str = "config.yaml") -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def main():
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

    print("\n✅ Phase 2 complete.")


if __name__ == "__main__":
    main()
