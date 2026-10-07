# Instructions for AI coding agents

You're helping someone publish a city-level map of the people, groups, and places in their hobby
(skill toys, board games, birding, or any niche community) from this template. The human-facing guide is [README.md](README.md). Read it, then follow this.

## Goal
A published, privacy-safe map for one community: valid `map.jsonc`, `python3 build.py` and
`python3 scripts/check_site.py` both clean, GitHub Pages deploying from Actions, and a clear way for
people to ask to be added. Pins for people are blurred; never publish exact home locations.

## Steps
1. **Collect facts from the user:** the hobby, map title, tagline, organizer name and URL, a shared
   contact email, the categories (label, plural, color, and whether each is people or places), the
   heading / tags label / join text, where the map should open (`center`, `zoom`), brand colors, how
   people should ask to be added (`add_url`), and the entries. Never invent entries or facts. Leave
   values `""` rather than guess.
2. **Edit `map.jsonc` only** for content. If an example in `examples/` is close, start by copying it
   over `map.jsonc`. Keep `//` comments on their own lines.
3. **Categories:** anything describing individuals gets `"people": true`. Only public places and
   organizations get `false`. When unsure, leave `people` out. The build then treats it as people.
4. **Coordinates:** use the city's coordinates for people. Places use their public venue,
   storefront, or park. Never a home address.
5. **Build and check:** `python3 build.py && python3 scripts/check_site.py`. Fix every error and
   WARNING. The check must print `OK`.
6. **Deploy:** the human creates the repo from the template and sets **Settings → Pages → Source:
   GitHub Actions**. Push to `main`, confirm the run is green and the Pages URL loads.

## Rules
- **Privacy is the product.** People stay city-level. Don't loosen `PEOPLE_GRID`/`PEOPLE_SPREAD`
  in `build.py`, don't add fields to `ENTRY_KEYS` that identify a person or place (address, email,
  phone, age, school), and don't remove the matching checks in `scripts/check_site.py`. No full
  names of children. Only list people who asked; remove on request.
- **Security:** no inline `<script>` (the JSON data block is the one exception), `<style>`,
  `style=""`, or `on*=` handlers. No `http://` links. No trackers, analytics, or outside fonts. Leaflet
  is vendored in `assets/vendor/leaflet/`. Don't swap it for a CDN.
- **Look:** square corners, no `box-shadow`, flat boxes. Colors (brand and per-category pins) come
  from the settings via the built `theme.css`. Don't hard-code hex values in `style.css`.
- **No hobby words in code.** Wording lives in the settings (`heading`, `tags_label`, `join_text`,
  category labels). Keep `build.py`, `map.js`, and `style.css` hobby-neutral.
- **Examples:** every file in `examples/` must build and pass the check (CI runs them all). Entries
  there are labeled samples, not real people or businesses.
- **Links:** relative only, so the map works at `user.github.io/repo/` and on a custom domain.
- **Smoke test:** `scripts/smoke_test.js` and `.github/workflows/smoke-test.yml` build the map and its examples and click
  through every page at phone width. Run it after changing `build.py` or `assets/` (needs Node and Playwright; see the header of
  the script for the commands).
- **No dependencies:** `build.py` and `scripts/check_site.py` stay standard-library Python 3.9+.

## Useful commands
```sh
python3 build.py --serve        # build + preview at http://localhost:8000/
python3 scripts/check_site.py   # must print "OK"
python3 build.py --config examples/birding-club.jsonc --out /tmp/birding   # build an example
python3 scripts/check_site.py --config examples/birding-club.jsonc --site /tmp/birding
```
