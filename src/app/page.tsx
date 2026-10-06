import { redirect } from 'next/navigation';
import { routing } from '@/i18n/routing';

export default function RootPage() {
  // The proxy (src/proxy.ts) handles this almost always; this runs only if it is bypassed.
  redirect(`/${routing.defaultLocale}`);
}
