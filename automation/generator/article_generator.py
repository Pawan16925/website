"""Advanced SEO-focused static article generator for StaxTech."""

from __future__ import annotations
import html, json, re
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOPICS = ROOT / "automation" / "data" / "topic-candidates.json"
ARTICLES = ROOT / "articles"
SITE_URL = "https://www.staxtech.in"
ADSENSE_CLIENT = "ca-pub-9005733002223091"

def slugify(value: str) -> str:
    value = re.sub(r"[^a-z0-9\s-]", "", value.lower())
    return re.sub(r"\s+", "-", value).strip("-")[:80].strip("-")

def classify(title: str) -> str:
    t = title.lower()
    if any(x in t for x in ("student","study","college","exam","career")): return "Student Technology"
    if any(x in t for x in ("website","html","css","javascript","developer","coding","programming")): return "Web Development"
    if any(x in t for x in ("software","app","tool","browser","productivity","chrome","github")): return "Software & Tools"
    return "AI & Technology"

def intent_title(topic: str, intent: str) -> str:
    if intent == "how-to": return f"{topic}: How It Works, Setup Steps and Key Tips"
    if intent == "comparison": return f"{topic}: Key Differences, Features and What to Check"
    if intent == "update": return f"{topic}: Latest Update, Features and What to Know"
    if intent == "review": return f"{topic}: Features, Compatibility, Privacy and Practical Review"
    return f"{topic}: Explained, Features and What to Know"

def related_items(slug: str) -> list[dict]:
    items = []
    for meta in ARTICLES.glob("*.json"):
        try: data = json.loads(meta.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError): continue
        if data.get("slug") and data.get("title") and data["slug"] != slug: items.append(data)
    return items[:4]

def article_body(topic: str, category: str, intent: str, related: list[dict]) -> str:
    safe = html.escape(topic)
    focus = {
        "Web Development":"performance, accessibility, compatibility, security, and maintainability",
        "Student Technology":"learning workflow, reliability, privacy, and practical study use",
        "Software & Tools":"features, compatibility, privacy, pricing, and workflow"
    }.get(category, "features, compatibility, privacy, security, reliability, and practical use")
    related_html = "".join(f'<li><a href="/articles/{html.escape(x["slug"],quote=True)}.html">{html.escape(x["title"])}</a></li>' for x in related)
    return f"""
<section class="stx-summary"><span class="stx-summary-label">Quick answer</span>
<p>{safe} is a technology topic attracting current search attention. The useful way to evaluate it is to identify what changed, who it helps, what devices or software it supports, and which details need verification from the official source.</p></section>
<h2>What is {safe}?</h2>
<p>{safe} may refer to a product, feature, software release, platform or technology change. Because technology details can change quickly, this guide focuses on practical evaluation rather than repeating unverified claims.</p>
<h2>Why is {safe} getting attention?</h2>
<p>Search interest commonly rises after a launch, update, feature announcement, compatibility change or wider adoption. Popularity is a signal of attention, not proof that something is right for every user.</p>
<h2>Key features and things to check</h2>
<div class="stx-check-grid">
<div class="stx-mini"><strong>Compatibility</strong><span>Devices, operating systems, browsers and supported versions.</span></div>
<div class="stx-mini"><strong>Features</strong><span>What is included, changed or limited by plan or device.</span></div>
<div class="stx-mini"><strong>Privacy</strong><span>Permissions, accounts, data collection and sharing controls.</span></div>
<div class="stx-mini"><strong>Security</strong><span>Official sources, updates, permissions and safe installation.</span></div></div>
<h2>How to evaluate {safe}</h2>
<ol><li>Check the latest official product, project or developer information.</li><li>Define the exact problem you want to solve.</li><li>Confirm device, operating-system, browser and regional compatibility.</li><li>Test the smallest useful feature before changing your whole workflow.</li><li>Avoid entering passwords, payment data or sensitive documents during early testing.</li><li>Compare the result with your current setup before committing time or money.</li></ol>
<h2>What matters most for {html.escape(category)}</h2>
<p>For this category, pay particular attention to <strong>{html.escape(focus)}</strong>. A high-search topic is not automatically a useful technology choice; fit and reliability matter too.</p>
<h2>Common mistakes to avoid</h2>
<ul><li>Using an outdated version or old feature list.</li><li>Installing software from unofficial download sources.</li><li>Granting unnecessary permissions.</li><li>Assuming a trending topic is suitable for every device or user.</li><li>Making a large workflow change before testing a small use case.</li></ul>
<h2>Frequently asked questions</h2>
<details open><summary>Is {safe} worth trying?</summary><p>It depends on the use case, compatibility, privacy requirements and expected benefit. A small reversible test is a sensible starting point.</p></details>
<details><summary>Is {safe} available for everyone?</summary><p>Availability can vary by device, operating system, region, account type and release stage. Check the official source for the current status.</p></details>
<details><summary>Where should I get the latest information?</summary><p>Use the official product or project website, documentation, release notes or verified announcement channel for time-sensitive details.</p></details>
<h2>Quick checklist</h2>
<table><thead><tr><th>Check</th><th>Question</th></tr></thead><tbody>
<tr><td>Intent</td><td>Am I looking for information, setup help, comparison or an update?</td></tr>
<tr><td>Compatibility</td><td>Does it work with my device and workflow?</td></tr>
<tr><td>Security</td><td>Is the source official?</td></tr>
<tr><td>Privacy</td><td>Do I understand permissions and data collection?</td></tr>
<tr><td>Value</td><td>Does it solve a real problem?</td></tr></tbody></table>
<h2>Related StaxTech guides</h2>
<ul>{related_html or "<li>More related guides will appear automatically as the library grows.</li>"}</ul>
<h2>Bottom line</h2>
<p>{safe} deserves attention when it connects to a real need. For fast-moving topics, verify current details from primary sources and test changes before making a larger commitment.</p>
"""

def render_page(title: str, description: str, category: str, date: str, canonical: str, topic: str, intent: str, related: list[dict]) -> str:
    faq = [
        {"@type":"Question","name":f"Is {topic} worth trying?","acceptedAnswer":{"@type":"Answer","text":"It depends on the use case, compatibility, privacy requirements and expected benefit."}},
        {"@type":"Question","name":f"Is {topic} available for everyone?","acceptedAnswer":{"@type":"Answer","text":"Availability can vary by device, operating system, region, account type and release stage."}},
        {"@type":"Question","name":"Where should I get the latest information?","acceptedAnswer":{"@type":"Answer","text":"Use the official product or project website, documentation, release notes or verified announcement channel."}}
    ]
    article_ld = json.dumps({"@context":"https://schema.org","@type":"Article","headline":title,"description":description,"datePublished":date,"dateModified":date,"inLanguage":"en-IN","author":{"@type":"Organization","name":"StaxTech"},"publisher":{"@type":"Organization","name":"StaxTech"},"mainEntityOfPage":{"@type":"WebPage","@id":canonical},"keywords":[topic,category,intent,"technology guide","StaxTech"]}, ensure_ascii=False)
    faq_ld = json.dumps({"@context":"https://schema.org","@type":"FAQPage","mainEntity":faq}, ensure_ascii=False)
    return f"""<!doctype html>
<html lang="en-IN"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)}</title><meta name="description" content="{html.escape(description)}">
<meta name="robots" content="index,follow,max-image-preview:large,max-snippet:-1,max-video-preview:-1">
<link rel="canonical" href="{html.escape(canonical,quote=True)}"><link rel="stylesheet" href="/assets/article.css">
<meta property="og:site_name" content="StaxTech"><meta property="og:title" content="{html.escape(title)}"><meta property="og:description" content="{html.escape(description)}"><meta property="og:type" content="article"><meta property="og:url" content="{html.escape(canonical,quote=True)}">
<meta name="twitter:card" content="summary_large_image"><meta name="twitter:title" content="{html.escape(title)}"><meta name="twitter:description" content="{html.escape(description)}">
<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client={ADSENSE_CLIENT}" crossorigin="anonymous"></script>
<script type="application/ld+json">{article_ld}</script><script type="application/ld+json">{faq_ld}</script></head>
<body class="stx-shell"><header class="stx-nav"><div class="stx-nav-inner"><a class="stx-brand" href="/">Stax<span>Tech</span></a><nav><a href="/">Home</a><a href="/articles/">Guides</a></nav></div></header>
<main class="stx-container"><article class="stx-article"><div class="stx-hero"><p class="stx-kicker">{html.escape(category)} · {html.escape(intent)}</p><h1>{html.escape(title)}</h1><p class="stx-lede">{html.escape(description)}</p><div class="stx-meta"><span>Published {date}</span><span>•</span><span>StaxTech Technology Guide</span></div></div>{article_body(topic,category,intent,related)}</article></main>
<footer class="stx-footer">© <span data-stx-year></span> StaxTech · Practical technology guides</footer><script src="/assets/article.js" defer></script></body></html>"""

def main() -> int:
    if not TOPICS.exists(): return 0
    try: data = json.loads(TOPICS.read_text(encoding="utf-8"))
    except json.JSONDecodeError: return 0
    topics = data.get("topics", [])
    if not topics: return 0
    ARTICLES.mkdir(parents=True, exist_ok=True)
    existing = {p.stem for p in ARTICLES.glob("*.json")}
    for candidate in topics:
        topic = str(candidate.get("title","")).strip()
        slug = slugify(topic)
        if len(slug) < 4 or slug in existing: continue
        category = classify(topic); intent = candidate.get("intent","informational")
        date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        title = intent_title(topic,intent)
        description = f"Understand {topic}: current context, key features, compatibility, privacy, security and practical steps in this StaxTech guide."
        canonical = f"{SITE_URL}/articles/{slug}.html"
        (ARTICLES/f"{slug}.html").write_text(render_page(title,description,category,date,canonical,topic,intent,related_items(slug)),encoding="utf-8")
        (ARTICLES/f"{slug}.json").write_text(json.dumps({"title":title,"slug":slug,"description":description,"category":category,"intent":intent,"url":canonical,"published":date,"source_topic":topic,"source":candidate.get("source","trend"),"source_url":candidate.get("source_url",""),"topic_score":candidate.get("score",0),"demand_score":candidate.get("demand_score",0)},indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
        print(f"Generated SEO article: {canonical} | score={candidate.get('score',0)} | intent={intent}")
        return 0
    print("No new article was generated.")
    return 0

if __name__ == "__main__": raise SystemExit(main())
