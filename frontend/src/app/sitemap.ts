import type { MetadataRoute } from 'next';

// Served at /sitemap.xml (generated at build). One real page — the dashboard;
// API endpoints and llms.txt don't belong in a sitemap (it maps indexable HTML).
export default function sitemap(): MetadataRoute.Sitemap {
  return [
    {
      url: 'https://theta.thevixguy.com',
      lastModified: new Date(),
      changeFrequency: 'daily', // one scan per trading day
      priority: 1,
    },
  ];
}
