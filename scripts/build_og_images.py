#!/usr/bin/env python3
"""Generate deterministic 1200×630 social cards for the AI series."""

from __future__ import annotations

import argparse
import html
import json
from pathlib import Path

from playwright.sync_api import sync_playwright


ROOT = Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=Path(__file__).with_name("ai-series.json"))
    parser.add_argument("--site", type=Path, default=ROOT)
    parser.add_argument("--slug")
    parser.add_argument("--title")
    parser.add_argument("--label")
    parser.add_argument("--subtitle")
    return parser.parse_args()


def card_markup(title: str, label: str, subtitle: str, one_brain: bool = False) -> str:
    title_size = 74 if len(title) < 58 else 65 if len(title) < 78 else 58
    glow = (
        "radial-gradient(circle at 84% 50%, transparent 0 72px, rgba(196,181,253,.28) 73px 75px, "
        "transparent 76px 132px, rgba(125,211,252,.2) 133px 135px, transparent 136px 205px, "
        "rgba(251,191,36,.12) 206px 208px, transparent 209px), "
        "radial-gradient(circle at 14% 58%, rgba(99,102,241,.35), transparent 36%)"
        if one_brain
        else "radial-gradient(circle at 12% 42%, rgba(37,99,235,.42), transparent 38%), radial-gradient(circle at 82% 12%, rgba(14,165,233,.18), transparent 34%)"
    )
    grid = (
        "radial-gradient(circle, rgba(255,255,255,.13) 0 2px, transparent 3px)"
        if one_brain
        else "linear-gradient(rgba(255,255,255,.035) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,.035) 1px, transparent 1px)"
    )
    grid_size = "84px 84px" if one_brain else "44px 44px"
    accent = "linear-gradient(90deg,#8b5cf6,#7dd3fc,#fbbf24)" if one_brain else "linear-gradient(90deg,#2563eb,#7dd3fc)"
    series_color = "#c4b5fd" if one_brain else "#93c5fd"
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
  background: {glow};
  content: "";
  inset: 0;
  position: absolute;
}}
body::after {{
  background-image: {grid};
  background-size: {grid_size};
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
.series {{ color: {series_color}; font-size: 16px; font-weight: 750; letter-spacing: .11em; text-transform: uppercase; }}
h1 {{ font-size: {title_size}px; letter-spacing: -.055em; line-height: 1.03; margin: 70px 0 0; max-width: 1000px; }}
.bottom {{ align-items: flex-end; display: flex; justify-content: space-between; margin-top: auto; }}
.subtitle {{ color: #a1a1aa; font-size: 20px; line-height: 1.42; max-width: 760px; }}
.url {{ color: #d4d4d8; font-size: 17px; font-weight: 650; }}
.accent {{ background: {accent}; height: 5px; left: 28px; position: absolute; top: 28px; width: 230px; z-index: 4; }}
</style></head><body>
<div class="frame"></div><div class="accent"></div>
<div class="content">
  <div class="top"><div class="name">Andrea Padula</div><div class="series">{html.escape(label)}</div></div>
  <h1>{html.escape(title)}</h1>
  <div class="bottom"><div class="subtitle">{html.escape(subtitle)}</div><div class="url">andreapadula.com</div></div>
</div>
</body></html>'''


def main() -> None:
    args = parse_args()
    output = args.site / "assets" / "articles"
    output.mkdir(parents=True, exist_ok=True)
    standalone_values = [args.slug, args.title, args.label, args.subtitle]
    if any(standalone_values) and not all(standalone_values):
        raise SystemExit("--slug, --title, --label, and --subtitle must be provided together")

    if all(standalone_values):
        one_brain = False
        entries = [
            {
                "slug": args.slug,
                "title": args.title,
                "label": args.label,
                "subtitle": args.subtitle,
            }
        ]
    else:
        manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
        series = manifest["series"]
        one_brain = series.get("body_class") == "one-brain-series"
        entries = [
            {
                "slug": series["slug"],
                "title": series["title"],
                "label": series["hero_label"],
                "subtitle": series["og_subtitle"],
            }
        ]
        total = len(manifest["articles"])
        for index, article in enumerate(manifest["articles"], start=1):
            entries.append(
                {
                    "slug": article["slug"],
                    "title": article["title"],
                    "label": f"{series['short_label']} · {index:02d}/{total:02d}",
                    "subtitle": article["description"],
                }
            )

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1200, "height": 630}, device_scale_factor=1)
        for entry in entries:
            page.set_content(card_markup(entry["title"], entry["label"], entry["subtitle"], one_brain=one_brain), wait_until="load")
            page.screenshot(path=str(output / f"{entry['slug']}.png"), type="png")
        browser.close()

    print(f"Generated {len(entries)} social cards in {output}")


if __name__ == "__main__":
    main()
