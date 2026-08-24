import { createFileRoute } from "@tanstack/react-router";
import { useState } from "react";
import {
  ArrowRight,
  ShieldCheck,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  HelpCircle,
  Loader2,
  FileCheck2,
  ExternalLink,
  Sparkles,
} from "lucide-react";

import { AppShell } from "@/components/app/app-shell";
import { PageHeader, SectionCard } from "@/components/app/ui-kit";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { api, type CheckAnswerResponse } from "@/lib/api";

export const Route = createFileRoute("/check-answer")({
  head: () => ({ meta: [{ title: "Check AI Answer — AI Hallucination Mitigation System" }] }),
  component: CheckAnswerPage,
});

function getStatusBadge(status?: string) {
  const norm = (status || "").toUpperCase();
  if (norm === "SUPPORTED") {
    return {
      label: "SUPPORTED",
      icon: CheckCircle2,
      color: "bg-emerald-500/15 text-emerald-600 dark:text-emerald-400 border-emerald-500/30",
    };
  }
  if (norm === "REFUTED") {
    return {
      label: "REFUTED",
      icon: XCircle,
      color: "bg-rose-500/15 text-rose-600 dark:text-rose-400 border-rose-500/30",
    };
  }
  return {
    label: "UNCERTAIN",
    icon: HelpCircle,
    color: "bg-amber-500/15 text-amber-600 dark:text-amber-400 border-amber-500/30",
  };
}

function getRiskBadge(risk?: string) {
  const norm = (risk || "MEDIUM").toUpperCase();
  if (norm === "LOW") {
    return {
      label: "LOW RISK",
      color: "bg-emerald-500/15 text-emerald-600 dark:text-emerald-400 border-emerald-500/30",
    };
  }
  if (norm === "HIGH") {
    return {
      label: "HIGH RISK",
      color: "bg-rose-500/15 text-rose-600 dark:text-rose-400 border-rose-500/30",
    };
  }
  return {
    label: "MEDIUM RISK",
    color: "bg-amber-500/15 text-amber-600 dark:text-amber-400 border-amber-500/30",
  };
}

function CheckAnswerPage() {
  const [text, setText] = useState("");
  const [result, setResult] = useState<CheckAnswerResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const checkAnswer = async () => {
    const cleanText = text.trim();
    if (!cleanText || cleanText.length < 15) {
      setError("Please paste a multi-sentence AI generated answer or paragraph to analyze (minimum 15 characters).");
      return;
    }

    setLoading(true);
    setError("");
    setResult(null);

    try {
      const resp = await api.checkAnswer(cleanText);
      setResult(resp);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "AI Answer check failed.");
    } finally {
      setLoading(false);
    }
  };

  const samplePrompt = () => {
    setText(
      "MicroRNAs regulate mRNA translation and induce cleavage of target genes. Penicillin is completely ineffective against bacterial infections. Insulin suppresses hepatic glucose production in human physiology."
    );
  };

  return (
    <AppShell>
      <PageHeader
        title="Check AI Answer (Decomposition & Audit)"
        description="Paste an AI-generated paragraph. The system decomposes it into atomic factual claims, verifies each claim across PubMed and SciFact, and compiles an overall reliability report."
      />

      <SectionCard title="AI-Generated Text to Audit">
        <Textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder="Paste AI response here (e.g. medical summaries, scientific explanations, or LLM generated answers)..."
          className="min-h-36 resize-none rounded-xl bg-background text-sm leading-relaxed"
        />
        <div className="mt-3 flex flex-wrap items-center justify-between gap-2 text-xs text-muted-foreground">
          <button
            type="button"
            onClick={samplePrompt}
            className="text-primary hover:underline font-medium inline-flex items-center gap-1"
          >
          </button>
          <span>{text.length}/5000 characters</span>
        </div>
      </SectionCard>

      <div className="mt-4 flex items-center gap-3">
        <Button
          className="h-12 rounded-xl px-7 font-medium shadow-sm"
          disabled={loading}
          onClick={() => void checkAnswer()}
        >
          {loading ? (
            <>
              <Loader2 className="size-4 mr-2 animate-spin" /> Auditing AI Answer Claims...
            </>
          ) : (
            <>
              Audit AI Answer <ArrowRight className="size-4 ml-2" />
            </>
          )}
        </Button>
      </div>

      {error && (
        <div role="alert" className="mt-4 rounded-xl border border-destructive/30 bg-destructive/10 p-4 text-sm text-destructive flex items-center gap-2">
          <AlertTriangle className="size-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {result && (
        <div className="mt-8 space-y-6">
          {/* Summary Reliability Card */}
          <div className="rounded-2xl border border-border bg-card p-6 shadow-sm">
            <div className="flex flex-wrap items-center justify-between gap-4 border-b border-border pb-6">
              <div>
                <span className="text-xs font-semibold tracking-wider text-muted-foreground uppercase">
                  AI Answer Reliability Audit
                </span>
                <div className="mt-2 flex items-center gap-3">
                  <div className="text-3xl font-black tracking-tight text-foreground">
                    {result.overall_reliability_score}%
                  </div>
                  <Badge variant="outline" className={`h-8 px-3 text-xs font-semibold ${getRiskBadge(result.overall_hallucination_risk).color}`}>
                    {getRiskBadge(result.overall_hallucination_risk).label}
                  </Badge>
                </div>
              </div>
            </div>

            {/* Claim Counts */}
            <div className="mt-6 grid grid-cols-2 gap-4 sm:grid-cols-4">
              <div className="rounded-xl border border-border bg-muted/30 p-3">
                <div className="text-xs text-muted-foreground">Total Claims Extracted</div>
                <div className="mt-1 text-xl font-bold">{result.total_claims}</div>
              </div>
              <div className="rounded-xl border border-emerald-500/20 bg-emerald-500/5 p-3">
                <div className="text-xs text-emerald-600 dark:text-emerald-400">Supported Claims</div>
                <div className="mt-1 text-xl font-bold text-emerald-600 dark:text-emerald-400">
                  {result.supported_claims_count}
                </div>
              </div>
              <div className="rounded-xl border border-rose-500/20 bg-rose-500/5 p-3">
                <div className="text-xs text-rose-600 dark:text-rose-400">Refuted (Hallucinations)</div>
                <div className="mt-1 text-xl font-bold text-rose-600 dark:text-rose-400">
                  {result.refuted_claims_count}
                </div>
              </div>
              <div className="rounded-xl border border-amber-500/20 bg-amber-500/5 p-3">
                <div className="text-xs text-amber-600 dark:text-amber-400">Uncertain Claims</div>
                <div className="mt-1 text-xl font-bold text-amber-600 dark:text-amber-400">
                  {result.uncertain_claims_count}
                </div>
              </div>
            </div>

            <p className="mt-4 text-xs sm:text-sm text-muted-foreground">
              {result.summary}
            </p>
          </div>

          {/* Claim by Claim Breakdown */}
          <SectionCard title={`Decomposed Claim Analysis (${result.claims.length})`}>
            <div className="space-y-4">
              {result.claims.map((c, idx) => {
                const badge = getStatusBadge(c.verification_status);
                const risk = getRiskBadge(c.hallucination_risk);
                return (
                  <div
                    key={idx}
                    className="rounded-xl border border-border bg-card p-4 transition-all hover:border-primary/40"
                  >
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-bold text-muted-foreground">Claim #{idx + 1}</span>
                        <span className={`inline-flex items-center gap-1 rounded-md border px-2 py-0.5 text-xs font-semibold ${badge.color}`}>
                          <badge.icon className="size-3" />
                          {badge.label}
                        </span>
                        <span className={`inline-flex items-center rounded-md border px-2 py-0.5 text-xs font-semibold ${risk.color}`}>
                          {risk.label}
                        </span>
                      </div>
                      <div className="text-xs text-muted-foreground">
                        {c.evidence_count} evidence source(s)
                      </div>
                    </div>

                    <p className="mt-2 text-sm font-semibold text-foreground">
                      "{c.claim}"
                    </p>

                    {c.explanation && (
                      <p className="mt-1.5 text-xs text-muted-foreground">
                        {c.explanation}
                      </p>
                    )}

                    {/* Supporting Sources */}
                    {c.supporting_evidence && c.supporting_evidence.length > 0 && (
                      <div className="mt-3 rounded-lg border border-emerald-500/20 bg-emerald-500/5 p-2.5">
                        <div className="text-xs font-semibold text-emerald-600 dark:text-emerald-400 flex items-center gap-1">
                          <CheckCircle2 className="size-3" /> Supporting Evidence:
                        </div>
                        {c.supporting_evidence.map((ev, eIdx) => (
                          <div key={eIdx} className="mt-1 text-xs text-foreground/80">
                            • <span className="font-medium">{ev.source}</span>: {ev.title}
                          </div>
                        ))}
                      </div>
                    )}

                    {/* Contradicting Sources */}
                    {c.contradicting_evidence && c.contradicting_evidence.length > 0 && (
                      <div className="mt-3 rounded-lg border border-rose-500/20 bg-rose-500/5 p-2.5">
                        <div className="text-xs font-semibold text-rose-600 dark:text-rose-400 flex items-center gap-1">
                          <AlertTriangle className="size-3" /> Contradicting Evidence:
                        </div>
                        {c.contradicting_evidence.map((ev, eIdx) => (
                          <div key={eIdx} className="mt-1 text-xs text-foreground/80">
                            • <span className="font-medium">{ev.source}</span>: {ev.title}
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </SectionCard>
        </div>
      )}
    </AppShell>
  );
}
