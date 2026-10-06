import type { Metadata } from 'next';

import { site } from '@/map.config';
export const metadata: Metadata = {
  title: 'Report an Entry',
  description: `Report an entry on ${site.name} for review.`,
  robots: { index: false, follow: false },
};

export default function ReportLayout({ children }: { children: React.ReactNode }) {
  return children;
}
