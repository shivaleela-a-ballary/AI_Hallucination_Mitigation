import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useRef, useState } from "react";
import { ArrowRight, CheckCircle2, CloudUpload, FileText, Info, X } from "lucide-react";

import { AppShell } from "@/components/app/app-shell";
import { PageHeader, SectionCard } from "@/components/app/ui-kit";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import { Slider } from "@/components/ui/slider";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import { exampleClaims, retrievalSources } from "@/data/mock";
import { cn } from "@/lib/utils";

export const Route = createFileRoute("/new-verification")({
  head: () => ({
    meta: [
      { title: "New Verification — AI Hallucination Mitigation System" },
      {
        name: "description",
        content: "Enter a claim or question, attach documents and choose retrieval sources to verify it.",
      },
      { property: "og:title", content: "New Verification — AI Hallucination Mitigation System" },
      {
        property: "og:description",
        content: "Enter a claim, attach documents and verify against trusted sources.",
      },
    ],
  }),
  component: NewVerification,
});

const MAX = 4000;

function NewVerification() {
  const [text, setText] = useState("");
  const [files, setFiles] = useState([{ name: "research_paper.pdf", size: "1.2 MB" }]);
  const [dragging, setDragging] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const navigate = useNavigate();

  const addFiles = (list: FileList | null) => {
    if (!list) return;
    setFiles((prev) => [
      ...prev,
      ...Array.from(list).map((f) => ({
        name: f.name,
        size: `${(f.size / 1024 / 1024).toFixed(1)} MB`,
      })),
    ]);
  };

  return (
    <AppShell>
      <PageHeader
        title="New Verification"
        description="Enter a claim, ask a question or upload documents."
      />

      <div className="grid gap-6 lg:grid-cols-2">
        <SectionCard
          title="1. Enter Claim or Question"
          action={<Info className="size-4 text-muted-foreground" aria-hidden="true" />}
        >
          <Textarea
            value={text}
            maxLength={MAX}
            onChange={(e) => setText(e.target.value)}
            placeholder="Type your claim or question here..."
            aria-label="Claim or question"
            className="min-h-[180px] resize-none rounded-xl bg-background text-base"
          />
          <p className="mt-2 text-right text-xs text-muted-foreground">
            {text.length}/{MAX}
          </p>

          <p className="mt-4 text-sm font-semibold">Example</p>
          <div className="mt-3 flex flex-wrap gap-2">
            {exampleClaims.map((c) => (
              <button
                key={c}
                type="button"
                onClick={() => setText(c)}
                className="rounded-lg border border-border bg-background px-3 py-1.5 text-xs font-medium text-muted-foreground transition-all hover:-translate-y-0.5 hover:border-primary/40 hover:text-foreground focus-visible:ring-2 focus-visible:ring-ring focus-visible:outline-none"
              >
                {c}
              </button>
            ))}
          </div>
        </SectionCard>

        <div className="flex flex-col gap-6">
          <SectionCard
            title="2. Upload Files (Optional)"
            action={<Info className="size-4 text-muted-foreground" aria-hidden="true" />}
          >
            <div
              onDragOver={(e) => {
                e.preventDefault();
                setDragging(true);
              }}
              onDragLeave={() => setDragging(false)}
              onDrop={(e) => {
                e.preventDefault();
                setDragging(false);
                addFiles(e.dataTransfer.files);
              }}
              className={cn(
                "flex flex-col items-center gap-3 rounded-xl border-2 border-dashed p-8 text-center transition-colors",
                dragging ? "border-primary bg-accent" : "border-primary/30 bg-accent/40",
              )}
            >
              <CloudUpload className="size-8 text-primary" aria-hidden="true" />
              <p className="text-sm font-medium">Drag &amp; drop files here</p>
              <p className="text-xs text-muted-foreground">or</p>
              <Button variant="secondary" onClick={() => inputRef.current?.click()} className="rounded-lg">
                Browse Files
              </Button>
              <input
                ref={inputRef}
                type="file"
                multiple
                className="sr-only"
                aria-label="Upload files"
                onChange={(e) => addFiles(e.target.files)}
              />
            </div>

            <ul className="mt-4 flex flex-col gap-2">
              {files.map((f, i) => (
                <li
                  key={`${f.name}-${i}`}
                  className="grid grid-cols-[auto_minmax(0,1fr)_auto] items-center gap-3 rounded-xl border border-border p-3"
                >
                  <FileText className="size-5 shrink-0 text-muted-foreground" aria-hidden="true" />
                  <span className="min-w-0">
                    <span className="block truncate text-sm font-medium">{f.name}</span>
                    <span className="block text-xs text-muted-foreground">{f.size}</span>
                  </span>
                  <span className="flex shrink-0 items-center gap-2">
                    <CheckCircle2 className="size-4 text-success" aria-hidden="true" />
                    <button
                      type="button"
                      aria-label={`Remove ${f.name}`}
                      onClick={() => setFiles((prev) => prev.filter((_, idx) => idx !== i))}
                      className="text-muted-foreground transition-colors hover:text-destructive focus-visible:ring-2 focus-visible:ring-ring focus-visible:outline-none"
                    >
                      <X className="size-4" />
                    </button>
                  </span>
                </li>
              ))}
            </ul>

            <p className="mt-3 text-xs text-muted-foreground">
              Supported files: PDF, TXT, DOCX, CSV (Max 20MB)
            </p>
          </SectionCard>

          <SectionCard
            title="3. Select Retrieval Source"
            action={<Info className="size-4 text-muted-foreground" aria-hidden="true" />}
          >
            <Select defaultValue={retrievalSources[0]}>
              <SelectTrigger className="h-11 w-full rounded-xl">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {retrievalSources.map((s) => (
                  <SelectItem key={s} value={s}>
                    {s}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </SectionCard>
        </div>
      </div>

      <div className="mt-6 grid gap-6 lg:grid-cols-[minmax(0,1fr)_auto] lg:items-center">
        <div className="card-soft px-5">
          <Accordion type="single" collapsible>
            <AccordionItem value="advanced" className="border-none">
              <AccordionTrigger className="text-sm font-semibold">Advanced Options</AccordionTrigger>
              <AccordionContent className="grid gap-6 pb-5 sm:grid-cols-2">
                <div>
                  <Label className="text-xs font-semibold">Evidence depth</Label>
                  <Slider defaultValue={[4]} min={1} max={10} step={1} className="mt-4" />
                  <p className="mt-2 text-xs text-muted-foreground">
                    Number of documents retrieved per claim.
                  </p>
                </div>
                <div className="flex flex-col gap-4">
                  <label className="flex items-center justify-between gap-4 text-sm">
                    Build knowledge graph
                    <Switch defaultChecked />
                  </label>
                  <label className="flex items-center justify-between gap-4 text-sm">
                    Strict citation mode
                    <Switch defaultChecked />
                  </label>
                </div>
              </AccordionContent>
            </AccordionItem>
          </Accordion>
        </div>

        <Button
          size="lg"
          className="h-14 rounded-xl px-10 text-base"
          onClick={() => navigate({ to: "/answer/$id", params: { id: "v2" } })}
        >
          Verify / Ask <ArrowRight className="size-4" />
        </Button>
      </div>
    </AppShell>
  );
}
