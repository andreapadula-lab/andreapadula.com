#!/usr/bin/env python3
"""Build the AI & Financial Services series from Medium-ready Markdown drafts."""

from __future__ import annotations

import argparse
import html
import json
import math
import re
from datetime import date
from pathlib import Path

import markdown


SITE_URL = "https://andreapadula.com"
AUTHOR_ID = f"{SITE_URL}/#person"
SERIES_SLUG = "ai-financial-services"
SERIES_URL = f"{SITE_URL}/{SERIES_SLUG}.html"
AUTHOR_IMAGE_URL = f"{SITE_URL}/andrea-padula.png"

LEGACY_ARTICLES = {
    "the-bank-of-2030": ("The Bank of 2030 Has 10x the Clients and Half the People", "June 2025"),
    "what-i-see-selling-ai-to-european-banks": ("What I See Selling AI to European Banks", "October 2024"),
    "most-ai-products-fail": ("Most AI Products Fail — Not Because of the Tech", "February 2025"),
    "why-banks-keep-buying-ai-they-will-never-use": ("Why Banks Keep Buying AI They’ll Never Use", "March 2025"),
    "the-eu-ai-act-is-a-competitive-advantage": ("The EU AI Act Is a Competitive Advantage", "April 2025"),
    "the-pilot-trap": ("The Pilot Trap", "May 2025"),
}


def parse_args() -> argparse.Namespace:
    root = Path(__file__).resolve().parents[1]
    default_drafts = root.parent / "medium"
    parser = argparse.ArgumentParser()
    parser.add_argument("--drafts", type=Path, default=default_drafts)
    parser.add_argument("--site", type=Path, default=root)
    parser.add_argument("--manifest", type=Path, default=Path(__file__).with_name("ai-series.json"))
    return parser.parse_args()


def read_draft(path: Path) -> tuple[str, str, str, int]:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    if not lines or not lines[0].startswith("# "):
        raise ValueError(f"Missing H1 in {path}")

    draft_title = lines[0][2:].strip()
    cursor = 1
    while cursor < len(lines) and not lines[cursor].strip():
        cursor += 1

    subtitle = ""
    if cursor < len(lines):
        candidate = lines[cursor].strip()
        if candidate.startswith("*") and candidate.endswith("*") and not candidate.startswith("**"):
            subtitle = candidate[1:-1].strip()
            cursor += 1

    body = "\n".join(lines[cursor:]).strip()
    footer_markers = [
        "\n---\n\n*Originally published",
        "\n---\n\nOriginally published",
    ]
    for marker in footer_markers:
        if marker in body:
            body = body.split(marker, 1)[0].rstrip()
            break

    body_html = markdown.markdown(body, extensions=["sane_lists", "toc"])
    source_match = re.search(r'(<h2 id="sources">Sources</h2>)\s*<ul>(.*?)</ul>', body_html, flags=re.DOTALL)
    if source_match:
        source_items = re.findall(r"<li>(.*?)</li>", source_match.group(2), flags=re.DOTALL)
        source_rows = "\n".join(f'<p class="source-item">• {item}</p>' for item in source_items)
        replacement = f'{source_match.group(1)}\n<div class="sources-list">\n{source_rows}\n</div>'
        body_html = body_html[: source_match.start()] + replacement + body_html[source_match.end() :]
    plain = re.sub(r"https?://\S+", " ", body)
    plain = re.sub(r"[#*_>`\[\]()—–-]", " ", plain)
    word_count = len(re.findall(r"\b[\w’']+\b", plain))
    return draft_title, subtitle, body_html, word_count


def title_key(value: str) -> str:
    value = value.replace("“", '"').replace("”", '"').replace("’", "'").replace("‘", "'")
    value = value.replace('"', "").rstrip(".")
    return re.sub(r"\s+", " ", value).strip().casefold()


def article_lookup(manifest: dict) -> dict[str, tuple[str, str]]:
    published = date.fromisoformat(manifest["published"]).strftime("%B %Y")
    lookup = dict(LEGACY_ARTICLES)
    for article in manifest["articles"]:
        lookup[article["slug"]] = (article["title"], published)
    return lookup


def json_ld_article(article: dict, word_count: int, published: str) -> str:
    url = f"{SITE_URL}/{article['slug']}.html"
    article_image = f"{SITE_URL}/assets/articles/{article['slug']}.png"
    graph = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "BlogPosting",
                "@id": f"{url}#article",
                "headline": article["title"],
                "description": article["description"],
                "datePublished": published,
                "dateModified": published,
                "inLanguage": "en",
                "wordCount": word_count,
                "image": {"@type": "ImageObject", "url": article_image, "width": 1200, "height": 630},
                "author": {"@id": AUTHOR_ID},
                "publisher": {"@id": AUTHOR_ID},
                "mainEntityOfPage": {"@type": "WebPage", "@id": url},
                "isPartOf": {"@type": "CollectionPage", "@id": SERIES_URL},
                "about": [
                    {"@type": "Thing", "name": "Artificial intelligence in financial services"},
                    {"@type": "Thing", "name": "Banking"},
                ],
                "keywords": article["keywords"],
            },
            {
                "@type": "Person",
                "@id": AUTHOR_ID,
                "name": "Andrea Padula",
                "url": f"{SITE_URL}/about.html",
                "image": AUTHOR_IMAGE_URL,
                "jobTitle": "Head of Partnerships & Business Development",
                "worksFor": {"@type": "Organization", "name": "Streetbeat", "url": "https://streetbeat.com"},
                "sameAs": [
                    "https://www.linkedin.com/in/andreapadula/",
                    "https://medium.com/@padula.andrea",
                ],
            },
            {
                "@type": "BreadcrumbList",
                "itemListElement": [
                    {"@type": "ListItem", "position": 1, "name": "Home", "item": f"{SITE_URL}/"},
                    {"@type": "ListItem", "position": 2, "name": "AI & Financial Services", "item": SERIES_URL},
                    {"@type": "ListItem", "position": 3, "name": article["title"], "item": url},
                ],
            },
        ],
    }
    return json.dumps(graph, ensure_ascii=False, indent=8)


def render_related(article: dict, lookup: dict[str, tuple[str, str]]) -> str:
    rows = []
    for slug in article["related"]:
        title, _ = lookup[slug]
        rows.append(
            f'''            <a class="related-link" href="{html.escape(slug)}.html">
                <span>{html.escape(title)}</span><span aria-hidden="true">→</span>
            </a>'''
        )
    return "\n".join(rows)


def render_article(article: dict, index: int, total: int, subtitle: str, body_html: str, word_count: int, published: str, lookup: dict[str, tuple[str, str]]) -> str:
    title = html.escape(article["title"])
    description = html.escape(article["description"], quote=True)
    url = f"{SITE_URL}/{article['slug']}.html"
    article_image = f"{SITE_URL}/assets/articles/{article['slug']}.png"
    reading_time = max(1, math.ceil(word_count / 220))
    tags = "\n".join(
        f'    <meta property="article:tag" content="{html.escape(keyword, quote=True)}">'
        for keyword in article["keywords"]
    )
    ld_json = json_ld_article(article, word_count, published)
    related = render_related(article, lookup)
    visible_date = date.fromisoformat(published).strftime("%B %d, %Y").replace(" 0", " ")

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} — Andrea Padula</title>
    <meta name="description" content="{description}">
    <meta name="author" content="Andrea Padula">
    <meta name="keywords" content="{html.escape(', '.join(article['keywords']), quote=True)}">
    <link rel="canonical" href="{url}">
    <meta property="og:site_name" content="Andrea Padula">
    <meta property="og:title" content="{title}">
    <meta property="og:description" content="{description}">
    <meta property="og:image" content="{article_image}">
    <meta property="og:image:alt" content="{title} — Andrea Padula">
    <meta property="og:image:width" content="1200">
    <meta property="og:image:height" content="630">
    <meta property="og:url" content="{url}">
    <meta property="og:type" content="article">
    <meta property="article:published_time" content="{published}">
    <meta property="article:modified_time" content="{published}">
    <meta property="article:author" content="{SITE_URL}/about.html">
    <meta property="article:section" content="AI &amp; Financial Services">
{tags}
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:title" content="{title}">
    <meta name="twitter:description" content="{description}">
    <meta name="twitter:image" content="{article_image}">
    <script type="application/ld+json">
{ld_json}
    </script>
    <link rel="stylesheet" href="assets/article.css">
</head>
<body>
<div class="progress-bar" id="progressBar"></div>
<nav class="site-nav" aria-label="Primary navigation">
    <div class="nav-inner">
        <a class="brand" href="/">Andrea Padula</a>
        <div class="nav-links">
            <a href="{SERIES_SLUG}.html">AI Series</a>
            <a href="about.html">About</a>
            <a href="https://www.linkedin.com/in/andreapadula/" rel="me">LinkedIn</a>
        </div>
    </div>
</nav>

<header class="article-hero">
    <div class="hero-inner">
        <div class="eyebrow">AI &amp; Financial Services · Essay {index:02d}/{total:02d}</div>
        <h1>{title}</h1>
        <p class="hero-subtitle">{html.escape(subtitle)}</p>
        <div class="article-meta">
            <a href="about.html" rel="author">Andrea Padula</a>
            <span class="meta-dot">{visible_date}</span>
            <span class="meta-dot">{reading_time} min read</span>
        </div>
    </div>
</header>

<main>
    <div class="article-shell">
        <article class="article-body">
{body_html}
        </article>
        <aside class="article-aside" aria-label="About this series">
            <div class="aside-card">
                <div class="aside-label">The series</div>
                <p>Ten evidence-led essays on what works, what fails, and where AI in financial services is going next.</p>
                <a href="{SERIES_SLUG}.html">Explore all ten →</a>
            </div>
        </aside>
    </div>

    <section class="related-section" aria-labelledby="related-heading">
        <div class="section-kicker" id="related-heading">Continue reading</div>
        <div class="related-links">
{related}
        </div>
    </section>

    <section class="author-box" aria-label="About the author">
        <div class="author-inner">
            <a href="about.html"><img src="andrea-padula.png" alt="Andrea Padula" width="66" height="66"></a>
            <div class="author-copy">
                <h2><a href="about.html">Andrea Padula</a></h2>
                <p>Head of Partnerships &amp; Business Development at Streetbeat. Writing from Milan about AI, financial services, and the bridge between European banking and Silicon Valley technology.</p>
                <p class="disclosure">Andrea leads Partnerships &amp; BD at Streetbeat; views are personal.</p>
            </div>
        </div>
    </section>
</main>

<footer class="site-footer">
    <p>© 2026 Andrea Padula · <a href="{SERIES_SLUG}.html">AI &amp; Financial Services</a> · <a href="mailto:andreapadula@streetbeat.com">Contact</a></p>
</footer>
<script src="assets/article.js" defer></script>
</body>
</html>
'''


def json_ld_series(manifest: dict) -> str:
    items = [
        {
            "@type": "ListItem",
            "position": index,
            "name": article["title"],
            "url": f"{SITE_URL}/{article['slug']}.html",
        }
        for index, article in enumerate(manifest["articles"], start=1)
    ]
    graph = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "CollectionPage",
                "@id": SERIES_URL,
                "url": SERIES_URL,
                "name": "AI in Financial Services: What Works, What Doesn’t, and What Comes Next",
                "description": "Ten evidence-led essays by Andrea Padula on AI adoption, governance, agents, wealth management, procurement, and the future of banking.",
                "inLanguage": "en",
                "datePublished": manifest["published"],
                "dateModified": manifest["published"],
                "author": {"@id": AUTHOR_ID},
                "mainEntity": {"@type": "ItemList", "numberOfItems": len(items), "itemListElement": items},
            },
            {
                "@type": "Person",
                "@id": AUTHOR_ID,
                "name": "Andrea Padula",
                "url": f"{SITE_URL}/about.html",
                "image": AUTHOR_IMAGE_URL,
                "jobTitle": "Head of Partnerships & Business Development",
                "sameAs": ["https://www.linkedin.com/in/andreapadula/", "https://medium.com/@padula.andrea"],
            },
        ],
    }
    return json.dumps(graph, ensure_ascii=False, indent=8)


def render_series(manifest: dict, drafts: dict[str, dict]) -> str:
    cards = []
    for index, article in enumerate(manifest["articles"], start=1):
        draft = drafts[article["slug"]]
        reading_time = max(1, math.ceil(draft["word_count"] / 220))
        cards.append(
            f'''        <a class="series-card" href="{html.escape(article['slug'])}.html">
            <div class="card-number">ESSAY {index:02d}</div>
            <h2>{html.escape(article['title'])}</h2>
            <p>{html.escape(article['description'])}</p>
            <div class="card-meta">{reading_time} min read · Primary sources</div>
            <span class="card-arrow" aria-hidden="true">→</span>
        </a>'''
        )
    cards_html = "\n".join(cards)
    ld_json = json_ld_series(manifest)
    description = "Ten evidence-led essays on AI in financial services: what creates value, what fails in production, and where banking and wealth management go next."

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI in Financial Services: What Works and What Comes Next — Andrea Padula</title>
    <meta name="description" content="{html.escape(description, quote=True)}">
    <meta name="author" content="Andrea Padula">
    <meta name="keywords" content="AI in financial services, AI in banking, banking AI use cases, AI governance, agentic AI banking, wealth management AI">
    <link rel="canonical" href="{SERIES_URL}">
    <meta property="og:site_name" content="Andrea Padula">
    <meta property="og:title" content="AI in Financial Services: What Works, What Doesn’t, and What Comes Next">
    <meta property="og:description" content="{html.escape(description, quote=True)}">
    <meta property="og:image" content="{SITE_URL}/assets/articles/{SERIES_SLUG}.png">
    <meta property="og:image:alt" content="AI in Financial Services — a ten-essay field guide by Andrea Padula">
    <meta property="og:image:width" content="1200">
    <meta property="og:image:height" content="630">
    <meta property="og:url" content="{SERIES_URL}">
    <meta property="og:type" content="website">
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:title" content="AI in Financial Services: What Works and What Comes Next">
    <meta name="twitter:description" content="{html.escape(description, quote=True)}">
    <meta name="twitter:image" content="{SITE_URL}/assets/articles/{SERIES_SLUG}.png">
    <script type="application/ld+json">
{ld_json}
    </script>
    <link rel="stylesheet" href="assets/article.css">
</head>
<body>
<nav class="site-nav" aria-label="Primary navigation">
    <div class="nav-inner">
        <a class="brand" href="/">Andrea Padula</a>
        <div class="nav-links">
            <a href="/">Home</a>
            <a href="about.html">About</a>
            <a href="https://medium.com/@padula.andrea" rel="me">Medium</a>
        </div>
    </div>
</nav>

<header class="series-hero">
    <div class="hero-inner">
        <div class="eyebrow">A ten-essay field guide</div>
        <h1>AI in Financial Services: What Works, What Doesn’t, and What Comes Next</h1>
        <p class="hero-subtitle">The model is only the beginning. The real questions are about workflows, authority, economics, trust, and who learns fastest.</p>
    </div>
</header>

<main>
    <section class="series-intro" aria-label="About the series">
        <div class="series-copy">
            <p>Financial institutions are no longer asking whether AI will matter. They are trying to separate useful systems from convincing demos—and move from experiments to accountable work.</p>
            <p>This series examines that transition from the operator’s side: <strong>what reaches production, what breaks, how governance must change, and where durable advantage will remain when capable models are available to everyone.</strong></p>
            <p>The essays draw on current evidence from the ECB, Bank of England, FCA, BIS, EBA, FSB, European legislation, and financial institutions deploying AI at scale.</p>
        </div>
        <aside class="series-note">
            <div class="label">Editorial standard</div>
            <p>Primary or first-party sources. Company figures identified as company-reported. No invented client stories or anonymous quotations. Current as of October 2026.</p>
        </aside>
    </section>

    <section class="series-grid" aria-label="Ten essays">
{cards_html}
    </section>

    <section class="series-cta">
        <div class="series-cta-inner">
            <h2>Working on AI inside a financial institution?</h2>
            <p>I speak with banks, wealth managers, and technology teams about adoption, partnerships, and the gap between a promising model and a working process.</p>
            <a class="button" href="mailto:andreapadula@streetbeat.com">Start a conversation</a>
        </div>
    </section>
</main>

<footer class="site-footer">
    <p>© 2026 Andrea Padula · <a href="about.html">About</a> · <a href="https://www.linkedin.com/in/andreapadula/">LinkedIn</a> · <a href="https://medium.com/@padula.andrea">Medium</a></p>
</footer>
</body>
</html>
'''


def main() -> None:
    args = parse_args()
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    published = manifest["published"]
    lookup = article_lookup(manifest)
    parsed: dict[str, dict] = {}

    for article in manifest["articles"]:
        draft_path = args.drafts / f"{article['slug']}.md"
        if not draft_path.exists():
            raise FileNotFoundError(f"Missing draft: {draft_path}")
        draft_title, subtitle, body_html, word_count = read_draft(draft_path)
        if title_key(draft_title) != title_key(article["title"]):
            raise ValueError(f"Title mismatch in {draft_path}: {draft_title!r} != {article['title']!r}")
        if not subtitle:
            raise ValueError(f"Missing italic subtitle in {draft_path}")
        if word_count < 1000:
            raise ValueError(f"Draft is unexpectedly short ({word_count} words): {draft_path}")
        parsed[article["slug"]] = {
            "subtitle": subtitle,
            "body_html": body_html,
            "word_count": word_count,
        }

    for index, article in enumerate(manifest["articles"], start=1):
        draft = parsed[article["slug"]]
        page = render_article(
            article,
            index,
            len(manifest["articles"]),
            draft["subtitle"],
            draft["body_html"],
            draft["word_count"],
            published,
            lookup,
        )
        (args.site / f"{article['slug']}.html").write_text(page, encoding="utf-8")

    (args.site / f"{SERIES_SLUG}.html").write_text(render_series(manifest, parsed), encoding="utf-8")
    print(f"Built {len(manifest['articles'])} articles and {SERIES_SLUG}.html")


if __name__ == "__main__":
    main()
