import type { MetadataRoute } from 'next';

// Served at /robots.txt (generated at build). Cloudflare's managed robots.txt
// prepends its content-signals block to whatever the origin serves — today the
// origin 404s, so visitors only see Cloudflare's comments; this gives the origin
// real directives plus the sitemap pointer. Journal privacy does NOT rely on
// this file (robots is advisory) — that's Cloudflare Access + the API gate.
export default function robots(): MetadataRoute.Robots {
  return {
    rules: {
      userAgent: '*',
      allow: '/',
    },
    sitemap: 'https://theta.thevixguy.com/sitemap.xml',
  };
}
