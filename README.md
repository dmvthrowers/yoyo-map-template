# Yo-Yo Map Template

A free map of the players, clubs, and shops near you, for a **yo-yo, kendama, or skill toy
community**. Edit one settings file, and GitHub builds and publishes the map for you. No servers,
logins, databases, or monthly fees.

It's the simple version of the [YoYo Map](https://map.dmvthrowers.club/) run by
[DMV Throwers](https://dmvthrowers.club/). That map needs Next.js, Supabase, and email. This one is a
single static page you update by hand, which suits a club with dozens of pins rather than
thousands.

- **Cost:** $0 on GitHub Pages.
- **Time:** about 15 minutes from "Use this template" to a live map.
- **Skills:** you can edit a text file in your web browser. An AI coding agent can do the whole thing (see [AGENTS.md](AGENTS.md)).
- **License:** [Unlicense](LICENSE), public domain. Leaflet, in `assets/vendor/leaflet/`, keeps its own [BSD-2 license](assets/vendor/leaflet/LICENSE).

**What you get:** one page with:

- **A map** with square pins for players, clubs, and shops, and checkboxes to show or hide each kind
- **A list of everyone** under the map. It works without JavaScript and with screen readers.
- **"Get on the map"** and **"How your privacy works"** sections
- An **"Add me to the map"** issue form, if you want people to ask through GitHub

**Privacy is built in, not optional:**

- Players are published at **city level only**. The build snaps each player's pin to a grid about
  10 km wide, then spreads pins in the same city so they don't stack. Even if someone types a
  home's exact coordinates into the settings file, the exact spot never reaches the website.
- The build **refuses** extra fields like `address`, `email`, `phone`, or `age`, and any name or
  note with an email address in it.
- No accounts, cookies, trackers, or outside fonts. A strict security policy allows only the site's
  own files plus the map tiles.

The look matches DMV Throwers: square corners, flat boxes with no shadows, serif headings, in your colors.

---

## Quick start

You need a free [GitHub account](https://github.com/signup).

1. **Make your own copy.** Click **Use this template → Create a new repository**. Keep it **Public**
   (free GitHub Pages needs that; nothing private goes in it).
2. **Turn on GitHub Pages.** In your new repository: **Settings → Pages → Build and deployment →
   Source → GitHub Actions**.
3. **Fill in `map.jsonc`.** Open it, click the pencil icon, and work top to bottom. Every line has a note.
   - Title, tagline, organizer, and a **shared** contact email for removal requests
   - `center` and `zoom`: where the map opens
   - `colors`: your brand colors
   - `entries`: delete the samples and add real people, clubs, and shops
4. **Commit.** GitHub builds and publishes the map in about a minute. Find the address under
   **Settings → Pages**.

### Adding someone

Copy a block in `entries` and change it:

```jsonc
{
  "name": "Sam",
  "type": "player",
  "city": "Arlington, VA",
  "lat": 38.88, "lon": -77.10,
  "toys": ["yo-yo"]
}
```

For `lat` and `lon`, use the **city's** coordinates. Search the city on
[openstreetmap.org](https://www.openstreetmap.org/), right-click the city center, and choose
**Show address**. For players, the build blurs whatever you enter. Clubs and shops are shown
exactly where you put them, so use their **public** meetup spot or storefront.

Only add people who asked to be listed, with a parent's OK for kids, and never a child's full name.
Remove anyone who asks, the same day: delete their block and commit.

### How people ask to be added

Pick one and put its address in `add_url`:

- **The built-in issue form:** `https://github.com/YOU/YOUR-REPO/issues/new?template=add-to-map.yml`.
  It's public, so it warns people not to post contact details.
- **A Google Form** or your club's contact page, if your members don't use GitHub.
- Leave `add_url` empty and people email `contact_email`.

## Preview on your computer (optional)

```sh
python3 build.py --serve        # http://localhost:8000/
python3 scripts/check_site.py   # must print "OK"
```

Python 3.9 or newer. Nothing to install.

## What's in here

| Path | What |
| --- | --- |
| `map.jsonc` | Everything you edit: settings and entries |
| `build.py` | Checks `map.jsonc`, blurs player pins, writes `_site/` |
| `scripts/check_site.py` | Runs before every deploy: security policy, links, and privacy checks |
| `assets/style.css`, `assets/map.js` | Look and map behavior |
| `assets/vendor/leaflet/` | [Leaflet](https://leafletjs.com) 1.9.4, the map library, served from your own site |
| `.github/workflows/deploy.yml` | Build, check, and publish on every commit to `main` |
| `.github/ISSUE_TEMPLATE/add-to-map.yml` | The public "Add me to the map" form |

## Map tiles

The street map under the pins comes from OpenStreetMap's free tile server. That's fine for a club
map with modest traffic under the
[OSM tile usage policy](https://operations.osmfoundation.org/policies/tiles/). If your map gets
busy, switch `tiles` to another provider. The build adds the new host to the security policy for you.

## Growing out of it

When you need self-serve sign-ups, email verification, or thousands of pins, look at the full
[yoyo-player-map](https://github.com/dmvthrowers/yoyo-player-map) app behind map.dmvthrowers.club.
Pair this map with a club website from
[yoyoclub-template](https://github.com/dmvthrowers/yoyoclub-template).
