const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:5000";

export type DiabetesRequest = {
  model?: string;
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
  Area_m2: number;
  Frontage_m: number | null;
  Access_Road_m: number | null;
  Floors: number;
  Bedrooms: number | null;
  Bathrooms: number | null;
  city: string;
  district: string;
  "Legal status": string;
  "Furniture state": string;
  "House direction": string;
  "Balcony direction": string;
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

export type CustomerBehaviorRequest = {
  model?: string;
  age: number;
  email_opt_in: number;
  has_app: number;
  customer_tenure_days: number;
  total_transactions: number;
  total_quantity: number;
  avg_discount: number;
  avg_shipping_cost: number;
  completed_orders: number;
  total_spent: number;
  avg_order_value: number;
  category_diversity: number;
  brand_diversity: number;
  cancelled_transactions: number;
  completed_transactions: number;
  pending_transactions: number;
  refunded_transactions: number;
  session_count: number;
  avg_session_duration: number;
  total_pages_viewed: number;
  avg_pages_viewed: number;
  conversion_rate: number;
  bounce_rate: number;
  cart_additions_total: number;
  cart_additions_avg: number;
  device_diversity: number;
  channel_diversity: number;
  review_count: number;
  avg_rating: number;
  low_rating_share: number;
  verified_review_share: number;
  helpful_votes_total: number;
  days_since_last_transaction: number;
  days_since_last_session: number;
  days_since_last_review: number;
  spend_category_clothing: number;
  spend_category_electronics: number;
  spend_category_food_grocery: number;
  spend_category_health: number;
  spend_category_jewelry: number;
  spend_category_office_supplies: number;
  spend_category_pet_supplies: number;
  spend_category_sports: number;
  gender: string;
  country: string;
  segment: string;
  top_category: string;
  top_brand: string;
  top_device: string;
  top_channel: string;
  review_text_all: string;
};

export type CustomerBehaviorResponse = {
  task: "customer_behavior";
  model?: ModelInfo;
  prediction: number;
  label: string;
  interpretation: string;
  churn_score?: number;
};

export type CustomerBehaviorCompareResult = {
  model_id: string;
  model_name: string;
  recommended: boolean;
  prediction: number;
  churn_score?: number;
};

export type CustomerBehaviorCompareResponse = {
  task: "customer_behavior";
  results: CustomerBehaviorCompareResult[];
  consensus: DiabetesConsensus;
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
  customer_behavior: {
    default_model: string;
    models: ModelOption[];
  };
};

export type HealthResponse = {
  status: "ok";
  models?: {
    diabetes: boolean;
    house: boolean;
    customer_behavior: boolean;
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

export function predictCustomerBehavior(payload: CustomerBehaviorRequest) {
  return requestJson<CustomerBehaviorResponse>("/api/customer-behavior", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function compareCustomerBehaviorModels(payload: CustomerBehaviorRequest) {
  const { model: _model, ...features } = payload;

  return requestJson<CustomerBehaviorCompareResponse>(
    "/api/customer-behavior/compare",
    {
      method: "POST",
      body: JSON.stringify(features),
    },
  );
}
