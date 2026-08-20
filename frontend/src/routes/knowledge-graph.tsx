import { createFileRoute } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { AppShell } from "@/components/app/app-shell";
import { PageHeader } from "@/components/app/ui-kit";
import { InteractiveKnowledgeGraph, type KnowledgeGraphData } from "@/components/app/interactive-knowledge-graph";
import { api } from "@/lib/api";

export const Route = createFileRoute("/knowledge-graph")({
  head: () => ({
    meta: [
      { title: "Knowledge Graph — AI Hallucination Mitigation System" },
      {
        name: "description",
        content: "Explore the entities and relationships used to ground and verify each generated answer.",
      },
      { property: "og:title", content: "Knowledge Graph — AI Hallucination Mitigation System" },
      { property: "og:description", content: "Entities and relations behind each verified answer." },
    ],
  }),
  component: KnowledgeGraphPage,
});

function KnowledgeGraphPage() {
  const [graphData, setGraphData] = useState<KnowledgeGraphData>({ nodes: [], edges: [] });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const answerId = new URLSearchParams(window.location.search).get("answer_id") ?? undefined;
    const stored = !answerId ? sessionStorage.getItem("latest-verification-graph") : null;
    const graphRequest = stored ? Promise.resolve(JSON.parse(stored)) : api.graph(answerId);

    graphRequest
      .then((data) => {
        setGraphData({
          nodes: (data.nodes || []).map((n: { id: string; label?: string; kind?: string }) => ({
            id: n.id,
            label: n.label ?? n.id,
            kind: n.kind ?? "entity",
          })),
          edges: (data.edges || []).map((e: { source: string; target: string; predicate?: string; relationship?: string }) => ({
            source: e.source,
            target: e.target,
            predicate: e.predicate ?? e.relationship ?? "relates",
          })),
        });
      })
      .catch(() => setError("Unable to load the knowledge graph for this answer."))
      .finally(() => setLoading(false));
  }, []);

  return (
    <AppShell>
      <PageHeader
        title="Knowledge Graph"
        description="Explore the interconnected entities and verified relationships behind your queries."
      />

      <div className="space-y-6">
        {loading && (
          <div className="flex h-[600px] items-center justify-center rounded-2xl border border-border bg-card">
            <p className="text-sm text-muted-foreground animate-pulse">Loading knowledge graph...</p>
          </div>
        )}

        {!loading && error && (
          <div className="rounded-2xl border border-destructive/30 bg-destructive/10 p-6 text-sm text-destructive">
            {error}
          </div>
        )}

        {!loading && !error && (
          <InteractiveKnowledgeGraph
            data={graphData}
            height="650px"
          />
        )}
      </div>
    </AppShell>
  );
}
