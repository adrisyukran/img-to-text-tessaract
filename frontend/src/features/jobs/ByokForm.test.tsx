import { fireEvent, render, screen, waitFor } from "@testing-library/react";

import { ByokForm } from "./ByokForm";

test("clears the key after a request-scoped BYOK submission", async () => {
  const onSubmit = vi.fn().mockResolvedValue(undefined);
  render(<ByokForm onSubmit={onSubmit} />);

  const input = screen.getByLabelText("API key");
  fireEvent.change(input, { target: { value: "secret-key" } });
  fireEvent.click(screen.getByRole("button", { name: /run ai correction/i }));

  await waitFor(() => expect(onSubmit).toHaveBeenCalledWith("openai_compatible", "secret-key"));
  expect(input).toHaveValue("");
});
