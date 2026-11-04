export type Doc = Record<string, unknown>;
export type Asset = { path: string; sha256: string };
export type Dataset = {
  dataset_id: string;
  chapter: number;
  logical_size: Doc;
  source: {
    url: string;
    citation: string;
    license_status: string;
    license_note: string;
    version: string;
  };
  files: Array<{ size_bytes: number; sha256: string }>;
  status: string;
  target: Doc;
};
export type RequestInput = {
  kind: string;
  features?: Record<string, string | number | null>;
  rows?: Doc[];
  text?: string;
  domain?: string;
  data_base64?: string;
  [key: string]: unknown;
};
export type ComparisonRequest = {
  schema_version: string;
  chapter: number;
  dataset_id: string;
  family: string;
  implementations: string[];
  input: RequestInput;
};
export type Overview = {
  dataset_id: string;
  chapter: number;
  scope: string;
  data_card: Asset;
  data_card_text: string;
  eda_summary: Doc;
  sample: {
    request: ComparisonRequest;
    input_split: string;
    sample_id: string;
  } | null;
  [key: string]: unknown;
};
export type Model = {
  model_id: string;
  family: string;
  implementation: string;
  backend: string;
  status: string;
  reason: string | null;
  contract: Asset;
};
export type FunctionRow = {
  id?: string;
  name?: string;
  signature?: string;
  role?: string;
  input_shape?: unknown;
  output_shape?: unknown;
  parameters?: number | null;
  mapping?: Doc;
  formula?: {
    expression: string;
    plain_explanation: string;
    example: string;
    symbols: Doc[];
  };
  [key: string]: unknown;
};
export type Contract = {
  model_id?: string;
  family?: string;
  backend?: string;
  functions?: FunctionRow[];
  layers?: Array<{
    id: string;
    parameter_count: number;
    input_shape: unknown;
    output_shape: unknown;
  }>;
  parameter_count?: number | null;
  composition_plain?: string;
  composition?: unknown;
  recurrent_unroll?: unknown;
  [key: string]: unknown;
};
export type Slot = {
  implementation: string;
  model_id: string | null;
  status: string;
  actual_backend: string | null;
  actual_device: string | null;
  artifact_sha256: string | null;
  inference_ms: number | null;
  prediction: Doc | null;
  error: Doc | null;
  input_sha256: string | null;
  comparison_group_sha256: string | null;
};
export type Job = {
  schema_version: string;
  job_id: string;
  status: string;
  comparison_valid: boolean;
  comparison_reason?: string | null;
  results: Slot[];
  trace_ids: string[];
  [key: string]: unknown;
};
export type Envelope<T> = {
  data: T;
  page?: number;
  page_size?: number;
  total?: number;
};
export type ResultIndex = {
  artifacts: Asset[];
  row_filter_hint: Record<string, string>;
  scope: string;
  cost_scope: string;
  live_demo_equivalent_to_historical_benchmark?: boolean;
};
