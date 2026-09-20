export type PublicSample = {
  id: string;
  title: string;
  description: string;
  page_count: number;
  preview_url: string;
  labels: string[];
};

export type JobStage =
  | "queued"
  | "rendering"
  | "preprocessing"
  | "ocr"
  | "correction"
  | "awaiting_byok"
  | "intelligence"
  | "exports"
  | "complete"
  | "failed";

export type JobStatus = {
  id: string;
  source_name: string;
  stage: JobStage;
  progress: number;
  current_page: number | null;
  total_pages: number;
  revision: number;
  error_code: string | null;
  error_detail: string | null;
  artifact_keys: string[];
  created_at: string;
  expires_at: string;
  status_url: string;
  events_url: string;
  document_url: string;
};

export type BoundingBox = {
  x: number;
  y: number;
  width: number;
  height: number;
};

export type OCRSpan = {
  id: string;
  text: string;
  bbox: BoundingBox;
  confidence: number;
  source: Record<string, number | string>;
};

export type DocumentBlock = {
  id: string;
  page_number: number;
  kind: string;
  span_ids: string[];
  raw_text: string;
  bbox: BoundingBox;
  confidence: number;
};

export type CorrectionPatch = {
  id: string;
  block_id: string;
  span_ids: string[];
  original_text: string;
  replacement_text: string;
  rationale: string;
  model_confidence: number;
  status: "proposed" | "accepted" | "rejected";
};

export type CanonicalDocument = {
  schema_version: "1.0";
  job_id: string;
  source_name: string;
  pages: Array<{
    number: number;
    width: number;
    height: number;
    spans: OCRSpan[];
    blocks: DocumentBlock[];
  }>;
  corrections: CorrectionPatch[];
  report: unknown | null;
};
