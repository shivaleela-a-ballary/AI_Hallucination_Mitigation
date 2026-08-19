import { createFileRoute } from "@tanstack/react-router";
import { useEffect, useState } from "react";

import { AppShell } from "@/components/app/app-shell";
import { PageHeader, SectionCard } from "@/components/app/ui-kit";
import { api } from "@/lib/api";

export const Route = createFileRoute("/settings")({
  head: () => ({ meta: [{ title: "Settings — AI Hallucination Mitigation System" }] }),
  component: SettingsPage,
});

function SettingsPage() {
  const [health, setHealth] = useState<{ status: string; scifact_corpus_available?: boolean; scifact_model_available?: boolean } | null>(null);
  const [error, setError] = useState("");
  useEffect(() => { api.health().then(setHealth).catch(() => setError("Unable to load backend status.")); }, []);
  return <AppShell>
    <PageHeader title="Settings" description="Runtime configuration and backend capability status." />
    <div className="grid gap-6 lg:grid-cols-2">
      <SectionCard title="Backend status">
        {!health && !error && <p className="text-sm text-muted-foreground">Loading...</p>}
        {error && <p role="alert" className="text-sm text-destructive">{error}</p>}
        {health && <dl className="space-y-3 text-sm"><div className="flex justify-between"><dt>API status</dt><dd className="font-semibold">{health.status}</dd></div><div className="flex justify-between"><dt>SciFact corpus</dt><dd>{health.scifact_corpus_available ? "Available" : "Unavailable"}</dd></div><div className="flex justify-between"><dt>SciFact model</dt><dd>{health.scifact_model_available ? "Available" : "Unavailable"}</dd></div></dl>}
      </SectionCard>
      <SectionCard title="Informational configuration">
        <p className="text-sm leading-relaxed text-muted-foreground">General knowledge retrieval uses the configured Wikipedia/MediaWiki provider. SciFact remains a verification component. Provider, threshold, model, CORS, and upload settings are server-side environment configuration and are not changed from this browser.</p>
      </SectionCard>
    </div>
  </AppShell>;
}
