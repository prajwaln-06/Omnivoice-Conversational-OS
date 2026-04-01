import { useState } from "react";
import { uploadSchema } from "../api/client";

function SchemaDropper() {
  const [dragActive, setDragActive] = useState(false);
  const [fields, setFields] = useState([]);
  const [domain, setDomain] = useState("");
  const [loading, setLoading] = useState(false);

  const handleDrop = async (e) => {
    e.preventDefault();
    setDragActive(false);
    setLoading(true);

    const file = e.dataTransfer.files[0];

    const schema = await uploadSchema(file);

    setDomain(schema.domain);
    setFields(schema.fields);
    setLoading(false);
  };

  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-[#020617] text-white">
      <h1 className="text-3xl mb-6 text-cyan-400">
        OmniVoice Schema Loader
      </h1>

      <div
        onDragOver={(e) => {
          e.preventDefault();
          setDragActive(true);
        }}
        onDragLeave={() => setDragActive(false)}
        onDrop={handleDrop}
        className={`w-[400px] h-[200px] flex items-center justify-center border-2 border-dashed rounded-xl cursor-pointer
        ${dragActive ? "border-cyan-400 shadow-lg" : "border-gray-600"}`}
      >
        Drag & Drop Schema
      </div>

      {loading && <p className="mt-4 text-amber-400">Processing...</p>}

      {domain && <p className="mt-4 text-green-400">Domain: {domain}</p>}

      <div className="mt-4">
        {fields.map((f, i) => (
          <div key={i} className="p-2 border border-cyan-400/20 rounded mb-2">
            {f.label}
          </div>
        ))}
      </div>
    </div>
  );
}

export default SchemaDropper;