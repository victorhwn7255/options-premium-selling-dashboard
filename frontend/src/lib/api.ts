import type { ScanResponse, HealthResponse, VerificationResult, EarningsVerificationResult } from './types';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || '';

export async function fetchLatestScan(): Promise<ScanResponse> {
  const res = await fetch(`${API_BASE}/api/scan/latest`);
  if (!res.ok) throw new Error('Failed to fetch cached scan');
  return res.json();
}

export async function triggerScan(): Promise<ScanResponse> {
  const res = await fetch(`${API_BASE}/api/scan`, { method: 'POST' });
  if (!res.ok) throw new Error(`Scan failed: ${res.status}`);
  const data = await res.json();

  // If backend returned full results (cached), return immediately
  if (data.tickers) return data as ScanResponse;

  // Backend started async scan — poll until complete
  return pollForScanResults();
}

export async function fetchScanStatus(): Promise<{ status: string; current: number; total: number; ticker: string }> {
  const res = await fetch(`${API_BASE}/api/scan/status`);
  if (!res.ok) throw new Error(`Status check failed: ${res.status}`);
  return res.json();
}

async function pollForScanResults(): Promise<ScanResponse> {
  const maxAttempts = 200; // ~16 minutes at 5s intervals
  for (let i = 0; i < maxAttempts; i++) {
    await new Promise(resolve => setTimeout(resolve, 5000));
    const status = await fetchScanStatus();
    if (status.status === 'error') throw new Error('Scan failed on server');
    if (status.status === 'completed' || status.status === 'idle') {
      // Scan finished — fetch the cached results
      return fetchLatestScan();
    }
  }
  throw new Error('Scan timed out');
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

export async function fetchVerificationLatest(): Promise<VerificationResult | null> {
  const res = await fetch(`${API_BASE}/api/verify/latest`);
  if (!res.ok) return null;
  const data = await res.json();
  // If no verification yet, API returns { message: "..." } without id
  if (!data.id) return null;
  return data as VerificationResult;
}

export async function fetchEarningsVerificationLatest(): Promise<EarningsVerificationResult | null> {
  const res = await fetch(`${API_BASE}/api/verify/earnings/latest`);
  if (!res.ok) return null;
  const data = await res.json();
  if (!data.id) return null;
  return data as EarningsVerificationResult;
}
