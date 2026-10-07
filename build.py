#!/usr/bin/env python3
"""Build the map site from map.jsonc into _site/.

    python3 build.py                                  # build
    python3 build.py --serve                          # build, then preview at http://localhost:8000/
    python3 build.py --config examples/x.jsonc --out /tmp/x   # build another settings file

Standard-library Python 3.9+ only. Errors stop the build; warnings print and continue.
"""
import argparse
import hashlib
import html
import json
import os
import re
import shutil
import sys
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent
ENTRY_KEYS = {"name", "type", "city", "lat", "lon", "tags", "link", "note"}
# People are snapped to a 0.1-degree grid (about 11 km north-south), then spread a little so
# pins in the same city don't stack. The spread is seeded from the entry, so builds are stable.
PEOPLE_GRID = 0.1
PEOPLE_SPREAD = 0.03
HEX = re.compile(r"^#[0-9A-Fa-f]{6}$")
SLUG = re.compile(r"^[a-z][a-z0-9-]{0,23}$")
TEXT_DEFAULTS = {
    "heading": "Who's Near You",
    "tags_label": "Into",
    "join_text": "Send your display name, your city, and what you're into. Groups and places: "
                 "send your public meeting spot or address and a link.",
}

errors, warnings = [], []
BASE_URL = ""   # public address, e.g. https://example.org/map/ ; "" when unknown (set in main)


def load_jsonc(path):
    """JSON that allows whole-line // comments and trailing commas."""
    # Blank out comment lines (instead of removing them) so error line numbers match the file.
    lines = ["" if l.lstrip().startswith("//") else l for l in path.read_text(encoding="utf-8").splitlines()]
    text = re.sub(r",(\s*[}\]])", r"\1", "\n".join(lines))
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        sys.exit(f"\n{path.name} has a typo near line {e.lineno}: {e.msg}.\n"
                 "Check for a missing comma or quote on that line or the one above it.\n")


def luminance(hex_color):
    def channel(c):
        c = int(c, 16) / 255
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (channel(hex_color[i:i + 2]) for i in (1, 3, 5))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a, b):
    la, lb = sorted((luminance(a), luminance(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def is_https(url):
    p = urlparse(url)
    return p.scheme == "https" and bool(p.netloc)


def is_people(cfg, type_key):
    """Categories are people unless they say otherwise, so a forgotten flag fails safe."""
    return cfg["categories"][type_key].get("people", True) is not False


def blur(entry):
    """City-level position for a person: snap to the grid, then a stable small offset."""
    lat = round(entry["lat"] / PEOPLE_GRID) * PEOPLE_GRID
    lon = round(entry["lon"] / PEOPLE_GRID) * PEOPLE_GRID
    seed = hashlib.sha256(f'{entry["name"]}|{entry["city"]}'.encode()).digest()
    dlat = (seed[0] / 255 - 0.5) * 2 * PEOPLE_SPREAD
    dlon = (seed[1] / 255 - 0.5) * 2 * PEOPLE_SPREAD
    return round(lat + dlat, 3), round(lon + dlon, 3)


def check_config(cfg):
    for key in ("title", "organizer", "contact_email", "tiles", "tiles_attribution"):
        if not str(cfg.get(key) or "").strip():
            errors.append(f'"{key}" is empty in the settings file.')
    for key in ("organizer_url", "add_url", "tiles_attribution_url"):
        if cfg.get(key) and not is_https(cfg[key]):
            errors.append(f'"{key}" must start with https:// (got {cfg[key]!r}).')
    if cfg.get("tiles") and not is_https(cfg["tiles"].replace("{", "").replace("}", "")):
        errors.append('"tiles" must be an https:// address.')
    center = cfg.get("center")
    if not (isinstance(center, list) and len(center) == 2 and all(isinstance(v, (int, float)) for v in center)):
        errors.append('"center" must look like [39.80, -89.64].')
    if not isinstance(cfg.get("zoom"), int) or not 1 <= cfg["zoom"] <= 18:
        errors.append('"zoom" must be a whole number from 1 to 18.')
    colors = cfg.get("colors") or {}
    for key in ("primary", "dark", "background"):
        if not HEX.match(str(colors.get(key, ""))):
            errors.append(f'colors.{key} must be a 6-digit hex color like "#B80000".')
    cats = cfg.get("categories")
    if not isinstance(cats, dict) or not 1 <= len(cats) <= 8:
        errors.append('"categories" needs 1 to 8 entries, like "player": { "label": "Player", ... }.')
        return
    for key, cat in cats.items():
        where = f'categories.{key}'
        if not SLUG.match(key):
            errors.append(f'{where}: the key must be short, lowercase letters, numbers, or dashes (like "player").')
        if not isinstance(cat, dict):
            errors.append(f"{where} must be a {{ ... }} block.")
            continue
        for field in ("label", "plural"):
            if not str(cat.get(field) or "").strip():
                errors.append(f'{where} needs a "{field}".')
        if not HEX.match(str(cat.get("color", ""))):
            errors.append(f'{where}.color must be a 6-digit hex color.')
        if "people" in cat and not isinstance(cat["people"], bool):
            errors.append(f'{where}.people must be true or false.')
    if not errors:
        if contrast("#ffffff", colors["primary"]) < 4.5:
            warnings.append("White text on colors.primary is hard to read (contrast under 4.5:1). Pick a darker primary.")
        if contrast(colors["dark"], colors["background"]) < 7:
            warnings.append("colors.dark text on colors.background is low contrast (under 7:1).")


def check_entries(cfg, entries):
    out = []
    if not isinstance(entries, list):
        errors.append('"entries" must be a list: "entries": [ {...}, {...} ]')
        return out
    cats = cfg.get("categories") if isinstance(cfg.get("categories"), dict) else {}
    for i, e in enumerate(entries, 1):
        where = f'Entry {i} ({e.get("name") or "no name"})' if isinstance(e, dict) else f"Entry {i}"
        if not isinstance(e, dict):
            errors.append(f"{where} must be a {{ ... }} block.")
            continue
        extra = set(e) - ENTRY_KEYS
        if extra:
            # Stops addresses, emails, phone numbers, and ages from slipping onto a public page.
            errors.append(f"{where} has fields the map doesn't publish: {', '.join(sorted(extra))}. "
                          f"Allowed: {', '.join(sorted(ENTRY_KEYS))}.")
        for key in ("name", "city"):
            if not isinstance(e.get(key), str) or not e[key].strip():
                errors.append(f'{where} needs a "{key}".')
        if e.get("type") not in cats:
            errors.append(f'{where}: "type" must be one of your categories: {", ".join(cats)}.')
        lat, lon = e.get("lat"), e.get("lon")
        if not (isinstance(lat, (int, float)) and -90 <= lat <= 90 and isinstance(lon, (int, float)) and -180 <= lon <= 180):
            errors.append(f'{where}: "lat" and "lon" must be numbers, like 39.78 and -89.65.')
        if "@" in str(e.get("name", "")) + str(e.get("note", "")):
            errors.append(f"{where}: no email addresses on the map. Put a link in \"link\" instead.")
        if e.get("link") and not is_https(e["link"]):
            errors.append(f'{where}: "link" must start with https://.')
        tags = e.get("tags", [])
        if not (isinstance(tags, list) and all(isinstance(t, str) for t in tags)):
            errors.append(f'{where}: "tags" must be a list like ["yo-yo", "kendama"].')
        if len(str(e.get("note", ""))) > 140:
            warnings.append(f"{where}: note is over 140 characters; keep it to one short line.")
        out.append(e)
    return out


def public_entries(cfg, entries):
    """What actually ships to the browser. People get blurred coordinates."""
    rows = []
    for e in entries:
        lat, lon = blur(e) if is_people(cfg, e["type"]) else (e["lat"], e["lon"])
        row = {"name": e["name"].strip(), "type": e["type"], "city": e["city"].strip(),
               "lat": lat, "lon": lon}
        for key in ("tags", "link", "note"):
            if e.get(key):
                row[key] = e[key]
        rows.append(row)
    order = list(cfg["categories"])
    rows.sort(key=lambda r: (r["city"].lower(), order.index(r["type"]), r["name"].lower()))
    return rows


def csp(cfg):
    tile_host = urlparse(cfg["tiles"].replace("{s}", "a")).netloc
    tile_src = f"https://{tile_host}"
    if "{s}" in cfg["tiles"]:
        tile_src = f"https://*.{tile_host.split('.', 1)[1]}"
    return ("default-src 'none'; script-src 'self'; style-src 'self'; "
            f"img-src 'self' {tile_src}; base-uri 'none'; form-action 'none'")


def page(cfg, title, description, body, slug="index"):
    e = html.escape
    canonical = BASE_URL if slug == "index" else (BASE_URL + slug + ".html" if BASE_URL else "")
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="{e(csp(cfg))}">
<meta name="referrer" content="strict-origin-when-cross-origin">
<title>{e(title)}</title>
<meta name="description" content="{e(description)}">
<link rel="icon" href="assets/favicon.svg" type="image/svg+xml">
{social_tags(cfg, title, description, canonical)}<link rel="stylesheet" href="assets/vendor/leaflet/leaflet.css">
<link rel="stylesheet" href="assets/style.css">
<link rel="stylesheet" href="assets/theme.css">
</head>
<body>
<a class="skip-link" href="#main-content">Skip to content</a>
{header(cfg)}
<main id="main-content">
{body}
</main>
{footer(cfg)}
</body>
</html>
"""


def social_tags(cfg, title, description, canonical):
    """Open Graph and Twitter tags always; canonical link and JSON-LD only once the public address is known."""
    e = html.escape
    tags = [
        f'<meta property="og:type" content="website">',
        f'<meta property="og:site_name" content="{e(cfg["title"])}">',
        f'<meta property="og:title" content="{e(title)}">',
        f'<meta property="og:description" content="{e(description)}">',
        '<meta name="twitter:card" content="summary">',
        f'<meta name="twitter:title" content="{e(title)}">',
        f'<meta name="twitter:description" content="{e(description)}">',
    ]
    if canonical:
        tags += [f'<link rel="canonical" href="{e(canonical)}">', f'<meta property="og:url" content="{e(canonical)}">']
        data = {
            "@context": "https://schema.org",
            "@type": "WebSite",
            "name": cfg["title"],
            "description": description,
            "url": BASE_URL,
            "publisher": {"@type": "Organization", "name": cfg["organizer"],
                          **({"url": cfg["organizer_url"]} if cfg.get("organizer_url") else {})},
        }
        # "</" can't appear in the JSON, so it can't close the script early.
        tags.append('<script type="application/ld+json">' + json.dumps(data).replace("</", "<\\/") + "</script>")
    return "\n".join(tags) + "\n"


def header(cfg):
    e = html.escape
    tagline = f'<p class="tagline">{e(cfg["tagline"])}</p>' if cfg.get("tagline") else ""
    add = (f'<a class="button" href="{e(cfg["add_url"])}" target="_blank" rel="noopener noreferrer">Add yourself</a>'
           if cfg.get("add_url") else f'<a class="button" href="index.html#join">Add yourself</a>')
    return f"""<header class="site-header">
<div class="wrap header-row">
<div>
<p class="site-title"><a href="index.html">{e(cfg["title"])}</a></p>
{tagline}
</div>
{add}
</div>
</header>"""


def footer(cfg):
    e = html.escape
    org = e(cfg["organizer"])
    if cfg.get("organizer_url"):
        org = f'<a href="{e(cfg["organizer_url"])}" target="_blank" rel="noopener noreferrer">{org}</a>'
    attribution = e(cfg["tiles_attribution"])
    if cfg.get("tiles_attribution_url"):
        attribution = (f'<a href="{e(cfg["tiles_attribution_url"])}" target="_blank" '
                       f'rel="noopener noreferrer">{attribution}</a>')
    email = e(cfg["contact_email"])
    return f"""<footer class="site-footer">
<div class="wrap">
<p>Run by {org}. Questions or removal requests: <a href="mailto:{email}">{email}</a>.</p>
<p>Map tiles {attribution}. Map library <a href="https://leafletjs.com" target="_blank" rel="noopener noreferrer">Leaflet</a>.</p>
</div>
</footer>"""


def list_words(words):
    words = list(words)
    if len(words) <= 2:
        return " and ".join(words)
    return ", ".join(words[:-1]) + ", and " + words[-1]


def index_body(cfg, rows):
    e = html.escape
    cats = cfg["categories"]
    text = {k: cfg.get(k) or v for k, v in TEXT_DEFAULTS.items()}
    counts = {t: sum(r["type"] == t for r in rows) for t in cats}
    filters = "\n".join(
        f'<label class="filter"><input type="checkbox" value="{t}" checked> '
        f'<span class="swatch pin-{t}" aria-hidden="true"></span>{e(c["plural"])} ({counts[t]})</label>'
        for t, c in cats.items())
    table_rows = []
    for r in rows:
        name = e(r["name"])
        if r.get("link"):
            name = f'<a href="{e(r["link"])}" target="_blank" rel="noopener noreferrer">{name}</a>'
        note = f'<br><span class="muted">{e(r["note"])}</span>' if r.get("note") else ""
        table_rows.append(
            f'<tr data-type="{r["type"]}"><td>{name}{note}</td><td>{e(cats[r["type"]]["label"])}</td>'
            f'<td>{e(r["city"])}</td><td>{e(", ".join(r.get("tags", [])))}</td></tr>')
    settings = {"center": cfg["center"], "zoom": cfg["zoom"], "tiles": cfg["tiles"],
                "attribution": cfg["tiles_attribution"],
                "labels": {t: c["label"] for t, c in cats.items()}}
    # A JSON data block is not executed, so the strict security policy allows it.
    data = json.dumps({"settings": settings, "entries": rows}, ensure_ascii=False).replace("</", "<\\/")
    join = (f'<p><a class="button" href="{e(cfg["add_url"])}" target="_blank" rel="noopener noreferrer">Add yourself</a></p>'
            if cfg.get("add_url") else "")
    email = e(cfg["contact_email"])
    map_label = "Map of " + list_words(c["plural"].lower() for c in cats.values())
    def sentence_list(plurals):
        """'Clubs, shops, and venues': only the first word capitalized, since it starts a sentence."""
        return list_words([plurals[0]] + [w.lower() for w in plurals[1:]]) if plurals else ""
    people = [c["plural"] for t, c in cats.items() if is_people(cfg, t)]
    places = [c["plural"] for t, c in cats.items() if not is_people(cfg, t)]
    privacy = []
    if people:
        privacy.append(f"<li>{e(sentence_list(people))} show up at city level only. Each pin is snapped to a grid "
                       "about 10 km wide, then nudged so people in the same city don't overlap.</li>")
    privacy += ["<li>No accounts, no cookies, no trackers. The map never asks for your location.</li>",
                "<li>No emails, phone numbers, or home addresses are published. The build refuses them.</li>"]
    if places:
        privacy.append(f"<li>{e(sentence_list(places))} are shown at the public spot they chose.</li>")
    return f"""<section class="wrap" aria-labelledby="map-heading">
<h1 id="map-heading">{e(text["heading"])}</h1>
<div class="search" hidden>
<label for="map-search">Search by name, city, or {e(text["tags_label"].lower())}</label>
<input type="search" id="map-search" autocomplete="off" spellcheck="false">
<p id="map-count" class="muted" aria-live="polite"></p>
</div>
<fieldset class="filters">
<legend>Show</legend>
{filters}
</fieldset>
<div id="map" class="map" role="region" aria-label="{e(map_label)}"></div>
<noscript><p class="muted">The map needs JavaScript. Everyone on it is also in the list below.</p></noscript>
</section>
<section class="wrap" aria-labelledby="list-heading">
<h2 id="list-heading">Everyone on the Map</h2>
<div class="table-scroll">
<table class="entries">
<thead><tr><th scope="col">Name</th><th scope="col">Type</th><th scope="col">City</th><th scope="col">{e(text["tags_label"])}</th></tr></thead>
<tbody>
{chr(10).join(table_rows)}
</tbody>
</table>
</div>
</section>
<section class="wrap" id="join" aria-labelledby="join-heading">
<h2 id="join-heading">Get on the Map</h2>
<p>{e(text["join_text"])}</p>
{join}
<p>Want off the map? Email <a href="mailto:{email}">{email}</a>. You'll be gone at the next update.</p>
</section>
<section class="wrap" aria-labelledby="privacy-heading">
<h2 id="privacy-heading">How Your Privacy Works</h2>
<ul>
{chr(10).join(privacy)}
</ul>
</section>
<script type="application/json" id="map-data">{data}</script>
<script src="assets/vendor/leaflet/leaflet.js" defer></script>
<script src="assets/map.js" defer></script>"""


def theme_css(cfg):
    c = cfg["colors"]
    css = (":root {\n"
           f"  --primary: {c['primary']};\n  --dark: {c['dark']};\n  --bg: {c['background']};\n"
           "}\n")
    for key, cat in cfg["categories"].items():
        css += f".pin-{key} {{ background: {cat['color']}; }}\n"
    return css


def build(config_path, out):
    cfg = load_jsonc(config_path)
    check_config(cfg)
    entries = check_entries(cfg, cfg.get("entries", []))
    for w in warnings:
        print(f"WARNING: {w}")
    if errors:
        print(f"\nThe map didn't build. Fix these in {config_path.name}:\n", file=sys.stderr)
        for err in errors:
            print(f"  - {err}", file=sys.stderr)
        sys.exit(1)
    rows = public_entries(cfg, entries)

    if out.exists():
        shutil.rmtree(out)
    shutil.copytree(ROOT / "assets", out / "assets")
    (out / "assets" / "theme.css").write_text(theme_css(cfg), encoding="utf-8")
    description = cfg.get("tagline") or f'{cfg["title"]}: who and what is near you.'
    (out / "index.html").write_text(
        page(cfg, cfg["title"], description, index_body(cfg, rows)), encoding="utf-8")
    missing = f"""<section class="wrap">
<h1>Page Not Found</h1>
<p>That page isn't here. <a href="index.html">Back to the map</a>.</p>
</section>"""
    (out / "404.html").write_text(page(cfg, f'Not found | {cfg["title"]}', description, missing, slug="404"), encoding="utf-8")
    (out / ".nojekyll").write_text("", encoding="utf-8")
    robots = "User-agent: *\nAllow: /\n"
    if BASE_URL:
        robots += f"\nSitemap: {BASE_URL}sitemap.xml\n"
        (out / "sitemap.xml").write_text(
            '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
            f"  <url><loc>{html.escape(BASE_URL)}</loc></url>\n</urlset>\n", encoding="utf-8")
    (out / "robots.txt").write_text(robots, encoding="utf-8")
    counts = []
    for t, c in cfg["categories"].items():
        n = sum(r["type"] == t for r in rows)
        counts.append(f'{n} {(c["label"] if n == 1 else c["plural"]).lower()}')
    counts = ", ".join(counts)
    print(f"Built {out.name}/ from {config_path.name} with {len(rows)} entries ({counts}).")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build the map site.")
    parser.add_argument("--config", default="map.jsonc", help="settings file (default: map.jsonc)")
    parser.add_argument("--out", default="_site", help="output folder (default: _site)")
    parser.add_argument("--base-url", default=os.environ.get("SITE_URL", ""),
                        help="public address, e.g. https://example.org/ (adds canonical links, JSON-LD and a sitemap)")
    parser.add_argument("--serve", action="store_true", help="preview at http://localhost:8000/")
    args = parser.parse_args()
    BASE_URL = args.base_url.strip()
    if BASE_URL and not BASE_URL.endswith("/"):
        BASE_URL += "/"
    if BASE_URL.startswith("http://"):
        BASE_URL = "https://" + BASE_URL[len("http://"):]   # Pages reports http:// until Enforce HTTPS is on
    out_dir = (ROOT / args.out).resolve()
    build((ROOT / args.config).resolve(), out_dir)
    if args.serve:
        import functools
        import http.server
        handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(out_dir))
        print("Preview at http://localhost:8000/  (Ctrl+C to stop)")
        http.server.ThreadingHTTPServer(("127.0.0.1", 8000), handler).serve_forever()
