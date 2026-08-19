import { createFileRoute, Link } from "@tanstack/react-router";
import { useState } from "react";
import { ArrowRight, ShieldCheck } from "lucide-react";

import { AppShell } from "@/components/app/app-shell";
import { PageHeader, ResultBadge, SectionCard } from "@/components/app/ui-kit";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { api, type VerificationResponse } from "@/lib/api";
import { claimStatus, shortExcerpt } from "@/lib/presentation";

export const Route = createFileRoute("/new-verification")({
  head: () => ({ meta: [{ title: "New Verification — AI Hallucination Mitigation System" }] }),
  component: NewVerification,
});

function NewVerification() {
  const [claim, setClaim] = useState("");
  const [evidence, setEvidence] = useState("");
  const [result, setResult] = useState<VerificationResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const verify = async () => {
    if (!claim.trim()) { setError("Enter a claim first."); return; }
    setLoading(true); setError(""); setResult(null);
    try {
      const verification = await api.verify(claim.trim(), evidence.trim());
      sessionStorage.setItem("latest-verification-graph", JSON.stringify(verification.knowledge_graph));
      setResult(verification);
    }
    catch (cause) { setError(cause instanceof Error ? cause.message : "Verification failed."); }
    finally { setLoading(false); }
  };

  return <AppShell>
    <PageHeader title="New Verification" description="Verify a claim against the local SciFact model and real evidence." />
    <div className="grid gap-6 lg:grid-cols-2">
      <SectionCard title="Claim">
        <Textarea value={claim} onChange={(event) => setClaim(event.target.value)} placeholder="Enter a scientific claim..." aria-label="Claim" className="min-h-32 resize-none rounded-xl bg-background" />
        <p className="mt-3 text-xs text-muted-foreground">If evidence is omitted, the backend retrieves relevant SciFact evidence. UNCERTAIN is an application state, not a model class.</p>
      </SectionCard>
      <SectionCard title="Evidence (optional)">
        <Textarea value={evidence} onChange={(event) => setEvidence(event.target.value)} placeholder="Paste evidence to verify, or leave blank for SciFact retrieval..." aria-label="Evidence" className="min-h-32 resize-none rounded-xl bg-background" />
        <p className="mt-3 text-xs text-muted-foreground">User-provided evidence is labeled as such. No evidence is invented.</p>
      </SectionCard>
    </div>
    <Button className="mt-6 h-12 rounded-xl" disabled={loading} onClick={() => void verify()}>{loading ? "Verifying..." : "Verify Claim"} <ArrowRight className="size-4" /></Button>
    {error && <p role="alert" className="mt-4 text-sm text-destructive">{error}</p>}
    {result && <div className="mt-6 grid gap-6 lg:grid-cols-2">
      <SectionCard title="Prediction">
        <div className="flex items-center gap-3"><ShieldCheck className="size-5 text-primary" /><ResultBadge result={claimStatus(result.claims[0] ?? { status: result.verification_status, claim: result.claim, evidence_titles: [], evidence_score: result.confidence_score, method: "SciFact" })} /></div>
        <p className="mt-3 text-sm text-muted-foreground">{result.confidence_available ? `Model confidence ${(result.confidence_score * 100).toFixed(1)}%` : "Confidence unavailable because evidence was insufficient."}</p>
        {result.probabilities && <dl className="mt-4 space-y-2 text-sm">{Object.entries(result.probabilities).map(([label, value]) => <div key={label} className="flex justify-between"><dt>{label}</dt><dd>{(value * 100).toFixed(1)}%</dd></div>)}</dl>}
      </SectionCard>
      <SectionCard title={`Evidence Used (${result.evidence.length})`}>
        {result.evidence.length ? <div className="space-y-3">{result.evidence.map((item) => <div key={`${item.source}:${item.title}`} className="rounded-xl border border-border p-3"><p className="text-sm font-semibold">{item.title}</p><p className="mt-1 text-xs text-muted-foreground">{shortExcerpt(item.content)}</p></div>)}</div> : <p className="text-sm text-muted-foreground">No sufficiently relevant evidence was found.</p>}
      </SectionCard>
      <SectionCard title={`Knowledge Graph (${result.knowledge_graph.nodes.length} nodes, ${result.knowledge_graph.edges.length} relationships)`}>
        {result.knowledge_graph.nodes.length ? <div className="grid gap-2 sm:grid-cols-2">{result.knowledge_graph.nodes.map((node) => <div key={node.id} className="rounded-xl border border-border p-3"><p className="text-sm font-semibold">{node.label ?? node.id}</p><p className="text-xs text-muted-foreground">{node.kind ?? "evidence node"}</p></div>)}</div> : <p className="text-sm text-muted-foreground">No evidence-derived relationships were found.</p>}
        {result.knowledge_graph.nodes.length > 0 && <Link to="/knowledge-graph" className="mt-4 inline-flex rounded-xl border border-border px-4 py-2 text-sm font-medium hover:border-primary hover:text-primary">Open interactive graph</Link>}
      </SectionCard>
    </div>}
  </AppShell>;
}
