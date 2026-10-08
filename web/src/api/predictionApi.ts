export function normaliseApiBaseUrl(value?: string): string {
  const configured = value?.trim().replace(/\/$/, "");
  if (!configured) return "http://127.0.0.1:5000";
  if (/^https?:\/\//i.test(configured)) return configured;
  return `https://${configured}`;
}

const API_BASE_URL = normaliseApiBaseUrl(
  import.meta.env?.VITE_API_BASE_URL,
);

export type Provenance = {
  version: string;
  model_sha256: string;
  preprocessor_sha256: string[];
};

export type ModelRegistryItem = {
  version: string;
  chapter: number;
  model_sha256: string;
  model_bytes: number;
  hash_verified: boolean;
  threshold?: number;
};

export type ModelRegistryResponse = {
  models: Record<string, ModelRegistryItem>;
};

export type HealthResponse = {
  status: "ok";
  service_version: string;
  models: Record<
    string,
    {
      version: string;
      chapter: number;
      hash_verified: boolean;
      model_sha256: string;
    }
  >;
};

export type DemoResponse<T> = {
  use_case: "diabetes" | "eurosat" | "customer" | "aapl";
  input: T;
  sample_key?: string;
};

export type DiabetesInput = {
  HighBP: number;
  HighChol: number;
  CholCheck: number;
  BMI: number;
  Smoker: number;
  Stroke: number;
  HeartDiseaseorAttack: number;
  PhysActivity: number;
  Fruits: number;
  Veggies: number;
  HvyAlcoholConsump: number;
  AnyHealthcare: number;
  NoDocbcCost: number;
  GenHlth: number;
  MentHlth: number;
  PhysHlth: number;
  DiffWalk: number;
  Sex: number;
  Age: number;
  Education: number;
  Income: number;
};

export type DiabetesResult = {
  probability: number;
  threshold: number;
  predicted_class: number;
  label: string;
  warning: string;
  provenance: Provenance;
  request_id: string;
};

export type EuroSatInput = {
  image_base64: string;
};

export type EuroSatResult = {
  predicted_class_index: number;
  predicted_class: string;
  top_classes: Array<{
    class_index: number;
    class_name: string;
    confidence: number;
  }>;
  input_shape: [number, number, number];
  warning: string;
  provenance: Provenance;
  request_id: string;
};

export type SequenceInput = {
  sequence: number[][];
};

export type CustomerResult = {
  probability: number;
  threshold: number;
  predicted_class: number;
  label: string;
  sequence_shape: [number, number];
  warning: string;
  provenance: Provenance;
  request_id: string;
};

export type AaplResult = {
  rnn_prediction_usd: number;
  naive_last_close_usd: number;
  delta_rnn_vs_naive_usd: number;
  sequence_shape: [number, number];
  warning: string;
  provenance: Provenance;
  request_id: string;
};

type ApiErrorEnvelope = {
  error?: {
    code?: string;
    message?: string;
  };
};

async function requestJson<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers: {
      Accept: "application/json",
      ...(options?.body ? { "Content-Type": "application/json" } : {}),
      ...options?.headers,
    },
  });

  const data = (await response.json().catch(() => ({}))) as ApiErrorEnvelope;

  if (!response.ok) {
    throw new Error(
      data.error?.message ??
        `Máy chủ trả về lỗi ${response.status}. Vui lòng thử lại.`,
    );
  }

  return data as T;
}

export function healthCheck() {
  return requestJson<HealthResponse>("/health");
}

export function getModelRegistry() {
  return requestJson<ModelRegistryResponse>("/api/models");
}

export function getDemo<T>(useCase: "diabetes" | "eurosat" | "customer" | "aapl") {
  return requestJson<DemoResponse<T>>(`/api/demo/${useCase}`);
}

export function predictDiabetes(input: DiabetesInput) {
  return requestJson<DiabetesResult>("/api/predict/diabetes", {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export function predictEuroSat(input: EuroSatInput) {
  return requestJson<EuroSatResult>("/api/predict/eurosat", {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export function predictCustomer(input: SequenceInput) {
  return requestJson<CustomerResult>("/api/predict/customer", {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export function predictAapl(input: SequenceInput) {
  return requestJson<AaplResult>("/api/predict/aapl", {
    method: "POST",
    body: JSON.stringify(input),
  });
}
