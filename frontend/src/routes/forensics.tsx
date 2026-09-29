import { createFileRoute, Link } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import {
  Activity,
  AlertCircle,
  AlertTriangle,
  ArrowRight,
  CheckCircle2,
  FileCheck,
  HelpCircle,
  Info,
  Loader2,
  Search,
  Sparkles,
  XCircle,
} from "lucide-react";

import { AppShell } from "@/components/app/app-shell";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { api, type ForensicsAnalysis, type ForensicsPattern } from "@/lib/api";
import { useVerification } from "@/lib/verification-context";
import { toast } from "sonner";

export const Route = createFileRoute("/forensics")({
  component: ForensicsPage,
});

const PATTERN_CATALOG = [
  {
    name: "Unsupported Numerical Claim",
    defaultSeverity: "critical",
    description: "Inventing or fabricating precise numbers, percentages, or sample sizes not grounded in corpus.",
    cues: ["100% cure rate", "1989", "99.9%", "zero mortality", "p < 0.00001"],
    example: "The Python programming language was originally created in 1989 while working at Google.",
  },
  {
    name: "Causal Overclaim",
    defaultSeverity: "high",
    description: "Asserting direct causation where underlying scientific studies only established correlation.",
    cues: ["directly causes", "proves causation", "sole determinant", "invariably leads to"],
    example: "Coffee consumption directly causes myocardial infarction in healthy adults.",
  },
  {
    name: "Population Mismatch",
    defaultSeverity: "high",
    description: "Claiming rodent, murine, or in-vitro cell assay responses apply directly to human patients.",
    cues: ["patients will experience", "in humans", "human clinical outcome"],
    example: "Murine cell assay outcomes presented as confirmed human clinical cures.",
  },
  {
    name: "Source Mismatch",
    defaultSeverity: "high",
    description: "Attributing a factual claim to a paper or organization whose content does not corroborate it.",
    cues: ["citing paper X", "documented in study", "published by [source]"],
    example: "Citing an observational survey to claim Phase III FDA efficacy.",
  },
  {
    name: "Absolute Language",
    defaultSeverity: "medium",
    description: "Using categorical terms that eliminate scientific nuance, confidence intervals, or exceptions.",
    cues: ["always", "never", "impossible", "undeniable", "guaranteed", "completely cures"],
    example: "This therapy is guaranteed to never cause any adverse side effects.",
  },
  {
    name: "Exaggeration",
    defaultSeverity: "medium",
    description: "Inflating modest statistical improvements into dramatic breakthroughs or absolute remedies.",
    cues: ["miraculous", "revolutionary breakthrough", "completely transforms", "unprecedented"],
    example: "A 2% improvement in survival was characterized as an unprecedented cure.",
  },
  {
    name: "Overgeneralization",
    defaultSeverity: "high",
    description: "Extrapolating narrow experimental findings to universal populations or unrelated domains.",
    cues: ["universally", "all patients", "every case", "without exception"],
    example: "Metformin cures all cancers regardless of tumor type or genetic predisposition.",
  },
  {
    name: "Temporal Mismatch",
    defaultSeverity: "medium",
    description: "Stating obsolete historical hypotheses or outdated timelines as current active facts.",
    cues: ["currently established", "standard protocol", "recently adopted in 1980"],
    example: "Citing discontinued 1990s experimental guidelines as active protocols.",
  },
  {
    name: "Entity Confusion",
    defaultSeverity: "high",
    description: "Conflating distinct proteins, institutions, employers, or regulatory bodies.",
    cues: ["interchangeably", "same mechanism", "identical role", "Google vs CWI"],
    example: "Confusing Guido's employment at Google (2005) with Python's origin at CWI (1989).",
  },
  {
    name: "Unsupported Attribution",
    defaultSeverity: "high",
    description: "Attributing discoveries or organizational backing without empirical citation.",
    cues: ["developed by", "created while working at", "officially endorsed by"],
    example: "Asserting a technology was built under corporate sponsorship without evidence.",
  },
  {
    name: "Contradictory Evidence",
    defaultSeverity: "critical",
    description: "Asserting statements directly refuted by authoritative empirical sources.",
    cues: ["refuted by literature", "contradictory trial findings", "opposing consensus"],
    example: "Asserting high-dose caffeine protects against stroke when trials demonstrate elevated risk.",
  },
  {
    name: "Insufficient Evidence",
    defaultSeverity: "medium",
    description: "Making factual claims that indexed corpora have zero authoritative data to verify.",
    cues: ["unindexed assertion", "sparse grounding", "unverified hypothesis"],
    example: "Asserting unstudied botanical compounds treat rare neuromuscular conditions.",
  },
];

function ForensicsPage() {
  const { currentVerification, setVerification } = useVerification();
  const [claimInput, setClaimInput] = useState("");
  const [diagnosing, setDiagnosing] = useState(false);
  const [analysisResult, setAnalysisResult] = useState<ForensicsAnalysis | null>(null);
  const [selectedFilter, setSelectedFilter] = useState<string>("all");

  // Synchronize with canonical verification
  useEffect(() => {
    if (currentVerification) {
      const claimText = currentVerification.claim || currentVerification.query || "";
      if (claimText) {
        setClaimInput(claimText);
      }
      if (currentVerification.forensics) {
        setAnalysisResult({
          ...currentVerification.forensics,
          claim_text: currentVerification.forensics.claim_text || claimText,
        });
      }
    }
  }, [currentVerification]);

  const handleDiagnose = async (textToTest?: string) => {
    const text = (textToTest ?? claimInput).trim();
    if (!text) {
      toast.error("Please enter a claim to inspect.");
      return;
    }

    try {
      setDiagnosing(true);
      const res = await api.checkAnswer(text);
      if (res) {
        setVerification(res);
        if (res.claims?.[0]?.forensics) {
          setAnalysisResult({
            ...res.claims[0].forensics,
            claim_text: res.claims[0].claim || text,
          });
          toast.success("Forensic diagnosis complete.");
        } else if (res.forensics) {
          setAnalysisResult({
            ...res.forensics,
            claim_text: res.claim || text,
          });
          toast.success("Forensic diagnosis complete.");
        }
      }
    } catch {
      toast.error("Failed to run forensic analysis.");
    } finally {
      setDiagnosing(false);
    }
  };

  // Build pattern map from analysis result
  const detectedPatternMap = new Map<string, any>();
  if (analysisResult?.detected_patterns) {
    analysisResult.detected_patterns.forEach((p: any) => {
      detectedPatternMap.set(p.pattern?.toLowerCase(), p);
    });
  }

  const filteredCatalog = PATTERN_CATALOG.filter((item) => {
    if (selectedFilter === "all") return true;
    const match = detectedPatternMap.get(item.name.toLowerCase());
    const severity = match?.severity || item.defaultSeverity;
    if (selectedFilter === "detected") return match?.detected === true;
    return severity === selectedFilter;
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
              12 Linguistic & Empirical Detectors Active
            </Badge>
          </div>
        </div>

        {/* Empty State Banner if no verification exists */}
        {!currentVerification && !analysisResult && (
          <div className="rounded-2xl border border-dashed border-[#1f325c] bg-[#081024] p-8 text-center space-y-3">
            <div className="size-12 rounded-xl bg-purple-500/10 border border-purple-500/20 flex items-center justify-center text-purple-400 mx-auto">
              <AlertCircle className="size-6" />
            </div>
            <h3 className="text-base font-bold text-white">No verification available. Verify a claim first.</h3>
            <p className="text-xs text-slate-400 max-w-md mx-auto">
              Perform a verification from the Check AI Answer or New Verification workspace to automatically inspect its empirical forensics.
            </p>
            <div className="pt-2">
              <Link to="/check-answer">
                <Button className="rounded-xl bg-purple-600 hover:bg-purple-500 text-white text-xs px-5 shadow-lg shadow-purple-600/30">
                  <FileCheck className="size-3.5 mr-2" /> Start New Verification
                </Button>
              </Link>
            </div>
          </div>
        )}

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
            <span>Test benchmark:</span>
            <button
              type="button"
              onClick={() => {
                const s = "The Python programming language was originally created by Guido van Rossum in 1989 while he was working at Google.";
                setClaimInput(s);
                void handleDiagnose(s);
              }}
              className="px-2.5 py-1 rounded-lg bg-[#0e1833] hover:bg-[#162550] border border-[#1b2c57] text-purple-300 transition-colors font-medium text-xs"
            >
              Guido van Rossum (Google vs CWI)
            </button>
            <button
              type="button"
              onClick={() => {
                const s = "Metformin completely cures 100% of all malignant breast cancers in all patients.";
                setClaimInput(s);
                void handleDiagnose(s);
              }}
              className="px-2.5 py-1 rounded-lg bg-[#0e1833] hover:bg-[#162550] border border-[#1b2c57] text-purple-300 transition-colors font-medium text-xs"
            >
              Numerical / Absolute Claim
            </button>
            <button
              type="button"
              onClick={() => {
                const s = "Dietary caffeine consumption directly causes acute stroke in healthy adults without exception.";
                setClaimInput(s);
                void handleDiagnose(s);
              }}
              className="px-2.5 py-1 rounded-lg bg-[#0e1833] hover:bg-[#162550] border border-[#1b2c57] text-purple-300 transition-colors font-medium text-xs"
            >
              Causal Overclaim
            </button>
          </div>

          {/* Diagnosis Result Card */}
          {analysisResult && (
            <div className="mt-4 rounded-xl border border-purple-500/30 bg-[#0c142b] p-5 space-y-4">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-[#18274d] pb-3">
                <div className="flex items-center gap-2.5 flex-wrap">
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
                  "{analysisResult.claim_text || claimInput || currentVerification?.claim || ""}"
                </p>
              </div>

              <div className="space-y-1">
                <p className="text-xs font-semibold text-purple-300">Forensic Diagnosis:</p>
                <p className="text-xs text-slate-300 leading-relaxed">
                  {analysisResult.explanation}
                </p>
              </div>

              {analysisResult.linguistic_cues && analysisResult.linguistic_cues.length > 0 && (
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

        {/* 12 Pattern Diagnostic Matrix */}
        <div className="space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div>
              <h2 className="text-lg font-bold text-white tracking-tight">12 Hallucination Pattern Diagnostics</h2>
              <p className="text-xs text-slate-400">
                Evidence-grounded status of all 12 distortion patterns evaluated for the active claim
              </p>
            </div>

            <div className="flex items-center gap-1.5 bg-[#0a1226] border border-[#17264a] p-1 rounded-xl">
              {["all", "detected", "critical", "high", "medium"].map((lvl) => (
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
            {filteredCatalog.map((item) => {
              const livePattern = detectedPatternMap.get(item.name.toLowerCase());
              const isDetected = livePattern?.detected === true;
              const severity = livePattern?.severity || item.defaultSeverity;
              const reason = livePattern?.reason || (analysisResult ? "Pattern criteria not triggered by the evaluated text." : item.description);
              const evidenceExcerpt = livePattern?.evidence;
              const confidence = livePattern?.confidence;

              return (
                <div
                  key={item.name}
                  className={`rounded-2xl border p-5 flex flex-col justify-between space-y-4 transition-all shadow-md ${
                    isDetected
                      ? "border-rose-500/50 bg-rose-950/20 shadow-rose-950/30"
                      : "border-[#172545] bg-[#091124] hover:border-purple-500/40"
                  }`}
                >
                  <div className="space-y-2.5">
                    <div className="flex items-center justify-between gap-2">
                      <h3 className="text-sm font-bold text-white flex items-center gap-1.5">
                        {isDetected ? (
                          <AlertTriangle className="size-4 text-rose-400 shrink-0" />
                        ) : (
                          <CheckCircle2 className="size-4 text-emerald-400 shrink-0" />
                        )}
                        {item.name}
                      </h3>

                      <Badge
                        className={`text-[10px] uppercase font-bold shrink-0 ${
                          isDetected
                            ? severity === "critical"
                              ? "bg-rose-600 text-white"
                              : "bg-rose-500/30 text-rose-300 border-rose-500/50"
                            : "bg-emerald-500/20 text-emerald-400 border-emerald-500/40"
                        }`}
                      >
                        {isDetected ? `${severity} Risk` : "Not Triggered"}
                      </Badge>
                    </div>

                    <div className="space-y-1">
                      <span className="text-[11px] font-semibold text-slate-400">Diagnosis:</span>
                      <p className="text-xs text-slate-300 leading-relaxed">
                        {reason}
                      </p>
                    </div>

                    {evidenceExcerpt && (
                      <div className="pt-2 border-t border-[#131f3b] space-y-1">
                        <span className="text-[10px] font-bold text-slate-500 uppercase">Evidence Reference:</span>
                        <p className="text-[11px] text-slate-400 italic bg-[#060c1d] p-2 rounded-lg border border-[#142240]">
                          {evidenceExcerpt}
                        </p>
                      </div>
                    )}

                    {confidence != null && (
                      <div className="flex items-center justify-between text-[11px] text-slate-400 pt-1">
                        <span>Confidence:</span>
                        <span className="font-semibold text-slate-200">{Math.round(confidence * 100)}%</span>
                      </div>
                    )}
                  </div>

                  <div className="rounded-xl bg-[#060c1d] border border-[#142240] p-3 text-xs space-y-1">
                    <span className="text-[10px] font-bold text-slate-500 uppercase">Example Distorted Assertion:</span>
                    <p className="text-[11px] text-slate-300 italic">"{item.example}"</p>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </AppShell>
  );
}
