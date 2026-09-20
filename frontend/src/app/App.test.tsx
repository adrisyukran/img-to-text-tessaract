import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import { vi } from "vitest";

import { App } from "./App";

vi.mock("../api/client", () => ({
  api: {
    get: vi.fn().mockResolvedValue({ status: "ready", environment: "test" }),
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
});
