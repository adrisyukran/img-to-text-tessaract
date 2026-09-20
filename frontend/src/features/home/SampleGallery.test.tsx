import { fireEvent, render, screen } from "@testing-library/react";

import type { PublicSample } from "../../api/types";
import { SampleGallery } from "./SampleGallery";

const sample: PublicSample = {
  id: "clean-letter",
  title: "Clean letter",
  description: "A high-contrast printed page.",
  page_count: 1,
  preview_url: "/api/v1/samples/clean-letter/preview",
  labels: ["clean", "printed"],
};

test("renders sample metadata and exposes an accessible run action", () => {
  const onRun = vi.fn();
  render(<SampleGallery samples={[sample]} onRun={onRun} />);

  expect(screen.getByRole("heading", { name: "Clean letter" })).toBeInTheDocument();
  expect(screen.getByText("A high-contrast printed page.")).toBeInTheDocument();
  fireEvent.click(screen.getByRole("button", { name: /run this sample/i }));
  expect(onRun).toHaveBeenCalledWith(sample);
});
