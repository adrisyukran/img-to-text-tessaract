import { useState, type FormEvent } from "react";

type ByokFormProps = {
  onSubmit: (provider: "gemini" | "openai_compatible", apiKey: string) => Promise<void>;
  onHostedSubmit?: () => Promise<void>;
  hostedProvider?: {
    enabled: boolean;
    remainingDocuments: number;
    resetAt: string | null;
  };
  disabled?: boolean;
};

export function ByokForm({
  onSubmit,
  onHostedSubmit,
  hostedProvider,
  disabled = false,
}: ByokFormProps) {
  const [provider, setProvider] = useState<"gemini" | "openai_compatible">("openai_compatible");
  const [apiKey, setApiKey] = useState("");
  const [busyMode, setBusyMode] = useState<"hosted" | "byok" | null>(null);
  const busy = busyMode !== null;

  async function runHosted() {
    if (!onHostedSubmit || busy || disabled || !hostedProvider?.remainingDocuments) return;
    setBusyMode("hosted");
    try {
      await onHostedSubmit();
    } finally {
      setBusyMode(null);
    }
  }

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!apiKey.trim() || busy || disabled) return;
    setBusyMode("byok");
    try {
      await onSubmit(provider, apiKey);
      setApiKey("");
    } finally {
      setBusyMode(null);
    }
  }

  return (
    <section className="ai-correction-panel" aria-label="AI correction options">
      {hostedProvider?.enabled && onHostedSubmit && (
        <div className="hosted-ai-option">
          <div>
            <p className="eyebrow">Optional AI pass</p>
            <h3>Try the hosted model</h3>
            <p>
              {hostedProvider.remainingDocuments} hosted runs remaining today. OCR text is sent
              to the configured model only when you choose this step.
            </p>
          </div>
          <button
            className="button button-primary"
            type="button"
            onClick={runHosted}
            disabled={busy || disabled || hostedProvider.remainingDocuments === 0}
          >
            {busyMode === "hosted"
              ? "Running hosted correction…"
              : hostedProvider.remainingDocuments === 0
                ? "Hosted quota exhausted"
                : "Run hosted correction"}
          </button>
        </div>
      )}

      <form className="byok-form" onSubmit={submit}>
        <div>
          <p className="eyebrow">Or use your own key</p>
          <h3>Bring your own provider key</h3>
          <p>
            Your key is sent over this request only. It is never stored with the job or rendered
            after submission.
          </p>
        </div>
        <label>
          Provider
          <select
            value={provider}
            onChange={(event) =>
              setProvider(event.target.value as "gemini" | "openai_compatible")
            }
            disabled={busy || disabled}
          >
            <option value="openai_compatible">OpenAI-compatible</option>
            <option value="gemini">Gemini</option>
          </select>
        </label>
        <label>
          API key
          <input
            type="password"
            value={apiKey}
            onChange={(event) => setApiKey(event.target.value)}
            placeholder="sk-… or AIza…"
            autoComplete="off"
            disabled={busy || disabled}
          />
        </label>
        <button className="button button-quiet" type="submit" disabled={busy || disabled}>
          {busyMode === "byok" ? "Running BYOK correction…" : "Run BYOK correction"}
        </button>
      </form>
    </section>
  );
}
