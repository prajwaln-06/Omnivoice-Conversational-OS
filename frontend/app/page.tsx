'use client';

import { useState, useEffect, useRef } from 'react';
import { Upload, Phone, Download, MessageCircle, Play, Square, CheckCircle, Pill, Cross, Activity, Star } from 'lucide-react';

const API_BASE = 'http://localhost:8000';

type Mode = 'passive' | 'agent';
type PassiveStatus = {
  sessionId: string;
  status: 'processing' | 'completed';
  currentStep: number;
  totalSteps: number;
  steps: string[];
  transcript?: string;
  json?: Record<string, any>;
  sentiment?: string;
  rxnorm?: {
    medications_validated: any[];
    drug_interactions: any[];
    interaction_count: number;
    has_severe_interactions: boolean;
  };
  icd10?: {
    code: string;
    description: string;
  }[];
};

type AgentStatus = {
  sessionId: string;
  status: 'active' | 'completed' | 'running' | 'stopped' | 'done' | 'error';
  steps: string[];
  uptime: number;
};

export default function OmniVoiceEngine() {
  const [mode, setMode] = useState<Mode>('passive');
  const [isProcessing, setIsProcessing] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [passiveData, setPassiveData] = useState<PassiveStatus | null>(null);
  const [agentData, setAgentData] = useState<AgentStatus | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Form inputs
  const [file, setFile] = useState<File | string | null>(null);
  const [domain, setDomain] = useState('Healthcare');
  const [whatsappNumber, setWhatsappNumber] = useState('');

  // Feedback Form State
  const [rating, setRating] = useState<number | null>(null);
  const [feedbackText, setFeedbackText] = useState('');
  const [feedbackSubmitted, setFeedbackSubmitted] = useState(false);

  // Polling effect for passive mode
  useEffect(() => {
    if (mode !== 'passive' || !sessionId || !isProcessing) return;

    const interval = setInterval(async () => {
      try {
        const res = await fetch(`${API_BASE}/passive/status/${sessionId}`);
        const data: PassiveStatus = await res.json();
        setPassiveData(data);

        // Clear interval when session finishes or fails
        if (data.status === 'done' || data.status === 'error' || data.status === 'stopped') {
          setIsProcessing(false);
          clearInterval(interval);
        }
      } catch (error) {
        console.error('[v0] Passive polling error:', error);
      }
    }, 1000);

    return () => clearInterval(interval);
  }, [sessionId, isProcessing, mode]);

  // Polling effect for agent mode
  useEffect(() => {
    if (mode !== 'agent' || !sessionId || !isProcessing) return;

    const interval = setInterval(async () => {
      try {
        const res = await fetch(`${API_BASE}/agent/status/${sessionId}`);
        const data: AgentStatus = await res.json();
        setAgentData(data);

        // Clear interval when session finishes or fails
        if (data.status === 'done' || data.status === 'error' || data.status === 'stopped') {
          setIsProcessing(false);
          clearInterval(interval);
        }
      } catch (error) {
        console.error('[v0] Agent polling error:', error);
      }
    }, 1000);

    return () => clearInterval(interval);
  }, [sessionId, isProcessing, mode]);

  const handlePassiveSubmit = async () => {
    if (!file || !domain || !whatsappNumber) {
      alert('Please fill all fields');
      return;
    }

    setIsProcessing(true);
    try {
      const formData = new FormData();
      formData.append('audio', file as Blob);
      formData.append('domain', domain);
      formData.append('to_number', whatsappNumber);

      const res = await fetch(`${API_BASE}/passive/run`, {
        method: 'POST',
        body: formData,
      });
      const data = await res.json();
      setSessionId(data.session_id || data.sessionId);
    } catch (error) {
      console.error('[v0] Passive submit error:', error);
      setIsProcessing(false);
    }
  };

  const handleAgentStart = async () => {
    if (!domain || !whatsappNumber) {
      alert('Please fill all fields');
      return;
    }

    setIsProcessing(true);
    try {
      const formData = new FormData();
      formData.append('domain', domain);
      formData.append('to_number', whatsappNumber);

      const res = await fetch(`${API_BASE}/agent/start`, {
        method: 'POST',
        body: formData,
      });
      const data = await res.json();
      setSessionId(data.session_id || data.sessionId);
    } catch (error) {
      console.error('[v0] Agent start error:', error);
      setIsProcessing(false);
    }
  };

  const handleReset = () => {
    setSessionId(null);
    setPassiveData(null);
    setAgentData(null);
    setIsProcessing(false);
    setFile(null);
    setDomain('Healthcare');
    setWhatsappNumber('');
    setRating(null);
    setFeedbackText('');
    setFeedbackSubmitted(false);
  };

  const downloadPDF = () => {
    // Simulate PDF download
    alert('PDF report generated and ready for download');
  };

  const handleStopSession = async () => {
    if (!sessionId) return;
    try {
      await fetch(`${API_BASE}/agent/end/${sessionId}`, { method: 'POST' });
    } catch (e) {
      console.error('Failed to end agent session', e);
    }
    // Update local state to stopped, keep logs visible
    if (agentData) {
      setAgentData({ ...agentData, status: 'stopped' });
    }
  };

  const submitFeedback = async (currentMode: string) => {
    try {
      await fetch(`${API_BASE}/feedback`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
          session_id: sessionId,
          rating: rating,
          comment: feedbackText,
          mode: currentMode
        })
      });
      setFeedbackSubmitted(true);
    } catch (e) {
      console.error('Feedback error:', e);
    }
  };

  return (
    <div className="min-h-screen bg-[#0a0a0f] text-[#f5f5f5] font-sans">
      {/* Header */}
      <header className="border-b border-[#2a2a35] bg-[#0f0f15] sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-gradient-to-br from-[#7c3aed] to-[#a78bfa] rounded-lg flex items-center justify-center">
              <Phone className="w-5 h-5 text-white" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-white">OmniVoice Engine</h1>
              <p className="text-xs text-[#a0a0b0]">Multilingual Voice AI · 22 Indian Languages</p>
            </div>
          </div>
          <div className="text-sm text-[#a0a0b0]">Session ID: {sessionId ? sessionId.substring(0, 15) + '...' : 'None'}</div>
        </div>

        {/* Mode Tabs */}
        <div className="border-t border-[#2a2a35] flex">
          <button
            onClick={() => !isProcessing && (setMode('passive'), handleReset())}
            className={`flex-1 px-6 py-3 font-medium transition-colors ${
              mode === 'passive'
                ? 'bg-[#1a1a24] text-[#7c3aed] border-b-2 border-[#7c3aed]'
                : 'text-[#a0a0b0] hover:text-[#f5f5f5]'
            }`}
          >
            Passive Listener
          </button>
          <button
            onClick={() => !isProcessing && (setMode('agent'), handleReset())}
            className={`flex-1 px-6 py-3 font-medium transition-colors ${
              mode === 'agent'
                ? 'bg-[#1a1a24] text-[#7c3aed] border-b-2 border-[#7c3aed]'
                : 'text-[#a0a0b0] hover:text-[#f5f5f5]'
            }`}
          >
            Live Agent
          </button>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-6 py-8">
        {!sessionId ? (
          // Input Form
          <div className="max-w-md mx-auto">
            <div className="bg-[#1a1a24] border border-[#2a2a35] rounded-lg p-6 space-y-4">
              <h2 className="text-lg font-semibold text-white mb-6">
                {mode === 'passive' ? 'Start Passive Listener' : 'Start Live Agent'}
              </h2>

              {mode === 'passive' && (
                <div>
                  <label className="block text-sm text-[#a0a0b0] mb-2">Upload File</label>
                  <input
                    type="file"
                    accept=".wav,.mp3"
                    className="hidden"
                    ref={fileInputRef}
                    onChange={(e) => {
                      if (e.target.files && e.target.files.length > 0) {
                        setFile(e.target.files[0]);
                      }
                    }}
                  />
                  <div
                    onClick={() => fileInputRef.current?.click()}
                    className="border-2 border-dashed border-[#3a3a45] rounded-lg p-6 text-center cursor-pointer hover:border-[#7c3aed] transition-colors"
                  >
                    <Upload className="w-6 h-6 mx-auto mb-2 text-[#7c3aed]" />
                    <p className="text-sm text-[#a0a0b0]">Click to upload audio file</p>
                    {file && <p className="text-xs text-[#7c3aed] mt-2">{(file as File)?.name || 'File selected'}</p>}
                  </div>
                </div>
              )}

              <div>
                <label className="block text-sm text-[#a0a0b0] mb-2">Domain</label>
                <select
                  value={domain}
                  onChange={(e) => setDomain(e.target.value)}
                  className="w-full bg-[#2a2a35] border border-[#3a3a45] rounded px-3 py-2 text-[#f5f5f5] text-sm focus:outline-none focus:border-[#7c3aed]"
                >
                  <option>Healthcare</option>
                  <option>Banking</option>
                  <option>Insurance</option>
                  <option>Retail</option>
                </select>
              </div>

              <div>
                <label className="block text-sm text-[#a0a0b0] mb-2">WhatsApp Number</label>
                <input
                  type="tel"
                  value={whatsappNumber}
                  onChange={(e) => setWhatsappNumber(e.target.value)}
                  placeholder="+91 98765 43210"
                  className="w-full bg-[#2a2a35] border border-[#3a3a45] rounded px-3 py-2 text-[#f5f5f5] text-sm placeholder-[#666666] focus:outline-none focus:border-[#7c3aed]"
                />
              </div>

              <button
                onClick={mode === 'passive' ? handlePassiveSubmit : handleAgentStart}
                disabled={isProcessing || (mode === 'passive' && !file)}
                className="w-full bg-[#7c3aed] hover:bg-[#6d28d9] disabled:opacity-50 disabled:cursor-not-allowed text-white font-medium py-2 rounded transition-colors flex items-center justify-center gap-2"
              >
                <Play className="w-4 h-4" />
                {mode === 'passive' ? 'Start Processing' : 'Start Session'}
              </button>
            </div>
          </div>
        ) : mode === 'passive' && passiveData ? (
          // Passive Mode Results
          <div className="space-y-6">
            {/* Stepper */}
            <div className="bg-[#1a1a24] border border-[#2a2a35] rounded-lg p-6">
              <h3 className="text-sm font-semibold text-[#a0a0b0] uppercase tracking-wider mb-6">Processing Pipeline</h3>
              <div className="flex flex-col gap-6">
                {(passiveData?.steps ?? []).map((step, idx) => {
                  const isLast = idx === (passiveData?.steps ?? []).length - 1;
                  const isProcessing = isLast && !['completed', 'done', 'error', 'stopped'].includes(passiveData.status);
                  
                  return (
                    <div key={idx} className="flex items-start gap-4 relative">
                      {!isLast && (
                        <div className="absolute top-8 left-4 w-[2px] h-[calc(100%-0.5rem)] bg-[#3a3a45] -ml-[1px]" />
                      )}
                      <div
                        className={`relative z-10 w-8 h-8 shrink-0 rounded-full flex items-center justify-center text-xs font-bold transition-colors ${
                          isProcessing
                            ? 'bg-[#1a1a24] border-2 border-[#7c3aed] text-[#7c3aed] animate-pulse'
                            : 'bg-[#7c3aed] text-white'
                        }`}
                      >
                        {idx + 1}
                      </div>
                      <p className="text-sm text-[#e4e4e7] mt-1.5 break-words flex-1 leading-snug">{step}</p>
                    </div>
                  );
                })}
              </div>
            </div>

            {passiveData.status === 'completed' && (
              <>
                {/* Transcript */}
                <div className="bg-[#1a1a24] border border-[#2a2a35] rounded-lg p-6">
                  <h3 className="text-sm font-semibold text-[#a0a0b0] uppercase tracking-wider mb-4">Transcript</h3>
                  <div className="bg-[#0a0a0f] rounded p-4 font-mono text-sm text-[#22ff00] max-h-48 overflow-y-auto whitespace-pre-wrap">
                    {(passiveData?.transcript ?? '') || 'No transcript available'}
                  </div>
                </div>

                {/* JSON Viewer */}
                {passiveData && (passiveData.json || passiveData.extracted) && (
                  <div className="bg-[#1a1a24] border border-[#2a2a35] rounded-lg p-6">
                    <h3 className="text-sm font-semibold text-[#a0a0b0] uppercase tracking-wider mb-4">Extracted Data</h3>
                    <div className="bg-[#0a0a0f] rounded p-4 font-mono text-sm text-[#fbbf24] max-h-48 overflow-y-auto">
                      <pre>{JSON.stringify((passiveData.json ?? passiveData.extracted ?? {}), null, 2)}</pre>
                    </div>
                  </div>
                )}

                {/* RxNorm Validation Card */}
                {passiveData?.rxnorm && (
                  <div className="bg-[#1a1a24] border border-[#2a2a35] rounded-lg p-6">
                    <h3 className="text-sm font-semibold text-[#a0a0b0] uppercase tracking-wider mb-4 flex items-center gap-2">
                      <Pill className="text-[#22ff00] w-4 h-4" />
                      Drug Validation · RxNorm (NIH)
                    </h3>
                    
                    <div className="space-y-3">
                      {passiveData.rxnorm.medications_validated?.map((med, idx) => (
                        <div key={idx} className="flex items-center justify-between bg-[#0a0a0f] p-3 rounded border border-[#2a2a35]">
                          <div>
                            <span className="text-[#f5f5f5] font-medium">{med.name}</span>
                            {med.rxcui && (
                              <span className="ml-2 text-xs font-mono text-[#a0a0b0] px-2 py-0.5 bg-[#2a2a35] rounded">
                                RxCUI: {med.rxcui}
                              </span>
                            )}
                          </div>
                          {med.valid ? (
                            <span className="text-[#22ff00] text-xs font-bold border border-[#22ff00] px-2 py-1 rounded">✓ Valid</span>
                          ) : (
                            <span className="text-[#ff4444] text-xs font-bold border border-[#ff4444] px-2 py-1 rounded">✗ Not Found</span>
                          )}
                        </div>
                      ))}
                      
                      {passiveData.rxnorm.has_severe_interactions ? (
                        <div className="mt-4 p-3 bg-red-900/20 border border-red-500/50 rounded flex flex-col gap-2">
                          <span className="text-[#ff4444] font-bold flex items-center gap-2">
                            ⚠️ Severe Drug Interaction Detected
                          </span>
                          <div className="text-xs text-red-200">
                            {passiveData.rxnorm.drug_interactions?.map((i, k) => (
                              <p key={k}>• {i.description}</p>
                            ))}
                          </div>
                        </div>
                      ) : passiveData.rxnorm.interaction_count === 0 ? (
                        <div className="mt-4 text-[#22ff00] text-sm flex items-center gap-2">
                          ✓ No interactions found
                        </div>
                      ) : null}
                    </div>
                  </div>
                )}

                {/* ICD-10 Codes Card */}
                {passiveData?.icd10 && passiveData.icd10.length > 0 && (
                  <div className="bg-[#1a1a24] border border-[#2a2a35] rounded-lg p-6">
                    <h3 className="text-sm font-semibold text-[#a0a0b0] uppercase tracking-wider mb-4 flex items-center gap-2">
                      <Activity className="text-[#7c3aed] w-4 h-4" />
                      Diagnosis Codes · ICD-10
                    </h3>
                    <div className="bg-[#0a0a0f] rounded-lg border border-[#2a2a35] overflow-hidden">
                      <table className="w-full text-sm text-left">
                        <thead className="bg-[#2a2a35] text-[#a0a0b0]">
                          <tr>
                            <th className="px-4 py-2 font-medium">Code</th>
                            <th className="px-4 py-2 font-medium">Description</th>
                          </tr>
                        </thead>
                        <tbody>
                          {passiveData.icd10.map((item, idx) => (
                            <tr key={idx} className="border-t border-[#2a2a35]">
                              <td className="px-4 py-3 font-mono text-[#c084fc] font-medium">{item.code}</td>
                              <td className="px-4 py-3 text-[#f5f5f5]">{item.description}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}

                {/* Sentiment & Actions */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div className="bg-[#1a1a24] border border-[#2a2a35] rounded-lg p-6">
                    <p className="text-sm text-[#a0a0b0] mb-3">Sentiment Analysis</p>
                    <div className="inline-block px-3 py-1 rounded-full text-sm font-medium bg-[#3a3a45] text-[#f59e0b]">
                      {(passiveData?.sentiment ?? '') || 'Neutral'}
                    </div>
                  </div>

                  <div className="flex gap-2">
                    <button
                      onClick={downloadPDF}
                      className="flex-1 bg-[#2a2a35] hover:bg-[#3a3a45] text-white font-medium py-2 rounded transition-colors flex items-center justify-center gap-2"
                    >
                      <Download className="w-4 h-4" />
                      Download PDF
                    </button>
                    <button
                      onClick={downloadPDF}
                      className="flex-1 bg-[#2a2a35] hover:bg-[#3a3a45] text-white font-medium py-2 rounded transition-colors flex items-center justify-center gap-2"
                    >
                      <MessageCircle className="w-4 h-4" />
                      Send WhatsApp
                    </button>
                  </div>
                </div>

                <button
                  onClick={handleReset}
                  className="w-full bg-[#2a2a35] hover:bg-[#3a3a45] text-white font-medium py-2 rounded transition-colors"
                >
                  Start New Session
                </button>

                {/* Passive Feedback Card */}
                {(passiveData.status === 'completed' || passiveData.status === 'done' || passiveData.status === 'stopped') && (
                  feedbackSubmitted ? (
                    <div className="bg-[#13131a] border border-[#7c3aed] rounded-lg p-6 text-center mt-6">
                      <p className="text-[#22ff00] font-medium flex items-center justify-center gap-2">
                        <CheckCircle className="w-5 h-5" /> Thank you for your feedback!
                      </p>
                    </div>
                  ) : (
                    <div className="bg-[#13131a] border border-[#7c3aed] rounded-lg p-6 mt-6">
                      <h3 className="text-white font-medium text-center mb-4">How was your OmniVoice experience?</h3>
                      <div className="flex justify-center gap-2 mb-2">
                        {[1, 2, 3, 4, 5].map((star) => (
                          <button key={star} onClick={() => setRating(star)} className="focus:outline-none">
                            <Star className={`w-8 h-8 ${rating && rating >= star ? 'text-yellow-400 fill-yellow-400' : 'text-gray-600'}`} />
                          </button>
                        ))}
                      </div>
                      <div className="text-center h-6 mb-4">
                        {rating && <span className="text-[#7c3aed] text-sm font-medium">{ ({1: 'Poor', 2: 'Fair', 3: 'Good', 4: 'Great', 5: 'Excellent'} as Record<number, string>)[rating] }</span>}
                      </div>
                      <textarea
                        value={feedbackText}
                        onChange={(e) => setFeedbackText(e.target.value)}
                        placeholder="Tell us more about your experience..."
                        className="w-full bg-[#0a0a0f] border border-[#2a2a35] rounded p-3 text-white text-sm mb-4 resize-none h-20 placeholder-gray-500 focus:border-[#7c3aed] focus:outline-none"
                      />
                      <button
                        onClick={() => submitFeedback('passive')}
                        disabled={!rating}
                        className={`w-full py-2 rounded text-white font-medium transition-colors ${rating ? 'bg-[#7c3aed] hover:bg-[#6d28d9]' : 'bg-gray-600 cursor-not-allowed'}`}
                      >
                        Submit Feedback
                      </button>
                    </div>
                  )
                )}
              </>
            )}
          </div>
        ) : mode === 'agent' && agentData ? (
          // Agent Mode Results
          <div className="space-y-6">
            {/* Status Badge */}
            <div className="flex items-center gap-3">
              <div className={`w-3 h-3 rounded-full ${agentData.status === 'active' || agentData.status === 'running' ? 'bg-[#22ff00] animate-pulse' : 'bg-[#666666]'}`} />
              <span className="font-mono text-sm text-[#a0a0b0]">
                Status: <span className="text-[#f5f5f5]">{(agentData.status || '').toUpperCase()}</span> · Uptime: <span className="text-[#f5f5f5]">{agentData.uptime ?? 0}s</span>
              </span>
            </div>

            {/* Terminal */}
            <div className="bg-[#0a0a0f] border border-[#2a2a35] rounded-lg p-6 font-mono text-xs h-64 overflow-y-auto">
              <div className="space-y-1">
                {(agentData?.steps ?? []).map((log, idx) => (
                  <div
                    key={idx}
                    className={
                      log.includes('[SUCCESS]') || log.includes('✅')
                        ? 'text-[#22ff00]'
                        : log.includes('[ERROR]') || log.includes('❌') || log.includes('⚠️')
                          ? 'text-[#ff4444]'
                          : log.includes('[LISTENING]') || log.includes('[TRANSCRIBED]') || log.includes('🤖')
                            ? 'text-[#60a5fa]'
                            : log.includes('👤')
                              ? 'text-[#ffffff]'
                              : 'text-[#a0a0b0]'
                    }
                  >
                    {log}
                  </div>
                ))}
              </div>
            </div>

            {agentData.status === 'done' && (
              <div className="bg-[#1f2937] border border-[#374151] rounded-lg p-4 mb-4 text-[#f5f5f5]">
                <div className="flex items-center gap-3 mb-2 text-[#22ff00]">
                 <CheckCircle className="w-5 h-5" />
                 <h3 className="font-semibold text-lg">Session Complete — MCP & PDF Processing Done</h3>
                 {agentData.whatsapp_sent && (
                    <span className="ml-auto bg-[#059669] text-white text-xs font-bold px-2 py-1 rounded">WhatsApp Sent ✓</span>
                 )}
                </div>
                
                <button
                  onClick={() => window.open(`${API_BASE}/passive/pdf/${sessionId}`)}
                  className="bg-[#7c3aed] hover:bg-[#6d28d9] text-white text-sm font-medium py-2 px-4 rounded transition-colors flex items-center justify-center gap-2 mt-3"
                >
                  <Download className="w-4 h-4" />
                  Download PDF Report
                </button>
                
                {agentData.extracted && Object.keys(agentData.extracted).length > 0 && (
                  <div className="mt-4">
                    <p className="text-sm text-[#a0a0b0] mb-2 font-medium">Extracted Data:</p>
                    <pre className="bg-[#0a0a0f] p-3 rounded-lg overflow-auto border border-[#2a2a35] text-xs text-[#d1d5db]">
                      {JSON.stringify(agentData.extracted, null, 2)}
                    </pre>
                  </div>
                )}
              </div>
            )}

            {agentData.status === 'stopped' && (
              <div className="bg-[#2a2a35] border border-[#3a3a45] rounded-lg p-3 text-center mb-4">
                <span className="text-[#a0a0b0] font-medium">Session Ended</span>
              </div>
            )}

            {agentData.status === 'completed' || agentData.status === 'done' || agentData.status === 'stopped' || agentData.status === 'error' ? (
              <>
                <button
                  onClick={handleReset}
                  className="w-full bg-[#7c3aed] hover:bg-[#6d28d9] text-white font-medium py-2 rounded transition-colors"
                >
                  Start New Session
                </button>
                
                {/* Agent Feedback Card */}
                {(agentData.status === 'completed' || agentData.status === 'done' || agentData.status === 'stopped') && (
                  feedbackSubmitted ? (
                    <div className="bg-[#13131a] border border-[#7c3aed] rounded-lg p-6 text-center mt-6">
                      <p className="text-[#22ff00] font-medium flex items-center justify-center gap-2">
                        <CheckCircle className="w-5 h-5" /> Thank you for your feedback!
                      </p>
                    </div>
                  ) : (
                    <div className="bg-[#13131a] border border-[#7c3aed] rounded-lg p-6 mt-6">
                      <h3 className="text-white font-medium text-center mb-4">How was your OmniVoice experience?</h3>
                      <div className="flex justify-center gap-2 mb-2">
                        {[1, 2, 3, 4, 5].map((star) => (
                          <button key={star} onClick={() => setRating(star)} className="focus:outline-none">
                            <Star className={`w-8 h-8 ${rating && rating >= star ? 'text-yellow-400 fill-yellow-400' : 'text-gray-600'}`} />
                          </button>
                        ))}
                      </div>
                      <div className="text-center h-6 mb-4">
                        {rating && <span className="text-[#7c3aed] text-sm font-medium">{ ({1: 'Poor', 2: 'Fair', 3: 'Good', 4: 'Great', 5: 'Excellent'} as Record<number, string>)[rating] }</span>}
                      </div>
                      <textarea
                        value={feedbackText}
                        onChange={(e) => setFeedbackText(e.target.value)}
                        placeholder="Tell us more about your experience..."
                        className="w-full bg-[#0a0a0f] border border-[#2a2a35] rounded p-3 text-white text-sm mb-4 resize-none h-20 placeholder-gray-500 focus:border-[#7c3aed] focus:outline-none"
                      />
                      <button
                        onClick={() => submitFeedback('agent')}
                        disabled={!rating}
                        className={`w-full py-2 rounded text-white font-medium transition-colors ${rating ? 'bg-[#7c3aed] hover:bg-[#6d28d9]' : 'bg-gray-600 cursor-not-allowed'}`}
                      >
                        Submit Feedback
                      </button>
                    </div>
                  )
                )}
              </>
            ) : null}

            {agentData.status === 'active' || agentData.status === 'running' ? (
              <button
                onClick={handleStopSession}
                className="w-full bg-red-600 hover:bg-red-700 text-white font-medium py-2 rounded transition-colors flex items-center justify-center gap-2"
              >
                <Square className="w-4 h-4" />
                Stop Session
              </button>
            ) : null}
          </div>
        ) : null}
      </main>
    </div>
  );
}
