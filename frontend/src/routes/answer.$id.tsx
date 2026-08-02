import { createFileRoute, Link, useParams } from "@tanstack/react-router";
import { ArrowLeft, Copy, Info, Share2 } from "lucide-react";

import { AppShell } from "@/components/app/app-shell";
import { ConfidenceBar, ResultBadge, SectionCard } from "@/components/app/ui-kit";
import { Button } from "@/components/ui/button";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import { toast } from "sonner";
import { answerDetail, answerEvidence, verifications } from "@/data/mock";

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
  const record = verifications.find((v) => v.id === id);
  const question = record?.text ?? answerDetail.question;
  const result = record?.result ?? answerDetail.result;
  const confidence = record?.confidence ?? answerDetail.confidence;
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
          <p className="text-sm leading-relaxed">{answerDetail.answer}</p>
        </SectionCard>

        <div className="grid gap-6 md:grid-cols-2">
          <SectionCard title="Result">
            <ResultBadge result={result} className="px-3 py-1.5 text-sm" />
          </SectionCard>

          <SectionCard
            title="Confidence Score"
            action={<Info className="size-4 text-muted-foreground" aria-hidden="true" />}
          >
            <div className="grid grid-cols-[minmax(0,1fr)_auto] items-center gap-3">
              <p className="text-3xl font-bold">{confidence.toFixed(2)}</p>
              <span className="rounded-md bg-muted px-2 py-1 text-xs font-semibold text-muted-foreground">
                {level}
              </span>
            </div>
            <div className="mt-3">
              <ConfidenceBar value={confidence} />
            </div>
            <p className="mt-2 text-xs text-muted-foreground">{pct}% evidence agreement</p>
          </SectionCard>
        </div>

        <SectionCard title="Supporting Evidence" bodyClassName="p-5 pt-2">
          <Accordion type="single" collapsible className="flex flex-col gap-2">
            {answerEvidence.map((e, i) => (
              <AccordionItem
                key={e.source}
                value={e.source}
                className="rounded-xl border border-border px-4"
              >
                <div className="grid grid-cols-[minmax(0,1fr)_auto] items-center gap-3">
                  <AccordionTrigger className="min-w-0 text-sm font-medium hover:no-underline">
                    <span className="truncate">
                      {i + 1}. {e.source}
                    </span>
                  </AccordionTrigger>
                  <Button asChild variant="secondary" size="sm" className="rounded-lg">
                    <a href={e.url} target="_blank" rel="noreferrer noopener">
                      View
                    </a>
                  </Button>
                </div>
                <AccordionContent className="text-sm text-muted-foreground">{e.snippet}</AccordionContent>
              </AccordionItem>
            ))}
          </Accordion>
        </SectionCard>
      </div>
    </AppShell>
  );
}
