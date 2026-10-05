#!/usr/bin/env python3
"""Build the map site from map.jsonc into _site/.

    python3 build.py           # build
    python3 build.py --serve   # build, then preview at http://localhost:8000/

Standard-library Python 3.9+ only. Errors stop the build; warnings print and continue.
"""
import hashlib
import html
import json
import re
import shutil
import sys
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "_site"
TYPES = {"player": "Player", "club": "Club", "shop": "Shop"}
ENTRY_KEYS = {"name", "type", "city", "lat", "lon", "toys", "link", "note"}
# Players are snapped to a 0.1-degree grid (about 11 km north-south), then spread a little so
# pins in the same city don't stack. The spread is seeded from the entry, so builds are stable.
PLAYER_GRID = 0.1
PLAYER_SPREAD = 0.03
HEX = re.compile(r"^#[0-9A-Fa-f]{6}$")

errors, warnings = [], []


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


def blur(entry):
    """City-level position for a player: snap to the grid, then a stable small offset."""
    lat = round(entry["lat"] / PLAYER_GRID) * PLAYER_GRID
    lon = round(entry["lon"] / PLAYER_GRID) * PLAYER_GRID
    seed = hashlib.sha256(f'{entry["name"]}|{entry["city"]}'.encode()).digest()
    dlat = (seed[0] / 255 - 0.5) * 2 * PLAYER_SPREAD
    dlon = (seed[1] / 255 - 0.5) * 2 * PLAYER_SPREAD
    return round(lat + dlat, 3), round(lon + dlon, 3)


def check_config(cfg):
    for key in ("title", "organizer", "contact_email", "tiles", "tiles_attribution"):
        if not str(cfg.get(key) or "").strip():
            errors.append(f'"{key}" is empty in map.jsonc.')
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
    for key in ("primary", "dark", "background", "player", "club", "shop"):
        if not HEX.match(str(colors.get(key, ""))):
            errors.append(f'colors.{key} must be a 6-digit hex color like "#B80000".')
    if not errors:
        if contrast("#ffffff", colors["primary"]) < 4.5:
            warnings.append("White text on colors.primary is hard to read (contrast under 4.5:1). Pick a darker primary.")
        if contrast(colors["dark"], colors["background"]) < 7:
            warnings.append("colors.dark text on colors.background is low contrast (under 7:1).")


def check_entries(entries):
    out = []
    if not isinstance(entries, list):
        errors.append('"entries" must be a list: "entries": [ {...}, {...} ]')
        return out
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
        if e.get("type") not in TYPES:
            errors.append(f'{where}: "type" must be one of {", ".join(TYPES)}.')
        lat, lon = e.get("lat"), e.get("lon")
        if not (isinstance(lat, (int, float)) and -90 <= lat <= 90 and isinstance(lon, (int, float)) and -180 <= lon <= 180):
            errors.append(f'{where}: "lat" and "lon" must be numbers, like 39.78 and -89.65.')
        if "@" in str(e.get("name", "")) + str(e.get("note", "")):
            errors.append(f"{where}: no email addresses on the map. Put a link in \"link\" instead.")
        if e.get("link") and not is_https(e["link"]):
            errors.append(f'{where}: "link" must start with https://.')
        toys = e.get("toys", [])
        if not (isinstance(toys, list) and all(isinstance(t, str) for t in toys)):
            errors.append(f'{where}: "toys" must be a list like ["yo-yo", "kendama"].')
        if len(str(e.get("note", ""))) > 140:
            warnings.append(f"{where}: note is over 140 characters; keep it to one short line.")
        out.append(e)
    return out


def public_entries(entries):
    """What actually ships to the browser. Players get blurred coordinates."""
    rows = []
    for e in entries:
        lat, lon = blur(e) if e["type"] == "player" else (e["lat"], e["lon"])
        row = {"name": e["name"].strip(), "type": e["type"], "city": e["city"].strip(),
               "lat": lat, "lon": lon}
        for key in ("toys", "link", "note"):
            if e.get(key):
                row[key] = e[key]
        rows.append(row)
    rows.sort(key=lambda r: (r["city"].lower(), r["type"], r["name"].lower()))
    return rows


def csp(cfg):
    tile_host = urlparse(cfg["tiles"].replace("{s}", "a")).netloc
    tile_src = f"https://{tile_host}"
    if "{s}" in cfg["tiles"]:
        tile_src = f"https://*.{tile_host.split('.', 1)[1]}"
    return ("default-src 'none'; script-src 'self'; style-src 'self'; "
            f"img-src 'self' {tile_src}; base-uri 'none'; form-action 'none'")


def page(cfg, title, description, body):
    e = html.escape
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="{e(csp(cfg))}">
<meta name="referrer" content="strict-origin-when-cross-origin">
<title>{e(title)}</title>
<meta name="description" content="{e(description)}">
<link rel="stylesheet" href="assets/vendor/leaflet/leaflet.css">
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


def index_body(cfg, rows):
    e = html.escape
    counts = {t: sum(r["type"] == t for r in rows) for t in TYPES}
    filters = "\n".join(
        f'<label class="filter"><input type="checkbox" value="{t}" checked> '
        f'<span class="swatch swatch-{t}" aria-hidden="true"></span>{label}s ({counts[t]})</label>'
        for t, label in TYPES.items())
    table_rows = []
    for r in rows:
        name = e(r["name"])
        if r.get("link"):
            name = f'<a href="{e(r["link"])}" target="_blank" rel="noopener noreferrer">{name}</a>'
        note = f'<br><span class="muted">{e(r["note"])}</span>' if r.get("note") else ""
        table_rows.append(
            f'<tr data-type="{r["type"]}"><td>{name}{note}</td><td>{TYPES[r["type"]]}</td>'
            f'<td>{e(r["city"])}</td><td>{e(", ".join(r.get("toys", [])))}</td></tr>')
    settings = {"center": cfg["center"], "zoom": cfg["zoom"], "tiles": cfg["tiles"],
                "attribution": cfg["tiles_attribution"], "types": TYPES}
    # A JSON data block is not executed, so the strict security policy allows it.
    data = json.dumps({"settings": settings, "entries": rows}, ensure_ascii=False).replace("</", "<\\/")
    join = (f'<p><a class="button" href="{e(cfg["add_url"])}" target="_blank" rel="noopener noreferrer">Add yourself</a></p>'
            if cfg.get("add_url") else "")
    email = e(cfg["contact_email"])
    return f"""<section class="wrap" aria-labelledby="map-heading">
<h1 id="map-heading">Who Throws Near You</h1>
<fieldset class="filters">
<legend>Show</legend>
{filters}
</fieldset>
<div id="map" class="map" role="region" aria-label="Map of players, clubs, and shops"></div>
<noscript><p class="muted">The map needs JavaScript. Everyone on it is also in the list below.</p></noscript>
</section>
<section class="wrap" aria-labelledby="list-heading">
<h2 id="list-heading">Everyone on the Map</h2>
<div class="table-scroll">
<table class="entries">
<thead><tr><th scope="col">Name</th><th scope="col">Type</th><th scope="col">City</th><th scope="col">Plays</th></tr></thead>
<tbody>
{chr(10).join(table_rows)}
</tbody>
</table>
</div>
</section>
<section class="wrap" id="join" aria-labelledby="join-heading">
<h2 id="join-heading">Get on the Map</h2>
<p>Send your display name, your city, and what you throw. Clubs and shops: send your public meetup spot or storefront and a link.</p>
{join}
<p>Want off the map? Email <a href="mailto:{email}">{email}</a>. You'll be gone at the next update.</p>
</section>
<section class="wrap" aria-labelledby="privacy-heading">
<h2 id="privacy-heading">How Your Privacy Works</h2>
<ul>
<li>Players show up at city level only. Your pin is snapped to a grid about 10 km wide, then nudged so people in the same city don't overlap.</li>
<li>No accounts, no cookies, no trackers. The map never asks for your location.</li>
<li>No emails, phone numbers, or home addresses are published. The build refuses them.</li>
<li>Clubs and shops are shown at the public spot they chose.</li>
</ul>
</section>
<script type="application/json" id="map-data">{data}</script>
<script src="assets/vendor/leaflet/leaflet.js" defer></script>
<script src="assets/map.js" defer></script>"""


def theme_css(cfg):
    c = cfg["colors"]
    return (":root {\n"
            f"  --primary: {c['primary']};\n  --dark: {c['dark']};\n  --bg: {c['background']};\n"
            f"  --pin-player: {c['player']};\n  --pin-club: {c['club']};\n  --pin-shop: {c['shop']};\n"
            "}\n")


def build():
    cfg = load_jsonc(ROOT / "map.jsonc")
    check_config(cfg)
    entries = check_entries(cfg.get("entries", []))
    for w in warnings:
        print(f"WARNING: {w}")
    if errors:
        print("\nThe map didn't build. Fix these in map.jsonc:\n", file=sys.stderr)
        for err in errors:
            print(f"  - {err}", file=sys.stderr)
        sys.exit(1)
    rows = public_entries(entries)

    if OUT.exists():
        shutil.rmtree(OUT)
    shutil.copytree(ROOT / "assets", OUT / "assets")
    (OUT / "assets" / "theme.css").write_text(theme_css(cfg), encoding="utf-8")
    description = cfg.get("tagline") or f'{cfg["title"]}: players, clubs, and shops.'
    (OUT / "index.html").write_text(
        page(cfg, cfg["title"], description, index_body(cfg, rows)), encoding="utf-8")
    missing = f"""<section class="wrap">
<h1>Page Not Found</h1>
<p>That page isn't here. <a href="index.html">Back to the map</a>.</p>
</section>"""
    (OUT / "404.html").write_text(page(cfg, f'Not found | {cfg["title"]}', description, missing), encoding="utf-8")
    (OUT / ".nojekyll").write_text("", encoding="utf-8")
    counts = ", ".join(f"{n} {t}{'' if n == 1 else 's'}"
                       for t, n in ((t, sum(r["type"] == t for r in rows)) for t in TYPES))
    print(f"Built _site/ with {len(rows)} entries ({counts}).")


if __name__ == "__main__":
    build()
    if "--serve" in sys.argv:
        import functools
        import http.server
        handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(OUT))
        print("Preview at http://localhost:8000/  (Ctrl+C to stop)")
        http.server.ThreadingHTTPServer(("127.0.0.1", 8000), handler).serve_forever()
