/**
 * Thin fetch wrapper around the existing FastAPI backend.
 * Base URL is read from EXPO_PUBLIC_API_BASE (set in app.config.ts / .env).
 *
 * Auth: magic-link issues a Supabase JWT — store it in SecureStore on the
 * client and attach as Authorization: Bearer <jwt>. For anonymous surfaces
 * (stack brief, claim check, risk projection) the JWT is optional.
 */
import * as SecureStore from 'expo-secure-store';

const BASE = process.env.EXPO_PUBLIC_API_BASE || 'https://healthuniverse.vercel.app';

async function authHeaders(): Promise<Record<string, string>> {
  const jwt = await SecureStore.getItemAsync('hu_jwt');
  return jwt ? { Authorization: `Bearer ${jwt}` } : {};
}

async function request<T>(method: string, path: string, body?: unknown): Promise<T> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(await authHeaders()),
  };
  const r = await fetch(`${BASE}${path}`, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!r.ok) {
    const text = await r.text().catch(() => '');
    throw new Error(`API ${r.status} ${path}: ${text.slice(0, 200)}`);
  }
  // Some endpoints return HTML for anon flows; callers know what to expect.
  const ct = r.headers.get('content-type') || '';
  return ct.includes('application/json') ? r.json() : (r.text() as unknown as T);
}

// ─── Typed endpoint helpers ───────────────────────────────────────

export interface TodayBriefing {
  date: string;
  summary: string;
  signals: {
    label: string;
    tone: 'neutral' | 'protective' | 'harmful' | 'mixed' | 'gold';
    count: number;
  }[];
  evidence_that_moved: {
    id: string;
    tier: string;
    factor: string;
    outcome: string;
    why: string;
    date: string;
  }[];
}

export interface StackBriefResult {
  summary: string;
  conditional_harms: {
    label: string;
    severity: 'high' | 'moderate' | 'low';
    mechanism: string;
    context: string;
    sources: string[];
  }[];
  synergies: { label: string; mechanism: string }[];
  evidence: {
    id: string;
    tier: string;
    factor: string;
    outcome: string;
    direction: 'protective' | 'harmful' | 'mixed';
    summary: string;
  }[];
}

export interface DailyBriefing {
  date: string;
  headline: string;
  signals: { label: string; value: string; delta?: string }[];
  anomalies: { metric: string; description: string }[];
  corpus_shifts: { description: string; count: number }[];
  loops: { label: string; due_days?: number }[];
  correlations: { pair: string; r: number; window_days: number }[];
}

export const api = {
  todayBriefing: () => request<TodayBriefing>('GET', '/api/me/briefing'),
  stackBrief: (items: string[]) =>
    request<StackBriefResult>('GET', `/api/me/stack?items=${encodeURIComponent(items.join(','))}`),
  synergies: (stack: string[]) =>
    request<{ rows: unknown[] }>('GET', `/api/me/synergies?stack=${encodeURIComponent(stack.join(','))}`),
  dailyBriefing: () => request<DailyBriefing>('GET', '/api/me/briefing'),
  claimCheck: (claim: string, profile_hints: Record<string, unknown> = {}) =>
    request<unknown>('POST', '/api/claim-check', { claim, profile_hints }),
  challenge: (plan: string) =>
    request<unknown>('POST', '/api/me/challenge', { plan }),
  riskProjection: (body: Record<string, unknown>) =>
    request<unknown>('POST', '/api/me/risk-projection', body),
  stackAnalysis: (stack_slugs: string[], lab_names: string[]) =>
    request<unknown>('POST', '/api/me/stack-analysis', { stack_slugs, lab_names }),
};
