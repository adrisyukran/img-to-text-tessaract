import type { IntelligenceReport as Report } from "../../api/types";

type IntelligenceReportProps = {
  report: Report | null;
  onCitation: (pageNumber: number, blockId: string) => void;
};

export function IntelligenceReport({ report, onCitation }: IntelligenceReportProps) {
  if (!report) {
    return (
      <section className="report-panel" aria-labelledby="report-heading">
        <p className="eyebrow">Document intelligence</p>
        <h2 id="report-heading">Report unavailable</h2>
        <p className="report-muted">
          The digital document is still useful. No source-cited report was generated for this run.
        </p>
      </section>
    );
  }

  return (
    <section className="report-panel" aria-labelledby="report-heading">
      <p className="eyebrow">Document intelligence</p>
      <h2 id="report-heading">A cited reading of the page</h2>
      <p className="report-summary">{report.summary.text}</p>
      <div className="report-columns">
        <div>
          <h3>Key points</h3>
          <ul className="report-list">
            {report.key_points.map((item, index) => (
              <li key={index}>
                <span>{item.text}</span>
                <CitationButtons citations={item.citations} onCitation={onCitation} />
              </li>
            ))}
          </ul>
        </div>
        <div>
          <h3>Entities</h3>
          <ul className="report-list">
            {report.entities.map((entity) => (
              <li key={entity.kind + entity.value}>
                <span>
                  <small>{entity.kind}</small>
                  {entity.value}
                </span>
                <CitationButtons citations={entity.citations} onCitation={onCitation} />
              </li>
            ))}
          </ul>
        </div>
      </div>
      {report.warnings.length > 0 && (
        <p className="report-muted">Limitations: {report.warnings.join(" ")}</p>
      )}
    </section>
  );
}

function CitationButtons({
  citations,
  onCitation,
}: {
  citations: Report["summary"]["citations"];
  onCitation: (pageNumber: number, blockId: string) => void;
}) {
  return (
    <span className="citation-buttons">
      {citations.map((citation) =>
        citation.block_ids.map((blockId) => (
          <button
            type="button"
            key={citation.page_number + blockId}
            onClick={() => onCitation(citation.page_number, blockId)}
          >
            p{citation.page_number} · {blockId}
          </button>
        )),
      )}
    </span>
  );
}
