import type { Metadata } from 'next';
import './globals.css';

const SITE_URL = 'https://theta.thevixguy.com';
const TITLE = 'Theta Harvest — Volatility Premium Scanner for Options Sellers';
const DESCRIPTION =
  'Daily 0–100 edge scores for selling options premium across 33 liquid US stocks and ETFs. ' +
  'Fuses volatility risk premium (VRP), IV percentile, term structure, RV stability, and skew — ' +
  'with hard risk gates and an at-a-glance market regime that says NO as clearly as GO.';

export const metadata: Metadata = {
  metadataBase: new URL(SITE_URL),
  title: {
    default: TITLE,
    template: '%s · Theta Harvest',
  },
  description: DESCRIPTION,
  icons: {
    icon: '/favicon.svg',
  },
  openGraph: {
    type: 'website',
    url: SITE_URL,
    siteName: 'Theta Harvest',
    title: TITLE,
    description: DESCRIPTION,
    images: [
      {
        url: '/og-banner.png',
        width: 1200,
        height: 476,
        alt: 'Theta Harvest — volatility premium scanner dashboard',
      },
    ],
  },
  twitter: {
    card: 'summary_large_image',
    title: TITLE,
    description: DESCRIPTION,
    images: ['/og-banner.png'],
  },
};

const themeScript = `
(function() {
  var t = localStorage.getItem('oh-theme');
  if (!t) t = 'dark';
  document.documentElement.setAttribute('data-theme', t);
})();
`;

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <script dangerouslySetInnerHTML={{ __html: themeScript }} />
      </head>
      <body>{children}</body>
    </html>
  );
}
