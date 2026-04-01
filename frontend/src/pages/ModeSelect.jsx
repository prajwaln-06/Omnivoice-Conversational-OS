import { useNavigate } from "react-router-dom";
import { useState } from "react";

export default function ModeSelect() {
  const nav = useNavigate();
  const [selectedMode, setSelectedMode] = useState("");

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
            onClick={() => nav("/dashboard")}
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
            }}
          >
            OmniVoice
          </div>
        </div>

        <div
          style={{
            fontSize: 13,
            color: "#7f8ea8",
            fontFamily: "JetBrains Mono, monospace",
          }}
        >
          Console v1.0
        </div>
      </div>

      <div
        style={{
          padding: "72px 48px 48px",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
        }}
      >
        <div
          style={{
            fontSize: 46,
            fontWeight: 700,
            textAlign: "center",
          }}
        >
          Select Listening Mode
        </div>

        <div
          style={{
            marginTop: 14,
            color: "#7f8ea8",
            fontSize: 18,
            textAlign: "center",
          }}
        >
          Choose how OmniVoice should capture the conversation
        </div>

        <div
          style={{
            marginTop: 44,
            width: "100%",
            maxWidth: 1180,
            display: "grid",
            gridTemplateColumns: "1fr 1fr",
            gap: 30,
          }}
        >
          <button
            onClick={() => setSelectedMode("active")}
            style={{
              minHeight: 360,
              borderRadius: 24,
              padding: "42px 30px",
              background: "rgba(15,23,42,0.88)",
              border:
                selectedMode === "active"
                  ? "1px solid rgba(34,211,238,0.60)"
                  : "1px solid rgba(34,211,238,0.18)",
              color: "#e6edf7",
              cursor: "pointer",
              textAlign: "center",
            }}
          >
            <div style={{ fontSize: 44 }}>🎤</div>
            <div style={{ marginTop: 28, fontSize: 28, fontWeight: 700 }}>
              Active Listening
            </div>
          </button>

          <button
            onClick={() => setSelectedMode("passive")}
            style={{
              minHeight: 360,
              borderRadius: 24,
              padding: "42px 30px",
              background: "rgba(15,23,42,0.88)",
              border:
                selectedMode === "passive"
                  ? "1px solid rgba(244,114,182,0.60)"
                  : "1px solid rgba(244,114,182,0.18)",
              color: "#e6edf7",
              cursor: "pointer",
              textAlign: "center",
            }}
          >
            <div style={{ fontSize: 44 }}>🎧</div>
            <div style={{ marginTop: 28, fontSize: 28, fontWeight: 700 }}>
              Passive Listening
            </div>
          </button>
        </div>

        <button
          onClick={() => {
            if (selectedMode === "active") nav("/active");
            if (selectedMode === "passive") nav("/passive");
          }}
          disabled={!selectedMode}
          style={{
            marginTop: 38,
            padding: "15px 28px",
            borderRadius: 12,
            border: "none",
            background: "#22d3ee",
            color: "#03111d",
            fontWeight: 700,
            fontSize: 15,
            cursor: selectedMode ? "pointer" : "not-allowed",
            opacity: selectedMode ? 1 : 0.45,
          }}
        >
          Continue →
        </button>
      </div>
    </div>
  );
}