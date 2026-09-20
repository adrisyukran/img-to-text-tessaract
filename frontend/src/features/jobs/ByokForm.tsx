import { useState, type FormEvent } from "react";

type ByokFormProps = {
  onSubmit: (provider: "gemini" | "openai_compatible", apiKey: string) => Promise<void>;
  disabled?: boolean;
};

export function ByokForm({ onSubmit, disabled = false }: ByokFormProps) {
  const [provider, setProvider] = useState<"gemini" | "openai_compatible">("openai_compatible");
  const [apiKey, setApiKey] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!apiKey.trim() || busy || disabled) return;
    setBusy(true);
    try {
      await onSubmit(provider, apiKey);
      setApiKey("");
    } finally {
      setBusy(false);
    }
  }

  return (
    <form className="byok-form" onSubmit={submit}>
      <div>
        <p className="eyebrow">Optional AI pass</p>
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
      <button className="button button-primary" type="submit" disabled={busy || disabled}>
        {busy ? "Running correction…" : "Run AI correction"}
      </button>
    </form>
  );
}
