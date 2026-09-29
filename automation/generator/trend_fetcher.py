"""
StaxTech Trend Fetcher

Fetches Google Trends RSS topics for configured target markets and stores normalized
trend candidates for the StaxTech topic discovery pipeline.
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
USER_AGENT = "StaxTech-TrendFetcher/3.0"
DEFAULT_GEO = "US"


def load_config() -> dict:
    if not CONFIG_FILE.exists():
        return {
            "sources": [{
                "name": "Google Trends United States",
                "type": "google_trends_rss",
                "geo": DEFAULT_GEO,
                "enabled": True,
                "weight": 100,
            }]
        }
    try:
        with CONFIG_FILE.open("r", encoding="utf-8") as file:
            return json.load(file)
    except (OSError, json.JSONDecodeError) as error:
        print(f"Invalid source configuration: {error}", file=sys.stderr)
        return {"sources": []}


def clean_text(value: str) -> str:
    value = re.sub(r"<[^>]+>", " ", value or "")
    return re.sub(r"\s+", " ", value).strip()


def fetch_google_trends(geo: str = DEFAULT_GEO) -> list[dict]:
    geo = str(geo or DEFAULT_GEO).upper()
    url = f"https://trends.google.com/trending/rss?geo={quote(geo)}"
    response = requests.get(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "application/rss+xml, application/xml, text/xml",
        },
        timeout=20,
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
            "source_url": entry.get("link", "") or url,
            "geo": geo,
        })
    return trends


def save_results(trends: list[dict]) -> None:
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text(
        json.dumps({
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "count": len(trends),
            "topics": trends,
        }, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def main() -> int:
    print("Starting StaxTech Trend Fetcher...")
    config = load_config()
    sources = [
        source for source in config.get("sources", [])
        if source.get("enabled", True)
        and source.get("type") == "google_trends_rss"
    ]
    sources.sort(key=lambda source: float(source.get("weight", 0) or 0), reverse=True)

    all_trends = []
    for source in sources:
        geo = str(source.get("geo", DEFAULT_GEO)).upper()
        try:
            print(f"Fetching Google Trends for {geo}...")
            fetched = fetch_google_trends(geo)
            print(f"Fetched {len(fetched)} topics for {geo}.")
            all_trends.extend(fetched)
        except Exception as error:
            print(f"Source {geo} failed: {error}", file=sys.stderr)

    # For a US-first site, never silently fall back to another country.
    # An empty US feed should result in zero publishable trend candidates,
    # not incorrectly targeted content.
    primary_geo = DEFAULT_GEO
    primary_sources = [s for s in sources if str(s.get("geo", "")).upper() == primary_geo]
    if primary_sources:
        all_trends = [trend for trend in all_trends if trend.get("geo") == primary_geo]

    unique = {}
    for trend in all_trends:
        key = clean_text(trend.get("title", "")).lower()
        if key:
            existing = unique.get(key)
            if existing is None or str(trend.get("geo", "")) == primary_geo:
                unique[key] = trend

    all_trends = list(unique.values())
    save_results(all_trends)
    print(f"Saved {len(all_trends)} US trend topics.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
