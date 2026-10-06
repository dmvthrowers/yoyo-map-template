# Setup

From an empty Supabase project to a live map. Plan on an hour. Every service has a free tier.

## 1. Edit the config

Open [`map.config.ts`](../map.config.ts) and set `site`, `organizer`, `toy`, `links` and `privacy`. Run `pnpm check`; it prints any config problem. Wording in `messages/en.json` uses `{{tokens}}` filled from the config, so rename the toy once and every page follows.

`privacy.blurMiles` is how far a person's pin is moved from their city. The app refuses anything under 5. The home page and privacy policy quote the number you set.

## 2. Supabase

1. Create a project at supabase.com.
2. Apply the migrations in `supabase/migrations/` in order. With the CLI: `supabase link --project-ref <ref>` then `supabase db push`. Or paste each file into the SQL Editor.
3. Copy the project URL, anon key and service-role key into `.env.local` (`NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_ROLE_KEY`).
4. Load the place list: `pnpm seed-locations`. It downloads city data and upserts it; safe to re-run.

The service-role key only runs on the server. Never put it in a `NEXT_PUBLIC_` variable and never commit `.env.local`.

## 3. Upstash (rate limits)

Create a Redis database at upstash.com and copy the REST URL and token into `UPSTASH_REDIS_REST_URL` and `UPSTASH_REDIS_REST_TOKEN`.

## 4. Resend (email)

1. Create an account at resend.com and verify your sending domain (add the DNS records they give you).
2. Set `RESEND_API_KEY` and `EMAIL_FROM`, for example `"Your Map <noreply@yourdomain.org>"`.

Email goes through a queue with daily limits so a spike can't blow your quota. `vercel.json` drains it daily. For faster delivery run `supabase/optional/email-drain-cron.sql` or add a QStash schedule (`QSTASH_*` keys).

## 5. Secrets

Generate each with `openssl rand -hex 32`: `ADMIN_PASSWORD`, `CRON_SECRET`, `REVALIDATE_SECRET`, `HEALTHCHECK_TOKEN`.

## 6. Optional services

- **Cloudflare Turnstile** on the submit and report forms: set both `NEXT_PUBLIC_TURNSTILE_SITE_KEY` and `TURNSTILE_SECRET_KEY`.
- **Sentry** error reporting: set `NEXT_PUBLIC_SENTRY_DSN`. Off when unset.
- **Healthchecks.io** job check-ins: `HEALTHCHECKS_PING_KEY`.

## 7. Run it

```bash
pnpm dev
```

Submit yourself on `/submit`, confirm the email, and check the pin appears near, but not on, your city.

## 8. Deploy to Vercel

1. Import the repo in Vercel.
2. Add every key from `.env.local.example` under **Environment Variables**. Mark the secrets Sensitive. Set `NEXT_PUBLIC_APP_URL` to your public address.
3. Deploy, then add your domain and point DNS at Vercel.
4. Pick a Vercel function region near your Supabase region, so database calls stay fast.

Daily cron jobs in `vercel.json` call `/api/cron` and `/api/admin/drain-email-queue`. Both need `CRON_SECRET`.

## Before you launch

- [ ] A lawyer has reviewed the privacy policy and terms.
- [ ] `/api/health?deep=1&token=<HEALTHCHECK_TOKEN>` returns ok in production.
- [ ] A test submission verifies, publishes, and can be deleted from `/profile`.
- [ ] `ADMIN_PASSWORD` is long and random.
- [ ] No secret is in the repo (`git log -p | grep -i service_role` finds nothing).
