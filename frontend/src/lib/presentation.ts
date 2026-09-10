import type { AnswerRecord, ClaimResult, Evidence, Verification, VerificationResult } from "./api";

export function resultFor(status: string): VerificationResult {
  if (status === "SUPPORTED") return "supported";
  if (status === "REFUTED") return "refuted";
  return "not-enough-info";
}

export function statusExplanation(status: string): string {
  if (status === "SUPPORTED") return "The available verification evidence supports the claim.";
  if (status === "REFUTED") return "The available verification evidence contradicts the claim.";
  return "The available evidence was insufficient for verification.";
}

export function confidenceLabel(record: Pick<AnswerRecord, "confidence_score" | "confidence_available">): string {
  if (!record.confidence_available || !(record.confidence_score > 0)) return "Not available";
  return `${(record.confidence_score * 100).toFixed(1)}%`;
}

export function answerParagraphs(answer: string): string[] {
  const normalized = answer.replace(/\s+/g, " ").trim();
  if (!normalized) return [];
  return normalized.split(/(?<=[.!?])\s+(?=[A-Z])/).reduce<string[]>((paragraphs, sentence) => {
    const current = paragraphs.at(-1);
    if (current && current.length < 360) paragraphs[paragraphs.length - 1] = `${current} ${sentence}`;
    else paragraphs.push(sentence);
    return paragraphs;
  }, []);
}

export function shortExcerpt(content: string, length = 360): string {
  const normalized = content.replace(/\s+/g, " ").trim();
  return normalized.length > length ? `${normalized.slice(0, length).trimEnd()}...` : normalized;
}

export function sourceKey(source: Evidence): string {
  return `${source.source}:${source.title}`;
}

export function claimStatus(result: ClaimResult): VerificationResult {
  return resultFor(result.status);
}

export function mapHistoryRecord(item: AnswerRecord): Verification {
  const date = item.created_at ? new Date(item.created_at) : new Date();
  const sources = item.sources || item.evidence || [];
  const answerText = item.answer || (item as unknown as { response?: string }).response || "";
  const queryText = item.query || (item as unknown as { user_query?: string }).user_query || (item as unknown as { original_text?: string }).original_text || "";
  const confidence = item.confidence_score ?? (item as unknown as { confidence?: number }).confidence ?? 0;
  return {
    id: item.id || (item as unknown as { _id?: string })._id || String(Math.random()),
    type: "question",
    text: queryText,
    result: resultFor(item.verification_status),
    confidence: confidence,
    date: date.toLocaleDateString(),
    time: date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    answerPreview: answerText,
    sourceCount: sources.length,
    confidenceAvailable: Boolean(item.confidence_available ?? confidence > 0),
  };
}
