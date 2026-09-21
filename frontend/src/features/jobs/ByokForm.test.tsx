import { fireEvent, render, screen, waitFor } from "@testing-library/react";

import { ByokForm } from "./ByokForm";

test("clears the key after a request-scoped BYOK submission", async () => {
  const onSubmit = vi.fn().mockResolvedValue(undefined);
  render(<ByokForm onSubmit={onSubmit} />);

  const input = screen.getByLabelText("API key");
  fireEvent.change(input, { target: { value: "secret-key" } });
  fireEvent.click(screen.getByRole("button", { name: /run byok correction/i }));

  await waitFor(() => expect(onSubmit).toHaveBeenCalledWith("openai_compatible", "secret-key"));
  expect(input).toHaveValue("");
});

test("offers quota-limited hosted correction without asking for a key", async () => {
  const onSubmit = vi.fn().mockResolvedValue(undefined);
  const onHostedSubmit = vi.fn().mockResolvedValue(undefined);

  render(
    <ByokForm
      onSubmit={onSubmit}
      onHostedSubmit={onHostedSubmit}
      hostedProvider={{
        enabled: true,
        remainingDocuments: 3,
        resetAt: "2026-09-22T00:00:00Z",
      }}
    />,
  );

  expect(screen.getByText(/3 hosted runs remaining/i)).toBeInTheDocument();
  fireEvent.click(screen.getByRole("button", { name: /run hosted correction/i }));

  await waitFor(() => expect(onHostedSubmit).toHaveBeenCalledTimes(1));
  expect(onSubmit).not.toHaveBeenCalled();
});

test("disables hosted correction when the anonymous quota is exhausted", () => {
  render(
    <ByokForm
      onSubmit={vi.fn().mockResolvedValue(undefined)}
      onHostedSubmit={vi.fn().mockResolvedValue(undefined)}
      hostedProvider={{
        enabled: true,
        remainingDocuments: 0,
        resetAt: "2026-09-22T00:00:00Z",
      }}
    />,
  );

  expect(screen.getByRole("button", { name: /hosted quota exhausted/i })).toBeDisabled();
});
