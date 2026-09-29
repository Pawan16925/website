"""
Free StaxTech article generator.

No paid AI API is required.
It turns a relevant trend into a practical, original utility-style article.
"""

from __future__ import annotations

import html
import json
import re
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOPICS = ROOT / "automation" / "data" / "topic-candidates.json"
ARTICLES = ROOT / "articles"
SITE_URL = "https://www.staxtech.in"


def slugify(value: str) -> str:
    value = re.sub(r"[^a-z0-9\s-]", "", value.lower())
    value = re.sub(r"\s+", "-", value).strip("-")
    return value[:75].strip("-")


def classify(title: str) -> str:
    t = title.lower()
    if any(x in t for x in ("student", "study", "college", "exam", "career")):
        return "Student Technology"
    if any(x in t for x in ("website", "html", "css", "javascript", "developer")):
        return "Web Development"
    if any(x in t for x in ("software", "app", "tool", "browser", "productivity")):
        return "Software & Tools"
    return "AI & Technology"


def article_body(topic: str) -> str:
    safe = html.escape(topic)
    return f"""
<p><strong>{safe}</strong> is a topic people are actively searching for.
This practical guide focuses on how to understand the topic, evaluate
options, and use it safely instead of simply repeating a headline.</p>

<h2>What is {safe}?</h2>
<p>The meaning depends on the user's goal. Start by identifying the exact
problem you want to solve before choosing a product, workflow, or method.</p>

<h2>Why it matters</h2>
<p>A useful technology choice should save time, improve a workflow, support
learning, or solve a concrete problem. Popularity alone is not a reason to
adopt something.</p>

<h2>What to check first</h2>
<ul>
<li><strong>Purpose:</strong> Define the result you need.</li>
<li><strong>Ease of use:</strong> Prefer a workflow you can repeat.</li>
<li><strong>Privacy:</strong> Check what information you must share.</li>
<li><strong>Cost:</strong> Check free limits and recurring charges.</li>
<li><strong>Reliability:</strong> Look for documentation and recovery options.</li>
</ul>

<h2>A simple way to get started</h2>
<ol>
<li>Write down the exact outcome you want.</li>
<li>Start with the smallest useful workflow.</li>
<li>Test it using non-sensitive information.</li>
<li>Measure whether it actually saves time or improves the result.</li>
<li>Keep the workflow only if the benefit is clear.</li>
</ol>

<h2>Common mistakes</h2>
<ul>
<li>Choosing a popular option without defining the actual problem.</li>
<li>Sharing passwords or private documents unnecessarily.</li>
<li>Paying before testing the available free workflow.</li>
<li>Assuming a trending topic is automatically the right solution.</li>
</ul>

<h2>Quick checklist</h2>
<table>
<thead><tr><th>Question</th><th>What to look for</th></tr></thead>
<tbody>
<tr><td>Does it solve my problem?</td><td>A specific useful outcome</td></tr>
<tr><td>Is it easy to use?</td><td>A repeatable workflow</td></tr>
<tr><td>Is it safe?</td><td>Clear privacy and security information</td></tr>
<tr><td>Is it affordable?</td><td>Transparent limits and pricing</td></tr>
</tbody>
</table>

<h2>Bottom line</h2>
<p>{safe} is worth exploring when it matches a specific need. Start small,
verify important details yourself, and keep the workflow that produces a
measurable benefit.</p>
"""


def main() -> None:
    data = json.loads(TOPICS.read_text(encoding="utf-8"))
    topics = data.get("topics", [])

    if not topics:
        print("No relevant topic. Nothing to publish.")
        return

    candidate = topics[0]
    topic = candidate["title"].strip()
    slug = slugify(topic)

    if len(slug) < 8:
        print("Topic is too short.")
        return

    category = classify(topic)
    date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    title = f"{topic}: A Practical Guide"
    description = (
        f"A practical StaxTech guide to understanding {topic}, "
        "evaluating options, and getting started."
    )
    canonical = f"{SITE_URL}/articles/{slug}.html"

    page = f"""<!doctype html>
<html lang="en-IN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)}</title>
<meta name="description" content="{html.escape(description)}">
<link rel="canonical" href="{canonical}">\n<link rel="stylesheet" href="/assets/article.css">
<meta property="og:title" content="{html.escape(title)}">
<meta property="og:description" content="{html.escape(description)}">
<meta property="og:type" content="article">
<meta property="og:url" content="{canonical}">\n<!-- Google AdSense -->\n<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-9005733002223091" crossorigin="anonymous"></script>
<script type="application/ld+json">
{json.dumps({
    "@context": "https://schema.org",
    "@type": "Article",
    "headline": title,
    "description": description,
    "datePublished": date,
    "dateModified": date,
    "author": {"@type": "Organization", "name": "StaxTech"},
    "publisher": {"@type": "Organization", "name": "StaxTech"},
    "mainEntityOfPage": canonical
}, ensure_ascii=False)}
</script>
</head>
<body>
<main>
<article>
<p><small>{category} · Published {date}</small></p>
<h1>{html.escape(title)}</h1>
{article_body(topic)}
</article>
</main>
</body>
</html>
"""

    ARTICLES.mkdir(parents=True, exist_ok=True)
    (ARTICLES / f"{slug}.html").write_text(page, encoding="utf-8")
    (ARTICLES / f"{slug}.json").write_text(
        json.dumps({
            "title": title,
            "slug": slug,
            "description": description,
            "category": category,
            "url": canonical,
            "published": date,
            "source_topic": topic,
            "source": candidate.get("source", "trend")
        }, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8"
    )

    print(f"Generated article: {slug}")


if __name__ == "__main__":
    main()
