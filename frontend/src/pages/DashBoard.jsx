import { useNavigate } from "react-router-dom";
import { useRef, useState } from "react";
import Navbar from "../components/NavBar";
import Card from "../components/Card";
import SchemaCard from "../components/SchemaCard";
import UploadBox from "../components/UploadBox";
import GlowButton from "../components/GlowButton";

const healthcareFields = [
  ["patient_name", "string"],
  ["age", "string"],
  ["symptoms", "array"],
  ["duration", "string"],
  ["fever_temp", "string"],
  ["prescription", "string"],
  ["follow_up", "string"],
];

export default function Dashboard() {
  const nav = useNavigate();
  const fileInputRef = useRef(null);

  const [schemaSource, setSchemaSource] = useState("preset");
  const [uploadedSchema, setUploadedSchema] = useState(null);

  const presetTitle = "Healthcare Assistant";
  const presetDomain = "healthcare";
  const presetDescription = "Schema for doctor-patient consultation extraction";
  const presetFields = healthcareFields;

  const previewTitle = uploadedSchema?.display_name || presetTitle;
  const previewDomain = uploadedSchema?.domain || presetDomain;
  const previewDescription = uploadedSchema
    ? "Custom schema uploaded successfully"
    : presetDescription;

  const previewFields = uploadedSchema?.fields
    ? uploadedSchema.fields.map((f) => [f.name, f.type])
    : presetFields;

  const handleUploadClick = () => {
    fileInputRef.current?.click();
  };

  const handleSchemaFile = async (event) => {
    const file = event.target.files?.[0];
    if (!file) return;

    try {
      const text = await file.text();
      const parsed = JSON.parse(text);
      setUploadedSchema(parsed);
      setSchemaSource("upload");
    } catch (error) {
      alert("Invalid schema JSON file");
    }
  };

  const handleContinue = () => {
    nav("/mode", {
      state: {
        schemaSource,
        schema:
          uploadedSchema || {
            domain: presetDomain,
            display_name: presetTitle,
            fields: previewFields.map(([name, type]) => ({ name, type })),
          },
      },
    });
  };

  return (
    <div className="min-h-screen bg-[#020617] text-white">
      <Navbar title="OmniVoice" />

      <div className="p-10">
        <div className="text-[42px] font-bold leading-tight">Command Center</div>
        <div className="mt-2 text-gray-400 text-lg">
          Configure your conversational pipeline
        </div>

        <div className="mt-6 flex items-center gap-4 flex-wrap">
          <div className="h-[34px] px-4 rounded-full border border-cyan-400/40 flex items-center text-cyan-400 text-sm font-mono">
            01
          </div>
          <div className="text-white text-sm">Choose or upload schema</div>
          <div className="text-slate-600 text-xl">›</div>
          <div className="text-gray-400 text-sm">Select listening mode</div>
          <div className="text-slate-600 text-xl">›</div>
          <div className="text-gray-400 text-sm">Review generated document</div>
        </div>

        <div className="mt-8 grid grid-cols-1 lg:grid-cols-2 gap-7">
          <Card>
            <div className="flex items-center gap-4">
              <div className="w-[58px] h-[58px] rounded-2xl bg-cyan-400/10 border border-cyan-400/20 flex items-center justify-center text-cyan-400 text-2xl">
                ◫
              </div>
              <div>
                <div className="text-2xl font-bold">Existing Schema</div>
                <div className="text-gray-400 mt-1 text-sm">
                  Select from pre-built domain schemas
                </div>
              </div>
            </div>

            <div className="mt-6">
              <SchemaCard
                title="Healthcare Consultation"
                fields="7 fields"
                active={schemaSource === "preset"}
                onClick={() => {
                  setSchemaSource("preset");
                  setUploadedSchema(null);
                }}
              />
            </div>
          </Card>

          <Card>
            <div className="flex items-center gap-4">
              <div className="w-[58px] h-[58px] rounded-2xl bg-pink-400/10 border border-pink-400/20 flex items-center justify-center text-pink-400 text-2xl">
                ↑
              </div>
              <div>
                <div className="text-2xl font-bold">Other Schema</div>
                <div className="text-gray-400 mt-1 text-sm">
                  Upload a custom schema JSON file
                </div>
              </div>
            </div>

            <div className="mt-6">
              <UploadBox onClick={handleUploadClick} />
              <input
                ref={fileInputRef}
                type="file"
                accept=".json,application/json"
                style={{ display: "none" }}
                onChange={handleSchemaFile}
              />
            </div>
          </Card>
        </div>

        <Card className="mt-7">
          <div className="flex justify-between items-start gap-4">
            <div>
              <div className="text-2xl font-bold">{previewTitle}</div>
              <div className="mt-1 text-gray-400 text-sm font-mono">
                {previewDomain}
              </div>
            </div>

            <div className="h-8 px-4 rounded-full border border-cyan-400/40 flex items-center text-sm text-cyan-400 font-mono">
              {previewFields.length} fields
            </div>
          </div>

          <div className="mt-4 text-gray-400 text-base">{previewDescription}</div>

          <div className="flex flex-wrap gap-2 mt-5">
            {previewFields.map(([name, type]) => (
              <div
                key={name}
                className="px-3 py-2 rounded-full border border-cyan-400/35 bg-cyan-400/5 text-cyan-400 text-sm font-mono"
              >
                {name}:{type}
              </div>
            ))}
          </div>
        </Card>

        <div className="mt-7 flex justify-end">
          <GlowButton onClick={handleContinue}>
            Continue to Mode Selection →
          </GlowButton>
        </div>
      </div>
    </div>
  );
}