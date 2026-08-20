import { createFileRoute, Link, useParams } from "@tanstack/react-router";
import { ArrowLeft, Copy, Info, Share2 } from "lucide-react";
import { useEffect, useState } from "react";

import { AppShell } from "@/components/app/app-shell";
import { ConfidenceBar, ResultBadge, SectionCard } from "@/components/app/ui-kit";
import { InteractiveKnowledgeGraph } from "@/components/app/interactive-knowledge-graph";
import { Button } from "@/components/ui/button";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import { toast } from "sonner";
import { api, toResult, type AnswerRecord } from "@/lib/api";
import { answerParagraphs, claimStatus, confidenceLabel, statusExplanation } from "@/lib/presentation";

export const Route = createFileRoute("/answer/$id")({
  head: () => ({
    meta: [
      { title: "Answer Details — AI Hallucination Mitigation System" },
      {
        name: "description",
        content: "Review the verified answer, its result, confidence score and supporting evidence.",
      },
      { property: "og:title", content: "Answer Details — AI Hallucination Mitigation System" },
      { property: "og:description", content: "Result, confidence score and supporting evidence." },
    ],
  }),
  component: AnswerDetails,
});

function AnswerDetails() {
  const { id } = useParams({ from: "/answer/$id" });
  const [record, setRecord] = useState<AnswerRecord | null>(null);
  const [error, setError] = useState("");
  useEffect(() => { api.answer(id).then(setRecord).catch((cause) => setError(cause instanceof Error ? cause.message : "Answer not found")); }, [id]);
  if (error) return <AppShell><p className="card-soft p-6 text-sm text-muted-foreground">Answer not found.</p></AppShell>;
  if (!record) return <AppShell><p className="text-sm text-muted-foreground">Loading answer…</p></AppShell>;
  const question = record.query;
  const result = toResult(record.verification_status);
  const confidence = record.confidence_score;
  const pct = Math.round(confidence * 100);
  const level = confidence >= 0.7 ? "High" : confidence >= 0.4 ? "Medium" : "Low";

  return (
    <AppShell>
      <div className="mb-6 grid grid-cols-[auto_minmax(0,1fr)_auto] items-center gap-3">
        <Link
          to="/history"
          aria-label="Back to history"
          className="grid size-10 place-items-center rounded-xl text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
        >
          <ArrowLeft className="size-5" />
        </Link>
        <h1 className="truncate text-2xl font-bold tracking-tight">Answer Details</h1>
        <Button
          variant="outline"
          className="rounded-xl"
          onClick={() => {
            navigator.clipboard?.writeText(window.location.href);
            toast.success("Link copied to clipboard");
          }}
        >
          <Share2 className="size-4" /> Share
        </Button>
      </div>

      <div className="flex flex-col gap-6">
        <SectionCard
          title="Your Question"
          action={
            <button
              type="button"
              aria-label="Copy question"
              onClick={() => {
                navigator.clipboard?.writeText(question);
                toast.success("Question copied");
              }}
              className="text-muted-foreground transition-colors hover:text-primary"
            >
              <Copy className="size-4" />
            </button>
          }
        >
          <p className="text-sm">{question}</p>
        </SectionCard>

        <SectionCard title="Answer">
          <div className="space-y-3 text-sm leading-relaxed">
            {answerParagraphs(record.answer).map((paragraph) => <p key={paragraph}>{paragraph}</p>)}
          </div>
        </SectionCard>

        <div className="grid gap-6 md:grid-cols-2">
          <SectionCard title="Result">
            <ResultBadge result={result} className="px-3 py-1.5 text-sm" />
            <p className="mt-3 text-sm text-muted-foreground">{statusExplanation(record.verification_status)}</p>
          </SectionCard>

          <SectionCard
            title="Confidence Score"
            action={<Info className="size-4 text-muted-foreground" aria-hidden="true" />}
          >
            {record.confidence_available && confidence > 0 ? <>
              <div className="grid grid-cols-[minmax(0,1fr)_auto] items-center gap-3">
                <p className="text-3xl font-bold">{confidence.toFixed(2)}</p>
                <span className="rounded-md bg-muted px-2 py-1 text-xs font-semibold text-muted-foreground">{level}</span>
              </div>
              <div className="mt-3"><ConfidenceBar value={confidence} /></div>
              <p className="mt-2 text-xs text-muted-foreground">{pct}% evidence agreement</p>
            </> : <p className="text-sm text-muted-foreground">Confidence unavailable because the available evidence was insufficient for verification.</p>}
          </SectionCard>
        </div>

        <SectionCard title={`Verified Claims (${record.claims.length})`}>
          {record.claims.length ? <div className="flex flex-col gap-3">
            {record.claims.map((claim) => <div key={claim.claim} className="rounded-xl border border-border p-4">
              <div className="flex flex-wrap items-center justify-between gap-2"><p className="text-sm font-medium">{claim.claim}</p><ResultBadge result={claimStatus(claim)} /></div>
              <p className="mt-2 text-xs text-muted-foreground">{claim.method} · Evidence confidence {(claim.evidence_score * 100).toFixed(1)}%</p>
            </div>)}
          </div> : <p className="text-sm text-muted-foreground">No claims were verified for this answer.</p>}
        </SectionCard>

        <SectionCard title="Supporting Evidence" bodyClassName="p-5 pt-2">
          <Accordion type="single" collapsible className="flex flex-col gap-2">
            {record.evidence.map((e, i) => (
              <AccordionItem
                key={`${e.source}-${e.title}`}
                value={`${e.source}-${e.title}`}
                className="rounded-xl border border-border px-4"
              >
                <div className="grid grid-cols-[minmax(0,1fr)_auto] items-center gap-3">
                  <AccordionTrigger className="min-w-0 text-sm font-medium hover:no-underline">
                    <span className="truncate">
                      {i + 1}. {e.title}
                    </span>
                  </AccordionTrigger>
                  {e.url ? <a href={e.url} target="_blank" rel="noreferrer" className="text-xs text-primary hover:underline">{e.source}</a> : <span className="text-xs text-muted-foreground">{e.source}</span>}
                </div>
                <AccordionContent className="text-sm text-muted-foreground">{e.content}</AccordionContent>
              </AccordionItem>
            ))}
          </Accordion>
          {!record.evidence.length && <p className="p-4 text-sm text-muted-foreground">No verified evidence was returned.</p>}
        </SectionCard>

        <SectionCard title={`Retrieved Sources (${record.sources.length})`}>
          {record.sources.length ? <div className="grid gap-3 md:grid-cols-2">{record.sources.map((source) => <article key={`${source.source}:${source.title}`} className="rounded-xl border border-border p-4"><div className="flex items-start justify-between gap-3"><h3 className="text-sm font-semibold">{source.title}</h3><span className="text-xs text-muted-foreground">{source.similarity_score.toFixed(2)}</span></div><p className="mt-2 text-xs text-muted-foreground">{source.source}</p>{source.url && <a href={source.url} target="_blank" rel="noreferrer" className="mt-2 inline-block text-xs text-primary hover:underline">Open source</a>}</article>)}</div> : <p className="text-sm text-muted-foreground">No verified sources were returned for this answer.</p>}
        </SectionCard>

        {record.knowledge_graph && record.knowledge_graph.nodes && record.knowledge_graph.nodes.length > 0 && (
          <SectionCard
            title={`Knowledge Graph (${record.knowledge_graph.nodes.length} nodes, ${record.knowledge_graph.edges.length} relationships)`}
            action={
              <Link
                to="/knowledge-graph"
                search={{ answer_id: record.id }}
                className="inline-flex items-center gap-1 text-xs font-semibold text-primary hover:underline"
              >
                Full Page View &rarr;
              </Link>
            }
          >
            <InteractiveKnowledgeGraph
              data={record.knowledge_graph}
              height="500px"
            />
          </SectionCard>
        )}

        <div className="flex flex-wrap gap-3">
          <a href={`/sources?answer_id=${encodeURIComponent(record.id)}`} className="rounded-xl border border-border px-4 py-2 text-sm font-medium hover:border-primary hover:text-primary">View sources for this answer</a>
          <a href={`/knowledge-graph?answer_id=${encodeURIComponent(record.id)}`} className="rounded-xl border border-border px-4 py-2 text-sm font-medium hover:border-primary hover:text-primary">View graph for this answer</a>
        </div>
      </div>
    </AppShell>
  );
}
