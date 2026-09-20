const formats = [
  ["markdown", "Markdown"],
  ["html", "HTML"],
  ["json", "Canonical JSON"],
  ["docx", "DOCX"],
] as const;

export function ExportMenu({ jobId }: { jobId: string }) {
  return (
    <div className="export-menu" aria-label="Document exports">
      <span>EXPORT</span>
      {formats.map(([format, label]) => (
        <a
          key={format}
          href={"/api/v1/jobs/" + jobId + "/exports/" + format}
          download
        >
          {label}
        </a>
      ))}
    </div>
  );
}
