import { NextResponse } from 'next/server';

import type { FinalPolicy } from '@/lib/policy/types';

const DEFAULT_ADVISOR_URL = 'http://localhost:8002';

type IncomingTurn = {
  role?: string;
  message?: string;
  timestamp?: number;
};

const hasMinimumUiFields = (policy: FinalPolicy): boolean => {
  const hasMenu = Boolean(policy?.menu?.title?.trim()) && Boolean(policy?.menu?.summary?.trim());
  const hasDetailSections = Array.isArray(policy?.detail?.sections) && policy.detail.sections.length > 0;
  const hasSecuritiesBlock = Array.isArray(policy?.detail?.portfolio?.securities);
  return hasMenu && hasDetailSections && hasSecuritiesBlock;
};

const normalizeTurns = (turns: IncomingTurn[]) => {
  const normalized = turns
    .filter((turn) => turn && typeof turn.message === 'string' && turn.message.trim())
    .map((turn) => {
      const role = turn.role === 'agent' ? 'agent' : 'client';
      const ts = Number.isFinite(turn.timestamp) ? Number(turn.timestamp) : Date.now();
      return {
        speaker: role,
        text: String(turn.message || '').trim(),
        ts_start_ms: Math.max(0, Math.floor(ts)),
      };
    })
    .sort((a, b) => a.ts_start_ms - b.ts_start_ms);

  return normalized;
};

export async function POST(req: Request) {
  let body: { session_id?: string; turns?: IncomingTurn[]; completion_reason?: string };
  try {
    body = await req.json();
  } catch {
    return NextResponse.json({ success: false, error: 'Invalid JSON request body' }, { status: 400 });
  }

  const sessionId = String(body?.session_id || '').trim() || `consult-${Date.now()}`;
  const turns = Array.isArray(body?.turns) ? body.turns : [];
  const normalizedTurns = normalizeTurns(turns);
  if (!normalizedTurns.length) {
    return NextResponse.json({ success: false, error: 'No transcript turns available' }, { status: 400 });
  }

  const advisorServiceUrl = (process.env.ADVISOR_SERVICE_URL || DEFAULT_ADVISOR_URL).replace(/\/$/, '');
  const advisorApiKey = process.env.ADVISOR_API_KEY?.trim();
  const headers = {
    'Content-Type': 'application/json',
    ...(advisorApiKey ? { 'X-Api-Key': advisorApiKey } : {}),
  };

  try {
    const ingestResponse = await fetch(`${advisorServiceUrl}/advisor/api/v1/consultation-ingest`, {
      method: 'POST',
      headers,
      body: JSON.stringify({
        session_id: sessionId,
        turns: normalizedTurns,
        completion_reason: body?.completion_reason || null,
      }),
      cache: 'no-store',
    });

    const ingestPayload = await ingestResponse.json();
    if (!ingestResponse.ok || !ingestPayload?.success || !ingestPayload?.ingest_id) {
      return NextResponse.json(
        {
          success: false,
          error: ingestPayload?.error || 'Failed to ingest consultation transcript',
          details: ingestPayload?.details,
        },
        { status: ingestResponse.status || 502 }
      );
    }

    const policyResponse = await fetch(`${advisorServiceUrl}/advisor/api/v1/generate-policy-json`, {
      method: 'POST',
      headers,
      body: JSON.stringify({
        consultation_ingest_id: ingestPayload.ingest_id,
      }),
      cache: 'no-store',
    });

    const policyPayload = (await policyResponse.json()) as FinalPolicy | { error?: string; details?: unknown };
    if (!policyResponse.ok) {
      return NextResponse.json(
        {
          success: false,
          error: (policyPayload as { error?: string }).error || 'Failed to generate policy',
          details: (policyPayload as { details?: unknown }).details,
        },
        { status: policyResponse.status || 502 }
      );
    }

    if (!hasMinimumUiFields(policyPayload as FinalPolicy)) {
      return NextResponse.json(
        {
          success: false,
          error: 'Policy output missing required UI fields',
        },
        { status: 502 }
      );
    }

    return NextResponse.json({
      success: true,
      policy: policyPayload,
      consultation_ingest_id: ingestPayload.ingest_id,
    });
  } catch (error) {
    return NextResponse.json(
      {
        success: false,
        error: 'Post-consultation policy pipeline failed',
        details: error instanceof Error ? error.message : 'Unknown error',
      },
      { status: 502 }
    );
  }
}
