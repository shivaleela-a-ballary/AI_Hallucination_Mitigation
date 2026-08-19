import { createFileRoute } from "@tanstack/react-router";
import { useEffect, useMemo, useState } from "react";
import {
  Background,
  Controls,
  MiniMap,
  ReactFlow,
  type Edge,
  type Node,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import { Search, X } from "lucide-react";

import { AppShell } from "@/components/app/app-shell";
import { PageHeader } from "@/components/app/ui-kit";
import { Input } from "@/components/ui/input";
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

const nodeStyle = {
  borderRadius: 16,
  padding: "10px 16px",
  border: "1px solid var(--primary)",
  background: "var(--accent)",
  color: "var(--accent-foreground)",
  fontWeight: 600,
  fontSize: 12,
};

function KnowledgeGraphPage() {
  const [query, setQuery] = useState("");
  const [selected, setSelected] = useState<string | null>(null);
  const [graph, setGraph] = useState<{ nodes: Node[]; edges: Edge[] }>({ nodes: [], edges: [] });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [selectedEdge, setSelectedEdge] = useState<Edge | null>(null);
  useEffect(() => {
    const answerId = new URLSearchParams(window.location.search).get("answer_id") ?? undefined;
    const stored = !answerId ? sessionStorage.getItem("latest-verification-graph") : null;
    const graphRequest = stored ? Promise.resolve(JSON.parse(stored)) : api.graph(answerId);
    graphRequest.then((value) => setGraph({
      nodes: value.nodes.map((node: { id: string; label?: string; kind?: string }, index: number) => ({ id: node.id, position: { x: (index % 4) * 220, y: Math.floor(index / 4) * 160 }, data: { label: node.label ?? node.id, kind: node.kind }, style: nodeStyle })),
      edges: value.edges.map((edge: { source: string; target: string; predicate?: string; relationship?: string }, index: number) => ({ ...edge, id: `edge-${index}`, type: "default", label: edge.predicate ?? edge.relationship })),
    })).catch(() => setError("Unable to load the knowledge graph for this answer.")).finally(() => setLoading(false));
  }, []);

  const nodes = useMemo(
    () =>
      graph.nodes.map((n) => {
        const label = String(n.data.label ?? "");
        const dim = query.length > 0 && !label.toLowerCase().includes(query.toLowerCase());
        return { ...n, style: { ...(n.style as object), opacity: dim ? 0.25 : 1 } };
      }),
    [graph.nodes, query],
  );
  const entity = selected ? graph.nodes.find((node) => node.id === selected) : null;

  return (
    <AppShell>
      <PageHeader title="Knowledge Graph" description="Explore entities and relations behind an answer." />

      <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_320px]">
        <div className="card-soft h-[600px] overflow-hidden p-0">
          <div className="border-b border-border p-4">
            <div className="relative">
              <Search
                className="absolute top-1/2 left-3 size-4 -translate-y-1/2 text-muted-foreground"
                aria-hidden="true"
              />
              <Input
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Search node..."
                aria-label="Search node"
                className="h-10 rounded-xl pl-9"
              />
            </div>
          </div>
          <div className="h-[calc(100%-73px)]">
            {loading && <p className="p-5 text-sm text-muted-foreground">Loading...</p>}
            {!loading && error && <p role="alert" className="p-5 text-sm text-destructive">{error}</p>}
            {!loading && !error && !graph.nodes.length && <p className="p-5 text-sm text-muted-foreground">Knowledge graph unavailable for this query because insufficient verified relationships were found.</p>}
            {!loading && !error && graph.nodes.length > 0 && <ReactFlow
              nodes={nodes}
              edges={graph.edges}
              fitView
              onNodeClick={(_, node) => setSelected(node.id)}
              onEdgeClick={(_, edge) => setSelectedEdge(edge)}
              proOptions={{ hideAttribution: true }}
            >
              <Background gap={20} />
              <Controls />
              <MiniMap pannable zoomable />
            </ReactFlow>}
          </div>
        </div>

        <aside className="card-soft h-fit p-5">
          {selectedEdge ? <>
            <div className="flex items-center justify-between"><h2 className="text-lg font-bold">Relationship</h2><button type="button" aria-label="Close relationship details" onClick={() => setSelectedEdge(null)}><X className="size-4" /></button></div>
            <p className="mt-3 text-sm text-muted-foreground">{String(selectedEdge.label ?? "Evidence relationship")}</p>
          </> : entity ? (
            <>
              <div className="grid grid-cols-[minmax(0,1fr)_auto] items-start gap-2">
                <div className="min-w-0">
                  <h2 className="truncate text-lg font-bold">{String(entity.data.label ?? entity.id)}</h2>
                  <p className="text-xs text-primary">{String(entity.data.kind ?? "evidence node")}</p>
                </div>
                <button
                  type="button"
                  aria-label="Close entity details"
                  onClick={() => setSelected(null)}
                  className="text-muted-foreground hover:text-foreground"
                >
                  <X className="size-4" />
                </button>
              </div>
              <p className="mt-3 text-sm text-muted-foreground">This node came from the latest API response.</p>
            </>
          ) : (
            <p className="text-sm text-muted-foreground">
              {graph.nodes.length ? "Select a node in the graph to inspect it." : "No real answer graph is available yet."}
            </p>
          )}
        </aside>
      </div>
    </AppShell>
  );
}
