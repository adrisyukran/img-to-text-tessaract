import { fireEvent, render, screen } from "@testing-library/react";

import { UploadDropzone } from "./UploadDropzone";

test("uses the same submit callback for the file picker", () => {
  const onSubmit = vi.fn();
  render(<UploadDropzone onSubmit={onSubmit} />);

  const input = document.querySelector('input[type="file"]') as HTMLInputElement;
  const file = new File(["scan"], "scan.pdf", { type: "application/pdf" });
  fireEvent.change(input, { target: { files: [file] } });

  expect(onSubmit).toHaveBeenCalledWith(file);
});
