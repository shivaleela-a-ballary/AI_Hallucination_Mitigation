import { createFileRoute } from "@tanstack/react-router";
import { useState } from "react";
import {
  AlertCircle,
  AlertTriangle,
  ArrowRight,
  BookOpen,
  CheckCircle2,
  ChevronDown,
  ChevronUp,
  Download,
  FileSearch,
  FileText,
  HelpCircle,
  Info,
  Layers,
  Loader2,
  ShieldAlert,
  ShieldCheck,
  Sparkles,
  UploadCloud,
  XCircle,
} from "lucide-react";

import { AppShell } from "@/components/app/app-shell";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { api, type PaperAuditResponse, type PaperAuditClaim } from "@/lib/api";
import { toast } from "sonner";

export const Route = createFileRoute("/research-paper-auditor")({
  component: ResearchPaperAuditorPage,
});

const SAMPLE_PAPERS = [
  {
    title: "Cardiovascular Prophylaxis & Secondary Event Prevention",
    text: `Abstract
Aspirin has been evaluated extensively for secondary cardiovascular event prophylaxis. In post-myocardial infarction cohorts, low-dose aspirin reduces relative risk of recurrent events by approximately 20% to 25% [1, 2]. However, widespread primary prevention remains contentious due to elevated gastrointestinal and intracerebral hemorrhagic risks.

Introduction
Cardiovascular diseases remain the leading contributor to global adult mortality. The efficacy of antiplatelet therapy in established ischemic arterial disease is supported by international guidelines.

Methods
We conducted a meta-analysis incorporating randomized clinical trials from PubMed and CrossRef, evaluating cohorts receiving 75mg to 100mg daily aspirin compared with placebo.

Results
Low-dose aspirin reduces the risk of secondary cardiovascular events significantly [1].
Patients in our trials experienced zero adverse hemorrhagic events in all instances without exception.
All adult human populations should unconditionally consume aspirin daily regardless of prior medical history.

Discussion
While secondary prophylactic utility is robustly verified, our findings reaffirm that categorical claims of universal safety without hemorrhage are contradictory to empirical clinical registries.`,
  },
  {
    title: "Metformin Evaluation in Diabetic Oncology Cohorts",
    text: `Abstract
Observational studies have suggested that biguanide therapy, specifically metformin, correlates with modest reductions in tumor incidence among diabetic cohorts. We investigated whether direct pharmacological intervention eradicates malignant neoplasia.

Methods
Cell culture assays and retrospective clinical registries across 12,000 diabetic patients were analyzed using multivariable regression modeling.

Results
Metformin was associated with an adjusted hazard ratio of 0.85 for colorectal carcinoma in diabetic patients [1].
Metformin completely cures 100% of all malignant breast cancers in all patients.
Metformin lowers hepatic gluconeogenesis through AMP-activated protein kinase activation [2].

Discussion
Laboratory findings demonstrate metabolic modulation, but assertions of complete curative cancer eradication are refuted by clinical trial consensus.`,
  },
];

function ResearchPaperAuditorPage() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [paperTitle, setPaperTitle] = useState("");
  const [paperText, setPaperText] = useState("");
  const [inputMode, setInputTextMode] = useState<"file" | "text">("text");
  const [auditing, setAuditing] = useState(false);
  const [auditReport, setAuditReport] = useState<PaperAuditResponse | null>(null);
  const [activeSection, setActiveSection] = useState<string>("All");

  const handleAudit = async () => {
    try {
      setAuditing(true);
      if (inputMode === "file" && selectedFile) {
        const res = await api.auditPaper(selectedFile);
        setAuditReport(res);
        toast.success("Manuscript audit completed successfully.");
      } else if (paperText.trim()) {
        const title = paperTitle.trim() || "Scientific Manuscript";
        const res = await api.auditPaperText(title, paperText);
        setAuditReport(res);
        toast.success("Manuscript audit completed successfully.");
      } else {
        toast.error("Please provide a paper file or paste manuscript text.");
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to audit manuscript.";
      toast.error(msg);
    } finally {
      setAuditing(false);
    }
  };

  const loadSample = (sample: typeof SAMPLE_PAPERS[0]) => {
    setInputTextMode("text");
    setPaperTitle(sample.title);
    setPaperText(sample.text);
    toast.info(`Loaded sample: ${sample.title}`);
  };

  const exportAuditSummary = () => {
    if (!auditReport) return;
    const jsonStr = JSON.stringify(auditReport, null, 2);
    const blob = new Blob([jsonStr], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${auditReport.paper_title.replace(/\s+/g, "_")}_audit_report.json`;
    a.click();
    toast.success("Audit report exported as JSON.");
  };

  const displayedClaims = auditReport
    ? auditReport.claims.filter((c) => activeSection === "All" || c.section.toLowerCase() === activeSection.toLowerCase())
    : [];

  return (
    <AppShell>
      <div className="space-y-7 max-w-6xl mx-auto">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-[#162340] pb-5">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <div className="size-8 rounded-lg bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center text-cyan-400">
                <FileSearch className="size-4.5" />
              </div>
              <h1 className="text-2xl font-extrabold text-white tracking-tight">
                Research Paper Auditor
              </h1>
            </div>
            <p className="text-xs sm:text-sm text-slate-400">
              Audit scientific papers across Abstract, Methods, Results, and Discussion against empirical evidence & citation integrity.
            </p>
          </div>

          <div className="flex items-center gap-2">
            <span className="text-xs text-slate-400 font-medium">Sample Papers:</span>
            {SAMPLE_PAPERS.map((s, idx) => (
              <button
                key={idx}
                type="button"
                onClick={() => loadSample(s)}
                className="text-xs px-2.5 py-1 rounded-lg bg-[#0e1935] hover:bg-[#162752] border border-[#1b2f61] text-cyan-300 font-medium transition-colors"
              >
                {idx === 0 ? "Cardiovascular" : "Oncology"}
              </button>
            ))}
          </div>
        </div>

        {/* Input Panel */}
        <div className="rounded-2xl border border-[#172545] bg-[#091124] p-6 space-y-4 shadow-lg">
          <div className="flex items-center justify-between">
            <h2 className="text-xs font-bold text-slate-300 uppercase tracking-wider">
              Upload Manuscript or Paste Sections
            </h2>
            <div className="flex items-center gap-1 bg-[#060c1d] border border-[#1b2b4f] p-0.5 rounded-lg text-xs">
              <button
                type="button"
                onClick={() => setInputTextMode("text")}
                className={`px-3 py-1 rounded-md font-semibold transition-colors ${
                  inputMode === "text" ? "bg-cyan-600 text-white" : "text-slate-400 hover:text-slate-200"
                }`}
              >
                Manuscript Text
              </button>
              <button
                type="button"
                onClick={() => setInputTextMode("file")}
                className={`px-3 py-1 rounded-md font-semibold transition-colors ${
                  inputMode === "file" ? "bg-cyan-600 text-white" : "text-slate-400 hover:text-slate-200"
                }`}
              >
                PDF Upload
              </button>
            </div>
          </div>

          {inputMode === "file" ? (
            <div className="rounded-xl border-2 border-dashed border-[#1c2c54] bg-[#060c1d] p-8 text-center space-y-3">
              <UploadCloud className="size-10 text-cyan-400 mx-auto" />
              <div className="space-y-1">
                <p className="text-sm font-semibold text-slate-200">
                  {selectedFile ? selectedFile.name : "Select or drag a PDF research paper"}
                </p>
                <p className="text-xs text-slate-400">PDF documents up to 20MB</p>
              </div>
              <input
                type="file"
                accept=".pdf"
                onChange={(e) => setSelectedFile(e.target.files?.[0] || null)}
                className="block mx-auto text-xs text-slate-400 file:mr-3 file:py-1.5 file:px-3.5 file:rounded-xl file:border-0 file:text-xs file:font-semibold file:bg-cyan-600 file:text-white hover:file:bg-cyan-500 cursor-pointer"
              />
            </div>
          ) : (
            <div className="space-y-3">
              <input
                value={paperTitle}
                onChange={(e) => setPaperTitle(e.target.value)}
                placeholder="Paper Title (e.g., Evaluation of Metformin in Oncology)"
                className="w-full h-10 rounded-xl bg-[#060c1d] border border-[#1c2c54] px-3.5 text-xs text-slate-100 placeholder:text-slate-500 focus:outline-none focus:border-cyan-500"
              />
              <textarea
                value={paperText}
                onChange={(e) => setPaperText(e.target.value)}
                rows={7}
                placeholder="Paste full paper sections (Abstract, Methods, Results, Discussion)..."
                className="w-full rounded-xl bg-[#060c1d] border border-[#1c2c54] p-3.5 text-xs text-slate-100 placeholder:text-slate-500 focus:outline-none focus:border-cyan-500 resize-y"
              />
            </div>
          )}

          <div className="flex justify-end pt-2 border-t border-[#131f3b]">
            <Button
              onClick={() => void handleAudit()}
              disabled={auditing || (inputMode === "file" ? !selectedFile : !paperText.trim())}
              className="rounded-xl bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white font-semibold text-xs px-6 shadow-md shadow-cyan-600/30"
            >
              {auditing ? (
                <>
                  <Loader2 className="size-3.5 mr-2 animate-spin" /> Auditing Paper Claims...
                </>
              ) : (
                <>
                  <Sparkles className="size-3.5 mr-2" /> Run Scientific Audit
                </>
              )}
            </Button>
          </div>
        </div>

        {/* Audit Report Results */}
        {auditReport && (
          <div className="space-y-6">
            {/* Overview Banner */}
            <div className="rounded-2xl border border-[#172545] bg-[#091124] p-6 space-y-5 shadow-xl">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-[#14203d] pb-4">
                <div className="space-y-1 max-w-2xl">
                  <span className="text-[10px] font-bold text-cyan-400 uppercase tracking-wider">
                    Audit Report Complete
                  </span>
                  <h3 className="text-lg font-bold text-white leading-snug">
                    {auditReport.paper_title}
                  </h3>
                  <p className="text-xs text-slate-400">
                    Analyzed {auditReport.total_sections} section(s): {auditReport.sections_analyzed.join(", ")}
                  </p>
                </div>

                <div className="flex items-center gap-2">
                  <Button
                    onClick={exportAuditSummary}
                    variant="outline"
                    size="sm"
                    className="rounded-xl border-[#1e3059] text-slate-200 text-xs hover:bg-[#101c38]"
                  >
                    <Download className="size-3.5 mr-1.5" /> Export Report
                  </Button>
                </div>
              </div>

              {/* Stats Row */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                <div className="rounded-xl bg-[#060c1d] border border-[#142240] p-4 text-center">
                  <span className="text-[10px] font-semibold text-slate-400 uppercase">Total Claims</span>
                  <p className="text-2xl font-bold text-white mt-1">{auditReport.total_claims}</p>
                  <span className="text-[10px] text-slate-500">Atomic assertions</span>
                </div>

                <div className="rounded-xl bg-[#060c1d] border border-[#142240] p-4 text-center">
                  <span className="text-[10px] font-semibold text-emerald-400 uppercase">Supported</span>
                  <p className="text-2xl font-bold text-emerald-400 mt-1">{auditReport.supported_claims}</p>
                  <span className="text-[10px] text-emerald-400/70">Empirically grounded</span>
                </div>

                <div className="rounded-xl bg-[#060c1d] border border-[#142240] p-4 text-center">
                  <span className="text-[10px] font-semibold text-rose-400 uppercase">Refuted / Contradicted</span>
                  <p className="text-2xl font-bold text-rose-400 mt-1">{auditReport.refuted_claims}</p>
                  <span className="text-[10px] text-rose-400/70">Contradicts evidence</span>
                </div>

                <div className="rounded-xl bg-[#060c1d] border border-[#142240] p-4 text-center">
                  <span className="text-[10px] font-semibold text-amber-400 uppercase">Unsupported Claims</span>
                  <p className="text-2xl font-bold text-amber-400 mt-1">{auditReport.unsupported_claim_count}</p>
                  <span className="text-[10px] text-amber-400/70">No citation or proof</span>
                </div>
              </div>

              <div className="rounded-xl bg-indigo-950/20 border border-indigo-500/25 p-4 text-xs text-slate-300 leading-relaxed">
                <strong className="text-cyan-400">Auditor Summary:</strong> {auditReport.summary}
              </div>
            </div>

            {/* Section Claims Filter & Breakdown */}
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h4 className="text-sm font-bold text-white">Section Claim Audits</h4>
                <div className="flex items-center gap-1.5 bg-[#091124] border border-[#172545] p-1 rounded-xl">
                  {["All", ...auditReport.sections_analyzed].map((sec) => (
                    <button
                      key={sec}
                      type="button"
                      onClick={() => setActiveSection(sec)}
                      className={`text-xs px-3 py-1 rounded-lg font-semibold capitalize transition-colors ${
                        activeSection.toLowerCase() === sec.toLowerCase()
                          ? "bg-cyan-600 text-white shadow"
                          : "text-slate-400 hover:text-slate-200"
                      }`}
                    >
                      {sec}
                    </button>
                  ))}
                </div>
              </div>

              <div className="space-y-3">
                {displayedClaims.map((claim, idx) => {
                  const status = claim.verification_status.toUpperCase();
                  const isSupported = status === "SUPPORTED";
                  const isRefuted = status === "REFUTED";

                  return (
                    <div
                      key={idx}
                      className="rounded-2xl border border-[#172545] bg-[#091124] p-5 space-y-3"
                    >
                      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                        <div className="flex items-center gap-2">
                          <Badge variant="outline" className="border-cyan-500/30 text-cyan-300 bg-cyan-950/20 text-xs">
                            {claim.section}
                          </Badge>
                          <Badge
                            className={
                              isSupported
                                ? "bg-emerald-500/20 text-emerald-400 border-emerald-500/40 text-xs"
                                : isRefuted
                                ? "bg-rose-500/20 text-rose-400 border-rose-500/40 text-xs"
                                : "bg-amber-500/20 text-amber-400 border-amber-500/40 text-xs"
                            }
                          >
                            {status}
                          </Badge>
                          {claim.has_citation ? (
                            <Badge variant="outline" className="border-slate-700 text-slate-300 text-[10px]">
                              Cited ({claim.citation_keys.join(", ")})
                            </Badge>
                          ) : (
                            <Badge variant="outline" className="border-amber-500/40 text-amber-400 bg-amber-950/20 text-[10px]">
                              ⚠️ Uncited Assertion
                            </Badge>
                          )}
                        </div>

                        <div className="text-xs text-slate-400">
                          Risk Score: <strong className={claim.risk_score > 0.6 ? "text-rose-400" : "text-emerald-400"}>{Math.round(claim.risk_score * 100)}%</strong>
                        </div>
                      </div>

                      <p className="text-xs sm:text-sm font-semibold text-slate-100 leading-relaxed">
                        "{claim.claim_text}"
                      </p>

                      {claim.notes && (
                        <p className="text-xs text-slate-400 leading-normal">
                          {claim.notes}
                        </p>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        )}
      </div>
    </AppShell>
  );
}
