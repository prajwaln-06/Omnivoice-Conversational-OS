const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";
const MOCK_MODE = String(import.meta.env.VITE_MOCK_MODE || "false").toLowerCase() === "true";

function normalizeMode(mode) {
  if (!mode) return "conversational";
  const lowered = String(mode).toLowerCase();
  if (lowered === "active") return "conversational";
  if (lowered === "passive") return "silent";
  return lowered;
}

async function parseResponse(res) {
  const payload = await res.json().catch(() => ({}));
  if (!res.ok) {
    const message = payload?.detail || payload?.message || `Request failed (${res.status})`;
    throw new Error(message);
  }
  return payload;
}

async function request(path, options = {}) {
  const res = await fetch(`${API_BASE}${path}`, options);
  return parseResponse(res);
}

export async function uploadSchema(schemaInput) {
  if (MOCK_MODE) {
    return { domain: typeof schemaInput === "string" ? schemaInput : schemaInput?.domain || "custom", fields: [] };
  }

  if (schemaInput instanceof File) {
    const formData = new FormData();
    formData.append("file", schemaInput);
    return request("/api/upload-schema", { method: "POST", body: formData });
  }

  if (typeof schemaInput === "string") {
    const schemaPayload = {
      domain: schemaInput,
      schema: {
        domain: schemaInput,
        fields: [],
      },
    };
    return request("/api/upload-schema", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(schemaPayload),
    });
  }

  const domain = schemaInput?.domain || "custom";
  return request("/api/upload-schema", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      domain,
      schema: schemaInput,
    }),
  });
}

export async function transcribe({ mode, audioFile, domain }) {
  if (MOCK_MODE) {
    return {
      session_id: crypto.randomUUID(),
      transcript: "Mock transcript",
      language: "en-IN",
      audio_s3_url: "s3://mock/audio.wav",
      analysis: {},
      sentiment: { label: "neutral", score: 0.5 },
      domain,
      mode: normalizeMode(mode),
    };
  }

  const formData = new FormData();
  const fileToSend = audioFile || new File([new Blob(["demo-audio"])], "demo.wav", { type: "audio/wav" });
  formData.append("audio", fileToSend);
  formData.append("domain", domain || "healthcare");
  formData.append("mode", normalizeMode(mode));

  return request("/api/transcribe", {
    method: "POST",
    body: formData,
  });
}

export async function analyze({ session_id, domain }) {
  if (MOCK_MODE) {
    return { session_id, extracted_data: { status: "pending_approval" } };
  }

  return request("/api/analyze", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id, domain }),
  });
}

export async function approve({ session_id, extracted_data }) {
  if (MOCK_MODE) {
    return { pdf_url: "/mock-report.pdf", whatsapp_sent: true };
  }

  return request("/api/approve", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id, extracted_data }),
  });
}

export async function getSession(sessionId) {
  return request(`/api/session/${sessionId}`, {
    method: "GET",
  });
}

export { API_BASE };