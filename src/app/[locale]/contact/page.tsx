import { Link } from '@/i18n/navigation';
import { getTranslations, setRequestLocale } from 'next-intl/server';
import { routing } from '@/i18n/routing';
import type { Metadata } from 'next';
import { organizer, site } from '@/map.config';

export const metadata: Metadata = {
  title: `Contact — ${site.name}`,
  description: `Get in touch with ${organizer.description}.`,
  alternates: { canonical: '/contact' },
};

export function generateStaticParams() {
  return routing.locales.map((locale) => ({ locale }));
}

export default async function ContactPage({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations();

  return (
    <div className="max-w-xl mx-auto px-4 py-12">
      <p className="text-xs uppercase tracking-[0.3em] text-brand-red font-bold mb-2">
        {t('contact.eyebrow')}
      </p>
      <h1 className="text-4xl mb-4">{t('contact.title')}</h1>
      <p className="text-navy/80 mb-8">{t('contact.description')}</p>

      <ul className="space-y-3 text-sm">
        <li>
          <span className="font-semibold">{t('contact.emailClub')}: </span>
          <a href={`mailto:${organizer.contactEmail}`} className="text-brand-red underline hover:opacity-80">
            {organizer.contactEmail}
          </a>
        </li>
        {organizer.instagram && (
          <li>
            <span className="font-semibold">{t('contact.instagram')}: </span>
            <a
              href={`https://instagram.com/${organizer.instagram}`}
              className="text-brand-red underline hover:opacity-80"
              target="_blank"
              rel="noopener noreferrer"
            >
              @{organizer.instagram}
            </a>
          </li>
        )}
        {organizer.phone && (
          <li>
            <span className="font-semibold">{t('contact.phone')}: </span>
            <a href={`tel:${organizer.phone}`} className="text-brand-red underline hover:opacity-80">
              {organizer.phone}
            </a>
          </li>
        )}
        {organizer.contactPerson && (
          <li>
            <span className="font-semibold">{t('contact.coordinator')}: </span>
            {organizer.contactPerson}
          </li>
        )}
      </ul>

      <div className="mt-10">
        <Link href="/" className="btn-ghost inline-block">
          ← {t('contact.backToHome')}
        </Link>
      </div>
    </div>
  );
}
