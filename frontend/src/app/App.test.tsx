import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import { vi } from "vitest";

import { App } from "./App";

vi.mock("../api/client", () => ({
  api: {
    get: vi.fn().mockImplementation((path: string) => {
      if (path === "/health/ready") {
        return Promise.resolve({ status: "ready", environment: "test" });
      }
      if (path === "/capabilities") {
        return Promise.resolve({
          accepted_media_types: ["application/pdf", "image/png", "image/jpeg"],
          max_upload_bytes: 15_000_000,
          max_pdf_pages: 12,
          artifact_ttl_seconds: 3600,
          hosted_provider: {
            enabled: true,
            remaining_documents: 20,
            reset_at: "2026-09-22T00:00:00Z",
          },
          byok_providers: ["gemini", "openai_compatible"],
        });
      }
      return Promise.resolve([]);
    }),
  },
}));

test("explains the document pipeline and reports API readiness", async () => {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  render(
    <QueryClientProvider client={queryClient}>
      <App />
    </QueryClientProvider>,
  );

  expect(
    screen.getByRole("heading", { name: /turn scanned pages into trustworthy text/i }),
  ).toBeInTheDocument();
  expect(await screen.findByText(/processing service online/i)).toBeInTheDocument();
  expect(await screen.findByText(/20 hosted runs remaining/i)).toBeInTheDocument();
});
