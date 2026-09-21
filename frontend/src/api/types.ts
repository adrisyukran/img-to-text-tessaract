export type PublicSample = {
  id: string;
  title: string;
  description: string;
  page_count: number;
  preview_url: string;
  labels: string[];
};

export type Capabilities = {
  accepted_media_types: string[];
  max_upload_bytes: number;
  max_pdf_pages: number;
  artifact_ttl_seconds: number;
  hosted_provider: {
    enabled: boolean;
    remaining_documents: number;
    reset_at: string | null;
  };
  byok_providers: string[];
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

export type ReportCitation = {
  page_number: number;
  block_ids: string[];
};

export type IntelligenceItem = {
  text: string;
  citations: ReportCitation[];
};

export type IntelligenceReport = {
  summary: IntelligenceItem;
  key_points: IntelligenceItem[];
  entities: Array<{
    kind: string;
    value: string;
    citations: ReportCitation[];
  }>;
  warnings: string[];
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
  report: IntelligenceReport | null;
};

export type EvaluationMetrics = {
  cer: number;
  wer: number;
};

export type EvaluationResult = {
  schema_version: "1.0";
  measured: boolean;
  generated_from_manifest_sha256: string;
  engine: string;
  preprocessing_profile: string;
  correction_provider: string;
  run_environment: string;
  aggregate: {
    raw: EvaluationMetrics;
    corrected: EvaluationMetrics | null;
  } | null;
  samples: Array<{
    id: string;
    title: string;
    labels: string[];
    page_count: number;
    elapsed_ms: number;
    raw: EvaluationMetrics;
    corrected: EvaluationMetrics | null;
    correction_count: number;
    representative_diffs: Array<{
      original: string;
      corrected: string;
      label: "improvement" | "regression" | "unchanged";
    }>;
  }>;
  methodology: string[];
  limitations: string[];
};
