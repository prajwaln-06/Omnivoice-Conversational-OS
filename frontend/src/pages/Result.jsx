import { useLocation, useNavigate } from "react-router-dom";
import { useMemo, useState } from "react";
import { approve } from "../api/client";

export default function Result() {
  const nav = useNavigate();
  const location = useLocation();

  const initialSessionId = location.state?.session_id || "";
  const initialTranscript = location.state?.transcript || "";
  const initialExtracted = location.state?.extracted_data || {};
  const initialDomain = location.state?.domain || "healthcare";
  const initialMode = location.state?.mode || "conversational";

  const [sessionId] = useState(initialSessionId);
  const [transcript] = useState(initialTranscript);
  const [domain] = useState(initialDomain);
  const [mode] = useState(initialMode);
  const [extractedData, setExtractedData] = useState(initialExtracted);
  const [approving, setApproving] = useState(false);
  const [pdfUrl, setPdfUrl] = useState("");
  const [error, setError] = useState("");

  const fields = useMemo(() => Object.entries(extractedData || {}), [extractedData]);

  const handleFieldChange = (key, value) => {
    setExtractedData((prev) => ({ ...prev, [key]: value }));
  };

  const handleApprove = async () => {
    try {
      setApproving(true);
      setError("");

      const data = await approve({
        session_id: sessionId,
        extracted_data: extractedData,
      });
      setPdfUrl(data.pdf_url || "");
      setApproving(false);
    } catch (err) {
      setApproving(false);
      setError(err.message || "Failed to approve and generate PDF");
    }
  };

  return (
    <div
      style={{
        minHeight: "100vh",
        background:
          "radial-gradient(circle at 50% 10%, rgba(34,211,238,0.08), transparent 28%), #020617",
        color: "#e6edf7",
        fontFamily: "Plus Jakarta Sans, sans-serif",
      }}
    >
      <div
        style={{
          height: 84,
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          padding: "0 40px",
          borderBottom: "1px solid rgba(34,211,238,0.10)",
          background: "rgba(2,6,23,0.72)",
          backdropFilter: "blur(12px)",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 14 }}>
          <button
            onClick={() => nav(-1)}
            style={{
              width: 42,
              height: 42,
              borderRadius: 12,
              border: "1px solid rgba(148,163,184,0.18)",
              background: "rgba(255,255,255,0.02)",
              color: "#94a3b8",
              cursor: "pointer",
            }}
          >
            ←
          </button>

          <div
            style={{
              fontSize: 28,
              fontWeight: 700,
              background: "linear-gradient(to right, #22d3ee, #10b981)",
              WebkitBackgroundClip: "text",
              WebkitTextFillColor: "transparent",
            }}
          >
            Analysis Results
          </div>
        </div>

        <div
          style={{
            fontSize: 13,
            color: approving ? "#22d3ee" : pdfUrl ? "#10b981" : "#7f8ea8",
            fontFamily: "JetBrains Mono, monospace",
          }}
        >
          {approving ? "APPROVING" : pdfUrl ? "READY" : "PENDING_APPROVAL"}
        </div>
      </div>

      <div
        style={{
          padding: "36px 40px",
          display: "grid",
          gridTemplateColumns: "1.4fr 1fr",
          gap: 28,
        }}
      >
        <div
          style={{
            background: "rgba(15,23,42,0.88)",
            border: "1px solid rgba(34,211,238,0.18)",
            borderRadius: 24,
            padding: 28,
          }}
        >
          <div style={{ fontSize: 20, marginBottom: 20 }}>Transcript</div>

          <div
            style={{
              minHeight: 500,
              borderRadius: 16,
              background: "rgba(2,6,23,0.6)",
              padding: 20,
              color: transcript ? "#dce9f8" : "#7f8ea8",
              lineHeight: 1.7,
              whiteSpace: "pre-wrap",
            }}
          >
            {transcript || "No transcript available"}
          </div>
        </div>

        <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
          <div
            style={{
              background: "rgba(15,23,42,0.88)",
              border: "1px solid rgba(34,211,238,0.18)",
              borderRadius: 20,
              padding: 20,
            }}
          >
            <div style={{ fontWeight: 600, marginBottom: 10 }}>Session Details</div>
            <div style={{ fontSize: 14, color: "#7f8ea8" }}>Domain: {domain}</div>
            <div style={{ fontSize: 14, color: "#7f8ea8" }}>Mode: {mode}</div>
            <div style={{ fontSize: 14, color: "#7f8ea8" }}>Session ID: {sessionId || "N/A"}</div>
          </div>

          <div
            style={{
              background: "rgba(15,23,42,0.88)",
              border: "1px solid rgba(34,211,238,0.18)",
              borderRadius: 20,
              padding: 20,
            }}
          >
            <div style={{ fontWeight: 600, marginBottom: 14 }}>Extracted Data</div>

            {fields.length === 0 ? (
              <div style={{ color: "#7f8ea8" }}>No extracted data available</div>
            ) : (
              fields.map(([key, value]) => (
                <div key={key} style={{ marginBottom: 12 }}>
                  <div
                    style={{
                      fontSize: 12,
                      color: "#22d3ee",
                      fontFamily: "JetBrains Mono, monospace",
                      marginBottom: 4,
                    }}
                  >
                    {key}
                  </div>
                  <input
                    value={Array.isArray(value) ? value.join(", ") : value ?? ""}
                    onChange={(e) => handleFieldChange(key, e.target.value)}
                    style={{
                      width: "100%",
                      padding: "10px 12px",
                      borderRadius: 10,
                      border: "1px solid rgba(34,211,238,0.18)",
                      background: "rgba(2,6,23,0.35)",
                      color: "#e6edf7",
                      outline: "none",
                    }}
                  />
                </div>
              ))
            )}
          </div>

          <div
            style={{
              background: "rgba(15,23,42,0.88)",
              border: "1px solid rgba(34,211,238,0.18)",
              borderRadius: 20,
              padding: 20,
            }}
          >
            <div style={{ fontWeight: 600, marginBottom: 12 }}>Actions</div>

            <button
              onClick={handleApprove}
              disabled={approving || !sessionId}
              style={{
                width: "100%",
                padding: "12px",
                marginBottom: 10,
                borderRadius: 10,
                background: "#22d3ee",
                border: "none",
                color: "#03111d",
                fontWeight: 700,
                cursor: approving || !sessionId ? "not-allowed" : "pointer",
                opacity: approving || !sessionId ? 0.6 : 1,
              }}
            >
              {approving ? "Generating PDF..." : "Approve & Generate PDF"}
            </button>

            {pdfUrl ? (
              <a
                href={pdfUrl}
                target="_blank"
                rel="noreferrer"
                style={{
                  display: "block",
                  width: "100%",
                  padding: "12px",
                  borderRadius: 10,
                  background: "#10b981",
                  color: "#03111d",
                  fontWeight: 700,
                  textAlign: "center",
                }}
              >
                Open PDF
              </a>
            ) : null}

            {error ? <div style={{ marginTop: 10, color: "#f87171" }}>{error}</div> : null}
          </div>
        </div>
      </div>
    </div>
  );
}