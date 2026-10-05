# Instructions for AI coding agents

You're helping someone publish a city-level map of yo-yo / skill toy players, clubs, and shops from
this template. The human-facing guide is [README.md](README.md). Read it, then follow this.

## Steps
1. **Collect facts from the user:** map title, tagline, organizer name and URL, a shared contact
   email, where the map should open (`center`, `zoom`), brand colors, how people should ask to be
   added (`add_url`), and the entries. Never invent entries or facts. Leave values `""` rather than guess.
2. **Edit `map.jsonc` only** for content. Keep `//` comments on their own lines.
3. **Coordinates:** use the city's coordinates for players. Clubs and shops use their public venue
   or storefront. Never a home address.
4. **Build and check:** `python3 build.py && python3 scripts/check_site.py`. Fix every error and
   WARNING. The check must print `OK`.
5. **Deploy:** the human creates the repo from the template and sets **Settings → Pages → Source:
   GitHub Actions**. Push to `main`, confirm the run is green and the Pages URL loads.

## Rules
- **Privacy is the product.** Players stay city-level. Don't loosen `PLAYER_GRID`/`PLAYER_SPREAD`
  in `build.py`, don't add fields to `ENTRY_KEYS` that identify a person or place (address, email,
  phone, age, school), and don't remove the matching checks in `scripts/check_site.py`. No full
  names of children. Only list people who asked; remove on request.
- **Security:** no inline `<script>` (the JSON data block is the one exception), `<style>`,
  `style=""`, or `on*=` handlers. No `http://` links. No trackers, analytics, or outside fonts. Leaflet
  is vendored in `assets/vendor/leaflet/`. Don't swap it for a CDN.
- **Look:** square corners, no `box-shadow`, flat boxes. Colors come from `map.jsonc` via the built
  `theme.css`. Don't hard-code hex values in `style.css`.
- **Links:** relative only, so the map works at `user.github.io/repo/` and on a custom domain.
- **No dependencies:** `build.py` and `scripts/check_site.py` stay standard-library Python 3.9+.

## Useful commands
```sh
python3 build.py --serve        # build + preview at http://localhost:8000/
python3 scripts/check_site.py   # must print "OK"
```
