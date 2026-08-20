import React, { useCallback, useMemo, useState } from "react";
import {
  Background,
  Controls,
  MiniMap,
  ReactFlow,
  Handle,
  Position,
  type Edge,
  type Node,
  type NodeProps,
  BackgroundVariant,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import {
  FileText,
  Sparkles,
  Maximize2,
  Minimize2,
  Search,
  Layers,
  X,
  Share2,
  ExternalLink,
  Tag,
} from "lucide-react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";

export interface KnowledgeGraphData {
  nodes: Array<{
    id: string;
    label?: string;
    kind?: string;
    [key: string]: unknown;
  }>;
  edges: Array<{
    source: string;
    target: string;
    predicate?: string;
    relationship?: string;
    source_title?: string;
    [key: string]: unknown;
  }>;
}

// ---------------------------------------------------------------------------
// Custom Source Node Component (Hub)
// ---------------------------------------------------------------------------
function SourceNode({ data, selected }: NodeProps) {
  const label = String(data.label ?? data.id ?? "Source");
  return (
    <div
      className={`group relative min-w-[200px] max-w-[280px] rounded-2xl border-2 px-4 py-3 shadow-lg transition-all duration-200 ${
        selected
          ? "border-primary bg-primary/10 shadow-primary/20 ring-2 ring-primary/30"
          : "border-primary/40 bg-card/95 hover:border-primary hover:shadow-primary/15"
      } backdrop-blur-md`}
    >
      <Handle type="target" position={Position.Top} className="!size-2 !bg-primary" />
      <Handle type="source" position={Position.Bottom} className="!size-2 !bg-primary" />
      <Handle type="target" position={Position.Left} className="!size-2 !bg-primary" />
      <Handle type="source" position={Position.Right} className="!size-2 !bg-primary" />

      <div className="flex items-center gap-2">
        <div className="grid size-7 shrink-0 place-items-center rounded-lg bg-primary/15 text-primary">
          <FileText className="size-4" />
        </div>
        <div className="min-w-0 flex-1">
          <span className="inline-block rounded-md bg-primary/10 px-1.5 py-0.5 text-[10px] font-bold tracking-wider text-primary uppercase">
            Evidence Source
          </span>
          <p className="mt-0.5 line-clamp-2 text-xs font-semibold text-foreground leading-snug">
            {label}
          </p>
        </div>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Custom Entity Node Component (Concept)
// ---------------------------------------------------------------------------
function EntityNode({ data, selected }: NodeProps) {
  const label = String(data.label ?? data.id ?? "Entity");
  return (
    <div
      className={`group relative min-w-[130px] max-w-[200px] rounded-xl border px-3 py-2 shadow-md transition-all duration-200 ${
        selected
          ? "border-emerald-500 bg-emerald-500/15 shadow-emerald-500/20 ring-2 ring-emerald-500/30"
          : "border-border/80 bg-secondary/80 hover:border-emerald-500/60 hover:bg-secondary"
      } backdrop-blur-sm`}
    >
      <Handle type="target" position={Position.Top} className="!size-1.5 !bg-emerald-500" />
      <Handle type="source" position={Position.Bottom} className="!size-1.5 !bg-emerald-500" />
      <Handle type="target" position={Position.Left} className="!size-1.5 !bg-emerald-500" />
      <Handle type="source" position={Position.Right} className="!size-1.5 !bg-emerald-500" />

      <div className="flex items-center gap-2">
        <div className="grid size-5 shrink-0 place-items-center rounded bg-emerald-500/15 text-emerald-600 dark:text-emerald-400">
          <Sparkles className="size-3" />
        </div>
        <div className="min-w-0 flex-1">
          <p className="truncate text-xs font-medium text-foreground">
            {label}
          </p>
          <span className="text-[9px] text-muted-foreground">Entity Concept</span>
        </div>
      </div>
    </div>
  );
}

const nodeTypes = {
  sourceNode: SourceNode,
  entityNode: EntityNode,
};

// ---------------------------------------------------------------------------
// Layout Calculator: Organic Radial Hub & Spoke Layout
// ---------------------------------------------------------------------------
function computeGraphLayout(rawNodes: KnowledgeGraphData["nodes"], rawEdges: KnowledgeGraphData["edges"]) {
  const sources = rawNodes.filter((n) => n.kind === "source");
  const entities = rawNodes.filter((n) => n.kind !== "source");

  const positions = new Map<string, { x: number; y: number }>();
  const centerX = 450;
  const centerY = 350;

  if (sources.length === 0) {
    // If no explicit sources, lay out in a pleasing grid/circle
    const count = rawNodes.length;
    const radius = Math.max(200, count * 35);
    rawNodes.forEach((node, i) => {
      const angle = (i / count) * 2 * Math.PI;
      positions.set(node.id, {
        x: centerX + Math.cos(angle) * radius,
        y: centerY + Math.sin(angle) * radius,
      });
    });
  } else {
    // Lay out sources in a prominent primary hub formation
    const sourceCount = sources.length;
    const hubRadius = Math.max(240, sourceCount * 120);

    sources.forEach((src, i) => {
      const angle = (i / sourceCount) * 2 * Math.PI - Math.PI / 2;
      positions.set(src.id, {
        x: centerX + Math.cos(angle) * hubRadius,
        y: centerY + Math.sin(angle) * hubRadius,
      });
    });

    // Map which entities belong to which sources
    const entityToSource = new Map<string, string>();
    rawEdges.forEach((edge) => {
      if (!entityToSource.has(edge.target)) {
        entityToSource.set(edge.target, edge.source);
      }
    });

    const sourceToEntities = new Map<string, string[]>();
    sources.forEach((s) => sourceToEntities.set(s.id, []));
    const unattached: string[] = [];

    entities.forEach((ent) => {
      const srcId = entityToSource.get(ent.id);
      if (srcId && sourceToEntities.has(srcId)) {
        sourceToEntities.get(srcId)!.push(ent.id);
      } else {
        unattached.push(ent.id);
      }
    });

    // Position entities in a clean ring surrounding their parent source
    sources.forEach((src) => {
      const srcPos = positions.get(src.id) || { x: centerX, y: centerY };
      const group = sourceToEntities.get(src.id) || [];
      const groupCount = group.length;
      const orbitRadius = Math.max(160, Math.min(320, groupCount * 26));

      group.forEach((entId, idx) => {
        const angle = (idx / Math.max(groupCount, 1)) * 2 * Math.PI;
        positions.set(entId, {
          x: srcPos.x + Math.cos(angle) * orbitRadius,
          y: srcPos.y + Math.sin(angle) * orbitRadius,
        });
      });
    });

    // Lay out unattached entities in an outer orbital ring
    const unattachedRadius = hubRadius + 280;
    unattached.forEach((entId, idx) => {
      const angle = (idx / Math.max(unattached.length, 1)) * 2 * Math.PI;
      positions.set(entId, {
        x: centerX + Math.cos(angle) * unattachedRadius,
        y: centerY + Math.sin(angle) * unattachedRadius,
      });
    });
  }

  // Build ReactFlow Nodes
  const nodes: Node[] = rawNodes.map((n) => {
    const isSource = n.kind === "source";
    const pos = positions.get(n.id) || { x: centerX, y: centerY };
    return {
      id: n.id,
      type: isSource ? "sourceNode" : "entityNode",
      position: pos,
      data: {
        label: n.label ?? n.id,
        kind: n.kind ?? (isSource ? "source" : "entity"),
        ...n,
      },
    };
  });

  // Build ReactFlow Edges with styles
  const edges: Edge[] = rawEdges.map((e, index) => {
    const isCoMention = e.predicate?.includes("co-mentioned");
    return {
      id: `edge-${e.source}-${e.target}-${index}`,
      source: e.source,
      target: e.target,
      label: e.predicate ?? e.relationship ?? "relates",
      animated: !isCoMention,
      style: {
        stroke: isCoMention ? "#3b82f6" : "#8b5cf6",
        strokeWidth: isCoMention ? 1.5 : 2,
        strokeDasharray: isCoMention ? "4 4" : undefined,
      },
      labelStyle: {
        fontSize: 10,
        fontWeight: 600,
        fill: "var(--muted-foreground)",
      },
      labelBgStyle: {
        fill: "var(--card)",
        fillOpacity: 0.85,
      },
      labelBgPadding: [4, 2] as [number, number],
      labelBgBorderRadius: 4,
      data: e,
    };
  });

  return { nodes, edges };
}

// ---------------------------------------------------------------------------
// Interactive Knowledge Graph Visualizer Component
// ---------------------------------------------------------------------------
interface InteractiveKnowledgeGraphProps {
  data: KnowledgeGraphData;
  height?: string | number;
  className?: string;
  showInspector?: boolean;
}

export function InteractiveKnowledgeGraph({
  data,
  height = "520px",
  className = "",
  showInspector = true,
}: InteractiveKnowledgeGraphProps) {
  const [searchTerm, setSearchTerm] = useState("");
  const [filterType, setFilterType] = useState<"all" | "source" | "entity">("all");
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const [selectedEdge, setSelectedEdge] = useState<Edge | null>(null);
  const [isFullscreen, setIsFullscreen] = useState(false);

  // Compute positioned graph elements
  const { nodes: initialNodes, edges } = useMemo(
    () => computeGraphLayout(data.nodes, data.edges),
    [data.nodes, data.edges]
  );

  // Filter nodes based on search and type filter
  const filteredNodes = useMemo(() => {
    return initialNodes.map((node) => {
      const label = String(node.data.label ?? "").toLowerCase();
      const matchesSearch = !searchTerm || label.includes(searchTerm.toLowerCase());
      const matchesFilter =
        filterType === "all" ||
        (filterType === "source" && node.data.kind === "source") ||
        (filterType === "entity" && node.data.kind !== "source");

      const isDimmed = !matchesSearch || !matchesFilter;

      return {
        ...node,
        style: {
          ...node.style,
          opacity: isDimmed ? 0.15 : 1,
          pointerEvents: isDimmed ? ("none" as const) : ("all" as const),
        },
      };
    });
  }, [initialNodes, searchTerm, filterType]);

  const selectedNode = useMemo(() => {
    if (!selectedNodeId) return null;
    return initialNodes.find((n) => n.id === selectedNodeId) ?? null;
  }, [selectedNodeId, initialNodes]);

  // Connected edges for the selected node
  const connectedEdges = useMemo(() => {
    if (!selectedNodeId) return [];
    return edges.filter(
      (e) => e.source === selectedNodeId || e.target === selectedNodeId
    );
  }, [selectedNodeId, edges]);

  const onNodeClick = useCallback((_: React.MouseEvent, node: Node) => {
    setSelectedNodeId(node.id);
    setSelectedEdge(null);
  }, []);

  const onEdgeClick = useCallback((_: React.MouseEvent, edge: Edge) => {
    setSelectedEdge(edge);
    setSelectedNodeId(null);
  }, []);

  if (!data.nodes.length) {
    return (
      <div className="flex h-64 flex-col items-center justify-center rounded-2xl border border-dashed border-border p-6 text-center text-muted-foreground">
        <Layers className="size-10 opacity-40" />
        <p className="mt-3 text-sm font-medium">No knowledge graph data available.</p>
        <p className="text-xs text-muted-foreground/70">
          Verify a claim or submit a question to generate entity relationships.
        </p>
      </div>
    );
  }

  const containerHeight = isFullscreen ? "100vh" : height;

  return (
    <div
      className={`relative overflow-hidden rounded-2xl border border-border bg-card shadow-sm transition-all duration-300 ${
        isFullscreen ? "fixed inset-0 z-50 rounded-none border-none" : ""
      } ${className}`}
      style={{ height: containerHeight }}
    >
      {/* Top Toolbar */}
      <div className="absolute top-3 left-3 z-10 flex flex-wrap items-center gap-2">
        <div className="relative">
          <Search className="absolute top-1/2 left-2.5 size-3.5 -translate-y-1/2 text-muted-foreground" />
          <Input
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Filter nodes..."
            className="h-8 w-44 rounded-lg bg-background/90 pl-8 text-xs backdrop-blur-md focus-visible:ring-1"
          />
          {searchTerm && (
            <button
              type="button"
              onClick={() => setSearchTerm("")}
              className="absolute top-1/2 right-2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
            >
              <X className="size-3" />
            </button>
          )}
        </div>

        {/* Filter Pills */}
        <div className="flex items-center rounded-lg border border-border bg-background/90 p-0.5 text-xs backdrop-blur-md">
          <button
            type="button"
            onClick={() => setFilterType("all")}
            className={`rounded-md px-2.5 py-1 font-medium transition-colors ${
              filterType === "all"
                ? "bg-primary text-primary-foreground shadow-xs"
                : "text-muted-foreground hover:text-foreground"
            }`}
          >
            All ({data.nodes.length})
          </button>
          <button
            type="button"
            onClick={() => setFilterType("source")}
            className={`flex items-center gap-1 rounded-md px-2.5 py-1 font-medium transition-colors ${
              filterType === "source"
                ? "bg-primary text-primary-foreground shadow-xs"
                : "text-muted-foreground hover:text-foreground"
            }`}
          >
            <FileText className="size-3" />
            Sources ({data.nodes.filter((n) => n.kind === "source").length})
          </button>
          <button
            type="button"
            onClick={() => setFilterType("entity")}
            className={`flex items-center gap-1 rounded-md px-2.5 py-1 font-medium transition-colors ${
              filterType === "entity"
                ? "bg-primary text-primary-foreground shadow-xs"
                : "text-muted-foreground hover:text-foreground"
            }`}
          >
            <Sparkles className="size-3" />
            Entities ({data.nodes.filter((n) => n.kind !== "source").length})
          </button>
        </div>
      </div>

      {/* Top-Right Action Buttons */}
      <div className="absolute top-3 right-3 z-10 flex items-center gap-2">
        <Button
          variant="outline"
          size="sm"
          onClick={() => setIsFullscreen(!isFullscreen)}
          className="h-8 rounded-lg bg-background/90 px-2.5 text-xs backdrop-blur-md"
          title={isFullscreen ? "Exit Fullscreen" : "Fullscreen Graph"}
        >
          {isFullscreen ? (
            <>
              <Minimize2 className="size-3.5" />
              <span className="ml-1 hidden sm:inline">Exit Fullscreen</span>
            </>
          ) : (
            <>
              <Maximize2 className="size-3.5" />
              <span className="ml-1 hidden sm:inline">Fullscreen</span>
            </>
          )}
        </Button>
      </div>

      {/* Main Interactive Flow Canvas */}
      <ReactFlow
        nodes={filteredNodes}
        edges={edges}
        nodeTypes={nodeTypes}
        onNodeClick={onNodeClick}
        onEdgeClick={onEdgeClick}
        fitView
        fitViewOptions={{ padding: 0.25 }}
        minZoom={0.15}
        maxZoom={2.0}
        proOptions={{ hideAttribution: true }}
      >
        <Background variant={BackgroundVariant.Dots} gap={24} size={1.2} className="opacity-40" />
        <Controls showInteractive={false} className="!bg-background/90 !border-border !rounded-xl !shadow-md backdrop-blur-md" />
        <MiniMap
          nodeColor={(n) => (n.data?.kind === "source" ? "#8b5cf6" : "#10b981")}
          maskColor="rgba(0, 0, 0, 0.25)"
          className="!bg-background/80 !border-border !rounded-xl overflow-hidden backdrop-blur-md"
        />
      </ReactFlow>

      {/* Bottom Floating Legend */}
      <div className="absolute bottom-3 left-3 z-10 flex items-center gap-3 rounded-xl border border-border bg-background/90 px-3 py-1.5 text-[11px] text-muted-foreground backdrop-blur-md shadow-xs">
        <div className="flex items-center gap-1.5">
          <span className="size-2.5 rounded-full bg-primary" />
          <span>Evidence Source</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="size-2.5 rounded-full bg-emerald-500" />
          <span>Entity Concept</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="h-0.5 w-3 bg-purple-500" />
          <span>Mentions</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="h-0.5 w-3 border-t border-dashed border-blue-500" />
          <span>Co-occurrence</span>
        </div>
      </div>

      {/* Side Inspector Drawer */}
      {showInspector && (selectedNode || selectedEdge) && (
        <div className="absolute top-3 right-3 bottom-3 z-20 w-80 overflow-y-auto rounded-xl border border-border bg-card/95 p-4 shadow-xl backdrop-blur-md animate-in slide-in-from-right-4">
          <div className="flex items-start justify-between gap-2 border-b border-border pb-3">
            <div className="flex items-center gap-2">
              {selectedNode?.data.kind === "source" ? (
                <FileText className="size-4 text-primary" />
              ) : selectedNode ? (
                <Sparkles className="size-4 text-emerald-500" />
              ) : (
                <Share2 className="size-4 text-blue-500" />
              )}
              <h4 className="text-xs font-bold tracking-wider text-muted-foreground uppercase">
                {selectedNode
                  ? selectedNode.data.kind === "source"
                    ? "Source Hub"
                    : "Entity Concept"
                  : "Relationship"}
              </h4>
            </div>
            <button
              type="button"
              onClick={() => {
                setSelectedNodeId(null);
                setSelectedEdge(null);
              }}
              className="rounded-md p-1 text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
            >
              <X className="size-4" />
            </button>
          </div>

          {selectedNode && (
            <div className="mt-3 space-y-3 text-xs">
              <div>
                <p className="text-[10px] text-muted-foreground uppercase font-bold">Node Label</p>
                <p className="mt-0.5 text-sm font-semibold text-foreground">
                  {String(selectedNode.data.label ?? selectedNode.id)}
                </p>
              </div>

              <div>
                <p className="text-[10px] text-muted-foreground uppercase font-bold">Connected Links</p>
                <p className="mt-0.5 text-sm font-bold text-primary">
                  {connectedEdges.length} {connectedEdges.length === 1 ? "relationship" : "relationships"}
                </p>
              </div>

              {connectedEdges.length > 0 && (
                <div>
                  <p className="mb-1.5 text-[10px] text-muted-foreground uppercase font-bold">Connected Entities</p>
                  <div className="max-h-48 space-y-1.5 overflow-y-auto pr-1">
                    {connectedEdges.map((e, idx) => {
                      const otherId = e.source === selectedNode.id ? e.target : e.source;
                      const otherNode = initialNodes.find((n) => n.id === otherId);
                      return (
                        <div
                          key={idx}
                          onClick={() => setSelectedNodeId(otherId)}
                          className="flex cursor-pointer items-center justify-between rounded-lg border border-border bg-secondary/50 p-2 transition-colors hover:border-primary/50 hover:bg-secondary"
                        >
                          <span className="truncate font-medium text-foreground">
                            {String(otherNode?.data.label ?? otherId)}
                          </span>
                          <span className="ml-1.5 shrink-0 rounded bg-background/80 px-1.5 py-0.5 text-[9px] text-muted-foreground">
                            {String(e.label ?? "linked")}
                          </span>
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}
            </div>
          )}

          {selectedEdge && (
            <div className="mt-3 space-y-3 text-xs">
              <div>
                <p className="text-[10px] text-muted-foreground uppercase font-bold">Predicate / Relation</p>
                <p className="mt-0.5 text-sm font-semibold text-primary">
                  {String(selectedEdge.label ?? "Relates")}
                </p>
              </div>
              <div>
                <p className="text-[10px] text-muted-foreground uppercase font-bold">Source Node</p>
                <p className="mt-0.5 font-medium text-foreground">
                  {String(initialNodes.find((n) => n.id === selectedEdge.source)?.data.label ?? selectedEdge.source)}
                </p>
              </div>
              <div>
                <p className="text-[10px] text-muted-foreground uppercase font-bold">Target Node</p>
                <p className="mt-0.5 font-medium text-foreground">
                  {String(initialNodes.find((n) => n.id === selectedEdge.target)?.data.label ?? selectedEdge.target)}
                </p>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
