export default function UploadBox({ onClick }) {
  return (
    <button
      onClick={onClick}
      className="upload-box p-12 text-center rounded-xl text-gray-400 w-full"
      type="button"
    >
      <div className="text-3xl mb-3">⬆</div>
      Drop schema JSON here
      <p className="text-sm mt-2">or click to browse</p>
    </button>
  );
}