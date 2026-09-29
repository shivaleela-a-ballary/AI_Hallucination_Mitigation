import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { AlertTriangle, ArrowRight } from "lucide-react";
import { AppShell } from "@/components/app/app-shell";
import { PageHeader } from "@/components/app/ui-kit";
import { Button } from "@/components/ui/button";
import { InteractiveKnowledgeGraph, type KnowledgeGraphData } from "@/components/app/interactive-knowledge-graph";
import { api } from "@/lib/api";
import { useVerification } from "@/lib/verification-context";

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
  const navigate = useNavigate();
  const { currentVerification, loading: authLoading } = useVerification();
  const [graphData, setGraphData] = useState<KnowledgeGraphData>({ nodes: [], edges: [] });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    // 1. Direct consumption from canonical current verification if graph exists
    if (
      currentVerification?.knowledge_graph?.nodes &&
      currentVerification.knowledge_graph.nodes.length > 0
    ) {
      const kg = currentVerification.knowledge_graph;
      setGraphData({
        nodes: (kg.nodes || []).map((n: { id: string; label?: string; kind?: string }) => ({
          id: n.id,
          label: n.label ?? n.id,
          kind: n.kind ?? "entity",
        })),
        edges: (kg.edges || []).map((e: { source: string; target: string; predicate?: string; relationship?: string }) => ({
          source: e.source,
          target: e.target,
          predicate: e.predicate ?? e.relationship ?? "relates",
        })),
      });
      setLoading(false);
      return;
    }

    // 2. Query by URL param answer_id or sessionStorage fallback
    const answerId = new URLSearchParams(window.location.search).get("answer_id") ?? undefined;
    const stored = !answerId && typeof window !== "undefined" ? sessionStorage.getItem("latest-verification-graph") : null;
    const graphRequest = stored ? Promise.resolve(JSON.parse(stored)) : api.graph(answerId);

    graphRequest
      .then((data) => {
        if (data?.nodes && data.nodes.length > 0) {
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
        }
      })
      .catch(() => {
        // Only set error if no current verification exists
        if (!currentVerification) {
          setError("Unable to load the knowledge graph for this answer.");
        }
      })
      .finally(() => setLoading(false));
  }, [currentVerification]);

  const hasGraph = graphData.nodes && graphData.nodes.length > 0;

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

        {!loading && !hasGraph && (
          <div className="rounded-2xl border border-[#172545] bg-[#091124] p-12 text-center max-w-xl mx-auto space-y-4 shadow-xl">
            <div className="size-16 rounded-2xl bg-amber-500/10 border border-amber-500/30 flex items-center justify-center text-amber-400 mx-auto">
              <AlertTriangle className="size-8" />
            </div>
            <h3 className="text-xl font-bold text-white">No verification available</h3>
            <p className="text-sm text-slate-400">
              Verify a claim or AI answer first to generate and explore the factual grounding knowledge graph.
            </p>
            <div className="pt-2">
              <Button
                onClick={() => navigate({ to: "/check-answer" })}
                className="rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-xs px-6"
              >
                Verify a Claim First <ArrowRight className="size-4 ml-1.5" />
              </Button>
            </div>
          </div>
        )}

        {!loading && hasGraph && (
          <InteractiveKnowledgeGraph
            data={graphData}
            height="650px"
          />
        )}
      </div>
    </AppShell>
  );
}
