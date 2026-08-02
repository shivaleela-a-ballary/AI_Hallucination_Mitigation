import { createFileRoute } from "@tanstack/react-router";
import { FileSearch, Share2, ShieldCheck, Sparkles } from "lucide-react";

import { AppShell } from "@/components/app/app-shell";
import { PageHeader, SectionCard } from "@/components/app/ui-kit";
import robot from "@/assets/robot.png";

export const Route = createFileRoute("/about")({
  head: () => ({
    meta: [
      { title: "About Us — AI Hallucination Mitigation System" },
      {
        name: "description",
        content:
          "How the AI Hallucination Mitigation System retrieves evidence, builds knowledge graphs and verifies answers.",
      },
      { property: "og:title", content: "About Us — AI Hallucination Mitigation System" },
      { property: "og:description", content: "How we ground AI answers in verifiable evidence." },
    ],
  }),
  component: AboutPage,
});

const pillars = [
  { icon: FileSearch, title: "Retrieve", text: "Pull passages from trusted corpora and your own documents." },
  { icon: Share2, title: "Structure", text: "Build a knowledge graph of entities and their relationships." },
  { icon: ShieldCheck, title: "Verify", text: "Score each claim against retrieved evidence, not model memory." },
  { icon: Sparkles, title: "Explain", text: "Return an answer with citations and a transparent confidence score." },
];

function AboutPage() {
  return (
    <AppShell>
      <PageHeader title="About Us" description="AI accuracy, built on real evidence." />

      <SectionCard>
        <div className="grid items-center gap-6 md:grid-cols-[minmax(0,1fr)_auto]">
          <div className="min-w-0">
            <h2 className="text-xl font-bold">Answers you can check, not just trust</h2>
            <p className="mt-2 text-sm text-muted-foreground">
              Large language models are fluent but not always factual. This system sits between the model and
              the user: every claim is retrieved, structured, verified and scored before it reaches you — with
              the evidence attached.
            </p>
          </div>
          <img src={robot} alt="" aria-hidden="true" loading="lazy" width={768} height={640} className="h-32 w-auto" />
        </div>
      </SectionCard>

      <div className="mt-6 grid gap-6 sm:grid-cols-2 xl:grid-cols-4">
        {pillars.map((p) => (
          <article key={p.title} className="card-soft p-5 transition-shadow hover:shadow-lift">
            <span className="grid size-11 place-items-center rounded-xl bg-accent text-primary">
              <p.icon className="size-5" aria-hidden="true" />
            </span>
            <h3 className="mt-4 text-base font-bold">{p.title}</h3>
            <p className="mt-1 text-sm text-muted-foreground">{p.text}</p>
          </article>
        ))}
      </div>
    </AppShell>
  );
}
