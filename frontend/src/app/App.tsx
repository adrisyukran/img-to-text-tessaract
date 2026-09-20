import { useEffect, useState } from "react";
import { useQuery } from "@tanstack/react-query";

import { ApiProblem, api } from "../api/client";
import type { CanonicalDocument, JobStatus, PublicSample } from "../api/types";
import { RawResult } from "../features/document/RawResult";
import { SampleGallery } from "../features/home/SampleGallery";
import { UploadDropzone } from "../features/home/UploadDropzone";
import { JobProgress } from "../features/jobs/JobProgress";
import { ByokForm } from "../features/jobs/ByokForm";
import { useJob } from "../features/jobs/useJob";
import { EvaluationDashboard } from "../features/evaluation/EvaluationDashboard";
import { IntelligenceReport } from "../features/report/IntelligenceReport";

type Readiness = {
  status: string;
  environment: string;
};

function jobIdFromLocation(): string | null {
  if (typeof window === "undefined") return null;
  const match = window.location.pathname.match(/^\/jobs\/([A-Za-z0-9_-]{1,80})$/);
  return match?.[1] ?? null;
}

export function App() {
  const readiness = useQuery({
    queryKey: ["health", "ready"],
    queryFn: () => api.get<Readiness>("/health/ready"),
    retry: false,
  });
  const samples = useQuery({
    queryKey: ["samples"],
    queryFn: () => api.get<PublicSample[]>("/samples"),
    retry: false,
  });
  const [activeJobId, setActiveJobId] = useState<string | null>(jobIdFromLocation);
  const [busyId, setBusyId] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);
  const [busyPatchId, setBusyPatchId] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const job = useJob(activeJobId);
  const documentQuery = useQuery({
    queryKey: ["document", activeJobId],
    queryFn: () => api.get<CanonicalDocument>("/jobs/" + activeJobId + "/document"),
    enabled: job.data?.stage === "complete" && Boolean(activeJobId),
    retry: false,
  });
  const sampleList = Array.isArray(samples.data) ? samples.data : [];

  useEffect(() => {
    const handlePopState = () => setActiveJobId(jobIdFromLocation());
    window.addEventListener("popstate", handlePopState);
    return () => window.removeEventListener("popstate", handlePopState);
  }, []);

  function showWorkspace() {
    window.setTimeout(() => {
      window.document.getElementById("workspace")?.scrollIntoView({ behavior: "smooth" });
    }, 0);
  }

  function openJob(jobId: string) {
    setActiveJobId(jobId);
    window.history.pushState({}, "", "/jobs/" + jobId);
    showWorkspace();
  }

  async function startSample(sample: PublicSample) {
    setActionError(null);
    setBusyId(sample.id);
    try {
      const form = new FormData();
      form.set("sample_id", sample.id);
      const created = await api.post<JobStatus>("/jobs", { body: form });
      openJob(created.id);
    } catch (error) {
      setActionError(error instanceof ApiProblem ? error.message : "The sample could not start.");
    } finally {
      setBusyId(null);
    }
  }

  async function uploadFile(file: File) {
    setActionError(null);
    setUploading(true);
    try {
      const form = new FormData();
      form.set("file", file);
      const created = await api.post<JobStatus>("/jobs", { body: form });
      openJob(created.id);
    } catch (error) {
      setActionError(error instanceof ApiProblem ? error.message : "The upload could not start.");
    } finally {
      setUploading(false);
    }
  }

  async function decidePatch(patchId: string, status: "accepted" | "rejected") {
    if (!activeJobId) return;
    setBusyPatchId(patchId);
    try {
      await api.patch("/jobs/" + activeJobId + "/corrections/" + patchId, {
        body: JSON.stringify({ status }),
        headers: { "Content-Type": "application/json" },
      });
      await documentQuery.refetch();
    } catch (error) {
      setActionError(
        error instanceof ApiProblem ? error.message : "The correction decision could not be saved.",
      );
    } finally {
      setBusyPatchId(null);
    }
  }

  async function runByok(
    provider: "gemini" | "openai_compatible",
    apiKey: string,
  ): Promise<void> {
    if (!activeJobId) return;
    setActionError(null);
    try {
      await api.post("/jobs/" + activeJobId + "/ai-correction", {
        body: JSON.stringify({ provider, api_key: apiKey }),
        headers: { "Content-Type": "application/json" },
      });
      await documentQuery.refetch();
    } catch (error) {
      setActionError(
        error instanceof ApiProblem ? error.message : "The AI correction could not be completed.",
      );
    }
  }

  function showCitation(pageNumber: number, blockId: string) {
    window.document.getElementById("source-" + blockId)?.scrollIntoView({ behavior: "smooth" });
    setActionError("Source: page " + pageNumber + ", block " + blockId);
  }

  return (
    <main className="app-shell">
      <nav className="topbar" aria-label="Primary navigation">
        <a className="brand" href="/">
          <span className="brand-mark" aria-hidden="true">
            ◈
          </span>
          Document Intelligence Lab
        </a>
        <span className="topbar-note">OCR / AI SYSTEMS</span>
      </nav>

      <section className="hero" aria-labelledby="hero-title">
        <div className="hero-copy">
          <p className="eyebrow">An observable document pipeline</p>
          <h1 id="hero-title">Turn scanned pages into trustworthy text.</h1>
          <p className="hero-lede">
            See how preprocessing, OCR confidence, reversible AI correction, and source-cited
            summaries work together on a single document.
          </p>
          <div className="hero-actions">
            <button className="button button-primary" type="button" onClick={showWorkspace}>
              Try a sample <span aria-hidden="true">↗</span>
            </button>
            <button
              className="button button-quiet"
              type="button"
              onClick={() => window.document.getElementById("upload-input")?.click()}
            >
              Upload a PDF
            </button>
          </div>
          <p className="privacy-note">
            <span aria-hidden="true">●</span> Local OCR by default · no account required
          </p>
        </div>

        <div className="hero-visual" aria-label="Pipeline preview">
          <div className="scan-card">
            <div className="scan-card-header">
              <span>DOCUMENT / 001</span>
              <span className="status-chip">ANALYZED</span>
            </div>
            <div className="document-sheet">
              <span className="sheet-kicker">FIELD NOTES / 1987</span>
              <span className="sheet-title">The shape of a readable archive</span>
              <span className="sheet-line wide" />
              <span className="sheet-line" />
              <span className="sheet-line medium" />
              <span className="sheet-line short" />
              <div className="sheet-stamp">
                OCR
                <br />
                RAW TEXT
              </div>
            </div>
            <div className="scan-card-footer">
              <span>1 page</span>
              <span>confidence bands</span>
              <span>source cited</span>
            </div>
          </div>
          <div className="floating-metric">
            <span className="metric-label">EVALUATION SURFACE</span>
            <strong>CER / WER</strong>
            <span className="metric-trend">raw vs corrected</span>
          </div>
        </div>
      </section>

      <section className="pipeline-strip" aria-label="Processing stages">
        {["Render", "Recognize", "Correct", "Explain"].map((stage, index) => (
          <div className="pipeline-step" key={stage}>
            <span className="pipeline-number">0{index + 1}</span>
            <span>{stage}</span>
          </div>
        ))}
      </section>

      <section className="system-status" aria-live="polite">
        <span
          className={"status-dot " + (readiness.isSuccess ? "ready" : "")}
          aria-hidden="true"
        />
        {readiness.isSuccess ? "Processing service online" : "Connecting to processing service"}
      </section>

      <section id="workspace" className="workspace-section" aria-labelledby="workspace-heading">
        <div className="workspace-intro">
          <div>
            <p className="eyebrow">Use the system</p>
            <h2 id="workspace-heading">Start with a real scan.</h2>
          </div>
          <p>
            Samples are pre-registered and measurable. Uploads stay in a short-lived isolated
            workspace.
          </p>
        </div>
        <UploadDropzone onSubmit={uploadFile} busy={uploading} />
        {actionError && (
          <p className="action-error" role="alert">
            {actionError}
          </p>
        )}
        {activeJobId && job.data && <JobProgress job={job.data} />}
        {activeJobId && job.isPending && (
          <p className="loading-note" role="status">
            Connecting to the processing trace…
          </p>
        )}
        {documentQuery.data && (
          <ByokForm onSubmit={runByok} disabled={documentQuery.isFetching} />
        )}
        {documentQuery.data && (
          <>
            <RawResult
              document={documentQuery.data}
              onDecide={decidePatch}
              busyPatchId={busyPatchId}
            />
            <IntelligenceReport report={documentQuery.data.report} onCitation={showCitation} />
          </>
        )}
      </section>

      <SampleGallery samples={sampleList} onRun={startSample} busyId={busyId} />
      <EvaluationDashboard />
    </main>
  );
}
