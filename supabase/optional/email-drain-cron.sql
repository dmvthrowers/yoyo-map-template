-- Optional: drain the email queue every few minutes from inside Supabase (pg_cron + pg_net).
-- vercel.json already drains once a day; run this if you want confirmation emails to go out sooner
-- on a Vercel plan that limits cron frequency. Not part of the migrations: edit the two values
-- below, then run it once in the SQL Editor.
--
--   <your-domain>  your public address, e.g. map.example.org
--   <CRON_SECRET>  the same value as the CRON_SECRET environment variable
--
-- Check that pg_cron and pg_net are enabled first (Database > Extensions).

select cron.schedule(
  'drain-email-queue',
  '*/5 * * * *',
  $$
  select net.http_get(
    url := 'https://<your-domain>/api/admin/drain-email-queue',
    headers := jsonb_build_object('Authorization', 'Bearer <CRON_SECRET>')
  );
  $$
);

-- To stop it: select cron.unschedule('drain-email-queue');
