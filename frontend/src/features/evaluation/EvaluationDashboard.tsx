import { useQuery } from "@tanstack/react-query";

import { api } from "../../api/client";
import type { EvaluationMetrics, EvaluationResult } from "../../api/types";

function percentage(value: number): string {
  return (value * 100).toFixed(1) + "%";
}

function MetricCard({ label, value, hint }: { label: string; value: string; hint: string }) {
  return (
    <article className="evaluation-metric">
      <span>{label}</span>
      <strong>{value}</strong>
      <small>{hint}</small>
    </article>
  );
}

function MetricPair({ metrics, prefix }: { metrics: EvaluationMetrics; prefix: string }) {
  return (
    <>
      <MetricCard label={prefix + " CER"} value={percentage(metrics.cer)} hint="character error rate" />
      <MetricCard label={prefix + " WER"} value={percentage(metrics.wer)} hint="word error rate" />
    </>
  );
}

export function EvaluationDashboard() {
  const evaluation = useQuery({
    queryKey: ["evaluation"],
    queryFn: () => api.get<EvaluationResult>("/evaluation"),
    retry: false,
  });
  const result = evaluation.data;
  const samples = result && Array.isArray(result.samples) ? result.samples : [];
  const aggregate = result?.aggregate ?? null;
  const limitations = result && Array.isArray(result.limitations) ? result.limitations : [];

  return (
    <section className="evaluation-section" aria-labelledby="evaluation-heading">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Quality, made inspectable</p>
          <h2 id="evaluation-heading">A benchmark you can question.</h2>
        </div>
        <p className="section-note">
          CER measures character mistakes. WER measures word mistakes. The dashboard keeps raw OCR
          and corrected output side by side so improvement is never assumed.
        </p>
      </div>
      {evaluation.isPending && <p className="evaluation-muted">Loading benchmark metadata…</p>}
      {evaluation.isError && (
        <p className="evaluation-muted">
          The benchmark is not available in this deployment. The pipeline remains usable without it.
        </p>
      )}
      {result && (
        <div className="evaluation-content">
          <div className="evaluation-meta">
            <span className="evaluation-badge">
              {result.measured ? "Measured run" : "Descriptive metadata"}
            </span>
            <span>{result.engine ?? "Evaluation metadata"}</span>
            <span>{samples.length} corpus samples</span>
            <span>{result.correction_provider ?? "Provider not recorded"}</span>
          </div>
          {aggregate ? (
            <div className="evaluation-metrics" aria-label="Aggregate benchmark metrics">
              <MetricPair metrics={aggregate.raw} prefix="Raw" />
              {aggregate.corrected && (
                <MetricPair metrics={aggregate.corrected} prefix="Corrected" />
              )}
            </div>
          ) : (
            <p className="evaluation-muted">
              No measured aggregate is published yet. Run the reproducible evaluation command to
              create one for this environment.
            </p>
          )}
          {samples.length > 0 && (
            <div className="evaluation-table-wrap">
              <table className="evaluation-table">
                <caption>Per-sample error rates</caption>
                <thead>
                  <tr>
                    <th scope="col">Sample</th>
                    <th scope="col">Raw CER</th>
                    <th scope="col">Corrected CER</th>
                    <th scope="col">Corrections</th>
                  </tr>
                </thead>
                <tbody>
                  {samples.map((sample) => (
                    <tr key={sample.id}>
                      <th scope="row">{sample.title}</th>
                      <td>{percentage(sample.raw.cer)}</td>
                      <td>{sample.corrected ? percentage(sample.corrected.cer) : "Not measured"}</td>
                      <td>{sample.correction_count}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
          <div className="evaluation-footnotes">
            <span>Preprocessing: {result.preprocessing_profile ?? "Not recorded"}</span>
            <span>{limitations.join(" ")}</span>
          </div>
        </div>
      )}
    </section>
  );
}
