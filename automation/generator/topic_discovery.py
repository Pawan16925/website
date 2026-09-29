"""
StaxTech topic discovery engine.

Phase 1:
- Loads configured StaxTech categories.
- Accepts candidate topics from a JSON source.
- Scores candidates for relevance.
- Writes shortlisted topics to automation/data/topic-candidates.json.

Live trend/API integrations will be added after the scoring pipeline is tested.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / "automation" / "config" / "topics.json"
OUTPUT = ROOT / "automation" / "data" / "topic-candidates.json"

KEYWORDS = {
    "AI & Technology": ["ai", "artificial intelligence", "technology", "tech", "automation"],
    "Software & Tools": ["software", "tool", "app", "saas", "browser", "productivity"],
    "Web Development": ["website", "web", "html", "css", "javascript", "developer"],
    "Student Technology": ["student", "study", "education", "college", "career", "exam"],
}


def load_config() -> dict:
    return json.loads(CONFIG.read_text(encoding="utf-8"))


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
    categories = config["categories"]
    results = []

    for candidate in candidates:
        title = candidate.get("title", "").strip()
        if not title:
            continue

        score, matched = score_topic(title, categories)

        if score >= 10:
            results.append({
                "title": title,
                "score": score,
                "matched_keywords": matched,
                "source": candidate.get("source", "manual"),
            })

    return sorted(results, key=lambda item: item["score"], reverse=True)


def main() -> None:
    config = load_config()

    # Temporary local input. A live trend provider will replace this later.
    candidates = [
        {"title": "AI tools for students", "source": "test"},
        {"title": "Best productivity software", "source": "test"},
        {"title": "HTML website optimization guide", "source": "test"},
        {"title": "Random celebrity news", "source": "test"},
    ]

    topics = shortlist(candidates, config)

    OUTPUT.write_text(
        json.dumps(
            {
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "topics": topics,
            },
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )

    print(f"Shortlisted {len(topics)} topics.")


if __name__ == "__main__":
    main()
