import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'Theta Harvest',
  description: 'Volatility analysis dashboard for premium selling opportunities. Data powered by MarketData.app.',
  icons: {
    icon: '/favicon.svg',
  },
};

const themeScript = `
(function() {
  var t = localStorage.getItem('oh-theme');
  if (!t) t = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
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
