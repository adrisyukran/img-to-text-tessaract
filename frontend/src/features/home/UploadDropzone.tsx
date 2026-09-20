import { useRef, useState } from "react";

type UploadDropzoneProps = {
  onSubmit: (file: File) => void;
  busy?: boolean;
};

export function UploadDropzone({ onSubmit, busy = false }: UploadDropzoneProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragging, setDragging] = useState(false);

  function accept(file: File | undefined) {
    if (!file || busy) return;
    onSubmit(file);
  }

  return (
    <section
      className={"upload-dropzone" + (dragging ? " dragging" : "")}
      onDragEnter={(event) => {
        event.preventDefault();
        setDragging(true);
      }}
      onDragOver={(event) => event.preventDefault()}
      onDragLeave={() => setDragging(false)}
      onDrop={(event) => {
        event.preventDefault();
        setDragging(false);
        accept(event.dataTransfer.files[0]);
      }}
    >
      <input
        ref={inputRef}
        id="upload-input"
        className="visually-hidden"
        type="file"
        accept=".pdf,image/png,image/jpeg"
        onChange={(event) => accept(event.target.files?.[0])}
      />
      <span className="upload-icon" aria-hidden="true">
        ↑
      </span>
      <div>
        <strong>{busy ? "Uploading document…" : "Bring your own scanned PDF"}</strong>
        <p>Drop a PDF, PNG, or JPEG here, or choose a file from your device.</p>
      </div>
      <button
        className="button button-quiet"
        type="button"
        onClick={() => inputRef.current?.click()}
        disabled={busy}
      >
        Choose file
      </button>
    </section>
  );
}
