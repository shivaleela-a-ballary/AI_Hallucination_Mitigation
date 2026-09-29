import React, { createContext, useContext, useEffect, useState, useCallback, type ReactNode } from "react";
import {
  api,
  type Evidence,
  type GraphResponse,
  type ForensicsAnalysis,
  type ClaimResult,
  type CheckAnswerClaim,
} from "./api";

export interface CanonicalVerification {
  id: string;
  query?: string;
  claim: string;
  answer?: string;
  verdict: string;
  verification_status: string;
  overall_verdict?: string;
  confidence: number;
  confidence_score: number;
  confidence_percentage?: number;
  risk_score: number; // strictly 0.0 to 1.0
  hallucination_risk_score?: number; // strictly 0 to 100
  hallucination_risk?: string;
  hallucination_risk_label?: string;
  evidence: Evidence[];
  sources: Evidence[];
  knowledge_graph?: GraphResponse;
  created_at?: string;
  analyzed_at?: string;
  forensics?: ForensicsAnalysis;
  risk_analysis?: {
    risk_score: number;
    hallucination_risk_score?: number;
    hallucination_risk_label?: string;
    evidence_quality?: string;
    source_agreement_ratio?: string;
    supporting_count?: number;
    contradicting_count?: number;
    uncertain_count?: number;
    explanation?: string;
    explanation_bullets?: string[];
  };
  before_after?: {
    original_text: string;
    corrected_text: string;
    original_stats?: Record<string, any>;
    corrected_stats?: Record<string, any>;
  };
  claims?: (ClaimResult | CheckAnswerClaim | any)[];
  why_flagged_list?: Array<{ icon: string; text: string }>;
  supporting_evidence?: Evidence[];
  contradicting_evidence?: Evidence[];
  uncertain_evidence?: Evidence[];
  explanation?: string;
  explanation_bullets?: string[];
  key_takeaway?: string;
  [key: string]: any;
}

const STORAGE_KEY = "canonical_verification";

/**
 * Normalizes any risk score to a float strictly between 0.0 and 1.0.
 * Handles integer percentages (e.g. 85 -> 0.85, 52 -> 0.52)
 * and already normalized values (e.g. 0.85 -> 0.85).
 */
export function normalizeRisk(score: number | null | undefined): number {
  if (score == null || isNaN(score)) return 0.50;
  let val = Number(score);
  if (val > 1.0) {
    val = val / 100;
  }
  return Math.min(1.0, Math.max(0.0, val));
}

/**
 * Returns a clean percentage string from 0% to 100% (e.g. "85%").
 */
export function formatRiskPercentage(score: number | null | undefined): string {
  const norm = normalizeRisk(score);
  return `${Math.round(norm * 100)}%`;
}

/**
 * Standardized risk tiers as requested:
 * LOW: 0% - 24%
 * MODERATE: 25% - 59%
 * HIGH: 60% - 100%
 */
export function getRiskTier(score: number | null | undefined): "low" | "moderate" | "high" {
  const norm = normalizeRisk(score);
  if (norm <= 0.24) return "low";
  if (norm <= 0.59) return "moderate";
  return "high";
}

/**
 * Clamps any percentage value strictly between 0 and 100.
 * Handles both 0.0 - 1.0 fractional values and 0 - 100 scales.
 */
export function clampPercentage(val: number | null | undefined): number {
  if (val == null || isNaN(val)) return 0;
  let num = Number(val);
  if (num > 0 && num <= 1.0) {
    num = num * 100;
  }
  return Math.min(100, Math.max(0, Math.round(num)));
}

/**
 * Converts any backend result (VerificationResponse, CheckAnswerResponse, history item)
 * into a single canonical verification structure.
 */
export function toCanonicalVerification(raw: any): CanonicalVerification | null {
  if (!raw) return null;
  const claimText = (raw.claim || raw.original_text || raw.query || raw.text || "").trim();
  if (!claimText && !raw.claims?.length) return null;

  const verdict = (raw.verdict || raw.verification_status || raw.overall_verdict || "UNVERIFIED").toUpperCase();
  const rawRisk = raw.risk_score ?? raw.hallucination_risk_score ?? (verdict === "REFUTED" ? 0.85 : verdict === "SUPPORTED" ? 0.12 : 0.50);
  const riskFloat = normalizeRisk(rawRisk);
  const confFloat = typeof raw.confidence === "number" ? raw.confidence : (typeof raw.confidence_score === "number" ? raw.confidence_score : 0.85);

  const sourcesList = Array.isArray(raw.sources) && raw.sources.length > 0
    ? raw.sources
    : (Array.isArray(raw.evidence) ? raw.evidence : []);

  const claimsList = Array.isArray(raw.claims) && raw.claims.length > 0
    ? raw.claims.map((c: any, i: number) => ({
        ...c,
        id: c.id ?? i + 1,
        claim: c.claim || claimText,
        status: (c.status || c.verdict || c.verification_status || verdict).toUpperCase(),
        verdict: (c.verdict || c.status || c.verification_status || verdict).toUpperCase(),
        verification_status: (c.verification_status || c.status || verdict).toUpperCase(),
        risk_score: normalizeRisk(c.risk_score ?? c.hallucination_risk_score ?? riskFloat),
        hallucination_risk_score: Math.round(normalizeRisk(c.risk_score ?? c.hallucination_risk_score ?? riskFloat) * 100),
        confidence_score: typeof c.confidence_score === "number" ? c.confidence_score : confFloat,
        forensics: c.forensics || raw.forensics,
        explanation: c.explanation || raw.explanation || "",
      }))
    : [
        {
          id: 1,
          claim: claimText,
          status: verdict,
          verdict: verdict,
          verification_status: verdict,
          risk_score: riskFloat,
          hallucination_risk_score: Math.round(riskFloat * 100),
          hallucination_risk_label: `${getRiskTier(riskFloat).charAt(0).toUpperCase() + getRiskTier(riskFloat).slice(1)} Risk`,
          confidence_score: confFloat,
          evidence_titles: sourcesList.map((s: any) => s.title || ""),
          evidence_score: confFloat,
          supporting_count: raw.supporting_count ?? (verdict === "SUPPORTED" ? 1 : 0),
          contradicting_count: raw.contradicting_count ?? (verdict === "REFUTED" ? 1 : 0),
          neutral_count: raw.neutral_count ?? 0,
          explanation: raw.explanation || "",
          forensics: raw.forensics,
        },
      ];

  const primaryClaim = claimsList[0]?.claim || claimText;

  // Ensure forensics has claim_text populated
  let forensicsObj = raw.forensics || claimsList[0]?.forensics;
  if (forensicsObj && !forensicsObj.claim_text) {
    forensicsObj = { ...forensicsObj, claim_text: primaryClaim };
  }

  const riskAnalysisObj = raw.risk_analysis || claimsList[0]?.risk_analysis || {
    risk_score: riskFloat,
    hallucination_risk_score: Math.round(riskFloat * 100),
    hallucination_risk_label: `${getRiskTier(riskFloat).charAt(0).toUpperCase() + getRiskTier(riskFloat).slice(1)} Risk`,
    evidence_quality: raw.evidence_quality || "MEDIUM",
    source_agreement_ratio: raw.source_agreement_ratio || `${sourcesList.length} / ${sourcesList.length}`,
    supporting_count: raw.supporting_count ?? (verdict === "SUPPORTED" ? 1 : 0),
    contradicting_count: raw.contradicting_count ?? (verdict === "REFUTED" ? 1 : 0),
    uncertain_count: raw.uncertain_count ?? 0,
    explanation: raw.explanation || (verdict === "REFUTED" ? "Claim contradicted by empirical literature." : "Claim evaluated against retrieved sources."),
    explanation_bullets: raw.explanation_bullets || [],
  };

  const beforeAfterObj = raw.before_after || {
    original_text: primaryClaim,
    corrected_text: raw.corrected_answer || primaryClaim,
    original_stats: {
      total_claims: claimsList.length,
      supported_count: raw.supported_claims_count ?? (verdict === "SUPPORTED" ? 1 : 0),
      refuted_count: raw.refuted_claims_count ?? (verdict === "REFUTED" ? 1 : 0),
      uncertain_count: raw.uncertain_claims_count ?? (verdict in { UNCERTAIN: 1, UNVERIFIED: 1 } ? 1 : 0),
      hallucination_rate: verdict === "REFUTED" ? 100 : 0,
      reliability_score: Math.round((1 - riskFloat) * 100),
      high_risk_claims: riskFloat >= 0.6 ? 1 : 0,
    },
    corrected_stats: {
      total_claims: claimsList.length,
      supported_count: claimsList.length,
      refuted_count: 0,
      uncertain_count: 0,
      hallucination_rate: 0,
      reliability_score: 96,
      high_risk_claims: 0,
    },
  };

  return {
    id: String(raw.id || raw._id || `verify-${Date.now()}`),
    query: raw.query || primaryClaim,
    claim: primaryClaim,
    answer: raw.answer || raw.corrected_answer || (primaryClaim ? `Verification for: ${primaryClaim}` : ""),
    verdict,
    verification_status: verdict,
    overall_verdict: verdict,
    confidence: confFloat,
    confidence_score: confFloat,
    confidence_percentage: Math.round(confFloat * 100),
    risk_score: riskFloat,
    hallucination_risk_score: Math.round(riskFloat * 100),
    hallucination_risk: raw.hallucination_risk || getRiskTier(riskFloat).toUpperCase(),
    hallucination_risk_label: raw.hallucination_risk_label || `${getRiskTier(riskFloat).charAt(0).toUpperCase() + getRiskTier(riskFloat).slice(1)} Risk`,
    evidence: sourcesList,
    sources: sourcesList,
    knowledge_graph: raw.knowledge_graph || { nodes: [], edges: [] },
    created_at: raw.created_at || new Date().toISOString(),
    analyzed_at: raw.analyzed_at || new Date().toLocaleString(),
    forensics: forensicsObj,
    risk_analysis: riskAnalysisObj,
    before_after: beforeAfterObj,
    claims: claimsList,
    why_flagged_list: raw.why_flagged_list || [],
    supporting_evidence: raw.supporting_evidence || [],
    contradicting_evidence: raw.contradicting_evidence || [],
    uncertain_evidence: raw.uncertain_evidence || [],
    explanation: raw.explanation || "",
    explanation_bullets: raw.explanation_bullets || [],
    key_takeaway: raw.key_takeaway || "",
  };
}

interface VerificationContextValue {
  currentVerification: CanonicalVerification | null;
  setVerification: (raw: any) => void;
  clearVerification: () => void;
  isLoading: boolean;
  refreshCurrentVerification: () => Promise<CanonicalVerification | null>;
}

const VerificationContext = createContext<VerificationContextValue>({
  currentVerification: null,
  setVerification: () => {},
  clearVerification: () => {},
  isLoading: false,
  refreshCurrentVerification: async () => null,
});

export function VerificationProvider({ children }: { children: ReactNode }) {
  const [currentVerification, setCurrentVerificationState] = useState<CanonicalVerification | null>(() => {
    if (typeof window !== "undefined" && typeof localStorage !== "undefined") {
      try {
        const stored = localStorage.getItem(STORAGE_KEY);
        if (stored) {
          return toCanonicalVerification(JSON.parse(stored));
        }
      } catch (e) {
        console.error("Failed to parse stored verification:", e);
      }
    }
    return null;
  });

  const [isLoading, setIsLoading] = useState(false);

  const setVerification = useCallback((raw: any) => {
    const canonical = toCanonicalVerification(raw);
    setCurrentVerificationState(canonical);
    if (typeof window !== "undefined" && typeof localStorage !== "undefined") {
      if (canonical) {
        try {
          localStorage.setItem(STORAGE_KEY, JSON.stringify(canonical));
          if (canonical.knowledge_graph) {
            sessionStorage.setItem("latest-verification-graph", JSON.stringify(canonical.knowledge_graph));
          }
        } catch (e) {
          console.error("Failed to persist verification to storage:", e);
        }
      } else {
        localStorage.removeItem(STORAGE_KEY);
      }
    }
  }, []);

  const clearVerification = useCallback(() => {
    setCurrentVerificationState(null);
    if (typeof window !== "undefined" && typeof localStorage !== "undefined") {
      localStorage.removeItem(STORAGE_KEY);
      sessionStorage.removeItem("latest-verification-graph");
    }
  }, []);

  const refreshCurrentVerification = useCallback(async () => {
    try {
      setIsLoading(true);
      const backendRecord = await api.currentVerification().catch(() => null);
      if (backendRecord) {
        const canonical = toCanonicalVerification(backendRecord);
        if (canonical) {
          setVerification(canonical);
          return canonical;
        }
      }
    } catch {
      // Backend might have no verification
    } finally {
      setIsLoading(false);
    }
    return currentVerification;
  }, [currentVerification, setVerification]);

  // Synchronize with backend on mount if not in localStorage
  useEffect(() => {
    if (!currentVerification) {
      void refreshCurrentVerification();
    }
  }, []);

  return (
    <VerificationContext.Provider
      value={{
        currentVerification,
        setVerification,
        clearVerification,
        isLoading,
        refreshCurrentVerification,
      }}
    >
      {children}
    </VerificationContext.Provider>
  );
}

export function useVerification() {
  const context = useContext(VerificationContext);
  if (!context) {
    throw new Error("useVerification must be used within a VerificationProvider");
  }
  return context;
}
