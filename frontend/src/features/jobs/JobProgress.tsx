import type { JobStage, JobStatus } from "../../api/types";

const stages: Array<{ id: JobStage; label: string; hint: string }> = [
  { id: "rendering", label: "Render", hint: "Turning pages into stable images" },
  { id: "preprocessing", label: "Prepare", hint: "Normalizing contrast and skew" },
  { id: "ocr", label: "Recognize", hint: "Reading words and confidence" },
  { id: "correction", label: "Correct", hint: "Proposing bounded, reversible edits" },
  { id: "exports", label: "Package", hint: "Building a portable document" },
];

const stageOrder: JobStage[] = [
  "queued",
  "rendering",
  "preprocessing",
  "ocr",
  "correction",
  "exports",
  "complete",
];

function stageState(stage: JobStage, current: JobStage): "done" | "active" | "pending" {
  if (current === "failed") return "pending";
  if (current === "complete") return "done";
  return stageOrder.indexOf(stage) < stageOrder.indexOf(current)
    ? "done"
    : stage === current
      ? "active"
      : "pending";
}

export function JobProgress({ job }: { job: JobStatus }) {
  const currentLabel =
    job.stage === "failed"
      ? "Processing stopped"
      : job.stage === "complete"
        ? "Document ready to inspect"
        : stages.find((stage) => stage.id === job.stage)?.hint ?? "Waiting for a worker";
  const pageStatus = job.current_page
    ? " · page " + job.current_page + " of " + job.total_pages
    : "";

  return (
    <section className="job-panel" aria-labelledby="job-heading">
      <div className="job-panel-header">
        <div>
          <p className="eyebrow">Live processing trace</p>
          <h2 id="job-heading">{job.source_name}</h2>
        </div>
        <span className={"job-stage-chip " + job.stage}>{job.stage}</span>
      </div>
      <p className="job-live-status" aria-live="polite">
        {currentLabel}
        {pageStatus}
      </p>
      <div
        className="job-progress-track"
        role="progressbar"
        aria-valuenow={Math.round(job.progress * 100)}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-label="Document processing progress"
      >
        <span style={{ width: Math.round(job.progress * 100) + "%" }} />
      </div>
      <ol className="job-stages">
        {stages.map((stage, index) => {
          const state = stageState(stage.id, job.stage);
          return (
            <li className={"job-stage " + state} key={stage.id}>
              <span className="job-stage-number">{String(index + 1).padStart(2, "0")}</span>
              <span>
                <strong>{stage.label}</strong>
                <small>{stage.hint}</small>
              </span>
              <span className="job-stage-check" aria-hidden="true">
                {state === "done" ? "✓" : state === "active" ? "•" : "—"}
              </span>
            </li>
          );
        })}
      </ol>
      {job.stage === "failed" && (
        <p className="job-error" role="alert">
          {job.error_detail ?? "The document could not be processed."}
        </p>
      )}
    </section>
  );
}
