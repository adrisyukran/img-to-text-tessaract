import type { CanonicalDocument, CorrectionPatch, DocumentBlock, OCRSpan } from "../../api/types";

function acceptedText(
  block: DocumentBlock,
  spans: OCRSpan[],
  corrections: CorrectionPatch[],
): string {
  const spanMap = new Map(spans.map((span) => [span.id, span]));
  const values = block.span_ids.map((spanId) => spanMap.get(spanId)?.text ?? "");
  corrections
    .filter((patch) => patch.block_id === block.id && patch.status === "accepted")
    .sort(
      (left, right) =>
        block.span_ids.indexOf(right.span_ids[0]) - block.span_ids.indexOf(left.span_ids[0]),
    )
    .forEach((patch) => {
      const start = block.span_ids.indexOf(patch.span_ids[0]);
      values.splice(start, patch.span_ids.length, patch.replacement_text);
    });
  return values.join(" ");
}

function confidenceClass(confidence: number): string {
  if (confidence < 0.65) return "confidence-low";
  if (confidence < 0.85) return "confidence-mid";
  return "confidence-high";
}

export function RawResult({ document }: { document: CanonicalDocument }) {
  const page = document.pages[0];
  const spanMap = new Map(page.spans.map((span) => [span.id, span]));
  return (
    <section className="result-panel" aria-labelledby="result-heading">
      <div className="result-heading">
        <div>
          <p className="eyebrow">Inspectable output</p>
          <h2 id="result-heading">What the system actually saw</h2>
        </div>
        <span className="result-count">
          {document.corrections.length} proposed correction
          {document.corrections.length === 1 ? "" : "s"}
        </span>
      </div>
      <div className="result-grid">
        <div className="page-preview">
          <div className="page-preview-toolbar">
            <span>PAGE {String(page.number).padStart(2, "0")}</span>
            <span>RAW IMAGE</span>
          </div>
          <img
            src={"/api/v1/jobs/" + document.job_id + "/pages/" + page.number + "/image"}
            alt={"Rendered scan page " + page.number}
          />
        </div>
        <div className="text-inspector">
          <div className="inspector-summary">
            <span>OCR BLOCKS</span>
            <span>{page.blocks.length}</span>
          </div>
          {page.blocks.map((block) => (
            <article className="text-block" key={block.id}>
              <div className="text-block-meta">
                <span>{block.kind.replace("_", " ")}</span>
                <span className={confidenceClass(block.confidence)}>
                  {Math.round(block.confidence * 100)}% confidence
                </span>
              </div>
              <p className="raw-text">
                {block.span_ids.map((spanId) => {
                  const span = spanMap.get(spanId);
                  return (
                    <mark className={confidenceClass(span?.confidence ?? 0)} key={spanId}>
                      {span?.text}
                    </mark>
                  );
                })}
              </p>
              <p className="accepted-text">
                <span>Derived text</span>
                {acceptedText(block, page.spans, document.corrections)}
              </p>
            </article>
          ))}
        </div>
      </div>
    </section>
  );
}
