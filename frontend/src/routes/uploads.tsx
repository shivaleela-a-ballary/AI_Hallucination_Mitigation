import { createFileRoute } from "@tanstack/react-router";
import { FileUp, Info } from "lucide-react";

import { AppShell } from "@/components/app/app-shell";
import { PageHeader, SectionCard } from "@/components/app/ui-kit";

export const Route = createFileRoute("/uploads")({
  head: () => ({ meta: [{ title: "Uploads — AI Hallucination Mitigation System" }] }),
  component: UploadsPage,
});

function UploadsPage() {
  return <AppShell>
    <PageHeader title="Uploads" description="Document ingestion capability status." />
    <SectionCard title="Document upload unavailable" action={<Info className="size-4 text-muted-foreground" />}>
      <div className="flex items-start gap-4">
        <FileUp className="mt-1 size-6 shrink-0 text-muted-foreground" />
        <p className="text-sm leading-relaxed text-muted-foreground">Document upload is not currently available because no ingestion endpoint is configured. Files are not indexed or used as evidence.</p>
      </div>
    </SectionCard>
  </AppShell>;
}
