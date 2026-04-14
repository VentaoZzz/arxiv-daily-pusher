# arXiv Daily Paper Pusher

## Description
Automatically fetch yesterday's arXiv papers, rank by keyword relevance, and push to Feishu (Lark) via webhook.

## Features
- Multi-group support with independent keywords
- Smart scoring: title matches weighted 2x, abstract 1x
- Dual-mode API: arxiv library with automatic HTTP fallback
- Per-group or single message push strategies

## Schedule
```yaml
schedule: "30 2 * * *"
```
Runs daily at 10:30 AM Beijing Time (02:30 UTC).

## Requirements
- Python 3.10+
- Dependencies: `arxiv`, `PyYAML`, `requests`
- Feishu Incoming Webhook URL

## Quick Start

1. **Install:**
```bash
pip install -r requirements.txt
```

2. **Configure:**
```bash
cp config.example.yaml config.yaml
# Edit config.yaml with your webhook URL and keywords
```

3. **Run:**
```bash
python main.py
```

## Configuration

See `config.example.yaml` for full configuration options:
- `groups`: Research groups with keywords
- `feishu_webhook`: Your Feishu bot webhook URL
- `top_k`: Papers per group (default: 6)
- `timezone_offset`: Hours from UTC (default: 8 for Beijing)
- `api_mode`: "auto" | "arxiv_only" | "http_only"
- `push_strategy`: "per_group" | "single"

## Manual Test
```bash
cd ~/.openclaw/skills/arxiv-daily-pusher
python main.py
```
