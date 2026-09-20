import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import { vi } from "vitest";

import { EvaluationDashboard } from "./EvaluationDashboard";

const mocks = vi.hoisted(() => ({ get: vi.fn() }));

vi.mock("../../api/client", () => ({
  api: { get: mocks.get },
}));

test("shows exact raw and corrected benchmark metrics", async () => {
  mocks.get.mockResolvedValue({
    schema_version: "1.0",
    measured: true,
    generated_from_manifest_sha256: "abc123",
    engine: "Tesseract",
    preprocessing_profile: "deskew-v1",
    correction_provider: "fixture-provider",
    run_environment: "test",
    aggregate: {
      raw: { cer: 0.2, wer: 0.3 },
      corrected: { cer: 0.1, wer: 0.2 },
    },
    samples: [],
    methodology: [],
    limitations: [],
  });
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });

  render(
    <QueryClientProvider client={queryClient}>
      <EvaluationDashboard />
    </QueryClientProvider>,
  );

  expect((await screen.findAllByText("20.0%")).length).toBe(2);
  expect(screen.getByText("10.0%")).toBeInTheDocument();
  expect(screen.getByText("Measured run")).toBeInTheDocument();
});
