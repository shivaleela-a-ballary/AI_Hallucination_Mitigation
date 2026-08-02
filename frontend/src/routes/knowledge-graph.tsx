import { createFileRoute } from "@tanstack/react-router";
import { useMemo, useState } from "react";
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
import { graphEntities } from "@/data/mock";

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

const baseNodes: Node[] = [
  { id: "power_plants", position: { x: 0, y: 0 }, data: { label: "Power Plants" }, style: nodeStyle },
  { id: "vehicles", position: { x: 0, y: 180 }, data: { label: "Vehicles" }, style: nodeStyle },
  { id: "so2", position: { x: 220, y: 0 }, data: { label: "Sulfur Dioxide" }, style: nodeStyle },
  { id: "nox", position: { x: 220, y: 180 }, data: { label: "Nitrogen Oxides" }, style: nodeStyle },
  { id: "sulfuric", position: { x: 440, y: 0 }, data: { label: "Sulfuric Acid" }, style: nodeStyle },
  { id: "nitric", position: { x: 440, y: 180 }, data: { label: "Nitric Acid" }, style: nodeStyle },
  {
    id: "acid_rain",
    position: { x: 670, y: 90 },
    data: { label: "Acid Rain" },
    style: {
      ...nodeStyle,
      background: "var(--primary)",
      color: "var(--primary-foreground)",
      fontSize: 14,
    },
  },
  { id: "forests", position: { x: 900, y: 20 }, data: { label: "Forests & Lakes" }, style: nodeStyle },
  { id: "epa", position: { x: 900, y: 170 }, data: { label: "EPA" }, style: nodeStyle },
];

const edgeBase = { type: "default", animated: true, style: { stroke: "var(--secondary)" } };

const baseEdges: Edge[] = [
  { id: "e1", source: "power_plants", target: "so2", label: "emits", ...edgeBase },
  { id: "e2", source: "vehicles", target: "nox", label: "emits", ...edgeBase },
  { id: "e3", source: "so2", target: "sulfuric", label: "forms", ...edgeBase },
  { id: "e4", source: "nox", target: "nitric", label: "forms", ...edgeBase },
  { id: "e5", source: "sulfuric", target: "acid_rain", label: "component of", ...edgeBase },
  { id: "e6", source: "nitric", target: "acid_rain", label: "component of", ...edgeBase },
  { id: "e7", source: "acid_rain", target: "forests", label: "damages", ...edgeBase },
  { id: "e8", source: "epa", target: "acid_rain", label: "documents", ...edgeBase },
];

function KnowledgeGraphPage() {
  const [query, setQuery] = useState("");
  const [selected, setSelected] = useState<string | null>("acid_rain");

  const nodes = useMemo(
    () =>
      baseNodes.map((n) => {
        const label = String(n.data.label ?? "");
        const dim = query.length > 0 && !label.toLowerCase().includes(query.toLowerCase());
        return { ...n, style: { ...(n.style as object), opacity: dim ? 0.25 : 1 } };
      }),
    [query],
  );

  const entity = selected ? graphEntities[selected] : null;

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
            <ReactFlow
              nodes={nodes}
              edges={baseEdges}
              fitView
              onNodeClick={(_, node) => setSelected(node.id)}
              proOptions={{ hideAttribution: true }}
            >
              <Background gap={20} />
              <Controls />
              <MiniMap pannable zoomable />
            </ReactFlow>
          </div>
        </div>

        <aside className="card-soft h-fit p-5">
          {entity ? (
            <>
              <div className="grid grid-cols-[minmax(0,1fr)_auto] items-start gap-2">
                <div className="min-w-0">
                  <h2 className="truncate text-lg font-bold">{entity.label}</h2>
                  <p className="text-xs font-medium text-primary">{entity.kind}</p>
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
              <p className="mt-3 text-sm text-muted-foreground">{entity.description}</p>
              <h3 className="mt-5 text-sm font-semibold">Relations</h3>
              <ul className="mt-2 flex flex-col gap-2">
                {entity.relations.map((r) => (
                  <li key={r} className="rounded-lg bg-muted px-3 py-2 text-xs font-medium">
                    {r}
                  </li>
                ))}
              </ul>
            </>
          ) : (
            <p className="text-sm text-muted-foreground">
              Select a node in the graph to inspect its entity details and relations.
            </p>
          )}
        </aside>
      </div>
    </AppShell>
  );
}
