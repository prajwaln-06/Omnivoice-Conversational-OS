export default function SchemaCard({ title, fields, active, onClick }) {
  return (
    <button
      onClick={onClick}
      className={`w-full p-5 rounded-xl cursor-pointer transition text-left ${
        active
          ? "glow-cyan border border-cyan-400 bg-cyan-400/5"
          : "border border-cyan-400/20 bg-white/[0.01]"
      }`}
    >
      <h3 className="text-lg font-semibold text-white">{title}</h3>
      <p className="text-gray-400 text-sm mt-1">{fields}</p>
    </button>
  );
}