-- 0001: baseline schema for a fresh install
--
-- The whole database in one forward-only migration: locations, entries (people, shops, clubs),
-- parent consents, verification tokens, reports, the email queue, and the public map view.
-- Add later changes as new numbered files; never edit one that has been applied.
--
-- Privacy and security, in short:
--   * Every table has row level security on.
--   * Browsers (the anon and authenticated roles) can read only: the location lists, the tag
--     list, visible entries (a fixed list of columns, no email, no consent data, no IPs) and the
--     map_entries view. They can write nothing.
--   * Everything else (consents, tokens, reports, the audit log, the email queue, the geocode
--     cache) is reachable only from the server with the service role key.
--   * Person pins hold already-blurred coordinates (see lib/geocode.ts); the exact point never
--     reaches the database for a person.

set search_path = public, extensions;

create extension if not exists citext with schema extensions;

-- =============================================================================
-- Locations (filled by `pnpm seed-locations`)
-- =============================================================================
create table public.countries (
  id    serial primary key,
  code  text not null unique check (char_length(code) = 2),
  name  text not null unique
);

create table public.regions (
  id          serial primary key,
  country_id  integer not null references public.countries (id) on delete cascade,
  code        text not null,
  name        text not null,
  unique (country_id, code),
  unique (country_id, name)
);

create table public.cities (
  id          serial primary key,
  country_id  integer not null references public.countries (id) on delete cascade,
  region_id   integer references public.regions (id) on delete set null,
  name        text not null,
  unique (country_id, region_id, name)
);

create index cities_country_id_idx on public.cities (country_id);
create index idx_cities_region_id on public.cities (region_id);

-- =============================================================================
-- Consent, entries, tokens, reports
-- =============================================================================
-- A parent or guardian's consent for a 13-17 year old. Server only.
create table public.parent_consents (
  id                  uuid primary key default gen_random_uuid(),
  created_at          timestamptz not null default now(),
  minor_display_name  text not null,
  minor_email         citext not null,
  parent_name         text not null,
  parent_email        citext not null,
  relationship        text not null,
  consent_token       text not null unique,   -- SHA-256 hash of the emailed token
  consented_at        timestamptz,
  consent_ip          inet,
  consent_user_agent  text,
  revoked_at          timestamptz,
  revoked_reason      text,
  constraint parent_consents_relationship_values check (relationship in ('parent', 'legal guardian'))
);

-- A listing: a person, a shop or a club. Several entries may share one email on purpose, so
-- email is NOT unique.
create table public.entries (
  id                      uuid primary key default gen_random_uuid(),
  created_at              timestamptz not null default now(),
  updated_at              timestamptz not null default now(),
  display_name            text not null,
  city                    text not null,
  region                  text,
  country                 text not null default 'US',   -- 2-letter code
  bio                     text,
  socials                 jsonb not null default '{}'::jsonb,
  lat                     double precision not null,    -- blurred for people, exact for shops/clubs
  lng                     double precision not null,
  email                   citext not null,
  age_band                text,
  parent_consent_id       uuid,
  is_visible              boolean not null default false,
  is_flagged              boolean not null default false,
  flagged_reason          text,
  verified_at             timestamptz,
  deleted_at              timestamptz,
  entity_type             text not null default 'person',
  exact_lat               double precision,             -- shops, and clubs that publish their venue
  exact_lng               double precision,
  address_line            text,
  postal_code             text,
  hours                   text,
  club_meeting_info       text,
  club_venue_public       boolean,
  contact_name            text,
  verified_owner          boolean not null default false,
  auto_hidden_by_reports  boolean not null default false,
  last_reminder_at        timestamptz,
  reminder_count          integer not null default 0,
  geocoded_at             timestamptz,
  country_id              integer not null,
  region_id               integer,
  city_id                 integer not null,
  location_status         text not null default 'auto_geocoded',

  constraint entries_display_name_check check (char_length(display_name) between 2 and 40),
  constraint entries_city_check check (char_length(city) between 2 and 80),
  constraint entries_bio_check check (char_length(bio) <= 280),
  constraint entries_socials_keys check (
    char_length(socials::text) <= 600
    and (socials - 'instagram' - 'youtube' - 'discord' - 'website') = '{}'::jsonb
  ),
  constraint entries_age_band_check check (age_band in ('13-17', '18+')),
  constraint entries_entity_type_check check (entity_type in ('person', 'shop', 'club')),
  constraint entries_address_line_length check (address_line is null or char_length(address_line) <= 200),
  constraint entries_postal_code_length check (postal_code is null or char_length(postal_code) <= 20),
  constraint entries_hours_length check (hours is null or char_length(hours) <= 500),
  constraint entries_club_meeting_info_length check (club_meeting_info is null or char_length(club_meeting_info) <= 500),
  constraint entries_contact_name_length check (contact_name is null or char_length(contact_name) <= 100),
  constraint entries_location_status_check check (
    location_status in ('verified', 'auto_geocoded', 'needs_research', 'awaiting_owner_response', 'dead_pin')
  ),
  -- What each kind of entry must (and must not) carry. People never hold an exact point or
  -- address; shops always do; a club holds one only when it chose to publish its venue.
  constraint entries_type_invariants check (
    case entity_type
      when 'person' then
        age_band is not null and exact_lat is null and exact_lng is null and address_line is null
        and postal_code is null and hours is null and club_meeting_info is null and club_venue_public is null
      when 'shop' then
        exact_lat is not null and exact_lng is not null and address_line is not null
        and age_band is null and club_meeting_info is null and club_venue_public is null
      when 'club' then
        club_venue_public is not null and age_band is null and hours is null
        and (
          (club_venue_public = false and exact_lat is null and exact_lng is null and address_line is null and postal_code is null)
          or (club_venue_public = true and exact_lat is not null and exact_lng is not null and address_line is not null)
        )
      else false
    end
  ),
  constraint entries_parent_consent_fk foreign key (parent_consent_id) references public.parent_consents (id) on delete restrict,
  constraint entries_country_id_fkey foreign key (country_id) references public.countries (id),
  constraint entries_region_id_fkey foreign key (region_id) references public.regions (id),
  constraint entries_city_id_fkey foreign key (city_id) references public.cities (id)
);

create index entries_age_band_idx on public.entries (age_band);
create index entries_city_id_idx on public.entries (city_id);
create index entries_country_id_idx on public.entries (country_id);
create index entries_region_id_idx on public.entries (region_id);
create index entries_created_at_idx on public.entries (created_at);
create index entries_entity_type_idx on public.entries (entity_type);
create index entries_is_visible_idx on public.entries (is_visible);
create index entries_parent_consent_id_idx on public.entries (parent_consent_id);
create index entries_visible_idx on public.entries (is_visible) where deleted_at is null;
create index entries_geocoded_at_idx on public.entries (geocoded_at nulls first) where deleted_at is null;
create index entries_location_status_idx on public.entries (location_status) where deleted_at is null;
create index entries_unverified_idx on public.entries (last_reminder_at nulls first)
  where verified_at is null and deleted_at is null and reminder_count < 3;
create index idx_entries_visible on public.entries (created_at desc) include (id, country_id, region_id, city_id)
  where is_visible = true and is_flagged = false and deleted_at is null and auto_hidden_by_reports = false;

-- Emailed links (verify, edit, delete, confirm location). Only the SHA-256 hash is stored.
create table public.verification_tokens (
  id          uuid primary key default gen_random_uuid(),
  created_at  timestamptz not null default now(),
  entry_id    uuid not null references public.entries (id) on delete cascade,
  token       text not null unique,
  purpose     text not null check (purpose in ('email_verify', 'edit_link', 'delete_link', 'location_confirm')),
  expires_at  timestamptz not null,
  used_at     timestamptz
);
create index verification_tokens_entry_idx on public.verification_tokens (entry_id);

create table public.reports (
  id              uuid primary key default gen_random_uuid(),
  created_at      timestamptz not null default now(),
  entry_id        uuid not null references public.entries (id) on delete cascade,
  reporter_ip     inet,
  reporter_email  citext,
  reason          text not null,
  details         text,
  resolved_at     timestamptz,
  resolution      text,
  constraint reports_reason_values check (
    reason in ('spam', 'harassment', 'impersonation', 'minor_unsafe', 'fake_business', 'unauthorized_listing', 'other')
  ),
  constraint reports_details_length check (details is null or char_length(details) <= 1000)
);
create index reports_entry_idx on public.reports (entry_id);

create table public.audit_log (
  id         bigserial primary key,
  at         timestamptz not null default now(),
  actor      text,
  action     text not null,
  target_id  uuid,
  meta       jsonb
);

-- Cached Nominatim answers (Nominatim allows about one request a second).
create table public.geocode_cache (
  query_hash  text primary key,
  query_kind  text not null check (query_kind in ('city', 'address')),
  result      jsonb not null,
  created_at  timestamptz not null default now()
);

-- =============================================================================
-- Tags (optional labels shown on listings: the toys someone throws, what a maker makes, ...)
-- =============================================================================
create table public.tag_catalog (
  category    text not null,
  value       text not null,
  label_en    text not null,
  sort_order  integer not null default 0,
  is_active   boolean not null default true,
  created_at  timestamptz not null default now(),
  primary key (category, value)
);

create table public.entry_tags (
  entry_id    uuid not null references public.entries (id) on delete cascade,
  category    text not null,
  value       text not null,
  created_at  timestamptz not null default now(),
  primary key (entry_id, category, value),
  foreign key (category, value) references public.tag_catalog (category, value)
);
create index entry_tags_category_value_idx on public.entry_tags (category, value);

insert into public.tag_catalog (category, value, label_en, sort_order) values
  ('skill_toy', 'yoyo',       'Yo-Yo',     1),
  ('skill_toy', 'kendama',    'Kendama',   2),
  ('skill_toy', 'diabolo',    'Diabolo',   3),
  ('skill_toy', 'juggling',   'Juggling',  4),
  ('skill_toy', 'footbag',    'Footbag',   5),
  ('skill_toy', 'spintop',    'Spin Top',  6),
  ('skill_toy', 'contact',    'Contact',   7),
  ('skill_toy', 'levistick',  'Levi Stick', 8),
  ('skill_toy', 'magic',      'Magic',     9),
  ('maker',     'wood',       'Wood',      1),
  ('maker',     'metal',      'Metal',     2),
  ('maker',     'plastic',    'Plastic',   3),
  ('maker',     'resin',      'Resin',     4),
  ('maker',     'hybrid',     'Hybrid',    5),
  ('artist',    'photographer', 'Photographer', 1),
  ('artist',    'illustrator',  'Illustrator',  2),
  ('artist',    'videographer', 'Videographer', 3),
  ('artist',    'designer',     'Designer',     4),
  ('for_hire',  'local',      'Local',     1),
  ('for_hire',  'regional',   'Regional',  2),
  ('for_hire',  'national',   'National',  3),
  ('for_hire',  'global',     'Global',    4)
on conflict do nothing;

-- =============================================================================
-- Email queue and budget (server only)
-- =============================================================================
create table public.email_queue (
  id          uuid primary key default gen_random_uuid(),
  template    text not null,
  to_email    text not null,
  payload     jsonb not null,
  not_before  timestamptz not null default now(),
  attempts    integer not null default 0,
  last_error  text,
  sent_at     timestamptz,
  created_at  timestamptz not null default now(),
  priority    smallint not null default 1,
  claimed_at  timestamptz,
  dead_at     timestamptz,
  expires_at  timestamptz
);
create index email_queue_drain_idx on public.email_queue (not_before) where sent_at is null;
create index email_queue_priority_drain_idx on public.email_queue (priority, not_before)
  where sent_at is null and dead_at is null;

create table public.email_send_log (
  id            bigserial primary key,
  to_email      text not null,
  template      text not null,
  last_sent_at  timestamptz not null default now()
);
create index email_send_log_to_email_idx on public.email_send_log (to_email);
create unique index email_send_log_to_template_uniq on public.email_send_log (to_email, template);

create table public.email_daily_usage (
  day   date primary key,
  sent  integer not null default 0
);

-- =============================================================================
-- Functions and triggers
-- =============================================================================
create function public.set_updated_at() returns trigger
language plpgsql set search_path = pg_catalog, public as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

-- Resolve the country / region / city ids from the text fields on an entry, adding the city to
-- the list when it isn't there yet.
create function public.sync_entry_location_fks() returns trigger
language plpgsql set search_path = '' as $$
declare
  v_country_id integer;
  v_region_id  integer;
  v_city_id    integer;
begin
  select id into v_country_id from public.countries where code = upper(trim(new.country));
  new.country_id := v_country_id;

  if new.region is not null and trim(new.region) <> '' then
    select id into v_region_id from public.regions
     where country_id = v_country_id and lower(name) = lower(trim(new.region)) limit 1;
    new.region_id := v_region_id;
  else
    new.region_id := null;
  end if;

  select id into v_city_id from public.cities
   where country_id = v_country_id
     and region_id is not distinct from new.region_id
     and lower(name) = lower(trim(new.city)) limit 1;

  if v_city_id is null and v_country_id is not null then
    insert into public.cities (country_id, region_id, name)
    values (v_country_id, new.region_id, initcap(trim(new.city)))
    on conflict (country_id, region_id, name) do nothing;

    select id into v_city_id from public.cities
     where country_id = v_country_id
       and region_id is not distinct from new.region_id
       and lower(name) = lower(trim(new.city));
  end if;

  new.city_id := v_city_id;
  return new;
end;
$$;

-- Keep country and region in step with the chosen city.
create function public.sync_entry_country_from_city() returns trigger
language plpgsql set search_path = '' as $$
begin
  if new.city_id is not null then
    select ci.country_id, ci.region_id into new.country_id, new.region_id
      from public.cities ci where ci.id = new.city_id;
  end if;
  return new;
end;
$$;

create trigger entries_updated_at
  before update on public.entries
  for each row execute function public.set_updated_at();

create trigger entries_sync_location_fks
  before insert or update of city, region, country on public.entries
  for each row execute function public.sync_entry_location_fks();

create trigger trg_sync_entry_country_from_city
  before insert or update of city_id, country_id, country on public.entries
  for each row execute function public.sync_entry_country_from_city();

-- Claim up to p_limit due emails for sending (safe with several workers at once).
create function public.claim_email_queue(p_limit integer) returns setof public.email_queue
language sql set search_path = '' as $$
  update public.email_queue q
     set claimed_at = now()
   where q.id in (
     select id from public.email_queue
      where sent_at is null
        and dead_at is null
        and not_before <= now()
        and (claimed_at is null or claimed_at < now() - interval '5 minutes')
      order by priority, not_before
      limit p_limit
      for update skip locked
   )
  returning q.*;
$$;

-- Today's send count (UTC): add some, or raise it to what the email provider reports.
create function public.record_email_send(p_count integer default 1) returns integer
language sql set search_path = '' as $$
  insert into public.email_daily_usage as u (day, sent)
  values ((now() at time zone 'utc')::date, p_count)
  on conflict (day) do update set sent = u.sent + excluded.sent
  returning u.sent;
$$;

create function public.observe_email_usage(p_used integer) returns integer
language sql set search_path = '' as $$
  insert into public.email_daily_usage as u (day, sent)
  values ((now() at time zone 'utc')::date, p_used)
  on conflict (day) do update set sent = greatest(u.sent, excluded.sent)
  returning u.sent;
$$;

-- =============================================================================
-- The public map: the only listing columns the world can read
-- =============================================================================
-- People get their blurred point; shops always show their exact point and address; a club shows
-- its venue only when it chose to. Hidden, flagged, deleted and auto-hidden entries never appear.
create view public.map_entries with (security_invoker = on) as
  select
    e.id,
    e.display_name,
    ci.name as city,
    r.name as region,
    c.code as country,
    e.bio,
    e.socials,
    e.entity_type,
    case
      when e.entity_type = 'shop' then e.exact_lat
      when e.entity_type = 'club' and e.club_venue_public = true then e.exact_lat
      else e.lat
    end as lat,
    case
      when e.entity_type = 'shop' then e.exact_lng
      when e.entity_type = 'club' and e.club_venue_public = true then e.exact_lng
      else e.lng
    end as lng,
    case
      when e.entity_type = 'shop' then e.address_line
      when e.entity_type = 'club' and e.club_venue_public = true then e.address_line
      else null::text
    end as address_line,
    case
      when e.entity_type = 'shop' then e.postal_code
      when e.entity_type = 'club' and e.club_venue_public = true then e.postal_code
      else null::text
    end as postal_code,
    case when e.entity_type = 'shop' then e.hours else null::text end as hours,
    case when e.entity_type = 'shop' then e.verified_owner else null::boolean end as verified_owner,
    case when e.entity_type = 'club' then e.club_meeting_info else null::text end as club_meeting_info,
    case when e.entity_type = 'club' then e.club_venue_public else null::boolean end as club_venue_public,
    e.created_at,
    (
      select jsonb_object_agg(agg.category, agg.vals)
        from (
          select et.category, jsonb_agg(et.value order by tc.sort_order) as vals
            from public.entry_tags et
            join public.tag_catalog tc on tc.category = et.category and tc.value = et.value
           where et.entry_id = e.id
           group by et.category
        ) agg
    ) as tags
  from public.entries e
  join public.countries c on c.id = e.country_id
  left join public.regions r on r.id = e.region_id
  left join public.cities ci on ci.id = e.city_id
  where e.is_visible = true and e.is_flagged = false and e.deleted_at is null and e.auto_hidden_by_reports = false;

-- =============================================================================
-- Row level security
-- =============================================================================
alter table public.countries         enable row level security;
alter table public.regions           enable row level security;
alter table public.cities            enable row level security;
alter table public.entries           enable row level security;
alter table public.parent_consents   enable row level security;
alter table public.verification_tokens enable row level security;
alter table public.reports           enable row level security;
alter table public.audit_log         enable row level security;
alter table public.geocode_cache     enable row level security;
alter table public.tag_catalog       enable row level security;
alter table public.entry_tags        enable row level security;
alter table public.email_queue       enable row level security;
alter table public.email_send_log    enable row level security;
alter table public.email_daily_usage enable row level security;

create policy public_read_countries on public.countries for select to anon, authenticated using (true);
create policy public_read_regions   on public.regions   for select to anon, authenticated using (true);
create policy public_read_cities    on public.cities    for select to anon, authenticated using (true);
create policy tag_catalog_read_all  on public.tag_catalog for select to anon, authenticated using (true);

create policy "public read visible entries" on public.entries for select to anon, authenticated
  using (is_visible = true and coalesce(is_flagged, false) = false and deleted_at is null
         and coalesce(auto_hidden_by_reports, false) = false);

create policy entry_tags_read_visible on public.entry_tags for select to anon, authenticated
  using (exists (
    select 1 from public.entries e
     where e.id = entry_tags.entry_id and e.is_visible = true and e.is_flagged = false
       and e.deleted_at is null and e.auto_hidden_by_reports = false
  ));

-- Server-only tables: no browser access at all, spelled out so it can't be loosened by accident.
create policy "No direct access" on public.parent_consents    as restrictive for all using (false);
create policy "No direct access" on public.verification_tokens as restrictive for all using (false);
create policy "No direct access" on public.reports            as restrictive for all using (false);
create policy "No direct access" on public.audit_log          as restrictive for all using (false);
create policy "No direct access" on public.geocode_cache      as restrictive for all using (false);
create policy "No direct access" on public.email_queue        as restrictive for all using (false);
create policy "No direct access" on public.email_send_log     as restrictive for all using (false);
create policy "No direct access" on public.email_daily_usage  as restrictive for all using (false);

-- =============================================================================
-- Grants: browsers read, the server does everything
-- =============================================================================
revoke all on all tables    in schema public from anon, authenticated;
revoke all on all sequences in schema public from anon, authenticated;
revoke all on all functions in schema public from public, anon, authenticated;

alter default privileges in schema public revoke all on tables    from anon, authenticated;
alter default privileges in schema public revoke all on sequences from anon, authenticated;
alter default privileges in schema public revoke all on functions from public, anon, authenticated;

grant select on public.countries, public.regions, public.cities, public.tag_catalog, public.entry_tags
  to anon, authenticated;
grant select on public.map_entries to anon, authenticated;

-- Listing columns a browser may read. Never email, consent, tokens, reminders or IPs.
grant select (
  id, created_at, display_name, entity_type, bio, socials, lat, lng, is_visible, is_flagged, deleted_at,
  auto_hidden_by_reports, exact_lat, exact_lng, address_line, postal_code, hours, club_meeting_info,
  club_venue_public, verified_owner, country_id, region_id, city_id
) on public.entries to anon, authenticated;

grant all on all tables    in schema public to service_role;
grant all on all sequences in schema public to service_role;
grant execute on all functions in schema public to service_role;
