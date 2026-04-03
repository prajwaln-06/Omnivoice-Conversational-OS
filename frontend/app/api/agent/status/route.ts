import { NextRequest, NextResponse } from 'next/server';

export async function GET(request: NextRequest) {
  try {
    const sessionId = request.nextUrl.searchParams.get('sessionId');

    if (!sessionId) {
      return NextResponse.json({ error: 'Missing sessionId' }, { status: 400 });
    }

    const sessions = (global as any).sessions || {};
    const session = sessions[sessionId];

    if (!session) {
      return NextResponse.json({ error: 'Session not found' }, { status: 404 });
    }

    // Simulate adding new logs periodically
    const elapsedSeconds = Math.floor((Date.now() - session.createdAt.getTime()) / 1000);
    
    const additionalLogs = [
      '[LISTENING] Waiting for user input...',
      '[TRANSCRIBED] User said: "Doctor, I have a persistent cough"',
      '[LLM] Processing medical history...',
      '[RESPONSE] "How long have you had this cough?"',
      '[TTS] Speaking response...',
      '[LISTENING] Waiting for user input...',
    ];

    if (elapsedSeconds > 3) {
      session.logs = session.logs.concat(
        additionalLogs.slice(0, Math.min(Math.floor(elapsedSeconds / 2), additionalLogs.length))
      );
    }

    let status = 'active';
    if (elapsedSeconds > 30) {
      status = 'completed';
    }

    return NextResponse.json({
      sessionId,
      status,
      logs: session.logs,
      uptime: elapsedSeconds,
    });
  } catch (error) {
    return NextResponse.json({ error: 'Failed to fetch status' }, { status: 500 });
  }
}
