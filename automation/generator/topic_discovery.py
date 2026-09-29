"""StaxTech topic discovery using live trends and Search Console data."""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / "automation" / "config" / "topics.json"
TREND_INPUT = ROOT / "automation" / "data" / "trend-candidates.json"
GSC_INPUT = ROOT / "automation" / "data" / "search-console-candidates.json"
OUTPUT = ROOT / "automation" / "data" / "topic-candidates.json"

KEYWORDS = {
    "AI & Technology": ["ai", "artificial intelligence", "technology", "tech", "automation", "android", "iphone", "ios", "windows", "macos", "linux", "google", "microsoft", "apple", "samsung", "oppo", "vivo", "oneplus", "realme", "xiaomi", "pixel", "coloros", "oxygenos", "hyperos", "gemini", "chatgpt", "copilot", "claude", "openai", "processor", "chip", "gpu", "software", "update", "launch", "release", "cybersecurity", "cloud", "robot"],
    "Software & Tools": ["software", "tool", "app", "apps", "saas", "browser", "productivity", "chrome", "edge", "firefox", "whatsapp", "telegram", "instagram", "youtube", "notion", "canva", "github", "microsoft 365", "google workspace"],
    "Web Development": ["website", "web", "html", "css", "javascript", "developer", "coding", "programming", "api", "react", "node", "python", "wordpress"],
    "Student Technology": ["student", "study", "education", "college", "career", "exam", "learning", "online course", "scholarship"],
}

EXCLUDED_TERMS = [
    "lottery", "satta", "matka", "result", "horoscope", "astrology", "celebrity",
    "movie", "film", "song", "cricket", "football", "election", "politics",
    "politician", "party", "minister", "crime", "murder", "weather",
    "stock price", "share price",
]


def load_json(path: Path, default: dict) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip().lower())


def score_topic(title: str, categories: list[str]) -> tuple[int, list[str]]:
    text = normalize(title)
    if any(term in text for term in EXCLUDED_TERMS):
        return 0, []

    matched = []
    score = 0
    for category in categories:
        for keyword in KEYWORDS.get(category, []):
            if keyword in text:
                matched.append(keyword)
                score += 10

    if re.search(r"\b(?:android|ios|windows|macos|linux)\s+\d", text):
        matched.append("operating-system-version")
        score += 20
    if re.search(r"\b(?:coloros|oxygenos|hyperos|one ui)\s*\d", text):
        matched.append("mobile-os-version")
        score += 30
    if re.search(r"\b(?:ai|app|software|update|launch|release)\b", text):
        score += 10

    return min(score, 100), sorted(set(matched))


def main() -> None:
    config = load_json(CONFIG, {})
    trends = load_json(TREND_INPUT, {"topics": []}).get("topics", [])
    gsc = load_json(GSC_INPUT, {"topics": []}).get("topics", [])

    candidates = []

    for item in trends:
        score, matched = score_topic(item.get("title", ""), config.get("categories", []))
        if score >= 10:
            candidates.append({
                "title": item["title"],
                "score": score,
                "matched_keywords": matched,
                "source": item.get("source", "Google Trends"),
                "source_url": item.get("source_url", ""),
                "approx_traffic": item.get("approx_traffic", ""),
                "published": item.get("published", ""),
                "geo": item.get("geo", ""),
            })

    for item in gsc:
        score, matched = score_topic(item.get("title", ""), config.get("categories", []))
        if score >= 10:
            # Search Console signals are valuable because they represent
            # queries that already surfaced the site in Google Search.
            signal = min(30, round(float(item.get("impressions", 0)) / 10))
            candidates.append({
                "title": item["title"],
                "score": min(100, score + signal),
                "matched_keywords": matched + ["search-console-query"],
                "source": "Google Search Console",
                "source_url": item.get("source_url", ""),
                "clicks": item.get("clicks", 0),
                "impressions": item.get("impressions", 0),
                "ctr": item.get("ctr", 0),
                "position": item.get("position", 0),
            })

    unique = {}
    for item in candidates:
        key = normalize(item["title"])
        if key not in unique or item["score"] > unique[key]["score"]:
            unique[key] = item

    topics = sorted(
        unique.values(),
        key=lambda x: x["score"],
        reverse=True,
    )

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(
        json.dumps({
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "trend_input_count": len(trends),
            "search_console_input_count": len(gsc),
            "shortlisted_count": len(topics),
            "topics": topics,
        }, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    print(
        f"Processed {len(trends)} Trends + {len(gsc)} Search Console queries; "
        f"shortlisted {len(topics)} topics."
    )
    if topics:
        print(f"Selected: {topics[0]['title']} ({topics[0]['source']})")
    else:
        print("No suitable technology topic found; publication will be skipped.")


if __name__ == "__main__":
    main()
