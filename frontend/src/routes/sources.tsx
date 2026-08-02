import { createFileRoute } from "@tanstack/react-router";
import { ExternalLink, Library } from "lucide-react";
import { motion } from "motion/react";

import { AppShell } from "@/components/app/app-shell";
import { PageHeader, ConfidenceBar } from "@/components/app/ui-kit";
import { Button } from "@/components/ui/button";
import { sourceLibrary } from "@/data/mock";

export const Route = createFileRoute("/sources")({
  head: () => ({
    meta: [
      { title: "Sources — AI Hallucination Mitigation System" },
      {
        name: "description",
        content: "Browse the retrieval sources used for verification: Wikipedia, papers, gov data and more.",
      },
      { property: "og:title", content: "Sources — AI Hallucination Mitigation System" },
      { property: "og:description", content: "The evidence corpora behind every verified answer." },
    ],
  }),
  component: SourcesPage,
});

function SourcesPage() {
  return (
    <AppShell>
      <PageHeader title="Sources" description="The evidence corpora used to ground every answer." />

      <div className="grid gap-6 md:grid-cols-2 xl:grid-cols-3">
        {sourceLibrary.map((s, i) => (
          <motion.article
            key={s.id}
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3, delay: i * 0.06 }}
            whileHover={{ y: -6 }}
            className="card-soft flex flex-col gap-4 p-5 transition-shadow hover:shadow-lift"
          >
            <div className="flex min-w-0 items-center gap-3">
              <span className="grid size-10 shrink-0 place-items-center rounded-xl bg-accent text-primary">
                <Library className="size-5" aria-hidden="true" />
              </span>
              <div className="min-w-0">
                <h2 className="truncate text-base font-bold">{s.title}</h2>
                <p className="text-xs text-muted-foreground">
                  {s.documents.toLocaleString()} documents indexed
                </p>
              </div>
            </div>

            <p className="text-sm text-muted-foreground">{s.snippet}</p>

            <div>
              <div className="mb-2 flex items-center justify-between text-xs font-medium">
                <span className="text-muted-foreground">Relevance score</span>
                <span className="tabular-nums">{s.relevance.toFixed(2)}</span>
              </div>
              <ConfidenceBar value={s.relevance} />
            </div>

            <Button variant="outline" className="mt-auto rounded-xl">
              Open Source <ExternalLink className="size-4" />
            </Button>
          </motion.article>
        ))}
      </div>
    </AppShell>
  );
}
