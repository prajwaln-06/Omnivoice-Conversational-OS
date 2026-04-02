import { useRef, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { analyze, transcribe } from "../api/client";

export default function Passive() {
  const nav = useNavigate();
  const location = useLocation();
  const fileInputRef = useRef(null);

  const domain = location.state?.domain || location.state?.schema?.domain || "healthcare";
  const mode = location.state?.mode || "silent";
  const schema = location.state?.schema || null;

  const [uploadedFile, setUploadedFile] = useState(null);
  const [status, setStatus] = useState("idle");
  const [error, setError] = useState("");

  const handlePick = () => fileInputRef.current?.click();

  const handleFile = async (event) => {
    const file = event.target.files?.[0];
    if (!file) return;

    setUploadedFile(file);
    setError("");
    setStatus("processing");

    try {
      const transcribeData = await transcribe({ mode, domain, audioFile: file });
      const analyzeData = await analyze({ session_id: transcribeData.session_id, domain });

      nav("/result", {
        state: {
          session_id: analyzeData.session_id,
          extracted_data: analyzeData.extracted_data,
          transcript: transcribeData.transcript,
          domain,
          mode,
          schema,
          audio_s3_url: transcribeData.audio_s3_url,
        },
      });
    } catch (err) {
      setStatus("idle");
      setError(err.message || "Failed to upload and analyze audio");
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
            onClick={() => nav("/mode")}
            style={{
              width: 42,
              height: 42,
              borderRadius: 12,
              border: "1px solid rgba(148,163,184,0.18)",
              background: "rgba(255,255,255,0.02)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              color: "#94a3b8",
              fontSize: 20,
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
              lineHeight: 1,
            }}
          >
            Passive Listening
          </div>
        </div>

        <div
          style={{
            fontSize: 13,
            color: status === "processing" ? "#22d3ee" : "#7f8ea8",
            fontFamily: "JetBrains Mono, monospace",
          }}
        >
          {status === "processing" ? "Processing..." : "Pending Approval"}
        </div>
      </div>

      <div
        style={{
          padding: "36px 40px 40px",
          display: "grid",
          gridTemplateColumns: "1fr 1fr",
          gap: 28,
        }}
      >
        <div
          style={{
            background: "rgba(15,23,42,0.88)",
            border: "1px solid rgba(34,211,238,0.18)",
            borderRadius: 24,
            padding: "34px 28px",
            backdropFilter: "blur(16px)",
            minHeight: 420,
            display: "flex",
            flexDirection: "column",
          }}
        >
          <div style={{ fontSize: 30, fontWeight: 700, textAlign: "center" }}>
            Upload Conversation Audio
          </div>

          <div
            style={{
              marginTop: 12,
              color: "#7f8ea8",
              fontSize: 16,
              lineHeight: 1.7,
              textAlign: "center",
            }}
          >
            Upload a pre-recorded call or consultation for silent transcription and analysis
          </div>

          <button
            onClick={handlePick}
            style={{
              marginTop: 28,
              flex: 1,
              minHeight: 270,
              borderRadius: 24,
              border: "2px dashed rgba(34,211,238,0.28)",
              background:
                "linear-gradient(180deg, rgba(255,255,255,0.02), rgba(255,255,255,0.01))",
              color: "#dce9f8",
              cursor: "pointer",
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              justifyContent: "center",
            }}
          >
            <div
              style={{
                width: 98,
                height: 98,
                borderRadius: 999,
                background: "rgba(34,211,238,0.08)",
                border: "1px solid rgba(34,211,238,0.20)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                boxShadow: "0 0 28px rgba(34,211,238,0.14)",
                fontSize: 42,
                color: "#22d3ee",
              }}
            >
              ⤴
            </div>

            <div style={{ marginTop: 22, fontSize: 24, fontWeight: 700 }}>
              Drop audio file here
            </div>

            <div style={{ marginTop: 10, color: "#7f8ea8", fontSize: 15 }}>
              WAV, MP3, M4A, OGG, FLAC supported
            </div>
          </button>

          <input
            ref={fileInputRef}
            type="file"
            accept=".wav,.mp3,.m4a,.webm,.ogg,.flac,audio/*"
            style={{ display: "none" }}
            onChange={handleFile}
          />
        </div>

        <div
          style={{
            background: "rgba(15,23,42,0.88)",
            border: "1px solid rgba(34,211,238,0.18)",
            borderRadius: 24,
            padding: "34px 28px",
            minHeight: 420,
            display: "flex",
            flexDirection: "column",
            justifyContent: "center",
            alignItems: "center",
          }}
        >
          {!uploadedFile && !error && (
            <div
              style={{
                color: "#7f8ea8",
                fontSize: 16,
                textAlign: "center",
                maxWidth: 320,
                lineHeight: 1.7,
              }}
            >
              Upload an audio file to begin passive analysis
            </div>
          )}

          {uploadedFile && !error && (
            <>
              <div style={{ width: "100%", fontSize: 28, fontWeight: 700, textAlign: "center" }}>
                {status === "processing" ? "Analyzing Audio..." : "Audio Ready"}
              </div>

              <div
                style={{
                  marginTop: 12,
                  width: "100%",
                  color: "#7f8ea8",
                  fontSize: 16,
                  textAlign: "center",
                  lineHeight: 1.7,
                }}
              >
                {status === "processing"
                  ? "Your upload is being transcribed and analyzed by the backend"
                  : "Your file has been uploaded and is ready for review"}
              </div>

              <div
                style={{
                  marginTop: 24,
                  width: "100%",
                  padding: "18px 18px",
                  borderRadius: 18,
                  border: "1px solid rgba(34,211,238,0.18)",
                  background: "rgba(2,6,23,0.35)",
                  display: "flex",
                  alignItems: "center",
                  gap: 14,
                }}
              >
                <div
                  style={{
                    width: 52,
                    height: 52,
                    borderRadius: 14,
                    background: "rgba(34,211,238,0.08)",
                    border: "1px solid rgba(34,211,238,0.20)",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    color: "#22d3ee",
                    fontSize: 24,
                    flexShrink: 0,
                  }}
                >
                  ♪
                </div>

                <div>
                  <div style={{ fontSize: 16, fontWeight: 600 }}>
                    {uploadedFile.name}
                  </div>
                  <div
                    style={{
                      marginTop: 4,
                      fontSize: 13,
                      color: "#7f8ea8",
                      fontFamily: "JetBrains Mono, monospace",
                    }}
                  >
                    {(uploadedFile.size / (1024 * 1024)).toFixed(1)} MB
                  </div>
                </div>
              </div>
            </>
          )}

          {error && <div style={{ color: "#f87171" }}>{error}</div>}
        </div>
      </div>
    </div>
  );
}