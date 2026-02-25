import { NextResponse } from 'next/server';

const DEFAULT_ADVISOR_URL = 'http://localhost:8002';

export async function POST() {
  const advisorServiceUrl = (process.env.ADVISOR_SERVICE_URL || DEFAULT_ADVISOR_URL).replace(/\/$/, '');
  const advisorApiKey = process.env.ADVISOR_API_KEY?.trim();
  const endpoint = `${advisorServiceUrl}/advisor/api/v1/policy-voice/signed-url`;

  try {
    const response = await fetch(endpoint, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(advisorApiKey ? { 'X-Api-Key': advisorApiKey } : {}),
      },
      cache: 'no-store',
    });

    const payload = await response.json();
    if (!response.ok) {
      return NextResponse.json(
        {
          success: false,
          error: payload?.error ?? 'Failed to create policy voice session',
          details: payload?.details,
        },
        { status: response.status }
      );
    }

    return NextResponse.json(payload, { status: 200 });
  } catch (error) {
    return NextResponse.json(
      {
        success: false,
        error: 'Policy voice session request failed',
        details: error instanceof Error ? error.message : 'Unknown error',
      },
      { status: 502 }
    );
  }
}
