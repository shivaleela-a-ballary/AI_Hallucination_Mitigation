import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import {
  Activity,
  AlertTriangle,
  ArrowRight,
  BookOpen,
  CheckCircle2,
  ChevronDown,
  ChevronUp,
  Copy,
  ExternalLink,
  FileCheck,
  FileText,
  HelpCircle,
  Layers,
  Loader2,
  RefreshCw,
  Scale,
  ShieldAlert,
  ShieldCheck,
  Sparkles,
  Upload,
  XCircle,
} from "lucide-react";

import { AppShell } from "@/components/app/app-shell";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Textarea } from "@/components/ui/textarea";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { api, type CheckAnswerResponse, type CheckAnswerClaim, type UploadedDocument } from "@/lib/api";
import { toast } from "sonner";

export const Route = createFileRoute("/check-answer")({
  validateSearch: (search: Record<string, unknown>) => ({
    q: typeof search.q === "string" ? search.q : "",
  }),
  component: CheckAnswerPage,
});

const samplePresets = [
  {
    label: "Oncology Overclaim",
    text: "Metformin completely eliminates 100% of all malignant breast cancer tumors without any side effects in human clinical trials.",
  },
  {
    label: "Cardiovascular Claim",
    text: "Low-dose aspirin is universally prescribed to prevent primary myocardial infarction, eliminating cardiac risk in all patients.",
  },
  {
    label: "Genetics / CRISPR",
    text: "CRISPR-Cas9 gene editing has achieved zero off-target cleavage mutations in all therapeutic clinical settings worldwide.",
  },
];

function CheckAnswerPage() {
  const search = Route.useSearch();
  const [inputText, setInputText] = useState(search.q || "");
  const [selectedDocId, setSelectedDocId] = useState<string>("");
  const [uploadedDocs, setUploadedDocs] = useState<UploadedDocument[]>([]);
  const [analyzing, setAnalyzing] = useState(false);
  const [result, setResult] = useState<CheckAnswerResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [expandedClaim, setExpandedClaim] = useState<number | null>(null);
  const [activeTab, setActiveTab] = useState("claims");

  useEffect(() => {
    // Load available reference documents for optional contextual ingestion
    api.getUploads().then((res) => {
      if (res?.documents) setUploadedDocs(res.documents);
    }).catch(() => {});
  }, []);

  const handleRunAnalysis = async (textToAnalyze?: string) => {
    const text = (textToAnalyze ?? inputText).trim();
    if (!text || text.length < 5) {
      toast.error("Please enter an answer of at least 5 characters.");
      return;
    }

    try {
      setAnalyzing(true);
      setError(null);
      const res = await api.checkAnswer(text, {
        document_id: selectedDocId || undefined,
      });
      setResult(res);
      toast.success("Analysis complete: Verified against empirical corpus.");
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to analyze answer.";
      setError(msg);
      toast.error(msg);
    } finally {
      setAnalyzing(false);
    }
  };

  const handlePresetSelect = (presetText: string) => {
    setInputText(presetText);
    void handleRunAnalysis(presetText);
  };

  return (
    <AppShell>
      <div className="space-y-7 max-w-6xl mx-auto">
        {/* Header Banner */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-[#162340] pb-5">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <div className="size-8 rounded-lg bg-indigo-500/10 border border-indigo-500/30 flex items-center justify-center text-indigo-400">
                <FileCheck className="size-4.5" />
              </div>
              <h1 className="text-2xl font-extrabold text-white tracking-tight">
                Check AI Answer Workspace
              </h1>
            </div>
            <p className="text-xs sm:text-sm text-slate-400">
              Decompose AI responses into factual claims, inspect evidence grounding, detect forensics patterns, and view empirical corrections.
            </p>
          </div>

          <div className="flex items-center gap-2">
            <span className="text-xs text-slate-400 font-medium">Quick Presets:</span>
            {samplePresets.map((preset) => (
              <button
                key={preset.label}
                type="button"
                onClick={() => handlePresetSelect(preset.text)}
                className="text-xs px-2.5 py-1 rounded-lg bg-[#0e1935] hover:bg-[#162752] border border-[#1b2f61] text-indigo-300 font-medium transition-colors"
              >
                {preset.label}
              </button>
            ))}
          </div>
        </div>

        {/* Input & Context Panel */}
        <div className="rounded-2xl border border-[#172545] bg-[#091124] p-5 space-y-4 shadow-lg">
          <div className="flex items-center justify-between">
            <label htmlFor="ai-answer-input" className="text-xs font-bold text-slate-300 uppercase tracking-wider">
              Paste AI-Generated Response
            </label>
            <span className="text-xs text-slate-500">{inputText.length} characters</span>
          </div>

          <Textarea
            id="ai-answer-input"
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            placeholder="Paste multi-sentence AI answer here (e.g., 'Metformin cures 100% of all malignant tumors...')"
            rows={4}
            className="rounded-xl border-[#1d2d52] bg-[#060c1d] p-4 text-sm text-slate-100 placeholder:text-slate-500 focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 resize-y"
          />

          {/* Contextual Document Ingestion Attachment */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pt-2 border-t border-[#131f3b]">
            <div className="flex items-center gap-2.5 text-xs text-slate-400">
              <BookOpen className="size-4 text-indigo-400 shrink-0" />
              <span>Reference Document (Optional):</span>
              <select
                value={selectedDocId}
                onChange={(e) => setSelectedDocId(e.target.value)}
                className="rounded-lg border border-[#1d2d52] bg-[#0c1630] px-2.5 py-1 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
              >
                <option value="">Default SciFact Knowledge Base (Indexed)</option>
                {uploadedDocs.map((doc) => (
                  <option key={doc.id} value={doc.id}>
                    Attached: {doc.title} ({doc.filename})
                  </option>
                ))}
              </select>
            </div>

            <div className="flex items-center gap-2 self-end sm:self-auto">
              {inputText && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => {
                    setInputText("");
                    setResult(null);
                  }}
                  className="text-xs text-slate-400 hover:text-slate-200"
                >
                  Clear
                </Button>
              )}
              <Button
                onClick={() => void handleRunAnalysis()}
                disabled={analyzing || !inputText.trim()}
                className="rounded-xl bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 text-white font-semibold text-xs px-5 shadow-md shadow-indigo-600/30"
              >
                {analyzing ? (
                  <>
                    <Loader2 className="size-3.5 mr-2 animate-spin" /> Verifying Claims...
                  </>
                ) : (
                  <>
                    <Sparkles className="size-3.5 mr-2" /> Decompose & Verify
                  </>
                )}
              </Button>
            </div>
          </div>
        </div>

        {error && (
          <div className="rounded-xl border border-rose-500/30 bg-rose-500/10 p-4 text-xs text-rose-300 flex items-center gap-3">
            <XCircle className="size-5 shrink-0 text-rose-400" />
            <span>{error}</span>
          </div>
        )}

        {/* Verification Results Panel */}
        {result && (
          <div className="space-y-6">
            {/* Overview Metric Row */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
              <div className="rounded-2xl border border-[#172545] bg-[#091124] p-4 text-center">
                <p className="text-[11px] font-semibold text-slate-400 uppercase">Reliability Score</p>
                <p className="text-2xl font-bold text-white mt-1">
                  {Math.round(result.overall_reliability_score * 100)}%
                </p>
                <span className="text-[10px] text-slate-500">Based on factual grounding</span>
              </div>

              <div className="rounded-2xl border border-[#172545] bg-[#091124] p-4 text-center">
                <p className="text-[11px] font-semibold text-slate-400 uppercase">Hallucination Risk</p>
                <Badge
                  className={`mt-2 ${
                    result.overall_hallucination_risk === "HIGH"
                      ? "bg-rose-500/20 text-rose-400 border-rose-500/40"
                      : result.overall_hallucination_risk === "MODERATE"
                      ? "bg-amber-500/20 text-amber-400 border-amber-500/40"
                      : "bg-emerald-500/20 text-emerald-400 border-emerald-500/40"
                  }`}
                >
                  {result.overall_hallucination_risk} RISK
                </Badge>
              </div>

              <div className="rounded-2xl border border-[#172545] bg-[#091124] p-4 text-center">
                <p className="text-[11px] font-semibold text-slate-400 uppercase">Claims Decomposed</p>
                <p className="text-2xl font-bold text-cyan-400 mt-1">{result.total_claims}</p>
                <span className="text-[10px] text-slate-500">
                  {result.supported_claims_count} supported · {result.refuted_claims_count} refuted
                </span>
              </div>

              <div className="rounded-2xl border border-[#172545] bg-[#091124] p-4 text-center">
                <p className="text-[11px] font-semibold text-slate-400 uppercase">Empirical Proof</p>
                <div className="mt-2 inline-flex items-center gap-1.5 text-xs font-semibold text-emerald-400">
                  <ShieldCheck className="size-4" />
                  <span>Cross-Referenced</span>
                </div>
              </div>
            </div>

            {/* Evidence Quality Safeguard Banner */}
            <div className="rounded-xl border border-indigo-500/20 bg-indigo-950/20 px-4 py-3 flex items-center justify-between text-xs text-slate-300">
              <div className="flex items-center gap-2.5">
                <ShieldCheck className="size-4 text-cyan-400 shrink-0" />
                <span>
                  <strong>Evidence Separation Safeguard Active:</strong> Semantic similarity is strictly separated from factual entailment. Irrelevant or contradictory scientific papers are flagged.
                </span>
              </div>
              <Badge variant="outline" className="border-cyan-500/30 text-cyan-400 shrink-0">
                FAISS + SciFact Grounded
              </Badge>
            </div>

            {/* Results Tabs: Claims vs Corrected Answer */}
            <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4">
              <TabsList className="bg-[#0b1328] border border-[#172545] p-1 rounded-xl">
                <TabsTrigger value="claims" className="rounded-lg text-xs font-semibold data-[state=active]:bg-indigo-600 data-[state=active]:text-white">
                  Decomposed Claims ({result.claims.length})
                </TabsTrigger>
                <TabsTrigger value="correction" className="rounded-lg text-xs font-semibold data-[state=active]:bg-indigo-600 data-[state=active]:text-white">
                  Corrected Answer (Before/After)
                </TabsTrigger>
                <TabsTrigger value="sources" className="rounded-lg text-xs font-semibold data-[state=active]:bg-indigo-600 data-[state=active]:text-white">
                  Evidence Sources
                </TabsTrigger>
              </TabsList>

              {/* TAB 1: CLAIMS */}
              <TabsContent value="claims" className="space-y-4">
                {result.claims.map((claimItem, idx) => {
                  const status = claimItem.verification_status.toUpperCase();
                  const isSupported = status === "SUPPORTED";
                  const isRefuted = status === "REFUTED";
                  const isExpanded = expandedClaim === idx;
                  const riskScore = claimItem.risk_score ?? (isRefuted ? 0.85 : isSupported ? 0.15 : 0.5);

                  return (
                    <div
                      key={idx}
                      className="rounded-2xl border border-[#172545] bg-[#091124] overflow-hidden transition-colors"
                    >
                      <div className="p-5 space-y-3">
                        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                          <div className="flex items-center gap-2">
                            <span className="size-6 rounded-md bg-[#101b36] border border-[#1c2c54] text-slate-400 font-bold text-xs flex items-center justify-center">
                              #{idx + 1}
                            </span>
                            <Badge
                              className={
                                isSupported
                                  ? "bg-emerald-500/20 text-emerald-400 border-emerald-500/40 font-bold text-xs"
                                  : isRefuted
                                  ? "bg-rose-500/20 text-rose-400 border-rose-500/40 font-bold text-xs"
                                  : "bg-amber-500/20 text-amber-400 border-amber-500/40 font-bold text-xs"
                              }
                            >
                              {status}
                            </Badge>

                            {claimItem.forensics?.pattern_type && claimItem.forensics.pattern_type !== "None / Valid" && (
                              <Badge variant="outline" className="border-rose-500/40 text-rose-300 bg-rose-950/20 text-[11px]">
                                🕵️ {claimItem.forensics.pattern_type}
                              </Badge>
                            )}
                          </div>

                          <div className="flex items-center gap-3 text-xs text-slate-400">
                            <span>Risk Score: <strong className={riskScore > 0.6 ? "text-rose-400" : riskScore > 0.25 ? "text-amber-400" : "text-emerald-400"}>{Math.round(riskScore * 100)}%</strong></span>
                            <span>Confidence: <strong className="text-slate-200">{Math.round(claimItem.confidence_score * 100)}%</strong></span>
                          </div>
                        </div>

                        <p className="text-sm font-semibold text-slate-100 leading-relaxed">
                          "{claimItem.claim}"
                        </p>

                        <p className="text-xs text-slate-400 leading-normal">
                          {claimItem.explanation}
                        </p>

                        {/* Verified Correction Card if Available */}
                        {claimItem.correction && (
                          <div className="mt-3 rounded-xl border border-emerald-500/30 bg-emerald-950/20 p-3.5 space-y-2">
                            <div className="flex items-center justify-between text-xs">
                              <span className="font-bold text-emerald-400 flex items-center gap-1.5">
                                <CheckCircle2 className="size-4 text-emerald-400" />
                                Verified Factual Correction
                              </span>
                              <Badge variant="outline" className="border-emerald-500/40 text-emerald-300 text-[10px]">
                                Risk Reduced by {claimItem.correction.risk_reduction_pct}%
                              </Badge>
                            </div>
                            <p className="text-xs text-slate-200 font-medium">
                              "{claimItem.correction.candidate_correction}"
                            </p>
                          </div>
                        )}

                        {/* Expand / Collapse Evidence Toggle */}
                        <div className="pt-2 flex justify-between items-center border-t border-[#121c33]">
                          <span className="text-xs text-slate-500">
                            {claimItem.evidence_count} evidence source(s) evaluated
                          </span>
                          <button
                            type="button"
                            onClick={() => setExpandedClaim(isExpanded ? null : idx)}
                            className="text-xs text-indigo-400 hover:text-indigo-300 font-semibold flex items-center gap-1"
                          >
                            {isExpanded ? "Hide Evidence" : "Inspect Evidence Details"}
                            {isExpanded ? <ChevronUp className="size-3.5" /> : <ChevronDown className="size-3.5" />}
                          </button>
                        </div>
                      </div>

                      {/* Evidence Dropdown */}
                      {isExpanded && (
                        <div className="bg-[#060c1d] border-t border-[#172545] p-5 space-y-3">
                          <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider">
                            Corpus Evidence Match Details
                          </h4>
                          {claimItem.supporting_evidence?.length > 0 && (
                            <div className="space-y-2">
                              <span className="text-xs font-semibold text-emerald-400">Supporting Evidence:</span>
                              {claimItem.supporting_evidence.map((ev, sIdx) => (
                                <div key={sIdx} className="rounded-xl border border-emerald-500/20 bg-emerald-950/10 p-3 text-xs text-slate-300 space-y-1">
                                  <div className="flex justify-between font-semibold text-emerald-300">
                                    <span>{ev.title || "Evidence Document"}</span>
                                    <span>{Math.round((ev.similarity_score || 0) * 100)}% match</span>
                                  </div>
                                  <p className="text-slate-400 text-[11px] leading-relaxed">
                                    {ev.content}
                                  </p>
                                </div>
                              ))}
                            </div>
                          )}

                          {claimItem.contradicting_evidence?.length > 0 && (
                            <div className="space-y-2">
                              <span className="text-xs font-semibold text-rose-400">Contradicting Evidence:</span>
                              {claimItem.contradicting_evidence.map((ev, cIdx) => (
                                <div key={cIdx} className="rounded-xl border border-rose-500/20 bg-rose-950/10 p-3 text-xs text-slate-300 space-y-1">
                                  <div className="flex justify-between font-semibold text-rose-300">
                                    <span>{ev.title || "Contradictory Source"}</span>
                                    <span>{Math.round((ev.similarity_score || 0) * 100)}% match</span>
                                  </div>
                                  <p className="text-slate-400 text-[11px] leading-relaxed">
                                    {ev.content}
                                  </p>
                                </div>
                              ))}
                            </div>
                          )}

                          {(!claimItem.supporting_evidence?.length && !claimItem.contradicting_evidence?.length) && (
                            <p className="text-xs text-slate-500 italic">
                              No definitive supporting or refuting citations found in current corpus. Classified as UNCERTAIN.
                            </p>
                          )}
                        </div>
                      )}
                    </div>
                  );
                })}
              </TabsContent>

              {/* TAB 2: CORRECTED ANSWER (BEFORE / AFTER) */}
              <TabsContent value="correction" className="space-y-5">
                <div className="rounded-2xl border border-[#172545] bg-[#091124] p-6 space-y-6">
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-[#14203d] pb-4">
                    <div>
                      <h3 className="text-base font-bold text-white">Before vs After Hallucination Mitigation</h3>
                      <p className="text-xs text-slate-400">Direct comparison of original AI response against evidence-grounded answer</p>
                    </div>
                    {result.before_after && (
                      <Badge className="bg-emerald-500/20 text-emerald-400 border-emerald-500/30 text-xs font-bold self-start sm:self-auto">
                        Risk Reduced by {result.before_after.risk_reduction_percentage}%
                      </Badge>
                    )}
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    {/* Before Column */}
                    <div className="rounded-xl border border-rose-500/30 bg-rose-950/10 p-5 space-y-3">
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-bold text-rose-400 uppercase tracking-wider flex items-center gap-1.5">
                          <XCircle className="size-4" /> Original AI Response
                        </span>
                        <Badge variant="outline" className="border-rose-500/30 text-rose-400 text-[10px]">
                          Unmitigated
                        </Badge>
                      </div>
                      <p className="text-xs sm:text-sm text-slate-300 leading-relaxed whitespace-pre-wrap">
                        {result.original_text}
                      </p>
                    </div>

                    {/* After Column */}
                    <div className="rounded-xl border border-emerald-500/30 bg-emerald-950/10 p-5 space-y-3">
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-bold text-emerald-400 uppercase tracking-wider flex items-center gap-1.5">
                          <CheckCircle2 className="size-4" /> Grounded & Verified Output
                        </span>
                        <Badge variant="outline" className="border-emerald-500/30 text-emerald-400 text-[10px]">
                          Evidence Grounded
                        </Badge>
                      </div>
                      <p className="text-xs sm:text-sm text-emerald-100 font-medium leading-relaxed whitespace-pre-wrap">
                        {result.corrected_answer || result.original_text}
                      </p>
                    </div>
                  </div>

                  <div className="rounded-xl bg-[#0c152e] border border-[#1a2b54] p-4 text-xs text-slate-300 space-y-1">
                    <strong className="text-cyan-400">Zero Correction Hallucination Guarantee:</strong>
                    <p className="text-slate-400 leading-relaxed">
                      Every proposed correction is verified against empirical evidence before display. If adequate evidence is lacking, claims are hedged or designated uncertain rather than generating unverified assertions.
                    </p>
                  </div>
                </div>
              </TabsContent>

              {/* TAB 3: EVIDENCE SOURCES */}
              <TabsContent value="sources" className="space-y-4">
                <div className="rounded-2xl border border-[#172545] bg-[#091124] p-6 space-y-4">
                  <h3 className="text-base font-bold text-white">Corpus Evidence Sources Evaluated</h3>
                  <div className="space-y-3">
                    {result.claims.flatMap((c) => [...(c.supporting_evidence || []), ...(c.contradicting_evidence || [])]).length > 0 ? (
                      result.claims.flatMap((c) => [...(c.supporting_evidence || []), ...(c.contradicting_evidence || [])]).map((s, idx) => (
                        <div key={idx} className="rounded-xl bg-[#0c1630] border border-[#192a50] p-4 text-xs space-y-1.5">
                          <div className="flex justify-between font-semibold text-slate-200">
                            <span className="truncate max-w-lg">{s.title || "Corpus Source"}</span>
                            <span className="text-indigo-400 font-mono text-[11px]">
                              {Math.round((s.similarity_score || 0) * 100)}% relevance
                            </span>
                          </div>
                          <p className="text-slate-400 text-[11px] leading-relaxed">{s.content}</p>
                          <div className="flex items-center gap-3 pt-1 text-[10px] text-slate-500 font-medium">
                            <span>Source: {s.source || "SciFact / Biomedical"}</span>
                            {s.url && (
                              <a href={s.url} target="_blank" rel="noreferrer" className="text-indigo-400 hover:underline flex items-center gap-1">
                                View Paper <ExternalLink className="size-2.5" />
                              </a>
                            )}
                          </div>
                        </div>
                      ))
                    ) : (
                      <p className="text-xs text-slate-500 py-4 text-center">
                        No external documents retrieved above strict relevance threshold.
                      </p>
                    )}
                  </div>
                </div>
              </TabsContent>
            </Tabs>
          </div>
        )}
      </div>
    </AppShell>
  );
}
