# Community Map Template

A free, privacy-first map of the people, groups, and places in your hobby. It started with
**yo-yo and skill toy clubs** and works for any niche community: kendama, board games, birding,
knitting, model rockets, run clubs. Edit one settings file, and GitHub builds and publishes the map
for you. No servers, logins, databases, or monthly fees.

It's the simple version of the [YoYo Map](https://map.dmvthrowers.club/) run by
[DMV Throwers](https://dmvthrowers.club/). That map needs Next.js, Supabase, and email. This one is a
single static page you update by hand, which suits a community with dozens of pins rather than
thousands.

- **Cost:** $0 on GitHub Pages.
- **Time:** about 15 minutes from "Use this template" to a live map.
- **Skills:** you can edit a text file in your web browser. An AI coding agent can do the whole thing (see [AGENTS.md](AGENTS.md)).
- **License:** [Unlicense](LICENSE), public domain. Leaflet, in `assets/vendor/leaflet/`, keeps its own [BSD-2 license](assets/vendor/leaflet/LICENSE).

**What you get:** one page with:

- **A map** with square pins in your own categories (players, clubs, shops, or birders, hotspots,
  game nights...), and checkboxes to show or hide each one
- **A list of everyone** under the map. It works without JavaScript and with screen readers.
- **"Get on the map"** and **"How your privacy works"** sections, written from your settings
- An **"Add me to the map"** issue form, if you want people to ask through GitHub

**Privacy is built in, not optional:**

- Each category is marked as people or places. **People are published at city level only.** The
  build snaps each person's pin to a grid about 10 km wide, then spreads pins in the same city so
  they don't stack. Even if someone types a home's exact coordinates into the settings file, the
  exact spot never reaches the website. A category with no `people` setting is treated as people.
- The build **refuses** extra fields like `address`, `email`, `phone`, or `age`, and any name or
  note with an email address in it.
- No accounts, cookies, trackers, or outside fonts. A strict security policy allows only the site's
  own files plus the map tiles.

The look comes from DMV Throwers: square corners, flat boxes with no shadows, serif headings, in your colors.

---

## Quick start

You need a free [GitHub account](https://github.com/signup).

1. **Make your own copy.** Click **Use this template → Create a new repository**. Keep it **Public**
   (free GitHub Pages needs that; nothing private goes in it).
2. **Turn on GitHub Pages.** In your new repository: **Settings → Pages → Build and deployment →
   Source → GitHub Actions**.
3. **Pick a starting point.** `map.jsonc` is set up for a yo-yo club. For something else, copy one of
   the examples over it:

   | Example | Categories |
   | --- | --- |
   | `map.jsonc` (default) | Players · Clubs · Shops |
   | `examples/kendama-club.jsonc` | Players · Clubs · Shops |
   | `examples/board-game-group.jsonc` | Players · Game nights · Stores |
   | `examples/birding-club.jsonc` | Birders · Clubs · Hotspots |

4. **Fill in `map.jsonc`.** Open it, click the pencil icon, and work top to bottom. Every line has a note.
   - Title, tagline, organizer, and a **shared** contact email for removal requests
   - Your words: the heading, what the tags column is called, and what to send to get listed
   - `categories`: up to 8 kinds of pins, each with a label, a color, and `people: true` or `false`
   - `center` and `zoom`: where the map opens
   - `colors`: your brand colors
   - `entries`: delete the samples and add real ones
5. **Commit.** GitHub builds and publishes the map in about a minute. Find the address under
   **Settings → Pages**.

   A red X on the Actions tab that says **"the map still shows the template's sample content"**
   means the sample title, organizer, `example.org` addresses or sample entries are still in
   `map.jsonc`. Your copy won't publish them; replace them and commit again.

### Adding an entry

Copy a block in `entries` and change it. `type` is one of your category keys:

```jsonc
{
  "name": "Sam",
  "type": "player",
  "city": "Arlington, VA",
  "lat": 38.88, "lon": -77.10,
  "tags": ["yo-yo"]
}
```

For `lat` and `lon`, use the **city's** coordinates. Search the city on
[openstreetmap.org](https://www.openstreetmap.org/), right-click the city center, and choose
**Show address**. For people, the build blurs whatever you enter. Places are shown exactly where you
put them, so use a **public** meeting spot, storefront, or park.

Only add people who asked to be listed, with a parent's OK for kids, and never a child's full name.
Remove anyone who asks, the same day: delete their block and commit.

### How people ask to be added

Pick one and put its address in `add_url`:

- **The built-in issue form:** `https://github.com/YOU/YOUR-REPO/issues/new?template=add-to-map.yml`.
  It's public, so it warns people not to post contact details.
- **A Google Form** or your group's contact page, if your members don't use GitHub.
- Leave `add_url` empty and people email `contact_email`.

## Preview on your computer (optional)

```sh
python3 build.py --serve        # http://localhost:8000/
python3 scripts/check_site.py   # must print "OK"

# Try an example without touching map.jsonc
python3 build.py --config examples/birding-club.jsonc --serve
```

Python 3.9 or newer. Nothing to install.

To add search-engine tags (canonical link, structured data, `sitemap.xml`), give the build your
public address: `python3 build.py --base-url https://example.org/map/`. On GitHub Pages the deploy
workflow does this for you.

## What's in here

| Path | What |
| --- | --- |
| `map.jsonc` | Everything you edit: settings, categories, and entries |
| `examples/` | Ready-made settings for other kinds of groups |
| `build.py` | Checks the settings, blurs people's pins, writes `_site/` |
| `scripts/check_site.py` | Runs before every deploy: security policy, links, and privacy checks |
| `assets/style.css`, `assets/map.js` | Look and map behavior |
| `assets/favicon.svg` | The browser-tab icon (replace it with your own) |
| `assets/vendor/leaflet/` | [Leaflet](https://leafletjs.com) 1.9.4, the map library, served from your own site |
| `.github/workflows/deploy.yml` | Build, check, and publish on every commit to `main` |
| `.github/ISSUE_TEMPLATE/add-to-map.yml` | The public "Add me to the map" form |

## Map tiles

The street map under the pins comes from OpenStreetMap's free tile server. That's fine for a
community map with modest traffic under the
[OSM tile usage policy](https://operations.osmfoundation.org/policies/tiles/). If your map gets
busy, switch `tiles` to another provider. The build adds the new host to the security policy for you.

## Growing out of it

When you need self-serve sign-ups, email verification, or thousands of pins, look at the full
[yoyo-player-map](https://github.com/dmvthrowers/yoyo-player-map) app behind map.dmvthrowers.club.
That app is MIT licensed (this template is public domain) and blurs players to about 10 miles; this
template snaps them to a roughly 10 km grid.
Pair this map with a club website from
[yoyoclub-template](https://github.com/dmvthrowers/yoyoclub-template).

## Words you'll see

| Word | Plain meaning |
| --- | --- |
| **JSONC** | A settings file that allows `//` comments, so every setting can explain itself |
| **GitHub Actions** | GitHub's free robot. It builds and checks your site every time you save a change |
| **GitHub Pages** | GitHub's free web hosting for the site the robot builds |
| **CSP** | Content Security Policy: a rule in each page that only lets it load its own files |
| **Preset** | A ready-made set of defaults (colors, wording) you start from and then change |

## The family

These templates share one look, one way of working, and one checklist. Pick the one that fits.

| Template | Use it for |
| --- | --- |
| [yoyoclub-template](https://github.com/dmvthrowers/yoyoclub-template) | A club website: meetups, team, gallery, FAQ |
| [yoyo-contest-template](https://github.com/dmvthrowers/yoyo-contest-template) | A contest website: schedule, divisions, sponsors, results |
| [Scouts-Template-Site](https://github.com/dmvthrowers/Scouts-Template-Site) | A Scout pack or troop, Girl Scout troop, or kids club website |
| [yoyo-map-template](https://github.com/dmvthrowers/yoyo-map-template) | A city-level community map with privacy built in |
| [yoyo-registration-template](https://github.com/dmvthrowers/yoyo-registration-template) | Contest registration, payments and day-of tools (Next.js, Stripe, Supabase) |
| [yoyo-player-map](https://github.com/dmvthrowers/yoyo-player-map) | The full player map app behind map.dmvthrowers.club |
