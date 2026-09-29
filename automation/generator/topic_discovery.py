"""Advanced StaxTech topic discovery using demand, freshness and search intent signals."""

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
    "AI & Technology": ["ai","artificial intelligence","technology","tech","automation","android","iphone","ios","windows","macos","linux","google","microsoft","apple","samsung","oppo","vivo","oneplus","realme","xiaomi","pixel","coloros","oxygenos","hyperos","one ui","gemini","chatgpt","copilot","claude","openai","processor","chip","gpu","software","update","launch","release","cybersecurity","cloud","robot","developer","browser"],
    "Software & Tools": ["software","tool","app","apps","saas","browser","productivity","chrome","edge","firefox","whatsapp","telegram","instagram","youtube","notion","canva","github","microsoft 365","google workspace"],
    "Web Development": ["website","web","html","css","javascript","developer","coding","programming","api","react","node","python","wordpress"],
    "Student Technology": ["student","study","education","college","career","exam","learning","online course","scholarship"],
}
EXCLUDED_TERMS = ["lottery","satta","matka","horoscope","astrology","celebrity","movie","film","song","cricket","football","election","politics","politician","party","minister","crime","murder","weather","stock price","share price","betting","casino"]
INTENT_PHRASES = [
    ("how to","how-to"),("how do","how-to"),("guide","how-to"),("tutorial","how-to"),
    ("what is","informational"),("meaning","informational"),("explained","informational"),
    ("latest","update"),("update","update"),("new","update"),("release","update"),("launch","update"),
    ("vs","comparison"),("versus","comparison"),("compare","comparison"),("review","review"),
    ("features","features"),("price","commercial"),
]

def load_json(path: Path, default: dict) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default

def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip().lower())

def infer_intent(title: str) -> str:
    text = normalize(title)
    for phrase, intent in INTENT_PHRASES:
        if phrase in text:
            return intent
    return "informational"

def demand_score(item: dict) -> int:
    raw = str(item.get("approx_traffic", "")).replace(",", "").lower()
    for marker, score in [("500k",35),("200k",32),("100k",30),("50k",27),("20k",24),("10k",21),("5k",18),("2k",14)]:
        if marker in raw:
            return score
    try:
        return min(35, max(0, round(float(raw) / 200)))
    except ValueError:
        return 0

def relevance_score(title: str, categories: list[str]) -> tuple[int,list[str]]:
    text = normalize(title)
    if any(term in text for term in EXCLUDED_TERMS):
        return 0, []
    matched, score = [], 0
    for category in categories:
        for keyword in KEYWORDS.get(category, []):
            if keyword in text:
                matched.append(keyword)
                score += 7
    if re.search(r"\b(?:android|ios|windows|macos|linux)\s+\d", text):
        matched.append("operating-system-version"); score += 18
    if re.search(r"\b(?:coloros|oxygenos|hyperos|one ui)\s*\d", text):
        matched.append("mobile-os-version"); score += 22
    if re.search(r"\b(?:ai|app|software|update|launch|release|latest|new)\b", text):
        score += 6
    return min(score, 55), sorted(set(matched))

def main() -> None:
    config = load_json(CONFIG, {})
    trends = load_json(TREND_INPUT, {"topics":[]}).get("topics", [])
    gsc = load_json(GSC_INPUT, {"topics":[]}).get("topics", [])
    candidates = []

    for item in trends:
        title = item.get("title", "")
        rel, matched = relevance_score(title, config.get("categories", []))
        if rel < 8: continue
        demand = demand_score(item)
        intent = infer_intent(title)
        intent_bonus = 10 if intent in {"how-to","update","comparison"} else 5
        candidates.append({
            "title": title, "score": min(100, rel + demand + intent_bonus),
            "relevance_score": rel, "demand_score": demand, "freshness_score": 20,
            "intent": intent, "matched_keywords": matched,
            "source": item.get("source","Google Trends"), "source_url": item.get("source_url",""),
            "approx_traffic": item.get("approx_traffic",""), "published": item.get("published",""),
            "geo": item.get("geo","")
        })

    for item in gsc:
        title = item.get("title", "")
        rel, matched = relevance_score(title, config.get("categories", []))
        if rel < 8: continue
        impressions = float(item.get("impressions",0) or 0)
        clicks = float(item.get("clicks",0) or 0)
        position = float(item.get("position",0) or 0)
        opportunity = min(30, round(impressions / 10))
        position_bonus = 8 if 5 <= position <= 30 else (4 if 1 <= position <= 50 else 0)
        intent = infer_intent(title)
        candidates.append({
            "title": title,
            "score": min(100, rel + opportunity + position_bonus + (6 if clicks == 0 and impressions > 10 else 0)),
            "relevance_score": rel, "demand_score": opportunity, "freshness_score": 10,
            "intent": intent, "matched_keywords": matched + ["search-console-query"],
            "source": "Google Search Console", "source_url": item.get("source_url",""),
            "clicks": clicks, "impressions": impressions, "ctr": item.get("ctr",0),
            "position": position
        })

    unique = {}
    for item in candidates:
        key = normalize(item["title"])
        if key not in unique or item["score"] > unique[key]["score"]:
            unique[key] = item
    topics = sorted(unique.values(), key=lambda x:(x["score"],x.get("demand_score",0)), reverse=True)

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps({
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "strategy": "demand + relevance + freshness + search-intent opportunity",
        "trend_input_count": len(trends), "search_console_input_count": len(gsc),
        "shortlisted_count": len(topics), "topics": topics
    }, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Processed {len(trends)} Trends + {len(gsc)} Search Console queries; shortlisted {len(topics)} topics.")
    if topics:
        print(f"Top topic: {topics[0]['title']} | score={topics[0]['score']} | intent={topics[0]['intent']}")
    else:
        print("No suitable technology topic found; publication will be skipped.")

if __name__ == "__main__":
    main()
