"""
StaxTech Trend Fetcher

Fetches Google Trends RSS topics for configured target markets and stores normalized
trend candidates for the StaxTech topic discovery pipeline.

Only topic metadata is collected. Source article content is not copied.
"""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

import feedparser
import requests


ROOT = Path(__file__).resolve().parents[2]
CONFIG_FILE = ROOT / "automation" / "config" / "sources.json"
OUTPUT_FILE = ROOT / "automation" / "data" / "trend-candidates.json"

USER_AGENT = "StaxTech-TrendFetcher/2.0"


def load_config() -> dict:
    if not CONFIG_FILE.exists():
        return {
            "sources": [{
                "name": "Google Trends India",
                "type": "google_trends_rss",
                "geo": "US",
                "enabled": True
            }]
        }

    with CONFIG_FILE.open("r", encoding="utf-8") as file:
        return json.load(file)


def clean_text(value: str) -> str:
    value = re.sub(r"<[^>]+>", " ", value or "")
    return re.sub(r"\s+", " ", value).strip()


def fetch_google_trends(geo: str = "IN") -> list[dict]:
    url = f"https://trends.google.com/trending/rss?geo={quote(geo)}"

    response = requests.get(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "application/rss+xml, application/xml, text/xml"
        },
        timeout=20
    )
    response.raise_for_status()

    feed = feedparser.parse(response.content)

    if feed.bozo and not feed.entries:
        raise RuntimeError("Unable to parse Google Trends RSS feed.")

    trends = []

    for entry in feed.entries:
        title = clean_text(entry.get("title", ""))
        if not title:
            continue

        trends.append({
            "title": title,
            "published": clean_text(entry.get("published", "")),
            "approx_traffic": clean_text(entry.get("ht_approx_traffic", "")),
            "source": "Google Trends",
            "source_url": entry.get("link", ""),
            "geo": geo
        })

    return trends


def save_results(trends: list[dict]) -> None:
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    output = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "count": len(trends),
        "topics": trends
    }

    with OUTPUT_FILE.open("w", encoding="utf-8") as file:
        json.dump(output, file, indent=2, ensure_ascii=False)


def main() -> int:
    print("Starting StaxTech Trend Fetcher...")

    config = load_config()
    all_trends = []

    for source in config.get("sources", []):
        if not source.get("enabled", True):
            continue

        try:
            if source.get("type") == "google_trends_rss":
                geo = source.get("geo", "IN")
                print(f"Fetching Google Trends for {geo}...")
                all_trends.extend(fetch_google_trends(geo))
        except Exception as error:
            print(f"Source failed: {error}", file=sys.stderr)

    unique = {}
    for trend in all_trends:
        key = trend["title"].lower().strip()
        unique.setdefault(key, trend)

    all_trends = list(unique.values())
    save_results(all_trends)

    print(f"Saved {len(all_trends)} trend topics.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
