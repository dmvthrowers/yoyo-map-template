/**
 * Everything about YOUR map lives here: its name, who runs it, which toy it's about, where it
 * opens and which links it shows. Edit this file first; docs/SETUP.md walks through it.
 *
 * Wording in the message files (messages/en.json) can use {{tokens}} that are filled from this
 * file when the page loads, e.g. "Find {{toys}} {{players}} near you". The list is in
 * `textTokens` below.
 *
 * This file is imported by server and browser code: nothing secret belongs here. Secrets are
 * environment variables (see .env.local.example).
 */

/** The map itself: its name, its address and where it opens. */
export const site = {
  /** Shown in the nav, page titles, emails and the footer. */
  name: 'Skill Toy Map',
  /** Where space is tight: the "offline" page and email subjects. */
  shortName: 'Toy Map',
  /** Your public address. Set NEXT_PUBLIC_APP_URL in production; this is the local default. */
  url: process.env.NEXT_PUBLIC_APP_URL || process.env.NEXT_PUBLIC_SITE_URL || 'http://localhost:3000',
  /** Source code link in the footer. Leave '' to hide it. */
  repoUrl: '',
  /** A short line under the project name in the footer, e.g. 'DC · MD · VA'. Leave '' to hide it. */
  regionLabel: 'Your Region',
  /** Where the map opens: [latitude, longitude] and a Leaflet zoom level (3 = continent, 10 = city). */
  mapView: { center: [39.5, -98.35] as [number, number], zoom: 4 },
};

/** The club or group that runs the map. */
export const organizer = {
  name: 'Your Club',
  /** One line about you, used on the contact page and in email footers. */
  description: 'Your Club, a skill toy community',
  url: 'https://example.org/',
  founded: 2024,
  /** Shown on the contact, privacy and terms pages, and in parent-consent emails. */
  contactEmail: 'hello@example.org',
  /** Gets report alerts. Defaults to contactEmail; ADMIN_NOTIFICATION_EMAIL overrides it. */
  adminEmail: process.env.ADMIN_NOTIFICATION_EMAIL || 'hello@example.org',
  /** Instagram handle without the @. Leave '' to hide it. */
  instagram: '',
  /** Optional contact person and phone for the contact page. Leave '' to hide them. */
  contactPerson: '',
  phone: '',
  /** Optional line for email footers, e.g. a nonprofit registration number. Leave '' to hide it. */
  legalNote: '',
  /** "These terms are governed by {{jurisdiction}} law." Have a lawyer review the legal pages. */
  jurisdiction: 'your state',
};

/**
 * The toy the map is about. These words fill the {{tokens}} in the messages. Change them for
 * kendama, diabolo, spin tops, juggling or "skill toys" in general.
 */
export const toy = {
  singular: 'yo-yo',
  plural: 'yo-yos',
  /** What a person on the map is called, e.g. 'player', 'thrower', 'juggler'. */
  person: 'player',
  people: 'players',
};

/** Links around the site. Each list can be empty. */
export const links = {
  /** The thin bar above the nav (desktop). */
  topbar: [{ label: 'Your Club', href: 'https://example.org/', external: false }] as { label: string; href: string; external?: boolean }[],
  /** The organizer column in the footer. */
  footer: [{ label: 'Home', href: 'https://example.org/' }] as { label: string; href: string }[],
  /** A "Keep exploring" block on the home page. Leave [] to hide it. */
  explore: [] as { title: string; body: string; href: string }[],
  /** A donate button in the nav. Leave url '' to hide it. */
  donate: { url: '', label: 'Donate', title: 'Support the club' },
};

/**
 * Privacy. Person pins are shown at a random spot up to this many miles from their city, so the
 * map never shows where anyone lives. It is the project's central promise: a smaller blur is
 * refused (see blurMiles below), and the home page and privacy policy quote the number.
 */
export const privacy = {
  blurMiles: 10,
  /** The lowest blur the app will honor. */
  minBlurMiles: 5,
};

/** The blur actually used: your setting, but never below the minimum, and never NaN. */
export function blurMiles(): number {
  const n = Number(privacy.blurMiles);
  return Number.isFinite(n) ? Math.max(privacy.minBlurMiles, n) : privacy.minBlurMiles;
}

const cap = (s: string) => s.replace(/(^|[\s-])([a-z])/g, (_m, sep: string, ch: string) => sep + ch.toUpperCase());

/** Values for {{tokens}} in messages/*.json. */
export const textTokens: Record<string, string> = {
  siteName: site.name,
  shortName: site.shortName,
  orgName: organizer.name,
  orgDescription: organizer.description,
  contactEmail: organizer.contactEmail,
  jurisdiction: organizer.jurisdiction,
  founded: String(organizer.founded),
  year: String(new Date().getFullYear()),
  regionLabel: site.regionLabel,
  toy: toy.singular,
  toys: toy.plural,
  Toy: cap(toy.singular),
  Toys: cap(toy.plural),
  player: toy.person,
  players: toy.people,
  Player: cap(toy.person),
  Players: cap(toy.people),
  blurMiles: String(blurMiles()),
};

/** Checks an edited config for mistakes. Returns a list of problems; empty means fine. */
export function configIssues(): string[] {
  const out: string[] = [];
  const emailRe = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  if (!site.name.trim()) out.push('site.name is empty');
  if (!/^https?:\/\//.test(site.url)) out.push('site.url must start with http:// or https://');
  if (!emailRe.test(organizer.contactEmail)) out.push('organizer.contactEmail is not an email address');
  if (!emailRe.test(organizer.adminEmail)) out.push('organizer.adminEmail is not an email address');
  const [lat, lng] = site.mapView.center;
  if (!(lat >= -90 && lat <= 90 && lng >= -180 && lng <= 180)) out.push('site.mapView.center must be [latitude, longitude]');
  if (!(site.mapView.zoom >= 1 && site.mapView.zoom <= 18)) out.push('site.mapView.zoom must be between 1 and 18');
  if (!(Number(privacy.blurMiles) >= privacy.minBlurMiles)) out.push(`privacy.blurMiles must be at least ${privacy.minBlurMiles} (smaller blurs are refused)`);
  if (organizer.instagram.startsWith('@')) out.push('organizer.instagram: leave off the @');
  for (const l of [...links.topbar, ...links.footer, ...links.explore]) {
    if (!/^https?:\/\//.test(l.href)) out.push(`link "${'label' in l ? l.label : l.title}" must start with http:// or https://`);
  }
  if (links.donate.url && !/^https?:\/\//.test(links.donate.url)) out.push('links.donate.url must start with http:// or https://');
  return out;
}
