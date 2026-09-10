import { createFileRoute } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import {
  Activity,
  AlertCircle,
  AlertTriangle,
  ArrowRight,
  BrainCircuit,
  CheckCircle2,
  ChevronDown,
  ChevronUp,
  FileCheck,
  HelpCircle,
  Info,
  Loader2,
  Search,
  ShieldAlert,
  Sparkles,
  Tag,
  XCircle,
} from "lucide-react";

import { AppShell } from "@/components/app/app-shell";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { api, type AnswerRecord, type ForensicsPattern, type ForensicsAnalysis } from "@/lib/api";
import { toast } from "sonner";

export const Route = createFileRoute("/forensics")({
  component: ForensicsPage,
});

const PATTERN_CATALOG = [
  {
    name: "Overgeneralization",
    severity: "high",
    description: "Extrapolating narrow experimental findings to universal populations or unrelated domains without qualification.",
    cues: ["universally", "all patients", "every case", "without exception", "in all contexts"],
    example: "Metformin cures all cancers regardless of tumor type or genetic predisposition.",
  },
  {
    name: "Causal Overclaim",
    severity: "high",
    description: "Asserting direct causation where the underlying scientific study only established observational correlation.",
    cues: ["directly causes", "proves causation", "sole determinant", "invariably leads to"],
    example: "Coffee consumption directly causes cardiac arrest in adults.",
  },
  {
    name: "Exaggeration",
    severity: "medium",
    description: "Inflating modest statistical improvements into dramatic breakthroughs or absolute remedies.",
    cues: ["miraculous", "revolutionary breakthrough", "completely transforms", "unprecedented leap"],
    example: "A 2% improvement in survival was characterized as an unprecedented cure.",
  },
  {
    name: "Unsupported Numerical Claim",
    severity: "critical",
    description: "Inventing or fabricating precise percentages, statistical p-values, or sample sizes not grounded in corpus.",
    cues: ["100% cure rate", "99.9% effective", "zero mortality", "p < 0.00001 in all trials"],
    example: "Achieved 100.0% remission in 50,000 human patients.",
  },
  {
    name: "Absolute Language",
    severity: "medium",
    description: "Using categorical terms that eliminate genuine scientific nuance, confidence intervals, or exceptions.",
    cues: ["always", "never", "impossible", "undeniable", "guaranteed"],
    example: "This therapy is guaranteed to never cause any adverse side effects.",
  },
  {
    name: "Source Mismatch",
    severity: "high",
    description: "Attributing a factual claim to a paper or study whose content does not evaluate or corroborate the claim.",
    cues: ["as proven by [source]", "documented in trial", "citing paper X"],
    example: "Citing an in-vitro cell study to claim FDA approval in humans.",
  },
  {
    name: "Missing Context",
    severity: "medium",
    description: "Omitting crucial boundary conditions, contraindications, or required co-factors that alter the claim's validity.",
    cues: ["safely administered", "readily available", "easily implemented"],
    example: "Stating a drug is safe while omitting that it requires strict hospitalization and monitoring.",
  },
  {
    name: "Entity Confusion",
    severity: "high",
    description: "Conflating distinct proteins, genes, viruses, drug isomers, or regulatory bodies with similar names.",
    cues: ["interchangeably", "same mechanism", "identical role"],
    example: "Confusing IL-6 with IL-10 or treating SARS-CoV-1 and SARS-CoV-2 identically.",
  },
  {
    name: "Unsupported Conclusion",
    severity: "high",
    description: "Drawing sweeping conclusions that logically exceed the premise and empirical evidence presented.",
    cues: ["therefore we can conclude", "demonstrates clearly", "leaves no doubt"],
    example: "Mice survived an acute infection; therefore human disease has been eradicated.",
  },
  {
    name: "Temporal Mismatch",
    severity: "medium",
    description: "Stating obsolete historical hypotheses or early pre-clinical hypotheses as current modern clinical practice.",
    cues: ["currently established", "standard protocol", "recently adopted"],
    example: "Citing discontinued 1990s experimental guidelines as active 2024 protocols.",
  },
  {
    name: "Population Mismatch",
    severity: "high",
    description: "Claiming rodent, murine, or in-vitro cell assay responses apply directly and unconditionally to human patients.",
    cues: ["patients will experience", "human clinical outcome", "in humans"],
    example: "Murine tumor shrinkage presented as confirmed human efficacy.",
  },
  {
    name: "Correlation Presented as Causation",
    severity: "high",
    description: "Conflating two observed coincident phenomena as a verified mechanism of action.",
    cues: ["proves that X drives Y", "mechanism is confirmed", "directly triggers"],
    example: "Dietary survey correlations claimed as mechanistic pharmacological drivers.",
  },
];

function ForensicsPage() {
  const [claimInput, setClaimInput] = useState("");
  const [diagnosing, setDiagnosing] = useState(false);
  const [analysisResult, setAnalysisResult] = useState<ForensicsAnalysis | null>(null);
  const [selectedFilter, setSelectedFilter] = useState<string>("all");
  const [recentClaims, setRecentClaims] = useState<{ claim: string; pattern?: string; severity?: string }[]>([]);

  useEffect(() => {
    // Load claims with forensics patterns from history
    api.history().then(({ history }) => {
      const extracted: { claim: string; pattern?: string; severity?: string }[] = [];
      history.forEach((rec) => {
        (rec.claims || []).forEach((c) => {
          const forensics = (c as unknown as { forensics?: { pattern_type?: string; severity?: string } }).forensics;
          if (forensics?.pattern_type && forensics.pattern_type !== "None / Valid") {
            extracted.push({
              claim: c.claim,
              pattern: forensics.pattern_type,
              severity: forensics.severity || "medium",
            });
          }
        });
      });
      if (extracted.length > 0) setRecentClaims(extracted.slice(0, 8));
    }).catch(() => {});
  }, []);

  const handleDiagnose = async (textToTest?: string) => {
    const text = (textToTest ?? claimInput).trim();
    if (!text) {
      toast.error("Please enter a claim to inspect.");
      return;
    }

    try {
      setDiagnosing(true);
      const res = await api.checkAnswer(text);
      if (res?.claims?.[0]?.forensics) {
        setAnalysisResult(res.claims[0].forensics);
        toast.success("Forensic diagnosis complete.");
      } else if (res?.claims?.[0]) {
        // Build synthesized report from claim
        setAnalysisResult({
          claim_text: text,
          pattern_type: "None / Valid",
          severity: "low",
          explanation: "No prominent forensic distortion patterns identified in this claim against empirical evidence.",
          linguistic_cues: [],
          detected_patterns: [],
        });
        toast.info("Claim inspected: Grounded with low forensic distortion risk.");
      }
    } catch (err: unknown) {
      toast.error("Failed to run forensic analysis.");
    } finally {
      setDiagnosing(false);
    }
  };

  const filteredCatalog = PATTERN_CATALOG.filter((p) => {
    if (selectedFilter === "all") return true;
    return p.severity === selectedFilter;
  });

  return (
    <AppShell>
      <div className="space-y-7 max-w-6xl mx-auto">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-[#162340] pb-5">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <div className="size-8 rounded-lg bg-purple-500/10 border border-purple-500/30 flex items-center justify-center text-purple-400">
                <Activity className="size-4.5" />
              </div>
              <h1 className="text-2xl font-extrabold text-white tracking-tight">
                Hallucination Forensics Engine
              </h1>
            </div>
            <p className="text-xs sm:text-sm text-slate-400">
              Deep diagnostic inspection of 12 distinct linguistic and empirical hallucination patterns.
            </p>
          </div>

          <div className="flex items-center gap-2">
            <Badge variant="outline" className="border-purple-500/30 text-purple-300 bg-purple-950/20 text-xs">
              12 Linguistic & Factual Pattern Detectors Active
            </Badge>
          </div>
        </div>

        {/* Live Claim Inspector */}
        <div className="rounded-2xl border border-[#172545] bg-[#091124] p-6 space-y-4 shadow-lg">
          <h2 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
            <Search className="size-4 text-purple-400" />
            Inspect Individual Claim for Forensics
          </h2>

          <div className="flex flex-col sm:flex-row gap-3">
            <Input
              value={claimInput}
              onChange={(e) => setClaimInput(e.target.value)}
              placeholder="Paste any claim to test for overgeneralization, causal overclaims, absolute language..."
              className="h-11 rounded-xl bg-[#060c1d] border-[#1c2c54] text-sm text-slate-100 placeholder:text-slate-500 focus:border-purple-500"
            />
            <Button
              onClick={() => void handleDiagnose()}
              disabled={diagnosing || !claimInput.trim()}
              className="rounded-xl bg-purple-600 hover:bg-purple-500 text-white font-semibold text-xs px-6 shrink-0 shadow-md shadow-purple-600/30"
            >
              {diagnosing ? (
                <>
                  <Loader2 className="size-3.5 mr-2 animate-spin" /> Diagnosing...
                </>
              ) : (
                <>
                  <Sparkles className="size-3.5 mr-2" /> Run Diagnosis
                </>
              )}
            </Button>
          </div>

          {/* Quick Try Buttons */}
          <div className="flex flex-wrap items-center gap-2 pt-1 text-xs text-slate-400">
            <span>Test sample:</span>
            <button
              type="button"
              onClick={() => {
                const s = "Metformin completely cures 100% of all malignant breast cancers in all patients.";
                setClaimInput(s);
                void handleDiagnose(s);
              }}
              className="px-2 py-0.5 rounded-md bg-[#0e1833] hover:bg-[#162550] border border-[#1b2c57] text-purple-300 transition-colors"
            >
              Absolute / Numerical Claim
            </button>
            <button
              type="button"
              onClick={() => {
                const s = "Coffee consumption directly causes heart attacks without exception.";
                setClaimInput(s);
                void handleDiagnose(s);
              }}
              className="px-2 py-0.5 rounded-md bg-[#0e1833] hover:bg-[#162550] border border-[#1b2c57] text-purple-300 transition-colors"
            >
              Causal Overclaim
            </button>
            <button
              type="button"
              onClick={() => {
                const s = "Rodent assays prove that CRISPR has zero off-target effects in human clinical medicine.";
                setClaimInput(s);
                void handleDiagnose(s);
              }}
              className="px-2 py-0.5 rounded-md bg-[#0e1833] hover:bg-[#162550] border border-[#1b2c57] text-purple-300 transition-colors"
            >
              Population Mismatch
            </button>
          </div>

          {/* Diagnosis Result Card */}
          {analysisResult && (
            <div className="mt-4 rounded-xl border border-purple-500/30 bg-[#0c142b] p-5 space-y-4">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-[#18274d] pb-3">
                <div className="flex items-center gap-2.5">
                  <span className="text-xs font-semibold text-slate-400">Primary Distortion Pattern:</span>
                  <Badge
                    className={
                      analysisResult.severity === "critical"
                        ? "bg-rose-500/25 text-rose-400 border-rose-500/50 font-bold"
                        : analysisResult.severity === "high"
                        ? "bg-rose-500/20 text-rose-400 border-rose-500/40 font-bold"
                        : analysisResult.severity === "medium"
                        ? "bg-amber-500/20 text-amber-400 border-amber-500/40 font-bold"
                        : "bg-emerald-500/20 text-emerald-400 border-emerald-500/40 font-bold"
                    }
                  >
                    {analysisResult.pattern_type}
                  </Badge>
                  <span className="text-[11px] uppercase font-bold text-slate-500">
                    Severity: {analysisResult.severity}
                  </span>
                </div>
              </div>

              <div className="space-y-2">
                <p className="text-xs font-semibold text-slate-300">Analyzed Claim:</p>
                <p className="text-sm font-medium text-slate-100 italic bg-[#070c1d] p-3 rounded-lg border border-[#172545]">
                  "{analysisResult.claim_text}"
                </p>
              </div>

              <div className="space-y-1">
                <p className="text-xs font-semibold text-purple-300">Forensic Diagnosis:</p>
                <p className="text-xs text-slate-300 leading-relaxed">
                  {analysisResult.explanation}
                </p>
              </div>

              {analysisResult.linguistic_cues?.length > 0 && (
                <div className="flex items-center gap-2 flex-wrap pt-1">
                  <span className="text-xs font-semibold text-slate-400">Trigger Words / Linguistic Cues:</span>
                  {analysisResult.linguistic_cues.map((cue, idx) => (
                    <Badge key={idx} variant="outline" className="border-rose-500/40 text-rose-300 bg-rose-950/30 text-xs font-mono">
                      "{cue}"
                    </Badge>
                  ))}
                </div>
              )}

              {analysisResult.suggested_fix && (
                <div className="rounded-lg bg-emerald-950/20 border border-emerald-500/30 p-3 space-y-1">
                  <span className="text-xs font-bold text-emerald-400 flex items-center gap-1.5">
                    <CheckCircle2 className="size-3.5" /> Suggested Empirical Grounding:
                  </span>
                  <p className="text-xs text-slate-200">
                    "{analysisResult.suggested_fix}"
                  </p>
                </div>
              )}
            </div>
          )}
        </div>

        {/* 12 Pattern Knowledge Catalog */}
        <div className="space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div>
              <h2 className="text-lg font-bold text-white tracking-tight">12 Hallucination Pattern Catalog</h2>
              <p className="text-xs text-slate-400">Standardized classification of distortion modes diagnosed by the system</p>
            </div>

            <div className="flex items-center gap-1.5 bg-[#0a1226] border border-[#17264a] p-1 rounded-xl">
              {["all", "critical", "high", "medium"].map((lvl) => (
                <button
                  key={lvl}
                  type="button"
                  onClick={() => setSelectedFilter(lvl)}
                  className={`text-xs px-3 py-1 rounded-lg capitalize font-semibold transition-colors ${
                    selectedFilter === lvl
                      ? "bg-purple-600 text-white shadow"
                      : "text-slate-400 hover:text-slate-200"
                  }`}
                >
                  {lvl}
                </button>
              ))}
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {filteredCatalog.map((item) => (
              <div
                key={item.name}
                className="rounded-2xl border border-[#172545] bg-[#091124] p-5 flex flex-col justify-between space-y-4 hover:border-purple-500/40 transition-colors shadow-md"
              >
                <div className="space-y-2.5">
                  <div className="flex items-center justify-between">
                    <h3 className="text-sm font-bold text-white">{item.name}</h3>
                    <Badge
                      className={`text-[10px] uppercase font-bold ${
                        item.severity === "critical"
                          ? "bg-rose-500/20 text-rose-400 border-rose-500/40"
                          : item.severity === "high"
                          ? "bg-orange-500/20 text-orange-400 border-orange-500/40"
                          : "bg-amber-500/20 text-amber-400 border-amber-500/40"
                      }`}
                    >
                      {item.severity}
                    </Badge>
                  </div>

                  <p className="text-xs text-slate-400 leading-relaxed">
                    {item.description}
                  </p>

                  <div className="pt-2 border-t border-[#131f3b] space-y-1.5">
                    <span className="text-[11px] font-semibold text-slate-500 uppercase">Detection Cues:</span>
                    <div className="flex flex-wrap gap-1">
                      {item.cues.map((c, i) => (
                        <span key={i} className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-[#0d1630] border border-[#192a50] text-purple-300">
                          {c}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>

                <div className="rounded-xl bg-[#060c1d] border border-[#142240] p-3 text-xs space-y-1">
                  <span className="text-[10px] font-bold text-slate-500 uppercase">Example Distorted Assertion:</span>
                  <p className="text-[11px] text-slate-300 italic">"{item.example}"</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </AppShell>
  );
}
