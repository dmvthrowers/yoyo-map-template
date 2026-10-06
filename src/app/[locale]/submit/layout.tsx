import type { Metadata } from 'next';

import { site, toy } from '@/map.config';
export const metadata: Metadata = {
  title: `Add Yourself to the ${site.name}`,
  description: `Add yourself, your shop, or your ${toy.singular} club to the community map. Opt-in, city-level only, takes about a minute.`,
  alternates: { canonical: '/submit' },
  openGraph: {
    title: `Add Yourself to the ${site.name}`,
    description: `Join the global community of ${toy.singular} ${toy.people}. Opt-in, privacy-first.`,
    url: '/submit',
  },
};

export default function SubmitLayout({ children }: { children: React.ReactNode }) {
  return children;
}
