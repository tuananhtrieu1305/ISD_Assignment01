const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:5000";

export type DiabetesRequest = {
  model?: string;
  Glucose: number;
  BMI: number;
  Age: number;
  Pregnancies: number;
  BloodPressure: number;
  DiabetesPedigreeFunction: number;
};

export type DiabetesResponse = {
  task: "diabetes";
  model?: ModelInfo;
  prediction: number;
  label: string;
  probability?: number;
  disclaimer: string;
};

export type DiabetesCompareResult = {
  model_id: string;
  model_name: string;
  recommended: boolean;
  prediction: number;
  probability?: number;
};

export type DiabetesConsensus = {
  majority_prediction: number;
  agreeing_models: number;
  total_models: number;
  agreement_ratio: number;
};

export type DiabetesCompareResponse = {
  task: "diabetes";
  results: DiabetesCompareResult[];
  consensus: DiabetesConsensus;
};

export type HouseRequest = {
  model?: string;
  Area: number;
  Frontage: number;
  "Access Road": number;
  Floors: number;
  Bedrooms: number;
  Bathrooms: number;
};

export type HouseResponse = {
  task: "house";
  model?: ModelInfo;
  predicted_price: number;
  unit_note: string;
};

export type HouseCompareResult = {
  model_id: string;
  model_name: string;
  recommended: boolean;
  predicted_price: number;
};

export type HouseSpread = {
  min: number;
  max: number;
  mean: number;
  median: number;
  range: number;
};

export type HouseCompareResponse = {
  task: "house";
  results: HouseCompareResult[];
  spread: HouseSpread;
  unit_note: string;
};

export type ModelInfo = {
  id: string;
  name: string;
};

export type ModelOption = ModelInfo & {
  recommended: boolean;
};

export type ModelOptionsResponse = {
  diabetes: {
    default_model: string;
    models: ModelOption[];
  };
  house: {
    default_model: string;
    models: ModelOption[];
  };
};

export type HealthResponse = {
  status: "ok";
  models?: {
    diabetes: boolean;
    house: boolean;
  };
};

async function requestJson<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...options?.headers,
    },
    ...options,
  });

  const data = await response.json().catch(() => ({}));

  if (!response.ok) {
    const message =
      typeof data.error === "string" ? data.error : "Request failed.";
    throw new Error(message);
  }

  return data as T;
}

export function healthCheck() {
  return requestJson<HealthResponse>("/health");
}

export function getModelOptions() {
  return requestJson<ModelOptionsResponse>("/api/models");
}

export function predictDiabetes(payload: DiabetesRequest) {
  return requestJson<DiabetesResponse>("/api/diabetes", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function compareDiabetesModels(payload: DiabetesRequest) {
  const { model: _model, ...features } = payload;

  return requestJson<DiabetesCompareResponse>("/api/diabetes/compare", {
    method: "POST",
    body: JSON.stringify(features),
  });
}

export function predictHouse(payload: HouseRequest) {
  return requestJson<HouseResponse>("/api/house", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function compareHouseModels(payload: HouseRequest) {
  const { model: _model, ...features } = payload;

  return requestJson<HouseCompareResponse>("/api/house/compare", {
    method: "POST",
    body: JSON.stringify(features),
  });
}
