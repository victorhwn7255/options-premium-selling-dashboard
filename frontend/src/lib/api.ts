import type { ScanResponse, HealthResponse } from './types';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || '';

export async function fetchLatestScan(): Promise<ScanResponse> {
  const res = await fetch(`${API_BASE}/api/scan/latest`);
  if (!res.ok) throw new Error('Failed to fetch cached scan');
  return res.json();
}

export async function triggerScan(): Promise<ScanResponse> {
  const res = await fetch(`${API_BASE}/api/scan`, { method: 'POST' });
  if (!res.ok) throw new Error(`Scan failed: ${res.status}`);
  return res.json();
}

export async function fetchHealth(): Promise<HealthResponse> {
  const res = await fetch(`${API_BASE}/api/health`);
  if (!res.ok) throw new Error(`Health check failed: ${res.status}`);
  return res.json();
}

export async function fetchTickerHistory(ticker: string, days = 120) {
  const res = await fetch(`${API_BASE}/api/ticker/${ticker}/history?days=${days}`);
  if (!res.ok) throw new Error(`History fetch failed: ${res.status}`);
  return res.json();
}

export async function fetchUniverse() {
  const res = await fetch(`${API_BASE}/api/universe`);
  if (!res.ok) throw new Error(`Universe fetch failed: ${res.status}`);
  return res.json();
}

export async function refreshEarnings(): Promise<{ earnings: Record<string, number | null>; remaining: number }> {
  const res = await fetch(`${API_BASE}/api/earnings/refresh`, { method: 'POST' });
  if (!res.ok) throw new Error(`Earnings refresh failed: ${res.status}`);
  return res.json();
}

export async function fetchEarningsRemaining(): Promise<{ remaining: number }> {
  const res = await fetch(`${API_BASE}/api/earnings/remaining`);
  if (!res.ok) throw new Error(`Earnings remaining check failed: ${res.status}`);
  return res.json();
}
