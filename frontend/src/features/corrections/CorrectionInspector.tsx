import type { CorrectionPatch } from "../../api/types";

type CorrectionInspectorProps = {
  patches: CorrectionPatch[];
  onDecide: (patchId: string, status: "accepted" | "rejected") => void;
  busyPatchId?: string | null;
};

export function CorrectionInspector({
  patches,
  onDecide,
  busyPatchId = null,
}: CorrectionInspectorProps) {
  return (
    <aside className="correction-inspector" aria-labelledby="correction-heading">
      <div className="inspector-summary">
        <span id="correction-heading">AI CORRECTIONS</span>
        <span>{patches.length}</span>
      </div>
      {patches.length === 0 && (
        <p className="inspector-empty">No bounded corrections were proposed for this document.</p>
      )}
      {patches.map((patch) => (
        <article className="correction-card" key={patch.id}>
          <div className="correction-card-meta">
            <span>{patch.status}</span>
            <span>{Math.round(patch.model_confidence * 100)}% model confidence</span>
          </div>
          <div className="correction-diff" aria-label="Correction diff">
            <del>{patch.original_text}</del>
            <span aria-hidden="true">→</span>
            <ins>{patch.replacement_text}</ins>
          </div>
          <p>{patch.rationale}</p>
          <div className="correction-actions">
            <button
              type="button"
              onClick={() => onDecide(patch.id, "accepted")}
              disabled={busyPatchId === patch.id}
            >
              Accept
            </button>
            <button
              type="button"
              onClick={() => onDecide(patch.id, "rejected")}
              disabled={busyPatchId === patch.id}
            >
              Reject
            </button>
          </div>
        </article>
      ))}
    </aside>
  );
}
