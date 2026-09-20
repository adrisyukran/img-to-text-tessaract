import type { PublicSample } from "../../api/types";

type SampleGalleryProps = {
  samples: PublicSample[];
  onRun: (sample: PublicSample) => void;
  busyId?: string | null;
};

export function SampleGallery({ samples, onRun, busyId = null }: SampleGalleryProps) {
  return (
    <section className="sample-section" aria-labelledby="sample-heading">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Start with a controlled input</p>
          <h2 id="sample-heading">Three scans. One inspectable pipeline.</h2>
        </div>
        <p className="section-note">
          Every sample has ground truth, so the result is more than a demo. It is a measurable
          experiment.
        </p>
      </div>
      <div className="sample-grid">
        {samples.map((sample, index) => (
          <article className="sample-card" key={sample.id}>
            <div className={"sample-card-art sample-art-" + index} aria-hidden="true">
              <span className="sample-art-label">{String(index + 1).padStart(2, "0")}</span>
              <span className="sample-art-lines" />
            </div>
            <div className="sample-card-body">
              <div className="sample-card-meta">
                <span>{sample.page_count} page</span>
                <span>{sample.id}</span>
              </div>
              <h3>{sample.title}</h3>
              <p>{sample.description}</p>
              <div className="sample-labels" aria-label="Sample characteristics">
                {sample.labels.map((label) => (
                  <span key={label}>{label}</span>
                ))}
              </div>
              <button
                className="sample-run"
                type="button"
                onClick={() => onRun(sample)}
                disabled={busyId !== null}
              >
                {busyId === sample.id ? "Queueing…" : "Run this sample"}
                <span aria-hidden="true">↗</span>
              </button>
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}
