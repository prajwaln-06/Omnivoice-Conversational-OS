export default function GlowButton({ children, onClick, disabled = false, className = "" }) {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className={`px-6 py-3 rounded-xl font-semibold transition ${
        disabled
          ? "bg-cyan-400/40 text-black/60 cursor-not-allowed"
          : "bg-cyan-400 text-black shadow-[0_0_20px_#22d3ee] hover:scale-105"
      } ${className}`}
    >
      {children}
    </button>
  );
}