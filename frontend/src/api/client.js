const MOCK_MODE = true;

const delay = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

const generateSessionId = () => 
  'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, c => {
    const r = Math.random() * 16 | 0;
    return (c === 'x' ? r : (r & 0x3 | 0x8)).toString(16);
  });

const mockHealthcareSession = {
  session_id: generateSessionId(),
  domain: "healthcare",
  mode: "conversational",
  transcript: "Doctor: Good morning, what brings you in today?\nPatient: I've been having a persistent cough for about two weeks now, along with a mild fever.\nDoctor: I see. How high has your fever been?\nPatient: Around 100.4°F, it comes and goes.\nDoctor: Any other symptoms? Chest pain, shortness of breath?\nPatient: Some chest tightness when I cough, but no shortness of breath.\nDoctor: Let me prescribe some antibiotics and a cough suppressant. I'd also like to schedule a follow-up in one week.",
  extracted_data: {
    patient_name: "Rajesh Kumar",
    age: "34",
    symptoms: ["persistent cough", "mild fever", "chest tightness"],
    duration: "2 weeks",
    fever_temp: "100.4°F",
    prescription: "Amoxicillin 500mg, Dextromethorphan syrup",
    follow_up: "1 week"
  },
  status: "pending_approval",
  audio_s3_url: "s3://omnivoice-audio/sessions/mock-healthcare.wav",
  pdf_url: "/mock-report.pdf",
  whatsapp_sent: false,
  created_at: new Date().toISOString()
};

const mockBankingSession = {
  session_id: generateSessionId(),
  domain: "banking",
  mode: "conversational",
  transcript: "Agent: Welcome to SecureBank, how may I assist you?\nCustomer: I'd like to inquire about a home loan.\nAgent: Sure! What's the property value you're looking at?\nCustomer: Around 75 lakhs in Pune.\nAgent: Great. Your current income and employment?\nCustomer: I'm a software engineer, annual income 18 lakhs.\nAgent: We can offer up to 80% financing at 8.5% interest. Shall I start the application?",
  extracted_data: {
    customer_name: "Priya Sharma",
    inquiry_type: "Home Loan",
    property_value: "₹75,00,000",
    location: "Pune",
    employment: "Software Engineer",
    annual_income: "₹18,00,000",
    offered_rate: "8.5% p.a.",
    follow_up: "Application initiated"
  },
  status: "pending_approval",
  audio_s3_url: "s3://omnivoice-audio/sessions/mock-banking.wav",
  pdf_url: "/mock-report.pdf",
  whatsapp_sent: false,
  created_at: new Date().toISOString()
};

export async function uploadSchema(fileOrPreset: string | File) {
  if (MOCK_MODE) {
    await delay(1500);
    if (typeof fileOrPreset === 'string') {
      return { success: true, domain: fileOrPreset, message: `Schema '${fileOrPreset}' loaded successfully` };
    }
    return { success: true, domain: "custom", message: "Custom schema uploaded successfully" };
  }
  // Real API call placeholder
  throw new Error("Real API not implemented");
}

export async function transcribe(payload: { mode: string; audioFile?: File; domain: string }) {
  if (MOCK_MODE) {
    await delay(3000);
    const session = payload.domain === 'banking' ? mockBankingSession : mockHealthcareSession;
    return { ...session, mode: payload.mode === 'active' ? 'conversational' : 'silent' };
  }
  throw new Error("Real API not implemented");
}

export async function analyze(payload: { session_id: string }) {
  if (MOCK_MODE) {
    await delay(2000);
    return { success: true, session_id: payload.session_id, status: "pending_approval" };
  }
  throw new Error("Real API not implemented");
}

export async function approve(payload: { session_id: string }) {
  if (MOCK_MODE) {
    await delay(1000);
    return { success: true, session_id: payload.session_id, status: "approved" };
  }
  throw new Error("Real API not implemented");
}

export async function getSession(sessionId: string) {
  if (MOCK_MODE) {
    await delay(500);
    return mockHealthcareSession;
  }
  throw new Error("Real API not implemented");
}

export function getMockSession(domain: string, mode: string) {
  const base = domain === 'banking' ? { ...mockBankingSession } : { ...mockHealthcareSession };
  base.session_id = generateSessionId();
  base.mode = mode === 'active' ? 'conversational' : 'silent';
  base.created_at = new Date().toISOString();
  return base;
}