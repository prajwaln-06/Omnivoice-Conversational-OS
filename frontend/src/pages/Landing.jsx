import { useNavigate } from "react-router-dom";

export default function Landing() {
  const nav = useNavigate();

  return (
    <div
      style={{
        minHeight: "100vh",
        background:
          "radial-gradient(circle at 50% 10%, rgba(34,211,238,0.08), transparent 28%), #020617",
        display: "flex",
        flexDirection: "column",
        justifyContent: "center",
        alignItems: "center",
        textAlign: "center",
        color: "#e6edf7",
        fontFamily: "Plus Jakarta Sans, sans-serif",
        padding: 24,
      }}
    >
      <div
        style={{
          width: 70,
          height: 70,
          borderRadius: 16,
          border: "1px solid rgba(34,211,238,0.4)",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          boxShadow: "0 0 25px rgba(34,211,238,0.4)",
        }}
      >
        ✦
      </div>

      <h1
        style={{
          marginTop: 30,
          fontSize: 48,
          fontWeight: 700,
          background: "linear-gradient(to right, #22d3ee, #10b981)",
          WebkitBackgroundClip: "text",
          WebkitTextFillColor: "transparent",
        }}
      >
        OmniVoice Engine
      </h1>

      <p style={{ marginTop: 12, color: "#7f8ea8" }}>
        Domain-Agnostic Conversational OS for Bharat
      </p>

      <button
        onClick={() => nav("/dashboard")}
        style={{
          marginTop: 30,
          padding: "14px 36px",
          borderRadius: 10,
          border: "none",
          background: "#22d3ee",
          color: "#03111d",
          fontWeight: 700,
          cursor: "pointer",
          boxShadow: "0 0 25px rgba(34,211,238,0.35)",
        }}
      >
        Launch OmniVoice
      </button>
    </div>
  );
}