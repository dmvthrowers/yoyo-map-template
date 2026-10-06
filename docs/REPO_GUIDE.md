# Repo guide

| Path | What it holds |
| --- | --- |
| `map.config.ts` | Everything specific to your map: name, organizer, toy, links, privacy blur, token values |
| `messages/en.json` | All user-facing wording, with `{{tokens}}` from the config |
| `i18n/` | next-intl setup (English only; add a locale by adding it to `routing.ts` and a messages file) |
| `src/proxy.ts` | Locale routing (Next 16 "proxy", formerly middleware). Security headers and the CSP are in `next.config.js` |
| `src/app/[locale]/` | Pages: home, map, players, submit, profile, report, admin, status, contact, legal |
| `src/app/api/` | Routes: submit, verify, report, profile, admin actions, cron, health |
| `lib/site-text.ts` | Fills `{{tokens}}` in messages |
| `lib/jitter.ts`, `lib/geocode.ts` | The privacy blur: city lookup, then a random offset of at least the configured miles |
| `lib/email.ts` | Email templates and queue |
| `lib/rate-limit.ts` | Upstash limits on public write routes |
| `supabase/migrations/` | One consolidated baseline; add new files after it, never edit it once deployed |
| `supabase/optional/` | SQL you may choose to run, not applied automatically |
| `scripts/seed-locations.mjs` | Loads countries, regions and cities |

## Data and privacy

- The browser only reads, through the `map_entries` view and column-level grants. All writes go through server routes with the service-role key.
- Every table has row level security. `lib/schema.test.mjs` fails the build if a migration adds a table without it, or opens a write policy to the browser.
- Person pins are blurred in the application (`lib/geocode.ts` calls `lib/jitter.ts`). Never lower `minBlurMiles`.
- Teens 13 to 17 are not shown until a parent consents.

## Checks

`pnpm check` runs typecheck, lint, tests and the message parity check. CI runs the same plus a build.
