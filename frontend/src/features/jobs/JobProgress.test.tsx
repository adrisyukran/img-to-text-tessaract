import { render, screen } from "@testing-library/react";

import type { JobStatus } from "../../api/types";
import { JobProgress } from "./JobProgress";

const job: JobStatus = {
  id: "01ARZ3NDEKTSV4RRFFQ69G5FAV",
  source_name: "clean-letter.pdf",
  stage: "ocr",
  progress: 0.5,
  current_page: 1,
  total_pages: 1,
  revision: 4,
  error_code: null,
  error_detail: null,
  artifact_keys: [],
  created_at: "2026-09-20T00:00:00Z",
  expires_at: "2026-09-20T01:00:00Z",
  status_url: "/api/v1/jobs/01ARZ3NDEKTSV4RRFFQ69G5FAV",
  events_url: "/api/v1/jobs/01ARZ3NDEKTSV4RRFFQ69G5FAV/events",
  document_url: "/api/v1/jobs/01ARZ3NDEKTSV4RRFFQ69G5FAV/document",
};

test("renders accessible stage progress and page status", () => {
  render(<JobProgress job={job} />);

  expect(screen.getByRole("progressbar")).toHaveAttribute("aria-valuenow", "50");
  expect(screen.getByText(/page 1 of 1/i)).toBeInTheDocument();
  expect(screen.getByText("Recognize")).toBeInTheDocument();
});
