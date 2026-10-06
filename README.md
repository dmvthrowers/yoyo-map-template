# Skill Toy Map

**A privacy-first community map for any skill toy: yo-yo, kendama, diabolo, spin tops, juggling.** Fork it, edit one file, and your club has a map.

People opt in, pick a city, and appear on the map at a blurred spot, never at a real address. No accounts, no messaging, no tracking.

## What you get

- A map of players, shops and clubs, with search and a players directory.
- Email-verified submissions. Teens 13 to 17 need a parent's consent link before they appear.
- Reports, an admin page, and an email queue with daily usage limits.
- Privacy by design: pins are blurred at least 5 miles (default 10), the public map reads from a view with no emails or ages, and the browser can never write to the database.
- Your name, toy, region and links in one file: [`map.config.ts`](map.config.ts).

Stack: Next.js 16, React 18, Tailwind, Leaflet, Supabase (Postgres), Upstash (rate limits), Resend (email), optional Cloudflare Turnstile and Sentry. All have free tiers.

## Quick start

```bash
corepack enable
pnpm install
cp .env.local.example .env.local   # fill in the values; see docs/SETUP.md
pnpm dev
```

Open <http://localhost:3000>. Full setup, from an empty Supabase project to a live site, is in [docs/SETUP.md](docs/SETUP.md).

## Make it yours

1. Edit [`map.config.ts`](map.config.ts): name, organizer, toy, links, where the map opens.
2. Edit wording in `messages/en.json`. Words like `{{toys}}` and `{{players}}` come from the config.
3. Replace `public/favicon.svg` and the colors in `tailwind.config.js`.
4. Run `pnpm check`. It also flags a config mistake.

## Before you launch

Have a lawyer review the privacy policy and terms (`src/app/[locale]/legal/`). They fit this architecture, but they are drafts, not legal advice. In particular, confirm that the parental consent flow suits your risk tolerance and that the governing-law wording fits your organization.

## Commands

| Command | What it does |
| --- | --- |
| `pnpm dev` | Local dev server |
| `pnpm check` | Typecheck, lint, tests, message parity |
| `pnpm build` | Production build |
| `pnpm seed-locations` | Loads countries, regions and cities into Supabase |

## Docs

- [docs/SETUP.md](docs/SETUP.md): Supabase, Resend, Vercel, environment variables.
- [docs/REPO_GUIDE.md](docs/REPO_GUIDE.md): how the code is laid out.
- [AGENTS.md](AGENTS.md): notes for AI coding agents.

## License

Public domain under [The Unlicense](LICENSE).
