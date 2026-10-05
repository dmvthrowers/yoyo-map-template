# Security

This template builds a static site: no logins, forms, databases, cookies, or tracking.

Built-in protections:
- A strict Content Security Policy on every page: only the site's own files, plus images from the
  map tile host set in `map.jsonc`. No inline scripts or styles.
- Leaflet is served from the site itself, not a CDN.
- Player pins are blurred to city level at build time. Exact coordinates never reach the browser.
- `scripts/check_site.py` runs before every deploy. It blocks inline scripts, styles and event
  handlers, `http://` links, broken links, unblurred player pins, and unexpected entry fields.
- GitHub Actions are pinned to exact commit SHAs and kept current by Dependabot.

**Reporting a problem with the template:** open a GitHub issue. For anything sensitive, use
GitHub's private vulnerability reporting (Security tab) if the maintainer has enabled it.

**Removal from a map built from this template:** email that map's contact address, shown in its footer.
