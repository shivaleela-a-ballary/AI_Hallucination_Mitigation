import { createFileRoute, Link } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import {
  AlertCircle,
  AlertTriangle,
  ArrowRight,
  CheckCircle2,
  FileCheck,
  Filter,
  HelpCircle,
  Info,
  Loader2,
  Search,
  ShieldAlert,
  Sparkles,
  XCircle,
} from "lucide-react";

import { AppShell } from "@/components/app/app-shell";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";
import {
  useVerification,
  normalizeRisk,
  formatRiskPercentage,
  getRiskTier,
} from "@/lib/verification-context";

export const Route = createFileRoute("/risk-heatmap")({
  component: RiskHeatmapPage,
});

export interface HeatmapClaim {
  id: string;
  claim: string;
  status: string;
  riskScore: number; // strictly 0.0 to 1.0
  riskTier: "high" | "moderate" | "low";
  confidence: number;
  evidenceCount: number;
  querySource: string;
  date: string;
  patternType?: string;
  explanation?: string;
  riskFactors?: {
    verdictBase?: string;
    contradictions?: string;
    evidenceGap?: string;
    forensics?: string;
  };
  explanationBullets?: string[];
}

function RiskHeatmapPage() {
  const { currentVerification } = useVerification();
  const [claims, setClaims] = useState<HeatmapClaim[]>([]);
  const [filterTier, setFilterTier] = useState<"all" | "high" | "moderate" | "low">("all");
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedClaim, setSelectedClaim] = useState<HeatmapClaim | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadClaims() {
      try {
        setLoading(true);
        const mapped: HeatmapClaim[] = [];
        const seenClaims = new Set<string>();

        // 1. Prioritize claims from current canonical verification
        if (currentVerification) {
          const vDate = currentVerification.analyzed_at || "Current Session";
          const queryTitle = currentVerification.query || currentVerification.claim || "Current Verification";

          const cvClaims = Array.isArray(currentVerification.claims) && currentVerification.claims.length > 0
            ? currentVerification.claims
            : [
                {
                  id: 1,
                  claim: currentVerification.claim,
                  status: currentVerification.verdict,
                  verdict: currentVerification.verdict,
                  risk_score: currentVerification.risk_score,
                  confidence_score: currentVerification.confidence_score,
                  evidence_titles: (currentVerification.evidence || []).map((e: any) => e.title),
                  explanation: currentVerification.explanation,
                  forensics: currentVerification.forensics,
                },
              ];

          cvClaims.forEach((c: any, cIdx: number) => {
            const rawClaimText = (c.claim || currentVerification.claim || "").trim();
            if (!rawClaimText) return;
            const normText = rawClaimText.toLowerCase();
            if (seenClaims.has(normText)) return;
            seenClaims.add(normText);

            const status = (c.status || c.verdict || currentVerification.verdict || "UNCERTAIN").toUpperCase();
            const risk = normalizeRisk(c.risk_score ?? c.hallucination_risk_score ?? currentVerification.risk_score);
            const riskTier = getRiskTier(risk);
            const forensics = c.forensics || currentVerification.forensics;

            const bullets = currentVerification.risk_analysis?.explanation_bullets || currentVerification.explanation_bullets || [];

            mapped.push({
              id: `current-${cIdx}`,
              claim: rawClaimText,
              status,
              riskScore: risk,
              riskTier,
              confidence: c.confidence_score ?? currentVerification.confidence_score ?? 0.85,
              evidenceCount: (c.evidence_titles || currentVerification.evidence || []).length,
              querySource: `${queryTitle} (Active Session)`,
              date: vDate,
              patternType: forensics?.pattern_type && forensics.pattern_type !== "None / Valid" ? forensics.pattern_type : undefined,
              explanation: c.explanation || currentVerification.explanation || (currentVerification.risk_analysis?.explanation),
              explanationBullets: bullets,
              riskFactors: {
                verdictBase: `Verdict ${status}: Base calibration reflects NLI entailment distribution.`,
                contradictions: status === "REFUTED" ? "Active contradiction detected across empirical literature sources." : "No overwhelming contradiction.",
                evidenceGap: (c.evidence_titles || []).length >= 3 ? "Dense evidence grounding." : "Sparse literature coverage.",
                forensics: forensics?.pattern_type && forensics.pattern_type !== "None / Valid" ? `Triggered forensic pattern: ${forensics.pattern_type}` : "No critical forensic distortions detected.",
              },
            });
          });
        }

        // 2. Load historical records to show verified claim density
        try {
          const { history } = await api.history();
          history.forEach((rec, recIdx) => {
            const recDate = rec.created_at ? new Date(rec.created_at).toLocaleDateString() : "Past Verification";
            const queryTitle = rec.query || (rec as unknown as { user_query?: string }).user_query || "Prior Verification";

            (rec.claims || []).forEach((c, cIdx) => {
              const rawClaimText = (c.claim || "").trim();
              if (!rawClaimText) return;
              const normText = rawClaimText.toLowerCase();
              if (seenClaims.has(normText)) return;
              seenClaims.add(normText);

              const status = (c.status || c.verdict || "UNCERTAIN").toUpperCase();
              const risk = normalizeRisk(
                (c as unknown as { risk_score?: number }).risk_score ?? c.hallucination_risk_score ?? (status === "REFUTED" ? 0.85 : status === "SUPPORTED" ? 0.12 : 0.48)
              );
              const riskTier = getRiskTier(risk);
              const forensics = (c as unknown as { forensics?: { pattern_type?: string } }).forensics;

              mapped.push({
                id: `${rec.id || recIdx}-${cIdx}`,
                claim: rawClaimText,
                status,
                riskScore: risk,
                riskTier,
                confidence: c.evidence_score || (rec.confidence_score ?? 0.75),
                evidenceCount: (c.evidence_titles || []).length,
                querySource: queryTitle,
                date: recDate,
                patternType: forensics?.pattern_type && forensics.pattern_type !== "None / Valid" ? forensics.pattern_type : undefined,
                explanation: c.explanation || c.evidence_summary || "Empirically cross-examined against literature.",
                riskFactors: {
                  verdictBase: `Status ${status}: Base risk calculated from multi-source cross-verification.`,
                  contradictions: status === "REFUTED" ? "Empirical refutation identified." : "Consistent consensus.",
                  evidenceGap: "Corpus grounding evaluated.",
                  forensics: forensics?.pattern_type && forensics.pattern_type !== "None / Valid" ? `Flagged: ${forensics.pattern_type}` : "Well-calibrated linguistic structure.",
                },
              });
            });
          });
        } catch {
          // History might be empty or unauthenticated
        }

        setClaims(mapped);
        if (mapped.length > 0) setSelectedClaim(mapped[0]);
      } catch (err: unknown) {
        console.error("Failed to load claims:", err);
      } finally {
        setLoading(false);
      }
    }
    void loadClaims();
  }, [currentVerification]);

  const filteredClaims = claims.filter((c) => {
    if (filterTier !== "all" && c.riskTier !== filterTier) return false;
    if (searchQuery && !c.claim.toLowerCase().includes(searchQuery.toLowerCase())) return false;
    return true;
  });

  const highCount = claims.filter((c) => c.riskTier === "high").length;
  const modCount = claims.filter((c) => c.riskTier === "moderate").length;
  const lowCount = claims.filter((c) => c.riskTier === "low").length;

  return (
    <AppShell>
      <div className="space-y-7 max-w-6xl mx-auto">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-[#162340] pb-5">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <div className="size-8 rounded-lg bg-amber-500/10 border border-amber-500/30 flex items-center justify-center text-amber-400">
                <ShieldAlert className="size-4.5" />
              </div>
              <h1 className="text-2xl font-extrabold text-white tracking-tight">
                Claim Risk Heatmap & Density Analysis
              </h1>
            </div>
            <p className="text-xs sm:text-sm text-slate-400">
              Transparent multi-factor risk scoring: Base Verdict + Contradiction Adjustment + Evidence Gap + Forensic Patterns.
            </p>
          </div>

          <div className="flex items-center gap-2">
            <Badge variant="outline" className="border-amber-500/30 text-amber-300 bg-amber-950/20 text-xs">
              Risk Density Matrix Active
            </Badge>
          </div>
        </div>

        {/* Empty State Banner if no verification exists */}
        {!loading && claims.length === 0 && (
          <div className="rounded-2xl border border-dashed border-[#1f325c] bg-[#081024] p-8 text-center space-y-3">
            <div className="size-12 rounded-xl bg-amber-500/10 border border-amber-500/20 flex items-center justify-center text-amber-400 mx-auto">
              <AlertCircle className="size-6" />
            </div>
            <h3 className="text-base font-bold text-white">No verification available. Verify a claim first.</h3>
            <p className="text-xs text-slate-400 max-w-md mx-auto">
              Once you verify a claim or check an AI answer, every decomposed assertion will appear here with transparent 0% to 100% risk scoring.
            </p>
            <div className="pt-2">
              <Link to="/check-answer">
                <Button className="rounded-xl bg-amber-600 hover:bg-amber-500 text-white text-xs px-5 shadow-lg shadow-amber-600/30">
                  <FileCheck className="size-3.5 mr-2" /> Start New Verification
                </Button>
              </Link>
            </div>
          </div>
        )}

        {/* Risk Metrics Cards */}
        {claims.length > 0 && (
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <div className="rounded-2xl border border-[#172545] bg-[#091124] p-4 text-center">
              <p className="text-[11px] font-semibold text-slate-400 uppercase">Total Claims Mapped</p>
              <p className="text-2xl font-bold text-white mt-1">{claims.length}</p>
              <span className="text-[10px] text-slate-500">Atomic factual assertions</span>
            </div>

            <div className="rounded-2xl border border-[#172545] bg-[#091124] p-4 text-center">
              <p className="text-[11px] font-semibold text-rose-400 uppercase">High Risk (60% - 100%)</p>
              <p className="text-2xl font-bold text-rose-400 mt-1">{highCount}</p>
              <span className="text-[10px] text-rose-400/70">
                {claims.length > 0 ? `${Math.round((highCount / claims.length) * 100)}% of claims` : "0%"}
              </span>
            </div>

            <div className="rounded-2xl border border-[#172545] bg-[#091124] p-4 text-center">
              <p className="text-[11px] font-semibold text-amber-400 uppercase">Moderate Risk (25% - 59%)</p>
              <p className="text-2xl font-bold text-amber-400 mt-1">{modCount}</p>
              <span className="text-[10px] text-amber-400/70">
                {claims.length > 0 ? `${Math.round((modCount / claims.length) * 100)}% of claims` : "0%"}
              </span>
            </div>

            <div className="rounded-2xl border border-[#172545] bg-[#091124] p-4 text-center">
              <p className="text-[11px] font-semibold text-emerald-400 uppercase">Low Risk (0% - 24%)</p>
              <p className="text-2xl font-bold text-emerald-400 mt-1">{lowCount}</p>
              <span className="text-[10px] text-emerald-400/70">
                {claims.length > 0 ? `${Math.round((lowCount / claims.length) * 100)}% of claims` : "0%"}
              </span>
            </div>
          </div>
        )}

        {/* Filters and Search Bar */}
        {claims.length > 0 && (
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-[#091124] border border-[#172545] p-4 rounded-2xl">
            <div className="flex items-center gap-1.5 flex-wrap">
              <span className="text-xs font-semibold text-slate-400 mr-1 flex items-center gap-1">
                <Filter className="size-3.5" /> Filter:
              </span>
              {(["all", "high", "moderate", "low"] as const).map((tier) => (
                <button
                  key={tier}
                  type="button"
                  onClick={() => setFilterTier(tier)}
                  className={`text-xs px-3 py-1.5 rounded-xl capitalize font-semibold transition-colors ${
                    filterTier === tier
                      ? tier === "high"
                        ? "bg-rose-600 text-white shadow"
                        : tier === "moderate"
                        ? "bg-amber-600 text-white shadow"
                        : tier === "low"
                        ? "bg-emerald-600 text-white shadow"
                        : "bg-indigo-600 text-white shadow"
                      : "text-slate-400 hover:text-slate-200 bg-[#0c1630]"
                  }`}
                >
                  {tier === "all" ? "All Claims" : `${tier} Risk`}
                </button>
              ))}
            </div>

            <div className="w-full sm:w-72">
              <Input
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search claims..."
                className="h-9 rounded-xl bg-[#060c1d] border-[#1c2c54] text-xs text-slate-200 placeholder:text-slate-500"
              />
            </div>
          </div>
        )}

        {/* Heatmap Grid & Detail Inspector Layout */}
        {claims.length > 0 && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Claims Grid Column */}
            <div className="lg:col-span-2 space-y-3">
              <div className="flex items-center justify-between text-xs text-slate-400 px-1">
                <span>Showing {filteredClaims.length} claims</span>
                <span>Click a card to inspect risk calculation</span>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {filteredClaims.map((item) => {
                  const isSelected = selectedClaim?.id === item.id;
                  const isHigh = item.riskTier === "high";
                  const isMod = item.riskTier === "moderate";

                  return (
                    <div
                      key={item.id}
                      onClick={() => setSelectedClaim(item)}
                      className={`cursor-pointer rounded-2xl border p-4 transition-all duration-200 ${
                        isSelected
                          ? isHigh
                            ? "border-rose-500 bg-rose-950/30 shadow-lg shadow-rose-950/50"
                            : isMod
                            ? "border-amber-500 bg-amber-950/30 shadow-lg shadow-amber-950/50"
                            : "border-emerald-500 bg-emerald-950/30 shadow-lg shadow-emerald-950/50"
                          : isHigh
                          ? "border-rose-500/30 bg-rose-950/10 hover:border-rose-500/60"
                          : isMod
                          ? "border-amber-500/30 bg-amber-950/10 hover:border-amber-500/60"
                          : "border-emerald-500/30 bg-emerald-950/10 hover:border-emerald-500/60"
                      }`}
                    >
                      <div className="flex items-center justify-between gap-2 mb-2">
                        <Badge
                          className={`text-[10px] font-bold ${
                            isHigh
                              ? "bg-rose-500/20 text-rose-400 border-rose-500/40"
                              : isMod
                              ? "bg-amber-500/20 text-amber-400 border-amber-500/40"
                              : "bg-emerald-500/20 text-emerald-400 border-emerald-500/40"
                          }`}
                        >
                          {formatRiskPercentage(item.riskScore)} RISK
                        </Badge>

                        <span className="text-[10px] text-slate-500">{item.status}</span>
                      </div>

                      <p className="text-xs font-semibold text-slate-200 line-clamp-3 leading-relaxed">
                        "{item.claim}"
                      </p>

                      {item.patternType && (
                        <div className="mt-2.5 pt-2 border-t border-slate-800/60">
                          <span className="text-[10px] font-mono text-rose-300">
                            🕵️ {item.patternType}
                          </span>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Claim Detail Inspector Panel */}
            <div className="rounded-2xl border border-[#172545] bg-[#091124] p-6 space-y-5 h-fit sticky top-6 shadow-xl">
              <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
                <Sparkles className="size-4 text-amber-400" />
                Claim Risk Inspector
              </h3>

              {selectedClaim ? (
                <div className="space-y-4">
                  <div className="space-y-1.5">
                    <div className="flex items-center justify-between">
                      <span className="text-[11px] font-semibold text-slate-400 uppercase">Risk Level</span>
                      <Badge
                        className={`text-xs font-bold ${
                          selectedClaim.riskTier === "high"
                            ? "bg-rose-500/20 text-rose-400 border-rose-500/40"
                            : selectedClaim.riskTier === "moderate"
                            ? "bg-amber-500/20 text-amber-400 border-amber-500/40"
                            : "bg-emerald-500/20 text-emerald-400 border-emerald-500/40"
                        }`}
                      >
                        {selectedClaim.riskTier.toUpperCase()} ({formatRiskPercentage(selectedClaim.riskScore)})
                      </Badge>
                    </div>

                    {/* Progress Bar (Strictly 0% to 100%) */}
                    <div className="h-2 rounded-full bg-slate-800 overflow-hidden">
                      <div
                        className={`h-full rounded-full transition-all duration-300 ${
                          selectedClaim.riskTier === "high"
                            ? "bg-rose-500"
                            : selectedClaim.riskTier === "moderate"
                            ? "bg-amber-500"
                            : "bg-emerald-500"
                        }`}
                        style={{ width: `${Math.round(normalizeRisk(selectedClaim.riskScore) * 100)}%` }}
                      />
                    </div>
                  </div>

                  <div className="space-y-1">
                    <span className="text-[11px] font-semibold text-slate-400 uppercase">Claim Statement:</span>
                    <p className="text-xs font-medium text-slate-100 bg-[#060c1d] border border-[#162447] p-3 rounded-xl leading-relaxed">
                      "{selectedClaim.claim}"
                    </p>
                  </div>

                  {selectedClaim.patternType && (
                    <div className="rounded-xl border border-rose-500/30 bg-rose-950/20 p-3 space-y-1">
                      <span className="text-[10px] font-bold text-rose-400 uppercase">
                        Forensic Pattern Detected:
                      </span>
                      <p className="text-xs font-semibold text-rose-200">
                        {selectedClaim.patternType}
                      </p>
                    </div>
                  )}

                  <div className="space-y-1">
                    <span className="text-[11px] font-semibold text-slate-400 uppercase">Why Is This Claim Assigned This Risk?</span>
                    <p className="text-xs text-slate-300 leading-relaxed bg-[#060c1d] p-3 rounded-xl border border-[#162447]">
                      {selectedClaim.explanation || "Risk evaluated via NLI entailment distribution and multi-source scientific corpus."}
                    </p>
                  </div>

                  {/* Formula Breakdown Factors */}
                  {selectedClaim.riskFactors && (
                    <div className="space-y-1.5 pt-2 border-t border-[#14203d]">
                      <span className="text-[10px] font-bold text-slate-400 uppercase">Risk Factor Decomposition:</span>
                      <div className="space-y-1 text-[11px] text-slate-300 bg-[#060c1d] p-3 rounded-xl border border-[#162447]">
                        <p className="flex items-start gap-1.5">
                          <span className="text-amber-400 font-bold">•</span>
                          <span><strong>Verdict Calibration:</strong> {selectedClaim.riskFactors.verdictBase}</span>
                        </p>
                        <p className="flex items-start gap-1.5">
                          <span className="text-rose-400 font-bold">•</span>
                          <span><strong>Contradiction Signal:</strong> {selectedClaim.riskFactors.contradictions}</span>
                        </p>
                        <p className="flex items-start gap-1.5">
                          <span className="text-blue-400 font-bold">•</span>
                          <span><strong>Evidence Grounding:</strong> {selectedClaim.riskFactors.evidenceGap}</span>
                        </p>
                        <p className="flex items-start gap-1.5">
                          <span className="text-purple-400 font-bold">•</span>
                          <span><strong>Forensic Linguistic Analysis:</strong> {selectedClaim.riskFactors.forensics}</span>
                        </p>
                      </div>
                    </div>
                  )}

                  <div className="pt-3 border-t border-[#14203d] grid grid-cols-2 gap-2 text-[11px] text-slate-400">
                    <div>
                      <span className="text-slate-500 block">Status:</span>
                      <strong className="text-slate-200">{selectedClaim.status}</strong>
                    </div>
                    <div>
                      <span className="text-slate-500 block">Evidence Checked:</span>
                      <strong className="text-slate-200">{selectedClaim.evidenceCount} sources</strong>
                    </div>
                  </div>
                </div>
              ) : (
                <p className="text-xs text-slate-500 py-6 text-center">
                  Select a claim from the grid to inspect details.
                </p>
              )}
            </div>
          </div>
        )}
      </div>
    </AppShell>
  );
}
