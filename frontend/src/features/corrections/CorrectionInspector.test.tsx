import { fireEvent, render, screen } from "@testing-library/react";

import { CorrectionInspector } from "./CorrectionInspector";

test("shows safe diff text and exposes reversible decisions", () => {
  const onDecide = vi.fn();
  render(
    <CorrectionInspector
      patches={[
        {
          id: "p-1",
          block_id: "p1-b1",
          span_ids: ["p1-s1"],
          original_text: "<raw>",
          replacement_text: "corrected",
          rationale: "The scan confused the first character.",
          model_confidence: 0.98,
          status: "proposed",
        },
      ]}
      onDecide={onDecide}
    />,
  );

  expect(screen.getByText("<raw>")).toBeInTheDocument();
  fireEvent.click(screen.getByRole("button", { name: "Accept" }));
  expect(onDecide).toHaveBeenCalledWith("p-1", "accepted");
});
