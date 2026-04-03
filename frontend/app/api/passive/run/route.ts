import { NextRequest, NextResponse } from 'next/server';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { file, domain, whatsappNumber } = body;

    // Generate a session ID
    const sessionId = `passive-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;

    // Store in a simple in-memory store (in production, use database)
    const sessions = (global as any).sessions || {};
    sessions[sessionId] = {
      mode: 'passive',
      status: 'processing',
      currentStep: 0,
      file,
      domain,
      whatsappNumber,
      createdAt: new Date(),
      transcript: '',
      json: null,
      sentiment: null,
    };
    (global as any).sessions = sessions;

    return NextResponse.json({ sessionId });
  } catch (error) {
    return NextResponse.json({ error: 'Failed to start session' }, { status: 400 });
  }
}
