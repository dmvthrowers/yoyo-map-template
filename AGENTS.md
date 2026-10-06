# AGENTS.md

Guide for AI coding agents working on this template.

## What this is

A forkable community map for skill toys (Next.js 16, Supabase, Upstash, Resend). Everything specific to one club lives in `map.config.ts` and `messages/en.json`. Keep the template neutral: no club names, domains or addresses in code, docs or tests.

## Rules

- **The privacy blur is the product.** Person pins are blurred at least `privacy.minBlurMiles` (5). Never lower it, narrow it, or store or log true coordinates.
- **Least privilege in the database.** Every table has row level security; the browser has no write access. `lib/schema.test.mjs` enforces this. Add migrations as new files; do not edit the baseline.
- **No secrets in the repo.** Config files are imported by the browser. Secrets are environment variables only.
- **Wording goes in `messages/en.json`** with `{{tokens}}` for names and the toy words. No hardcoded "yo-yo" or club names.
- Keep `.env.local.example` in step with the variables the code reads.

## Before you push

```bash
pnpm check && pnpm build
```

## Where things are

See [docs/REPO_GUIDE.md](docs/REPO_GUIDE.md). Setup is in [docs/SETUP.md](docs/SETUP.md).
