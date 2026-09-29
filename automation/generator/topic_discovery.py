"""
StaxTech topic discovery engine.

Reads live trend candidates, scores them against StaxTech categories,
and writes only relevant topics to topic-candidates.json.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / "automation" / "config" / "topics.json"
TREND_INPUT = ROOT / "automation" / "data" / "trend-candidates.json"
OUTPUT = ROOT / "automation" / "data" / "topic-candidates.json"

KEYWORDS = {
    "AI & Technology": [
        "ai", "artificial intelligence", "technology", "tech", "automation"
    ],
    "Software & Tools": [
        "software", "tool", "app", "saas", "browser", "productivity"
    ],
    "Web Development": [
        "website", "web", "html", "css", "javascript", "developer"
    ],
    "Student Technology": [
        "student", "study", "education", "college", "career", "exam"
    ],
}


def load_json(path: Path, default: dict) -> dict:
    if not path.exists():
        return default

    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return default


def score_topic(title: str, categories: list[str]) -> tuple[int, list[str]]:
    text = title.lower()
    matched = []
    score = 0

    for category in categories:
        for keyword in KEYWORDS.get(category, []):
            if keyword in text:
                matched.append(keyword)
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
        })

    # Remove duplicate titles while preserving the highest score.
    unique = {}

    for item in results:
        key = item["title"].lower()

        if key not in unique or item["score"] > unique[key]["score"]:
            unique[key] = item

    return sorted(
        unique.values(),
        key=lambda item: item["score"],
        reverse=True,
    )


def main() -> None:
    config = load_json(CONFIG, {})
    trend_data = load_json(
        TREND_INPUT,
        {"topics": []},
    )

    candidates = trend_data.get("topics", [])
    topics = shortlist(candidates, config)

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)

    OUTPUT.write_text(
        json.dumps(
            {
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "input_count": len(candidates),
                "shortlisted_count": len(topics),
                "topics": topics,
            },
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )

    print(
        f"Processed {len(candidates)} trends; "
        f"shortlisted {len(topics)} relevant topics."
    )


if __name__ == "__main__":
    main()
