#!/usr/bin/env python3
"""Generate deterministic 1200×630 social cards for the AI series."""

from __future__ import annotations

import html
import json
from pathlib import Path

from playwright.sync_api import sync_playwright


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = json.loads((Path(__file__).with_name("ai-series.json")).read_text(encoding="utf-8"))
OUTPUT = ROOT / "assets" / "articles"


def card_markup(title: str, label: str, subtitle: str) -> str:
    title_size = 74 if len(title) < 58 else 65 if len(title) < 78 else 58
    return f'''<!doctype html>
<html><head><meta charset="utf-8"><style>
* {{ box-sizing: border-box; }}
html, body {{ margin: 0; width: 1200px; height: 630px; overflow: hidden; }}
body {{
  background: #08090c;
  color: #f4f4f5;
  font-family: Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  position: relative;
}}
body::before {{
  background:
    radial-gradient(circle at 12% 42%, rgba(37,99,235,.42), transparent 38%),
    radial-gradient(circle at 82% 12%, rgba(14,165,233,.18), transparent 34%);
  content: "";
  inset: 0;
  position: absolute;
}}
body::after {{
  background-image: linear-gradient(rgba(255,255,255,.035) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,.035) 1px, transparent 1px);
  background-size: 44px 44px;
  content: "";
  inset: 0;
  mask-image: linear-gradient(110deg, black, transparent 75%);
  opacity: .55;
  position: absolute;
}}
.frame {{ border: 1px solid rgba(255,255,255,.09); inset: 28px; position: absolute; z-index: 2; }}
.content {{ display: flex; flex-direction: column; height: 100%; padding: 64px 74px 58px; position: relative; z-index: 3; }}
.top {{ align-items: center; display: flex; justify-content: space-between; }}
.name {{ font-size: 21px; font-weight: 750; letter-spacing: -.02em; }}
.series {{ color: #93c5fd; font-size: 16px; font-weight: 750; letter-spacing: .11em; text-transform: uppercase; }}
h1 {{ font-size: {title_size}px; letter-spacing: -.055em; line-height: 1.03; margin: 70px 0 0; max-width: 1000px; }}
.bottom {{ align-items: flex-end; display: flex; justify-content: space-between; margin-top: auto; }}
.subtitle {{ color: #a1a1aa; font-size: 20px; line-height: 1.42; max-width: 760px; }}
.url {{ color: #d4d4d8; font-size: 17px; font-weight: 650; }}
.accent {{ background: linear-gradient(90deg,#2563eb,#7dd3fc); height: 5px; left: 28px; position: absolute; top: 28px; width: 230px; z-index: 4; }}
</style></head><body>
<div class="frame"></div><div class="accent"></div>
<div class="content">
  <div class="top"><div class="name">Andrea Padula</div><div class="series">{html.escape(label)}</div></div>
  <h1>{html.escape(title)}</h1>
  <div class="bottom"><div class="subtitle">{html.escape(subtitle)}</div><div class="url">andreapadula.com</div></div>
</div>
</body></html>'''


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    entries = [
        {
            "slug": "ai-financial-services",
            "title": "AI in Financial Services: What Works, What Doesn’t, and What Comes Next",
            "label": "10-essay field guide",
            "subtitle": "Workflows, authority, economics, trust—and who learns fastest.",
        }
    ]
    for index, article in enumerate(MANIFEST["articles"], start=1):
        entries.append(
            {
                "slug": article["slug"],
                "title": article["title"],
                "label": f"AI & Financial Services · {index:02d}/10",
                "subtitle": article["description"],
            }
        )

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1200, "height": 630}, device_scale_factor=1)
        for entry in entries:
            page.set_content(card_markup(entry["title"], entry["label"], entry["subtitle"]), wait_until="load")
            page.screenshot(path=str(OUTPUT / f"{entry['slug']}.png"), type="png")
        browser.close()

    print(f"Generated {len(entries)} social cards in {OUTPUT}")


if __name__ == "__main__":
    main()
