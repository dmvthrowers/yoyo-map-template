import { defineRouting } from 'next-intl/routing';

// English only to start. To add a language: copy messages/en.json to messages/<code>.json,
// translate it (keep the {{tokens}}), add the code here, and run `pnpm i18n:parity`.
export const locales = ['en'] as const;

export const routing = defineRouting({
  locales: [...locales],
  defaultLocale: 'en',
  localePrefix: 'always',
});
