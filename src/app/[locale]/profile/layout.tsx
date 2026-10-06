import type { Metadata } from 'next';

import { site } from '@/map.config';
export const metadata: Metadata = {
  title: 'Your Profile',
  description: `Manage your ${site.name} entry.`,
  robots: { index: false, follow: false },
};

export default function ProfileLayout({ children }: { children: React.ReactNode }) {
  return children;
}
