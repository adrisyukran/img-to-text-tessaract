import { useQuery } from "@tanstack/react-query";

import { api } from "../api/client";

type Readiness = {
  status: string;
  environment: string;
};

export function App() {
  const readiness = useQuery({
    queryKey: ["health", "ready"],
    queryFn: () => api.get<Readiness>("/health/ready"),
    retry: false,
  });

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
            <button className="button button-primary" type="button">
              Try a sample <span aria-hidden="true">↗</span>
            </button>
            <button className="button button-quiet" type="button">
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
                92.4%
              </div>
            </div>
            <div className="scan-card-footer">
              <span>3 pages</span>
              <span>14 corrections</span>
              <span>4.8s</span>
            </div>
          </div>
          <div className="floating-metric">
            <span className="metric-label">CORRECTION PRECISION</span>
            <strong>96.8%</strong>
            <span className="metric-trend">↑ measured on sample set</span>
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
    </main>
  );
}
