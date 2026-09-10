export type VerificationResult = "supported" | "refuted" | "not-enough-info";

export type Evidence = {
  title: string;
  content: string;
  source: string;
  similarity_score: number;
  url?: string | null;
  doi?: string | null;
  pmid?: string | null;
  authors?: string[];
  publication_date?: string | null;
  source_type?: string;
  relationship?: string;
  stance_score?: number;
  reliability_score?: number;
};

export type ClaimResult = {
  claim: string;
  status: string;
  verdict?: string;
  claim_type?: string;
  importance?: string;
  evidence_titles: string[];
  evidence_score: number;
  method: string;
  hallucination_risk_score?: number;
  hallucination_risk_label?: string;
  supporting_count?: number;
  contradicting_count?: number;
  neutral_count?: number;
  unverified_count?: number;
  evidence_summary?: string;
  explanation?: string;
  key_takeaway?: string;
};

export type GraphNode = {
  id: string;
  label?: string;
  kind?: string;
  description?: string;
  source?: string;
  [key: string]: unknown;
};

export type GraphEdge = {
  source: string;
  target: string;
  predicate?: string;
  relationship?: string;
  source_document?: string;
  source_title?: string;
  [key: string]: unknown;
};

export type GraphResponse = {
  nodes: GraphNode[];
  edges: GraphEdge[];
};

export type AnswerRecord = {
  id: string;
  query: string;
  answer: string;
  verification_status: string;
  confidence_score: number;
  confidence_available?: boolean;
  confidence_percentage?: number;
  hallucination_risk?: string;
  hallucination_risk_score?: number;
  hallucination_risk_label?: string;
  sources: Evidence[];
  evidence: Evidence[];
  supporting_evidence?: Evidence[];
  contradicting_evidence?: Evidence[];
  uncertain_evidence?: Evidence[];
  claims: ClaimResult[];
  confidence_explanation: string;
  created_at: string;
  knowledge_graph?: GraphResponse;
};

export type VerificationResponse = {
  id?: string;
  claim: string;
  verification_status: string;
  overall_verdict?: string;
  prediction?: string | null;
  confidence_score: number;
  confidence_percentage?: number;
  confidence_available: boolean;
  probabilities?: Record<string, number> | null;
  hallucination_risk_score?: number;
  hallucination_risk_label?: string;
  source_reliability_score?: number;
  source_reliability_label?: string;
  contradiction_status?: string;
  contradictions_subtext?: string;
  supporting_count?: number;
  contradicting_count?: number;
  neutral_count?: number;
  unverified_count?: number;
  key_takeaway?: string;
  evidence: Evidence[];
  supporting_evidence?: Evidence[];
  contradicting_evidence?: Evidence[];
  uncertain_evidence?: Evidence[];
  claims: ClaimResult[];
  confidence_explanation: string;
  explanation?: string;
  explanation_bullets?: string[];
  knowledge_graph: GraphResponse;
};

export type Verification = {
  id: string;
  type: "claim" | "question";
  text: string;
  result: VerificationResult;
  confidence: number;
  date: string;
  time: string;
  answerPreview: string;
  sourceCount: number;
  confidenceAvailable: boolean;
};

export type HealthResponse = {
  status: string;
  service?: string;
  version?: string;
  scifact_corpus_available?: boolean;
  scifact_model_available?: boolean;
  faiss_index_available?: boolean;
  mongodb_connected?: boolean;
  mongodb_mode?: string;
  database_name?: string;
  pubmed_available?: boolean;
  wikipedia_available?: boolean;
  subsystems?: Record<string, string>;
  stats?: {
    connected: boolean;
    storage_mode: string;
    database_name: string;
    users_count: number;
    history_count: number;
    settings_count: number;
  };
};

export type DocumentChunk = {
  title?: string;
  text?: string;
  content?: string;
  chunk_id?: number;
};

export type UploadedDocument = {
  id: string;
  filename: string;
  title: string;
  file_size: number;
  file_type: string;
  char_count?: number;
  chunk_count?: number;
  chunks?: DocumentChunk[];
  raw_text_preview?: string;
  user_id?: string | null;
  user_name?: string;
  created_at?: string;
};

export type ForensicsPattern = {
  pattern_type: string;
  description: string;
  explanation: string;
  severity: "low" | "medium" | "high" | "critical";
  linguistic_cues: string[];
  suggested_fix?: string;
};

export type ForensicsAnalysis = {
  claim_id?: string;
  claim_text: string;
  pattern_type: string;
  severity: "low" | "medium" | "high" | "critical";
  explanation: string;
  linguistic_cues: string[];
  suggested_fix?: string;
  detected_patterns: ForensicsPattern[];
};

export type VerifiedCorrection = {
  original_claim: string;
  candidate_correction: string;
  verified: boolean;
  verification_status: string;
  confidence_score: number;
  evidence_basis: string[];
  risk_reduction_pct: number;
};

export type CheckAnswerClaim = {
  claim: string;
  claim_type?: string;
  importance?: string;
  verification_status: string;
  confidence_score: number;
  hallucination_risk: string;
  risk_score?: number;
  evidence_count: number;
  supporting_evidence: Evidence[];
  contradicting_evidence: Evidence[];
  explanation: string;
  forensics?: ForensicsAnalysis | null;
  correction?: VerifiedCorrection | null;
  evidence_sources?: Evidence[];
};

export type BeforeAfterComparison = {
  original_text: string;
  corrected_text: string;
  original_risk_score: number;
  mitigated_risk_score: number;
  risk_reduction_percentage: number;
  claims_repaired: number;
  total_claims: number;
  evidence_grounding_score: number;
};

export type EvidenceQualityMetrics = {
  sources_consulted: number;
  high_relevance_sources: number;
  empirical_proof_available: boolean;
  evidence_sufficiency: string;
};

export type CheckAnswerResponse = {
  id?: string;
  created_at?: string;
  original_text: string;
  overall_reliability_score: number;
  overall_hallucination_risk: string;
  total_claims: number;
  supported_claims_count: number;
  refuted_claims_count: number;
  uncertain_claims_count: number;
  unverified_claims_count?: number;
  claims: CheckAnswerClaim[];
  summary: string;
  corrected_answer?: string;
  before_after?: BeforeAfterComparison | null;
  evidence_quality_metrics?: EvidenceQualityMetrics | null;
};

export type PaperAuditClaim = {
  id?: string;
  section: string;
  claim_text: string;
  verification_status: string;
  confidence_score: number;
  risk_score: number;
  has_citation: boolean;
  citation_keys: string[];
  evidence_available: boolean;
  notes?: string;
};

export type PaperAuditResponse = {
  paper_title: string;
  total_sections: number;
  sections_analyzed: string[];
  total_claims: number;
  supported_claims: number;
  refuted_claims: number;
  unsupported_claims: number;
  hallucination_risk_score: number;
  hallucination_risk_label: string;
  claims: PaperAuditClaim[];
  citations_found: string[];
  unsupported_claim_count: number;
  summary: string;
};

export type DashboardStats = {
  total_verifications: number;
  total_claims: number;
  supported_claims: number;
  refuted_claims: number;
  uncertain_claims: number;
  hallucination_rate: number;
  avg_confidence: number;
  risk_distribution: {
    low: number;
    moderate: number;
    high: number;
  };
  top_patterns: { pattern: string; count: number }[];
  source_distribution: Record<string, number>;
  recent_verifications: AnswerRecord[];
};

export type SourceRecord = {
  id: string;
  title: string;
  source_type: string;
  url: string;
  snippets: string[];
  verification_count: number;
  acceptance_status: string;
  avg_similarity: number;
  latest_used_at: string;
  referenced_in_records: string[];
};

export type UserSummary = {
  id: string;
  username: string;
  email: string;
  full_name?: string;
  role?: string;
  created_at?: string;
};

export type TokenResponse = {
  access_token: string;
  token_type: string;
  expires_in: number;
  user: UserSummary;
};

export type UserSettings = {
  id?: string;
  user_id?: string;
  theme: string;
  default_min_similarity: number;
  default_top_k: number;
  preferred_model: string;
  auto_save_history: boolean;
  email_notifications?: boolean;
  updated_at?: string;
};

export type UserProfileResponse = {
  user: UserSummary;
  settings?: UserSettings | null;
};

const apiBaseUrl =
  (import.meta.env.VITE_API_BASE_URL as string | undefined)?.replace(/\/$/, "") ??
  "http://127.0.0.1:8000/api";

function getAuthHeaders(): Record<string, string> {
  if (typeof window !== "undefined" && typeof localStorage !== "undefined") {
    const token = localStorage.getItem("auth_token");
    if (token) {
      return { Authorization: `Bearer ${token}` };
    }
  }
  return {};
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...getAuthHeaders(),
    ...((init?.headers as Record<string, string>) || {}),
  };

  const response = await fetch(`${apiBaseUrl}${path}`, {
    ...init,
    headers,
  });
  const body = await response.json().catch(() => null);
  if (!response.ok) {
    const errorDetail = body?.detail || body?.message || "Request failed.";
    throw new Error(typeof errorDetail === "string" ? errorDetail : JSON.stringify(errorDetail));
  }
  return body as T;
}

async function requestFormData<T>(path: string, init?: RequestInit): Promise<T> {
  const headers: Record<string, string> = {
    ...getAuthHeaders(),
    ...((init?.headers as Record<string, string>) || {}),
  };

  const response = await fetch(`${apiBaseUrl}${path}`, {
    ...init,
    headers,
  });
  const body = await response.json().catch(() => null);
  if (!response.ok) {
    const errorDetail = body?.detail || body?.message || "Request failed.";
    throw new Error(typeof errorDetail === "string" ? errorDetail : JSON.stringify(errorDetail));
  }
  return body as T;
}

export const api = {
  ask: (question: string) =>
    request<AnswerRecord>("/chat", { method: "POST", body: JSON.stringify({ question }) }),

  history: () => request<{ history: AnswerRecord[] }>("/history"),

  answer: (id: string) => request<AnswerRecord>(`/history/${encodeURIComponent(id)}`),

  deleteHistoryItem: (id: string) =>
    request<{ message: string; id: string }>(`/history/${encodeURIComponent(id)}`, {
      method: "DELETE",
    }),

  clearHistory: () =>
    request<{ message: string; deleted_count: number }>("/history", {
      method: "DELETE",
    }),

  verify: (claim: string, evidence?: string) =>
    request<VerificationResponse>("/verify", {
      method: "POST",
      body: JSON.stringify({ claim, evidence: evidence || "" }),
    }),

  checkAnswer: (
    text: string,
    options?: { document_id?: string; document_content?: string }
  ) =>
    request<CheckAnswerResponse>("/check-answer", {
      method: "POST",
      body: JSON.stringify({
        text,
        document_id: options?.document_id,
        document_content: options?.document_content,
      }),
    }),

  auditPaper: async (file: File) => {
    const formData = new FormData();
    formData.append("file", file);
    return requestFormData<PaperAuditResponse>("/paper-auditor/audit", {
      method: "POST",
      body: formData,
    });
  },

  auditPaperText: (title: string, text: string) =>
    request<PaperAuditResponse>("/paper-auditor/audit-text", {
      method: "POST",
      body: JSON.stringify({ title, text }),
    }),

  getDashboardStats: () => request<DashboardStats>("/dashboard/stats"),

  getSources: () => request<{ sources: SourceRecord[]; total_sources: number }>("/sources"),

  graph: (answerId?: string) =>
    request<GraphResponse>(
      answerId ? `/graph/${encodeURIComponent(answerId)}` : "/graph/latest"
    ),

  health: () => request<HealthResponse>("/health"),

  // Uploads & Document Ingestion
  getUploads: () => request<{ total: number; documents: UploadedDocument[] }>("/uploads"),

  getUpload: (id: string) =>
    request<UploadedDocument>(`/uploads/${encodeURIComponent(id)}`),

  deleteUpload: (id: string) =>
    request<{ message: string; id: string }>(`/uploads/${encodeURIComponent(id)}`, {
      method: "DELETE",
    }),

  uploadFile: async (file: File, title?: string) => {
    const formData = new FormData();
    formData.append("file", file);
    if (title) formData.append("title", title);
    return requestFormData<{ message: string; document: UploadedDocument }>("/uploads/file", {
      method: "POST",
      body: formData,
    });
  },

  uploadText: (title: string, content: string, sourceName?: string) =>
    request<{ message: string; document: UploadedDocument }>("/uploads/text", {
      method: "POST",
      body: JSON.stringify({
        title,
        content,
        source_name: sourceName || "Custom Document",
      }),
    }),

  // User Endpoints
  user: {
    profile: () => request<UserProfileResponse>("/user/profile"),

    updateProfile: (data: { full_name?: string; bio?: string; avatar_url?: string }) =>
      request<UserProfileResponse>("/user/profile", {
        method: "PUT",
        body: JSON.stringify(data),
      }),

    settings: () => request<UserSettings>("/user/settings"),

    updateSettings: (data: Partial<UserSettings>) =>
      request<UserSettings>("/user/settings", {
        method: "PUT",
        body: JSON.stringify(data),
      }),

    history: (limit?: number) =>
      request<{ history: AnswerRecord[]; count: number }>(
        `/user/history${limit ? `?limit=${limit}` : ""}`
      ),

    deleteHistoryItem: (id: string) =>
      request<{ message: string; id: string }>(`/user/history/${encodeURIComponent(id)}`, {
        method: "DELETE",
      }),

    clearHistory: () =>
      request<{ message: string; deleted_count: number }>("/user/history", {
        method: "DELETE",
      }),
  },

  // Auth Endpoints
  auth: {
    login: (username: string, password: string) =>
      request<TokenResponse>("/auth/login", {
        method: "POST",
        body: JSON.stringify({ username, password }),
      }),

    register: (data: {
      username: string;
      email: string;
      password: string;
      full_name?: string;
    }) =>
      request<TokenResponse>("/auth/register", {
        method: "POST",
        body: JSON.stringify(data),
      }),

    me: () => request<UserProfileResponse>("/auth/me"),

    logout: () =>
      request<{ message: string; status: string }>("/auth/logout", {
        method: "POST",
      }),
  },
};

export function toResult(status: string): VerificationResult {
  const s = status.toUpperCase();
  if (s === "SUPPORTED") return "supported";
  if (s === "REFUTED") return "refuted";
  return "not-enough-info";
}
