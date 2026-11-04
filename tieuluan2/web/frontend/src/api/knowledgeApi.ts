import { requestJson } from "./predictionApi.ts";

export type AgentDomain = "auto" | "medical" | "finance";

export type AgentCitation = {
  chunk_id: string;
  document_id: string;
};

export type AgentEvidence = AgentCitation & {
  text: string;
  score: number;
};

export type AgentResult = {
  answer: string;
  domain: "medical" | "finance" | null;
  citations: AgentCitation[];
  evidence: AgentEvidence[];
  route: {
    requested_domain: AgentDomain;
    selected_domain: "medical" | "finance" | null;
    tool: "medical_retriever" | "finance_retriever" | null;
  };
  graph_path: string[];
  abstained: boolean;
  abstention_reason: string | null;
  latency_ms: number;
  artifact_version: string | null;
  warning: string;
  request_id: string;
};

export function validateAgentQuestion(value: string): string {
  const question = value.trim().replace(/\s+/g, " ");
  if (question.length < 3) {
    throw new Error("Câu hỏi cần có ít nhất 3 ký tự.");
  }
  if (question.length > 500) {
    throw new Error("Câu hỏi không được vượt quá 500 ký tự.");
  }
  return question;
}

export function buildAgentPayload(question: string, domain: AgentDomain) {
  return { question: validateAgentQuestion(question), domain };
}

export function queryKnowledge(question: string, domain: AgentDomain) {
  return requestJson<AgentResult>("/api/agent/query", {
    method: "POST",
    body: JSON.stringify(buildAgentPayload(question, domain)),
  });
}
