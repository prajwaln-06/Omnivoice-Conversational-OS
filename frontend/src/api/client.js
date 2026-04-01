const MOCK_MODE = true;
const BASE_URL = "http://localhost:8000";

const delay = (ms) => new Promise((res) => setTimeout(res, ms));

export const uploadSchema = async (file) => {
  await delay(1000);
  return {
    domain: "healthcare",
    fields: [
      { name: "patient_name", type: "string", label: "Patient Name" },
      { name: "symptoms", type: "array", label: "Symptoms" },
      { name: "duration", type: "string", label: "Duration" },
      { name: "fever_temp", type: "string", label: "Fever Temp" },
      { name: "prescription", type: "string", label: "Prescription" },
      { name: "follow_up", type: "string", label: "Follow Up" }
    ],
    system_prompt: "Extract structured healthcare data"
  };
};

export const transcribe = async () => {
  await delay(1000);
  return {
    session_id: "mock-uuid-123",
    transcript: "I have fever since 2 days",
    language: "mixed"
  };
};

export const analyze = async () => {
  await delay(1000);
  return {
    session_id: "mock-uuid-123",
    extracted_data: {
      patient_name: "Ravi Kumar",
      symptoms: ["fever", "headache"],
      duration: "2 days",
      fever_temp: "101F",
      prescription: "",
      follow_up: ""
    }
  };
};

export const approve = async () => {
  await delay(1000);
  return {
    pdf_url: "https://mock-cdn.cloudfront.net/prescription.pdf",
    whatsapp_sent: true
  };
};

export const getSession = async () => {
  await delay(1000);
  return {
    session_id: "mock-uuid-123",
    status: "active",
    extracted_data: {}
  };
};