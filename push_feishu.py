"""
Pushes plain text paper recommendations to Feishu via Incoming Webhook.
Supports per-group messaging: each research group gets its own message.
"""

import requests
import time


def push_single_group(
    webhook_url: str,
    group_name: str,
    keywords: list[str],
    papers: list[dict],
    date_range: str,
) -> bool:
    """Push a single research group's results as one message."""

    lines = [f"📚 [{group_name}] {date_range}\n"]
    lines.append("=" * 50)
    lines.append(f"🔑 关键词：{', '.join(keywords)}")
    lines.append("=" * 50)

    if not papers:
        lines.append("\n⚠️ 昨日无匹配论文")
    else:
        for i, paper in enumerate(papers, 1):
            lines.append(f"\n[{i}] {paper['title']}")
            lines.append(f"📅 {paper['published_local']}  |  Score: {paper['score']}")
            lines.append(f"🔗 {paper['alphaxiv_url']}")

    message_text = "\n".join(lines)

    payload = {"msg_type": "text", "content": {"text": message_text}}

    try:
        resp = requests.post(webhook_url, json=payload, timeout=10)
        resp.raise_for_status()
        return True
    except Exception as e:
        print(f"     ❌ Push failed: {e}")
        return False


def push_to_feishu(
    webhook_url: str,
    group_results: list[dict],
    date_range: str,
    push_strategy: str = "per_group",
) -> None:
    """Push paper recommendations to Feishu."""

    if (not webhook_url) or webhook_url == "" or webhook_url == "PASTE_YOUR_WEBHOOK_URL_HERE":
        print("❌ ERROR: feishu_webhook is empty in config.yaml")
        return

    if push_strategy == "per_group":
        success_count = 0
        fail_count = 0

        for i, group in enumerate(group_results, 1):
            print(f"\n📤 Pushing Group {i}/{len(group_results)}: {group['group_name']}...")

            success = push_single_group(
                webhook_url=webhook_url,
                group_name=group["group_name"],
                keywords=group["keywords"],
                papers=group["papers"],
                date_range=date_range,
            )

            if success:
                print(f"   ✅ Successfully pushed {group['group_name']}")
                success_count += 1
            else:
                print(f"   ❌ Failed to push {group['group_name']}")
                fail_count += 1

            if i < len(group_results):
                time.sleep(2)

        print(f"\n📊 Push summary: {success_count} succeeded, {fail_count} failed")

    else:
        lines = [f"📚 arXiv 每日论文推荐 · {date_range}\n"]

        for group in group_results:
            lines.append(f"\n{'='*50}")
            lines.append(f"📌 {group['group_name']}")
            lines.append(f"🔑 关键词：{', '.join(group['keywords'])}")
            lines.append("=" * 50)

            if not group["papers"]:
                lines.append("⚠️ 昨日无匹配论文")
            else:
                for i, paper in enumerate(group["papers"], 1):
                    lines.append(f"\n[{i}] {paper['title']}")
                    lines.append(f"📅 {paper['published_local']}  |  Score: {paper['score']}")
                    lines.append(f"🔗 {paper['alphaxiv_url']}")

        message_text = "\n".join(lines)
        payload = {"msg_type": "text", "content": {"text": message_text}}

        try:
            resp = requests.post(webhook_url, json=payload, timeout=10)
            resp.raise_for_status()
            print("✅ Successfully pushed to Feishu (single message)")
        except Exception as e:
            print(f"❌ Failed to push to Feishu: {e}")


def format_date_range(start_utc, end_utc, local_tz) -> str:
    """Helper to format date range for title."""

    start_local = start_utc.astimezone(local_tz)
    return start_local.strftime("%Y-%m-%d")
