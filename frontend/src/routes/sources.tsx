import { createFileRoute } from "@tanstack/react-router";
import { ExternalLink, Library } from "lucide-react";
import { motion } from "motion/react";
import { useEffect, useState } from "react";

import { AppShell } from "@/components/app/app-shell";
import { PageHeader, ConfidenceBar } from "@/components/app/ui-kit";
import { api, type Evidence } from "@/lib/api";
import { shortExcerpt } from "@/lib/presentation";

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
  const [sources, setSources] = useState<Evidence[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  useEffect(() => { const answerId = new URLSearchParams(window.location.search).get("answer_id"); const sourcePromise = answerId ? api.answer(answerId).then((item) => [item]) : api.history().then(({ history }) => history); sourcePromise.then((records) => { const unique = new Map<string, Evidence>(); records.flatMap((item) => [...item.sources, ...item.evidence]).forEach((source) => unique.set(`${source.source}:${source.title}`, source)); setSources([...unique.values()]); }).catch(() => setError("Unable to load retrieved sources.")).finally(() => setLoading(false)); }, []);
  return (
    <AppShell>
      <PageHeader title="Sources" description="The evidence corpora used to ground every answer." />

      {loading && <p className="card-soft p-6 text-sm text-muted-foreground">Loading...</p>}
      {error && <p role="alert" className="card-soft p-6 text-sm text-destructive">{error}</p>}
      {!loading && !error && !sources.length && <p className="card-soft p-6 text-sm text-muted-foreground">No verified sources were returned for this answer.</p>}
      {!loading && !error && sources.length > 0 && <div className="grid gap-6 md:grid-cols-2 xl:grid-cols-3">
        {sources.map((s, i) => (
          <motion.article
            key={`${s.source}:${s.title}`}
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
                <p className="text-xs text-muted-foreground">{s.source}</p>
              </div>
            </div>

            <p className="text-sm text-muted-foreground">{shortExcerpt(s.content)}</p>

            <div>
              <div className="mb-2 flex items-center justify-between text-xs font-medium">
                <span className="text-muted-foreground">Relevance score</span>
                <span className="tabular-nums">{s.similarity_score.toFixed(2)}</span>
              </div>
              <ConfidenceBar value={s.similarity_score} />
            </div>

            {s.url ? <a href={s.url} target="_blank" rel="noreferrer" className="mt-auto inline-flex items-center justify-center gap-2 rounded-xl border border-border px-4 py-2 text-sm font-medium hover:border-primary hover:text-primary">Open Source <ExternalLink className="size-4" /></a> : <span className="mt-auto text-xs text-muted-foreground">No public URL provided</span>}
          </motion.article>
        ))}
      </div>}
    </AppShell>
  );
}
