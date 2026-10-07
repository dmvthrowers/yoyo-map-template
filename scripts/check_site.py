#!/usr/bin/env python3
"""Check the built site in _site/ before it goes live. Run after build.py:

    python3 build.py && python3 scripts/check_site.py
    python3 scripts/check_site.py --config examples/x.jsonc --site /tmp/x

Fails on: a missing Content Security Policy or one with 'unsafe-inline', inline scripts
(other than the map's JSON data block), inline styles or event handlers, http:// links,
broken internal links, a missing title or skip link, and any published entry with fields
beyond the allowed ones, a heading that skips a level (h1 to h3), or a pin in a "people" category that wasn't blurred. Prints "OK" when clean.
"""
import argparse
import json
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "_site"
CONFIG = ROOT / "map.jsonc"
sys.path.insert(0, str(ROOT))
import build  # noqa: E402  (reuses the same rules the build applies)

errors = []


class Page(HTMLParser):
    def __init__(self):
        super().__init__()
        self.refs, self.ids, self.problems = [], set(), []
        self.csp = None
        self.has_title = False
        self.levels = []
        self.data, self._in_data = "", False

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if a.get("id"):
            self.ids.add(a["id"])
        if tag == "title":
            self.has_title = True
        if len(tag) == 2 and tag[0] == "h" and tag[1] in "123456":
            self.levels.append(int(tag[1]))
        if tag == "meta" and (a.get("http-equiv") or "").lower() == "content-security-policy":
            self.csp = a.get("content") or ""
        if tag == "style":
            self.problems.append("inline <style> block")
        if tag == "script" and "src" not in a:
            if a.get("type") == "application/json" and a.get("id") == "map-data":
                self._in_data = True
            elif a.get("type") == "application/ld+json":
                pass   # structured data for search engines: data, not code
            else:
                self.problems.append("inline <script>")
        for k, v in a.items():
            if k == "style":
                self.problems.append(f"inline style on <{tag}>")
            elif k.startswith("on"):
                self.problems.append(f"event handler {k}= on <{tag}>")
            elif k in ("href", "src") and v:
                if v.lower().startswith("http:"):
                    self.problems.append(f"http:// link {v}")
                self.refs.append(v)

    def handle_endtag(self, tag):
        if tag == "script":
            self._in_data = False

    def handle_data(self, data):
        if self._in_data:
            self.data += data


def check_page(path):
    p = Page()
    p.feed(path.read_text(encoding="utf-8"))
    name = path.name
    for problem in p.problems:
        errors.append(f"{name}: {problem}")
    if not p.csp:
        errors.append(f"{name}: no Content Security Policy")
    elif "unsafe-inline" in p.csp or "unsafe-eval" in p.csp:
        errors.append(f"{name}: the security policy allows unsafe-inline/unsafe-eval")
    if not p.has_title:
        errors.append(f"{name}: no <title>")
    for prev, cur in zip(p.levels, p.levels[1:]):
        if cur > prev + 1:
            errors.append(f"{name}: heading jumps from h{prev} to h{cur}")
            break
    if "main-content" not in p.ids:
        errors.append(f"{name}: no main#main-content for the skip link")
    for ref in p.refs:
        u = urlparse(ref)
        if u.scheme or ref.startswith("//"):
            continue
        target = u.path or name
        if target.startswith("/"):
            errors.append(f"{name}: {ref} starts with / and breaks on project sites; use a relative link")
            continue
        if not (SITE / target).exists():
            errors.append(f"{name}: broken link {ref}")
        elif u.fragment and target == name and u.fragment not in p.ids:
            errors.append(f"{name}: link to #{u.fragment}, but nothing has that id")
    return p.data


def check_data(raw):
    if not raw:
        errors.append("index.html: the map data block is missing")
        return
    data = json.loads(raw)
    cfg = build.load_jsonc(CONFIG)
    people = {t for t in cfg["categories"] if build.is_people(cfg, t)}
    exact = {(e["lat"], e["lon"]) for e in cfg["entries"] if e.get("type") in people}
    for e in data["entries"]:
        extra = set(e) - build.ENTRY_KEYS
        if extra:
            errors.append(f"published entry {e.get('name')!r} has extra fields: {', '.join(sorted(extra))}")
        if e["type"] in people and (e["lat"], e["lon"]) in exact:
            errors.append(f"{e['name']!r} is published at the exact coordinates from {CONFIG.name}")


def main():
    global SITE, CONFIG
    parser = argparse.ArgumentParser(description="Check the built map site.")
    parser.add_argument("--config", default="map.jsonc", help="settings file the site was built from")
    parser.add_argument("--site", default="_site", help="built site folder")
    args = parser.parse_args()
    SITE, CONFIG = (ROOT / args.site).resolve(), (ROOT / args.config).resolve()
    if not (SITE / "index.html").exists():
        sys.exit(f"No {SITE}/index.html. Run python3 build.py first.")
    raw = ""
    for path in sorted(SITE.glob("*.html")):
        data = check_page(path)
        if path.name == "index.html":
            raw = data
    check_data(raw)
    if errors:
        print("Site check failed:")
        for err in errors:
            print(f"  - {err}")
        sys.exit(1)
    print("OK")


if __name__ == "__main__":
    main()
