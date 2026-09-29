"""StaxTech topic discovery and safety filter."""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / "automation" / "config" / "topics.json"
TREND_INPUT = ROOT / "automation" / "data" / "trend-candidates.json"
OUTPUT = ROOT / "automation" / "data" / "topic-candidates.json"

KEYWORDS = {
    "AI & Technology": [
        "ai", "artificial intelligence", "technology", "tech", "automation",
        "android", "iphone", "ios", "windows", "macos", "linux", "google",
        "microsoft", "apple", "samsung", "oppo", "vivo", "oneplus", "realme",
        "xiaomi", "pixel", "coloros", "oxygenos", "hyperos", "gemini", "chatgpt",
        "copilot", "claude", "openai", "processor", "chip", "gpu", "software",
        "update", "launch", "release", "cybersecurity", "cloud", "robot"
    ],
    "Software & Tools": [
        "software", "tool", "app", "apps", "saas", "browser", "productivity",
        "chrome", "edge", "firefox", "whatsapp", "telegram", "instagram",
        "youtube", "notion", "canva", "github", "microsoft 365", "google workspace"
    ],
    "Web Development": [
        "website", "web", "html", "css", "javascript", "developer", "coding",
        "programming", "api", "react", "node", "python", "wordpress"
    ],
    "Student Technology": [
        "student", "study", "education", "college", "career", "exam", "learning",
        "online course", "scholarship"
    ],
}

# Topics that are poor fits for an evergreen technology site.
EXCLUDED_TERMS = [
    "lottery", "satta", "matka", "result", "horoscope", "astrology",
    "celebrity", "movie", "film", "song", "cricket", "football",
    "election", "politics", "politician", "party", "minister",
    "crime", "murder", "weather", "stock price", "share price"
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

    matched: list[str] = []
    score = 0

    for category in categories:
        for keyword in KEYWORDS.get(category, []):
            if keyword in text:
                matched.append(keyword)
                score += 10

    # Product/version topics such as "ColorOS 17" are useful even when
    # the exact product name is not in the keyword list.
    if re.search(r"\b(?:android|ios|windows|macos|linux)\s+\d", text):
        matched.append("operating-system-version")
        score += 20

    if re.search(r"\b(?:coloros|oxygenos|hyperos|one ui)\s*\d", text):
        matched.append("mobile-os-version")
        score += 30

    if re.search(r"\b(?:ai|app|software|update|launch|release)\b", text):
        score += 10

    return min(score, 100), sorted(set(matched))


def shortlist(candidates: list[dict], config: dict) -> list[dict]:
    categories = config.get("categories", [])
    results = []

    for candidate in candidates:
        title = candidate.get("title", "").strip()
        if not title:
            continue

        score, matched = score_topic(title, categories)
        if score < 10:
            continue

        results.append({
            "title": title,
            "score": score,
            "matched_keywords": matched,
            "source": candidate.get("source", "unknown"),
            "source_url": candidate.get("source_url", ""),
            "approx_traffic": candidate.get("approx_traffic", ""),
            "published": candidate.get("published", ""),
            "geo": candidate.get("geo", ""),
        })

    unique = {}
    for item in results:
        key = normalize(item["title"])
        if key not in unique or item["score"] > unique[key]["score"]:
            unique[key] = item

    return sorted(
        unique.values(),
        key=lambda item: (item["score"], item.get("approx_traffic", "")),
        reverse=True,
    )


def main() -> None:
    config = load_json(CONFIG, {})
    trend_data = load_json(TREND_INPUT, {"topics": []})
    candidates = trend_data.get("topics", [])
    topics = shortlist(candidates, config)

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(
        json.dumps({
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "input_count": len(candidates),
            "shortlisted_count": len(topics),
            "topics": topics,
        }, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    print(f"Processed {len(candidates)} trends; shortlisted {len(topics)} relevant topics.")
    if topics:
        print(f"Selected: {topics[0]['title']} (score={topics[0]['score']})")
    else:
        print("No suitable technology topic found; publication will be skipped.")


if __name__ == "__main__":
    main()
