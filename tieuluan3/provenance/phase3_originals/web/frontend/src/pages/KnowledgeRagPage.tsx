import { FormEvent, useState } from "react";
import {
  AgentDomain,
  AgentResult,
  queryKnowledge,
  validateAgentQuestion,
} from "../api/knowledgeApi";
import ErrorMessage from "../components/ErrorMessage";
import LoadingState from "../components/LoadingState";

const samples: Record<Exclude<AgentDomain, "auto">, string> = {
  medical: "What are common complications of diabetes?",
  finance: "What was the change in revenue and operating expense?",
};

const abstentionLabels: Record<string, string> = {
  out_of_domain: "Câu hỏi nằm ngoài hai corpus đã khóa.",
  prompt_injection: "Yêu cầu cố thay đổi chỉ dẫn hệ thống nên đã bị từ chối.",
  medical_safety: "Agent không đưa chẩn đoán, liều dùng hoặc chỉ định cá nhân.",
  financial_safety: "Agent không đưa khuyến nghị mua bán hay dự báo thị trường.",
  guardrail: "Câu hỏi vi phạm guardrail của lớp trả lời.",
  insufficient_evidence: "Không tìm thấy bằng chứng đủ mạnh để trả lời.",
};

export default function KnowledgeRagPage() {
  const [domain, setDomain] = useState<AgentDomain>("auto");
  const [question, setQuestion] = useState("");
  const [result, setResult] = useState<AgentResult | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setResult(null);
    let cleanQuestion: string;
    try {
      cleanQuestion = validateAgentQuestion(question);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Câu hỏi không hợp lệ.");
      return;
    }
    setBusy(true);
    try {
      setResult(await queryKnowledge(cleanQuestion, domain));
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Không thể truy vấn KG-RAG.");
    } finally {
      setBusy(false);
    }
  }

  function useSample(nextDomain: Exclude<AgentDomain, "auto">) {
    setDomain(nextDomain);
    setQuestion(samples[nextDomain]);
    setResult(null);
    setError("");
  }

  return (
    <section className="rag-page">
      <div className="rag-hero">
        <div>
          <p className="eyebrow">Chương 5 · Knowledge Graph + RAG</p>
          <h1>Hỏi corpus. Xem đường đi của bằng chứng.</h1>
          <p>
            Agent định tuyến vào đúng miền, hợp nhất BM25, LSA và graph expansion,
            rồi chỉ trả lời khi có đoạn trích truy vết được.
          </p>
        </div>
        <aside className="rag-lock-card" aria-label="Cấu hình KG-RAG đã khóa">
          <span className="lock-mark" aria-hidden="true">B4</span>
          <div>
            <strong>Runtime đã khóa</strong>
            <p>2-hop · RRF 0,6 / 0,1 / 0,3</p>
          </div>
        </aside>
      </div>

      <div className="rag-workbench">
        <form className="rag-query-panel" onSubmit={submit}>
          <div className="panel-heading">
            <div>
              <span className="step-label">01 / Route</span>
              <h2>Đặt câu hỏi</h2>
            </div>
            <span className="rag-limit">{question.length}/500</span>
          </div>

          <div className="domain-switch" role="radiogroup" aria-label="Chọn miền dữ liệu">
            {(["auto", "medical", "finance"] as AgentDomain[]).map((value) => (
              <button
                key={value}
                type="button"
                role="radio"
                aria-checked={domain === value}
                className={domain === value ? "active" : ""}
                onClick={() => setDomain(value)}
              >
                {value === "auto" ? "Tự định tuyến" : value === "medical" ? "Medical" : "Finance"}
              </button>
            ))}
          </div>

          <label className="rag-question-field" htmlFor="rag-question">
            <span>Câu hỏi cho corpus</span>
            <textarea
              id="rag-question"
              value={question}
              maxLength={500}
              onChange={(event) => setQuestion(event.target.value)}
              placeholder="Ví dụ: What are common complications of diabetes?"
            />
          </label>

          <div className="sample-row" aria-label="Câu hỏi mẫu">
            <span>Mẫu nhanh</span>
            <button type="button" onClick={() => useSample("medical")}>Diabetes</button>
            <button type="button" onClick={() => useSample("finance")}>Revenue</button>
          </div>

          {error && <ErrorMessage message={error} />}

          <button className="primary-button rag-submit" type="submit" disabled={busy}>
            {busy ? "Đang truy xuất bằng chứng…" : "Chạy Agent KG-RAG"}
          </button>

          <p className="rag-policy-note">
            Không dùng API key. Không chẩn đoán y khoa, không khuyến nghị đầu tư và không thực thi code từ câu hỏi.
          </p>
        </form>

        <section className="rag-result-panel" aria-live="polite">
          {busy && <LoadingState />}
          {!busy && !result && (
            <div className="rag-empty-state">
              <span>02 / Evidence</span>
              <h2>Câu trả lời có nguồn sẽ xuất hiện tại đây.</h2>
              <p>Route, citation, graph path và artifact version luôn đi cùng kết quả.</p>
            </div>
          )}
          {!busy && result && (
            <>
              <div className="rag-result-meta">
                <span className={`domain-badge ${result.domain ?? "unknown"}`}>
                  {result.domain ?? "out of domain"}
                </span>
                <span>{result.route.tool ?? "no tool"}</span>
                <span>{result.latency_ms.toFixed(1)} ms</span>
              </div>

              <div className={`rag-answer ${result.abstained ? "abstained" : ""}`}>
                <p className="step-label">03 / Grounded answer</p>
                <h2>{result.abstained ? "Agent đã từ chối trả lời" : "Trả lời từ evidence"}</h2>
                <p>
                  {result.abstained
                    ? abstentionLabels[result.abstention_reason ?? ""] ?? "Không đủ bằng chứng phù hợp."
                    : result.answer}
                </p>
              </div>

              {result.graph_path.length > 0 && (
                <div className="graph-trace" aria-label="Đường đi Knowledge Graph">
                  <div className="result-section-heading">
                    <span>Graph path</span>
                    <small>{result.graph_path.length - 1} bước</small>
                  </div>
                  <ol>
                    {result.graph_path.map((node, index) => (
                      <li key={`${node}-${index}`}><span>{index + 1}</span><code>{node}</code></li>
                    ))}
                  </ol>
                </div>
              )}

              <div className="citation-block">
                <div className="result-section-heading">
                  <span>Citations</span>
                  <small>{result.citations.length} nguồn</small>
                </div>
                <div className="citation-list">
                  {result.citations.length === 0 && <p>Không phát citation khi Agent từ chối.</p>}
                  {result.citations.map((citation) => (
                    <code key={citation.chunk_id}>{citation.chunk_id}</code>
                  ))}
                </div>
              </div>

              {result.evidence.length > 0 && (
                <div className="evidence-stack">
                  <div className="result-section-heading">
                    <span>Evidence drawer</span>
                    <small>Top {result.evidence.length}</small>
                  </div>
                  {result.evidence.map((item, index) => (
                    <details key={item.chunk_id} open={index === 0}>
                      <summary>
                        <span>{String(index + 1).padStart(2, "0")}</span>
                        <code>{item.chunk_id}</code>
                        <b>{item.score.toFixed(4)}</b>
                      </summary>
                      <p>{item.text}</p>
                      <small>Document: {item.document_id}</small>
                    </details>
                  ))}
                </div>
              )}

              <div className="rag-result-footer">
                <span>{result.warning}</span>
                <code>{result.artifact_version}</code>
              </div>
            </>
          )}
        </section>
      </div>
    </section>
  );
}
