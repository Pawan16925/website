"""Production-safe static article generator for StaxTech.

Generates one original, useful HTML guide from a vetted trend candidate.
No external AI API is required.
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
MAX_ARTICLES_PER_RUN = 1
ADSENSE_CLIENT = "ca-pub-9005733002223091"


def slugify(value: str) -> str:
    value = re.sub(r"[^a-z0-9\s-]", "", value.lower())
    value = re.sub(r"\s+", "-", value).strip("-")
    return value[:80].strip("-")


def classify(title: str) -> str:
    t = title.lower()
    if any(x in t for x in ("student", "study", "college", "exam", "career")):
        return "Student Technology"
    if any(x in t for x in ("website", "html", "css", "javascript", "developer", "coding")):
        return "Web Development"
    if any(x in t for x in ("software", "app", "tool", "browser", "productivity", "chrome", "github")):
        return "Software & Tools"
    return "AI & Technology"


def existing_slugs() -> set[str]:
    return {p.stem for p in ARTICLES.glob("*.json")}


def article_body(topic: str, category: str) -> str:
    safe = html.escape(topic)
    if category == "Web Development":
        focus = "website performance, compatibility, accessibility, security, and maintainability"
    elif category == "Student Technology":
        focus = "learning workflow, reliability, privacy, and practical study use"
    elif category == "Software & Tools":
        focus = "features, compatibility, privacy, pricing, and everyday workflow"
    else:
        focus = "what the technology does, compatibility, privacy, reliability, and practical use"

    return f"""
<p><strong>{safe}</strong> is a technology topic currently attracting attention.
This guide explains how to evaluate it without treating a trend as a recommendation.</p>

<h2>What is {safe}?</h2>
<p>The exact details depend on the product, release, or service being discussed.
Before using it, verify the current version, supported devices, official documentation,
and availability in your region.</p>

<h2>What to check first</h2>
<ul>
<li><strong>Purpose:</strong> Identify the specific problem the technology should solve.</li>
<li><strong>Compatibility:</strong> Check supported devices, operating systems, browsers, or software versions.</li>
<li><strong>Privacy:</strong> Review permissions, data collection, account requirements, and sharing controls.</li>
<li><strong>Security:</strong> Prefer official downloads, updates, documentation, and trusted sources.</li>
<li><strong>Cost:</strong> Check free limits, subscriptions, regional pricing, and optional purchases.</li>
</ul>

<h2>Why people are paying attention</h2>
<p>Technology trends can matter because of a new release, product update, feature,
compatibility change, or broader adoption. For <strong>{safe}</strong>, the useful
questions are whether the change affects your workflow and whether the practical
benefit justifies switching or learning it.</p>

<h2>A practical way to evaluate it</h2>
<ol>
<li>Confirm the latest information from the official product or project source.</li>
<li>Write down the exact outcome you want.</li>
<li>Test the smallest useful feature first.</li>
<li>Use non-sensitive information while testing.</li>
<li>Compare the result with your current workflow before making a larger change.</li>
</ol>

<h2>What matters most for this category</h2>
<p>For this type of technology, pay particular attention to <strong>{focus}</strong>.
Those factors usually matter more than popularity alone.</p>

<h2>Common mistakes</h2>
<ul>
<li>Relying on an old version or outdated feature list.</li>
<li>Installing software from an unofficial download source.</li>
<li>Giving an app more permissions than it needs.</li>
<li>Sharing passwords, payment information, or private documents during testing.</li>
<li>Assuming a trending topic is automatically suitable for every user.</li>
</ul>

<h2>Quick checklist</h2>
<table>
<thead><tr><th>Check</th><th>Question</th></tr></thead>
<tbody>
<tr><td>Use case</td><td>Does it solve a specific problem?</td></tr>
<tr><td>Compatibility</td><td>Does it work with my device or workflow?</td></tr>
<tr><td>Security</td><td>Is the source official and is the software maintained?</td></tr>
<tr><td>Privacy</td><td>Do I understand what data is collected?</td></tr>
<tr><td>Value</td><td>Is the benefit worth the time or cost?</td></tr>
</tbody>
</table>

<h2>Bottom line</h2>
<p><strong>{safe}</strong> is worth investigating when it matches a real need.
Verify time-sensitive details with the official source, start with a small test,
and make changes only when the result is useful for your workflow.</p>
"""


def render_page(title: str, description: str, category: str, date: str, canonical: str, topic: str) -> str:
    article_json = json.dumps({
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": title,
        "description": description,
        "datePublished": date,
        "dateModified": date,
        "author": {"@type": "Organization", "name": "StaxTech"},
        "publisher": {"@type": "Organization", "name": "StaxTech"},
        "mainEntityOfPage": {"@type": "WebPage", "@id": canonical}
    }, ensure_ascii=False)

    return f"""<!doctype html>
<html lang="en-IN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)}</title>
<meta name="description" content="{html.escape(description)}">
<link rel="canonical" href="{html.escape(canonical, quote=True)}">
<link rel="stylesheet" href="/assets/article.css">
<meta property="og:title" content="{html.escape(title)}">
<meta property="og:description" content="{html.escape(description)}">
<meta property="og:type" content="article">
<meta property="og:url" content="{html.escape(canonical, quote=True)}">
<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client={ADSENSE_CLIENT}" crossorigin="anonymous"></script>
<script type="application/ld+json">{article_json}</script>
</head>
<body>
<header class="stx-nav"><div class="stx-container"><a href="/">StaxTech</a><a href="/articles/">Guides</a></div></header>
<main class="stx-shell">
<article class="stx-article">
<p><small>{html.escape(category)} · Published {html.escape(date)}</small></p>
<h1>{html.escape(title)}</h1>
{article_body(topic, category)}
</article>
</main>
<footer class="stx-footer"><div class="stx-container">© <span data-year></span> StaxTech</div></footer>
<script src="/assets/article.js" defer></script>
</body>
</html>
"""


def main() -> int:
    if not TOPICS.exists():
        print("Topic candidate file missing; skipping publication.")
        return 0

    try:
        data = json.loads(TOPICS.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        print("Topic candidate JSON is invalid; skipping publication.")
        return 0

    topics = data.get("topics", [])
    if not topics:
        print("No vetted technology topic. Nothing to publish.")
        return 0

    ARTICLES.mkdir(parents=True, exist_ok=True)
    published = 0

    for candidate in topics:
        if published >= MAX_ARTICLES_PER_RUN:
            break

        topic = str(candidate.get("title", "")).strip()
        if not topic:
            continue

        slug = slugify(topic)
        if len(slug) < 4 or slug in existing_slugs():
            continue

        category = classify(topic)
        date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        title = f"{topic}: What It Means and What to Check"
        description = (
            f"StaxTech's practical guide to {topic}, including compatibility, "
            "privacy, security, cost and useful evaluation steps."
        )
        canonical = f"{SITE_URL}/articles/{slug}.html"

        page = render_page(title, description, category, date, canonical, topic)
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
                "source": candidate.get("source", "trend"),
                "source_url": candidate.get("source_url", ""),
                "topic_score": candidate.get("score", 0)
            }, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8"
        )
        print(f"Generated article: {canonical}")
        published += 1

    if published == 0:
        print("No new article was generated (all candidates may already exist).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
