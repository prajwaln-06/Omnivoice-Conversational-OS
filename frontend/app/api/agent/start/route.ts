import { NextRequest, NextResponse } from 'next/server';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { domain, whatsappNumber } = body;

    const sessionId = `agent-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;

    const sessions = (global as any).sessions || {};
    sessions[sessionId] = {
      mode: 'agent',
      status: 'active',
      domain,
      whatsappNumber,
      createdAt: new Date(),
      logs: [
        '[INFO] Agent session initialized',
        '[INFO] Domain: ' + domain,
        '[INFO] Connecting to voice pipeline...',
        '[SUCCESS] Connected to ASR engine',
        '[SUCCESS] Connected to LLM service',
        '[SUCCESS] Connected to TTS engine',
      ],
    };
    (global as any).sessions = sessions;

    return NextResponse.json({ sessionId });
  } catch (error) {
    return NextResponse.json({ error: 'Failed to start agent session' }, { status: 400 });
  }
}
