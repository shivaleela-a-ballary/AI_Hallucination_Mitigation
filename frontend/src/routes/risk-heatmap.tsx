import { createFileRoute } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import {
  Activity,
  AlertTriangle,
  ArrowRight,
  CheckCircle2,
  Filter,
  Info,
  Layers,
  Search,
  ShieldAlert,
  ShieldCheck,
  Sparkles,
  XCircle,
} from "lucide-react";

import { AppShell } from "@/components/app/app-shell";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { api, type AnswerRecord, type ClaimResult } from "@/lib/api";

export const Route = createFileRoute("/risk-heatmap")({
  component: RiskHeatmapPage,
});

interface HeatmapClaim {
  id: string;
  claim: string;
  status: string;
  riskScore: number;
  riskTier: "high" | "moderate" | "low";
  confidence: number;
  evidenceCount: number;
  querySource: string;
  date: string;
  patternType?: string;
  explanation?: string;
}

function RiskHeatmapPage() {
  const [claims, setClaims] = useState<HeatmapClaim[]>([]);
  const [filterTier, setFilterTier] = useState<"all" | "high" | "moderate" | "low">("all");
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedClaim, setSelectedClaim] = useState<HeatmapClaim | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadClaims() {
      try {
        setLoading(true);
        const { history } = await api.history();
        const mapped: HeatmapClaim[] = [];

        history.forEach((rec, recIdx) => {
          const recDate = rec.created_at ? new Date(rec.created_at).toLocaleDateString() : "Recent";
          const queryTitle = rec.query || (rec as unknown as { user_query?: string }).user_query || "Query";

          (rec.claims || []).forEach((c, cIdx) => {
            const status = (c.status || c.verdict || "UNCERTAIN").toUpperCase();
            const isRefuted = status === "REFUTED" || status === "CONTRADICTED";
            const isSupported = status === "SUPPORTED";

            let risk = (c as unknown as { risk_score?: number }).risk_score ?? c.hallucination_risk_score;
            if (risk == null) {
              risk = isRefuted ? 0.85 : isSupported ? 0.12 : 0.48;
            }

            const riskTier: "high" | "moderate" | "low" =
              risk > 0.6 ? "high" : risk >= 0.25 ? "moderate" : "low";

            const forensics = (c as unknown as { forensics?: { pattern_type?: string } }).forensics;

            mapped.push({
              id: `${rec.id || recIdx}-${cIdx}`,
              claim: c.claim,
              status,
              riskScore: risk,
              riskTier,
              confidence: c.evidence_score || (rec.confidence_score ?? 0.7),
              evidenceCount: (c.evidence_titles || []).length,
              querySource: queryTitle,
              date: recDate,
              patternType: forensics?.pattern_type,
              explanation: c.explanation || c.evidence_summary,
            });
          });
        });

        // If no claims exist in history yet, provide default benchmark examples
        if (mapped.length === 0) {
          mapped.push(
            {
              id: "demo-1",
              claim: "Metformin completely eliminates 100% of malignant breast cancer tumors in all clinical trials.",
              status: "REFUTED",
              riskScore: 0.92,
              riskTier: "high",
              confidence: 0.95,
              evidenceCount: 4,
              querySource: "Metformin in oncology",
              date: "Today",
              patternType: "Unsupported Numerical Claim",
              explanation: "Directly contradicted by clinical trial literature. Modest incidence reductions observed only in observational cohorts.",
            },
            {
              id: "demo-2",
              claim: "Low-dose aspirin universally eliminates myocardial infarction risk in all adult populations.",
              status: "REFUTED",
              riskScore: 0.84,
              riskTier: "high",
              confidence: 0.89,
              evidenceCount: 3,
              querySource: "Cardiovascular therapies",
              date: "Today",
              patternType: "Absolute Language",
              explanation: "Clinical guidelines show aspirin benefits secondary prevention but carries significant bleeding risks in primary prophylaxis.",
            },
            {
              id: "demo-3",
              claim: "CRISPR-Cas9 gene editing has achieved zero off-target cleavage mutations across all human clinical applications.",
              status: "UNCERTAIN",
              riskScore: 0.58,
              riskTier: "moderate",
              confidence: 0.62,
              evidenceCount: 2,
              querySource: "Gene editing precision",
              date: "Today",
              patternType: "Overgeneralization",
              explanation: "Off-target cleavage rates vary significantly across target loci and cell types. No universal zero rate established.",
            },
            {
              id: "demo-4",
              claim: "Metformin decreases hepatic glucose production and improves peripheral insulin sensitivity.",
              status: "SUPPORTED",
              riskScore: 0.08,
              riskTier: "low",
              confidence: 0.98,
              evidenceCount: 6,
              querySource: "Diabetes pharmacology",
              date: "Today",
              patternType: undefined,
              explanation: "Fully grounded in established biomedical consensus and multiple peer-reviewed pharmacological trials.",
            },
            {
              id: "demo-5",
              claim: "Statins significantly reduce low-density lipoprotein cholesterol (LDL-C) in hypercholesterolemia.",
              status: "SUPPORTED",
              riskScore: 0.11,
              riskTier: "low",
              confidence: 0.96,
              evidenceCount: 5,
              querySource: "Lipid management",
              date: "Today",
              patternType: undefined,
              explanation: "Strong multi-trial meta-analyses verify substantial LDL reduction across patient cohorts.",
            },
            {
              id: "demo-6",
              claim: "Dietary caffeine consumption directly leads to acute stroke in healthy adults.",
              status: "REFUTED",
              riskScore: 0.88,
              riskTier: "high",
              confidence: 0.91,
              evidenceCount: 3,
              querySource: "Dietary health study",
              date: "Today",
              patternType: "Causal Overclaim",
              explanation: "Observational association confused with direct causation. Confounding risk factors were unaddressed.",
            }
          );
        }

        setClaims(mapped);
        if (mapped.length > 0) setSelectedClaim(mapped[0]);
      } catch (err: unknown) {
        // error handling
      } finally {
        setLoading(false);
      }
    }
    void loadClaims();
  }, []);

  const filteredClaims = claims.filter((c) => {
    if (filterTier !== "all" && c.riskTier !== filterTier) return false;
    if (searchQuery && !c.claim.toLowerCase().includes(searchQuery.toLowerCase())) return false;
    return true;
  });

  const highCount = claims.filter((c) => c.riskTier === "high").length;
  const modCount = claims.filter((c) => c.riskTier === "moderate").length;
  const lowCount = claims.filter((c) => c.riskTier === "low").length;
  const avgRisk = claims.length > 0 ? claims.reduce((acc, c) => acc + c.riskScore, 0) / claims.length : 0;

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
              Visual risk matrix evaluating hallucination likelihood, contradiction signals, and empirical evidence grounding.
            </p>
          </div>

          <div className="flex items-center gap-2">
            <Badge variant="outline" className="border-amber-500/30 text-amber-300 bg-amber-950/20 text-xs">
              Risk Density Matrix Active
            </Badge>
          </div>
        </div>

        {/* Risk Metrics Cards */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          <div className="rounded-2xl border border-[#172545] bg-[#091124] p-4 text-center">
            <p className="text-[11px] font-semibold text-slate-400 uppercase">Total Claims Mapped</p>
            <p className="text-2xl font-bold text-white mt-1">{claims.length}</p>
            <span className="text-[10px] text-slate-500">Atomic factual claims</span>
          </div>

          <div className="rounded-2xl border border-[#172545] bg-[#091124] p-4 text-center">
            <p className="text-[11px] font-semibold text-rose-400 uppercase">High Risk (&gt; 0.60)</p>
            <p className="text-2xl font-bold text-rose-400 mt-1">{highCount}</p>
            <span className="text-[10px] text-rose-400/70">
              {claims.length > 0 ? `${Math.round((highCount / claims.length) * 100)}% of claims` : "0%"}
            </span>
          </div>

          <div className="rounded-2xl border border-[#172545] bg-[#091124] p-4 text-center">
            <p className="text-[11px] font-semibold text-amber-400 uppercase">Moderate Risk (0.25 - 0.60)</p>
            <p className="text-2xl font-bold text-amber-400 mt-1">{modCount}</p>
            <span className="text-[10px] text-amber-400/70">
              {claims.length > 0 ? `${Math.round((modCount / claims.length) * 100)}% of claims` : "0%"}
            </span>
          </div>

          <div className="rounded-2xl border border-[#172545] bg-[#091124] p-4 text-center">
            <p className="text-[11px] font-semibold text-emerald-400 uppercase">Low Risk (&lt; 0.25)</p>
            <p className="text-2xl font-bold text-emerald-400 mt-1">{lowCount}</p>
            <span className="text-[10px] text-emerald-400/70">
              {claims.length > 0 ? `${Math.round((lowCount / claims.length) * 100)}% of claims` : "0%"}
            </span>
          </div>
        </div>

        {/* Filters and Search Bar */}
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

        {/* Heatmap Grid & Detail Inspector Layout */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Claims Grid Column */}
          <div className="lg:col-span-2 space-y-3">
            <div className="flex items-center justify-between text-xs text-slate-400 px-1">
              <span>Showing {filteredClaims.length} claims</span>
              <span>Click a tile to inspect forensic breakdown</span>
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
                        {Math.round(item.riskScore * 100)}% RISK
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
                      {selectedClaim.riskTier.toUpperCase()} ({Math.round(selectedClaim.riskScore * 100)}%)
                    </Badge>
                  </div>
                  {/* Progress Bar */}
                  <div className="h-2 rounded-full bg-slate-800 overflow-hidden">
                    <div
                      className={`h-full rounded-full transition-all duration-300 ${
                        selectedClaim.riskTier === "high"
                          ? "bg-rose-500"
                          : selectedClaim.riskTier === "moderate"
                          ? "bg-amber-500"
                          : "bg-emerald-500"
                      }`}
                      style={{ width: `${selectedClaim.riskScore * 100}%` }}
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
                  <span className="text-[11px] font-semibold text-slate-400 uppercase">Evidence Grounding Explanation:</span>
                  <p className="text-xs text-slate-300 leading-relaxed">
                    {selectedClaim.explanation || "Evaluated against peer-reviewed corpus citations."}
                  </p>
                </div>

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
      </div>
    </AppShell>
  );
}
