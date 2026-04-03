import { NextRequest, NextResponse } from 'next/server';

const PIPELINE_STEPS = [
  'Uploading File',
  'Transcribing Audio',
  'Processing with LLM',
  'Generating Response',
];

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

    // Simulate progress through pipeline steps
    const elapsedMs = Date.now() - session.createdAt.getTime();
    let currentStep = Math.floor(elapsedMs / 2000);
    let status = 'processing';

    if (currentStep >= PIPELINE_STEPS.length) {
      status = 'completed';
      currentStep = PIPELINE_STEPS.length - 1;
      
      // Provide mock data when completed
      session.transcript = `Doctor: Good morning, how can I help you today?\n\nPatient: I've been having severe headaches for the past week, especially in the mornings. The pain is usually on the right side of my head.\n\nDoctor: I see. How severe is the pain on a scale of 1-10?\n\nPatient: I'd say about 7 or 8. It's affecting my daily routine.\n\nDoctor: Have you taken any medication?\n\nPatient: Yes, I tried some over-the-counter painkillers, but they only provide temporary relief.`;
      
      session.json = {
        patientId: 'PAT-2024-001',
        visitType: 'consultation',
        symptoms: ['headache', 'morning onset', 'unilateral pain (right)'],
        severity: 'high',
        medication: 'over-the-counter painkillers (ineffective)',
        recommendation: 'Consider neuro consultation, imaging if persistent',
        followUp: '3 days',
      };
      
      session.sentiment = 'Anxious';
    }

    return NextResponse.json({
      sessionId,
      status,
      currentStep,
      totalSteps: PIPELINE_STEPS.length,
      steps: PIPELINE_STEPS,
      transcript: session.transcript,
      json: session.json,
      sentiment: session.sentiment,
    });
  } catch (error) {
    return NextResponse.json({ error: 'Failed to fetch status' }, { status: 500 });
  }
}
