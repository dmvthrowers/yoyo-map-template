
'use client';

import { useTranslations } from 'next-intl';
import { useRouter, usePathname } from '@/i18n/navigation';
import { useParams } from 'next/navigation';
import { routing } from '@/i18n/routing';
import React from 'react';

export default function LanguageSwitcher() {
  // The languages come from i18n/routing.ts. Each needs a nav.languages.<code> name in the messages.
  const locales = routing.locales.map((code) => ({ code: code as string, key: `nav.languages.${code}` }));
  const t = useTranslations();
  const router = useRouter();
  const pathname = usePathname();
  const params = useParams();
  const currentLocale = (params?.locale as string) || routing.defaultLocale;

  function handleChange(e: React.ChangeEvent<HTMLSelectElement>) {
    const code = e.target.value;
    const validCodes = locales.map(l => l.code);
    if (code && validCodes.includes(code)) {
      const search = window.location.search;
      const hash = window.location.hash;
      router.replace(pathname + search + hash, { locale: code });
    }
  }

  // Nothing to switch between until a second language is added.
  if (locales.length < 2) return null;

  return (
    <div className="flex items-center gap-2">
      <label htmlFor="language-switcher" className="text-xs text-navy/60">
        {t('nav.language')}
      </label>
      <select
        id="language-switcher"
        className="text-xs border px-2 py-1 bg-white text-brand-red focus:outline-none focus:ring-2 focus:ring-brand-red"
        onChange={handleChange}
        value={currentLocale}
      >
        {locales.map((l) => (
          <option key={l.code} value={l.code}>{t(l.key)}</option>
        ))}
      </select>
    </div>
  );
}
