import { NextIntlClientProvider, hasLocale } from 'next-intl';
import { getMessages, setRequestLocale, getTranslations } from 'next-intl/server';
import { notFound } from 'next/navigation';
import type { Metadata } from 'next';
import { Link } from '@/i18n/navigation';
import Navigation from '@/components/Navigation';
import { routing } from '@/i18n/routing';
import { links, organizer, site } from '@/map.config';
import '../globals.css';

// Site-wide defaults. Pages that set their own title/description override
// these; without them the homepage shipped with no <title> at all.
export async function generateMetadata({ params }: { params: Promise<{ locale: string }> }): Promise<Metadata> {
  const { locale } = await params;
  const t = await getTranslations({ locale, namespace: 'map' });
  return {
    metadataBase: new URL(site.url),
    title: t('pageTitle'),
    description: t('pageDescription'),
    openGraph: {
      title: t('pageTitle'),
      description: t('pageDescription'),
      siteName: site.name,
      type: 'website',
    },
    icons: { icon: '/favicon.svg' },
  };
}

export function generateStaticParams() {
  return routing.locales.map((locale) => ({ locale }));
}

export default async function Layout({ children, params }: { children: React.ReactNode; params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  if (!hasLocale(routing.locales, locale)) notFound();

  setRequestLocale(locale);
  const messages = await getMessages();
  // Use translations in the footer
  const t = await getTranslations();

  return (
    <html lang={locale}>
      <body className="min-h-screen flex flex-col">
        <NextIntlClientProvider locale={locale} messages={messages}>
          <header className="sticky top-0 z-40">
            <Navigation />
          </header>
          <main id="main-content" className="flex-1">
            {children}
          </main>
          <footer className="bg-dark-navy text-cream/80 border-t-4 border-brand-red mt-12">
            <div className="max-w-6xl mx-auto px-4 py-8 grid md:grid-cols-4 gap-6 text-sm">
              <div>
                <p className="font-display text-lg text-cream">{t('footer.title')}</p>
                <p className="mt-2">{t('footer.description')}</p>
              </div>
              <div>
                <p className="font-semibold uppercase tracking-wider text-xs mb-2">{organizer.name}</p>
                <ul className="space-y-1">
                  {links.footer.map((l) => (
                    <li key={l.href}><a href={l.href} className="hover:text-brand-red">{l.label}</a></li>
                  ))}
                </ul>
              </div>
              <div>
                <p className="font-semibold uppercase tracking-wider text-xs mb-2">{t('footer.legal')}</p>
                <ul className="space-y-1">
                  <li><Link className="hover:text-brand-red" href="/legal/privacy">{t('footer.privacy')}</Link></li>
                  <li><Link className="hover:text-brand-red" href="/legal/terms">{t('footer.terms')}</Link></li>
                </ul>
                <p className="font-semibold uppercase tracking-wider text-xs mt-4 mb-2">{t('footer.security')}</p>
                <ul className="space-y-1">
                  <li><Link className="hover:text-brand-red" href="/legal/security">{t('footer.securityBulletin')}</Link></li>
                  <li><Link className="hover:text-brand-red" href="/status">{t('footer.serviceStatus')}</Link></li>
                </ul>
              </div>
              <div>
                <p className="font-semibold uppercase tracking-wider text-xs mb-2">{t('footer.project')}</p>
                <ul className="space-y-1">
                  {site.repoUrl && (
                    <li><a href={site.repoUrl} target="_blank" rel="noopener noreferrer" className="hover:text-brand-red">{t('footer.github')}</a></li>
                  )}
                  <li><Link className="hover:text-brand-red" href="/contact">{t('footer.contact')}</Link></li>
                  {site.regionLabel && <li className="text-xs">{site.regionLabel}</li>}
                </ul>
              </div>
            </div>
            <div className="bg-navy py-3 text-center text-xs">
              <p>{t('footer.copyright')}</p>
            </div>
          </footer>
        </NextIntlClientProvider>
      </body>
    </html>
  );
}
