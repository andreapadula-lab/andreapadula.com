#!/usr/bin/env python3
"""Browser QA for the AI & Financial Services series."""

from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import urljoin, urlparse

from playwright.sync_api import sync_playwright


BASE_URL = "http://127.0.0.1:4173/"
ROOT = Path(__file__).resolve().parents[1]
MANIFEST = json.loads((Path(__file__).with_name("ai-series.json")).read_text(encoding="utf-8"))


def expect(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    slugs = [item["slug"] for item in MANIFEST["articles"]]
    console_errors: list[str] = []
    page_errors: list[str] = []

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        desktop = browser.new_context(viewport={"width": 1440, "height": 1000}, device_scale_factor=1)
        page = desktop.new_page()
        page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)
        page.on("pageerror", lambda error: page_errors.append(str(error)))

        response = page.goto(BASE_URL, wait_until="networkidle")
        expect(response is not None and response.status == 200, "Homepage did not return HTTP 200")
        expect(page.locator("a[href='ai-financial-services.html']").count() >= 1, "Homepage does not link to the series")
        expect(page.locator(".contact-grid .contact-card").count() == 3, "Homepage should show email, LinkedIn, and Medium contact cards")
        expect(page.evaluate("document.documentElement.scrollWidth <= window.innerWidth + 1"), "Homepage has horizontal overflow on desktop")

        response = page.goto(urljoin(BASE_URL, "ai-financial-services.html"), wait_until="networkidle")
        expect(response is not None and response.status == 200, "Series hub did not return HTTP 200")
        expect(page.locator("h1").count() == 1, "Series hub must have exactly one H1")
        expect(page.locator(".series-card").count() == 10, "Series hub must show exactly ten article cards")
        expect(page.locator(".series-card").first.get_attribute("href") == f"{slugs[0]}.html", "First card points to the wrong article")
        expect(page.evaluate("document.documentElement.scrollWidth <= window.innerWidth + 1"), "Series hub has horizontal overflow on desktop")
        page.screenshot(path="/tmp/andrea-ai-series-hub.png", full_page=True)

        for index, slug in enumerate(slugs, start=1):
            response = page.goto(urljoin(BASE_URL, f"{slug}.html"), wait_until="networkidle")
            expect(response is not None and response.status == 200, f"{slug}: HTTP status was not 200")
            expect(page.locator("h1").count() == 1, f"{slug}: expected one H1")
            expect(page.locator("article.article-body").count() == 1, f"{slug}: article body missing")
            expect(page.locator("article h2#sources").count() == 1, f"{slug}: Sources section missing")
            expect(page.locator("article a[href^='http']").count() >= 3, f"{slug}: fewer than three cited/internal absolute links")
            expect(page.locator("link[rel='canonical']").get_attribute("href") == f"https://andreapadula.com/{slug}.html", f"{slug}: wrong canonical")
            expect(page.evaluate("document.documentElement.scrollWidth <= window.innerWidth + 1"), f"{slug}: horizontal overflow on desktop")
            expect(page.locator(".eyebrow").inner_text().endswith(f"{index:02d}/10"), f"{slug}: wrong series position")
            for script in page.locator("script[type='application/ld+json']").all_text_contents():
                json.loads(script)

        page.goto(urljoin(BASE_URL, f"{slugs[0]}.html"), wait_until="networkidle")
        page.screenshot(path="/tmp/andrea-ai-article-desktop.png", full_page=True)
        desktop.close()

        mobile = browser.new_context(viewport={"width": 390, "height": 844}, device_scale_factor=1)
        mobile_page = mobile.new_page()
        mobile_page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)
        mobile_page.on("pageerror", lambda error: page_errors.append(str(error)))
        mobile_page.goto(BASE_URL, wait_until="networkidle")
        expect(mobile_page.locator(".contact-grid .contact-card").count() == 3, "Mobile homepage lost a contact card")
        expect(mobile_page.evaluate("document.documentElement.scrollWidth <= window.innerWidth + 1"), "Homepage has horizontal overflow on mobile")
        mobile_page.goto(urljoin(BASE_URL, "ai-financial-services.html"), wait_until="networkidle")
        expect(mobile_page.locator(".series-card").count() == 10, "Mobile hub lost article cards")
        expect(mobile_page.evaluate("document.documentElement.scrollWidth <= window.innerWidth + 1"), "Series hub has horizontal overflow on mobile")
        mobile_page.goto(urljoin(BASE_URL, f"{slugs[0]}.html"), wait_until="networkidle")
        expect(mobile_page.evaluate("document.documentElement.scrollWidth <= window.innerWidth + 1"), "Article has horizontal overflow on mobile")
        mobile_page.screenshot(path="/tmp/andrea-ai-article-mobile.png", full_page=True)
        mobile.close()
        browser.close()

    filtered_console = [error for error in console_errors if "Failed to load resource" not in error]
    expect(not filtered_console, f"Browser console errors: {filtered_console}")
    expect(not page_errors, f"Page errors: {page_errors}")
    print(f"QA passed: homepage + hub + {len(slugs)} articles, desktop and mobile")
    print("Screenshots: /tmp/andrea-ai-series-hub.png, /tmp/andrea-ai-article-desktop.png, /tmp/andrea-ai-article-mobile.png")


if __name__ == "__main__":
    main()
