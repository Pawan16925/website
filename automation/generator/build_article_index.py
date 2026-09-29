"""Build a modern, SEO-friendly StaxTech guide hub."""

from __future__ import annotations
import html, json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ARTICLES = ROOT / "articles"
SITE_URL = "https://www.staxtech.in"
ADSENSE_CLIENT = "ca-pub-9005733002223091"

def main() -> None:
    items = []
    for meta in ARTICLES.glob("*.json"):
        try: data = json.loads(meta.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError): continue
        if data.get("slug") and data.get("title"): items.append(data)
    items.sort(key=lambda x:x.get("published",""), reverse=True)

    cards = []
    for item in items:
        cards.append(
            f'<article class="stx-card"><p class="stx-kicker">{html.escape(item.get("category","Technology"))} · {html.escape(item.get("intent","guide"))}</p>'
            f'<h2><a href="/articles/{html.escape(item["slug"],quote=True)}.html">{html.escape(item["title"])}</a></h2>'
            f'<p>{html.escape(item.get("description",""))}</p><p class="stx-meta">{html.escape(item.get("published",""))} · Search score {html.escape(str(item.get("topic_score","")))}</p></article>'
        )
    cards_html = "".join(cards) or '<div class="stx-card"><p>No published guides yet. The next eligible technology topic will appear automatically.</p></div>'
    itemlist = [{"@type":"ListItem","position":i+1,"url":f'{SITE_URL}/articles/{x["slug"]}.html',"name":x["title"]} for i,x in enumerate(items)]
    ld = json.dumps({"@context":"https://schema.org","@type":"CollectionPage","name":"StaxTech Technology Guides","url":f"{SITE_URL}/articles/","mainEntity":{"@type":"ItemList","itemListElement":itemlist}}, ensure_ascii=False)

    page = f"""<!doctype html>
<html lang="en-US"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>StaxTech Technology Guides | AI, Software, Web & Student Tech</title>
<meta name="description" content="Fresh StaxTech guides on AI, software, technology updates, web development and student technology, organized around practical search intent.">
<meta name="robots" content="index,follow,max-image-preview:large,max-snippet:-1,max-video-preview:-1">
<link rel="canonical" href="{SITE_URL}/articles/"><link rel="stylesheet" href="/assets/article.css">
<meta property="og:title" content="StaxTech Technology Guides"><meta property="og:description" content="Practical, fresh technology guides from StaxTech."><meta property="og:type" content="website"><meta property="og:url" content="{SITE_URL}/articles/">
<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client={ADSENSE_CLIENT}" crossorigin="anonymous"></script>
<script type="application/ld+json">{ld}</script></head>
<body class="stx-shell"><header class="stx-nav"><div class="stx-nav-inner"><a class="stx-brand" href="/">Stax<span>Tech</span></a><nav><a href="/">Home</a><a href="/articles/">Guides</a></nav></div></header>
<main class="stx-container"><section class="stx-article">
<div class="stx-hero"><p class="stx-kicker">Fresh US technology intelligence</p><h1>Technology Guides</h1><p class="stx-lede">Practical, readable US-focused guides covering high-interest AI, software, web development and student technology topics.</p><div class="stx-meta"><span>{len(items)} guides</span><span>•</span><span>Updated automatically</span></div></div>
<div class="stx-grid">{cards_html}</div></section></main>
<footer class="stx-footer">© <span data-stx-year></span> StaxTech · Practical technology guides</footer><script src="/assets/article.js" defer></script></body></html>"""
    ARTICLES.mkdir(parents=True, exist_ok=True)
    (ARTICLES/"index.html").write_text(page,encoding="utf-8")
    print(f"Built SEO article index with {len(items)} articles.")

if __name__ == "__main__": main()
