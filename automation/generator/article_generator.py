"""
Generate one StaxTech article from the highest-scoring topic candidate.
Requires OPENAI_API_KEY in the GitHub Actions environment.
"""

from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[2]
TOPICS = ROOT / "automation" / "data" / "topic-candidates.json"
ARTICLES = ROOT / "articles"
SITE_URL = "https://www.staxtech.in"
MODEL = os.getenv("OPENAI_MODEL", "gpt-5.6-luna")


def slugify(value: str) -> str:
    value = re.sub(r"[^a-z0-9\s-]", "", value.lower())
    value = re.sub(r"\s+", "-", value).strip("-")
    return value[:80]


def call_openai(topic: str) -> dict:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not configured.")

    prompt = f"""
You are the StaxTech technology editor.

Create ONE genuinely useful, original article about:
{topic}

Rules:
- Do not copy or rewrite another article.
- Do not invent statistics, quotes, prices, or current-event claims.
- Do not cover politics, elections, medical diagnosis/treatment, legal advice,
  gambling, adult content, weapons, or financial investment advice.
- If the topic is ambiguous or unsafe, return publish=false.
- Use clear English and practical examples.
- Avoid keyword stuffing and clickbait.
- Return ONLY valid JSON with keys:
  publish, title, description, category, html, sources
- html may contain only h2,h3,p,ul,ol,li,strong,table,thead,tbody,tr,th,td.
- sources must be an array of URLs only when actually relied upon.
- Aim for 900-1400 words.
"""

    payload = json.dumps({
        "model": MODEL,
        "input": prompt,
        "max_output_tokens": 6000
    }).encode("utf-8")

    request = Request(
        "https://api.openai.com/v1/responses",
        data=payload,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        },
        method="POST"
    )

    with urlopen(request, timeout=120) as response:
        result = json.loads(response.read().decode("utf-8"))

    text = result.get("output_text", "").strip()
    if not text:
        raise RuntimeError("OpenAI returned no text.")

    return json.loads(text)


def main() -> None:
    data = json.loads(TOPICS.read_text(encoding="utf-8"))
    topics = data.get("topics", [])

    if not topics:
        print("No suitable topic found. Nothing to publish.")
        return

    article = call_openai(topics[0]["title"])

    if not article.get("publish"):
        print("Quality gate rejected the topic.")
        return

    title = article["title"].strip()
    slug = slugify(title)
    if not slug:
        raise RuntimeError("Could not create a valid article slug.")

    date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    canonical = f"{SITE_URL}/articles/{slug}.html"

    html = f"""<!doctype html>
<html lang="en-IN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>{article["title"]}</title>
  <meta name="description" content="{article["description"]}">
  <link rel="canonical" href="{canonical}">
  <meta property="og:title" content="{article["title"]}">
  <meta property="og:description" content="{article["description"]}">
  <meta property="og:type" content="article">
  <meta property="og:url" content="{canonical}">
</head>
<body>
  <main>
    <article>
      <p><small>Published {date} · StaxTech</small></p>
      <h1>{article["title"]}</h1>
      {article["html"]}
    </article>
  </main>
</body>
</html>
"""

    ARTICLES.mkdir(parents=True, exist_ok=True)
    (ARTICLES / f"{slug}.html").write_text(html, encoding="utf-8")
    (ARTICLES / f"{slug}.json").write_text(
        json.dumps({
            "title": title,
            "slug": slug,
            "description": article["description"],
            "category": article.get("category", "Technology"),
            "url": canonical,
            "published": date,
            "sources": article.get("sources", [])
        }, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8"
    )

    print(f"Generated article: {slug}")


if __name__ == "__main__":
    main()
