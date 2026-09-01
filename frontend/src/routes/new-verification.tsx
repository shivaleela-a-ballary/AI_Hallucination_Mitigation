import { createFileRoute, Link } from "@tanstack/react-router";
import { useEffect, useMemo, useRef, useState } from "react";
import {
  ArrowRight,
  ShieldCheck,
  ShieldAlert,
  HelpCircle,
  Loader2,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  ExternalLink,
  BookOpen,
  Layers,
  Sparkles,
  Info,
  FilePlus,
  Files,
  FileText,
  X,
  Upload,
} from "lucide-react";

import { AppShell } from "@/components/app/app-shell";
import { PageHeader, SectionCard } from "@/components/app/ui-kit";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { toast } from "sonner";
import { cn } from "@/lib/utils";
import { api, type VerificationResponse, type Evidence } from "@/lib/api";

const SUPPORTED_EXTENSIONS = [".pdf", ".txt", ".md", ".markdown", ".csv", ".json"];
const MAX_FILE_SIZE_BYTES = 25 * 1024 * 1024; // 25MB

function getFileExtension(filename: string): string {
  const parts = filename.split(".");
  return parts.length > 1 ? parts.pop()!.toLowerCase() : "txt";
}

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export const Route = createFileRoute("/new-verification")({
  validateSearch: (search: Record<string, unknown>) => ({
    claim: (search.claim as string) || "",
    evidence: (search.evidence as string) || "",
  }),
  head: () => ({ meta: [{ title: "New Verification — AI Hallucination Mitigation System" }] }),
  component: NewVerification,
});

function getStatusBadge(status?: string) {
  const norm = (status || "").toUpperCase();
  if (norm === "SUPPORTED") {
    return {
      label: "SUPPORTED",
      icon: CheckCircle2,
      color: "bg-emerald-500/15 text-emerald-600 dark:text-emerald-400 border-emerald-500/30",
    };
  }
  if (norm === "REFUTED") {
    return {
      label: "REFUTED",
      icon: XCircle,
      color: "bg-rose-500/15 text-rose-600 dark:text-rose-400 border-rose-500/30",
    };
  }
  if (norm === "UNVERIFIED") {
    return {
      label: "UNVERIFIED",
      icon: Info,
      color: "bg-sky-500/15 text-sky-600 dark:text-sky-400 border-sky-500/30",
    };
  }
  return {
    label: "UNCERTAIN",
    icon: HelpCircle,
    color: "bg-amber-500/15 text-amber-600 dark:text-amber-400 border-amber-500/30",
  };
}

function getRiskBadge(risk?: string) {
  const norm = (risk || "MEDIUM").toUpperCase();
  if (norm === "LOW") {
    return {
      label: "LOW RISK",
      color: "bg-emerald-500/15 text-emerald-600 dark:text-emerald-400 border-emerald-500/30",
    };
  }
  if (norm === "HIGH") {
    return {
      label: "HIGH RISK",
      color: "bg-rose-500/15 text-rose-600 dark:text-rose-400 border-rose-500/30",
    };
  }
  return {
    label: "MEDIUM RISK",
    color: "bg-amber-500/15 text-amber-600 dark:text-amber-400 border-amber-500/30",
  };
}

function getQualityBadge(quality?: string) {
  const norm = (quality || "MEDIUM").toUpperCase();
  if (norm === "HIGH") {
    return {
      label: "HIGH QUALITY",
      color: "bg-primary/15 text-primary border-primary/30",
    };
  }
  if (norm === "LOW") {
    return {
      label: "LOW QUALITY",
      color: "bg-muted text-muted-foreground border-border",
    };
  }
  return {
    label: "MEDIUM QUALITY",
    color: "bg-blue-500/15 text-blue-600 dark:text-blue-400 border-blue-500/30",
  };
}

function getSourceStyle(source: string) {
  const s = source.toLowerCase();
  if (s.includes("pubmed")) {
    return "bg-cyan-500/15 text-cyan-600 dark:text-cyan-400 border-cyan-500/30";
  }
  if (s.includes("scifact")) {
    return "bg-purple-500/15 text-purple-600 dark:text-purple-400 border-purple-500/30";
  }
  if (s.includes("wikipedia")) {
    return "bg-emerald-500/15 text-emerald-600 dark:text-emerald-400 border-emerald-500/30";
  }
  if (s.includes("upload") || s.includes("user")) {
    return "bg-amber-500/15 text-amber-600 dark:text-amber-400 border-amber-500/30";
  }
  return "bg-slate-500/15 text-slate-600 dark:text-slate-400 border-slate-500/30";
}

function getRelationshipBadge(relationship?: string) {
  const rel = (relationship || "UNCERTAIN").toUpperCase();
  if (rel === "SUPPORTS") {
    return {
      label: "SUPPORTS CLAIM",
      icon: CheckCircle2,
      color: "bg-emerald-500/15 text-emerald-600 dark:text-emerald-400 border-emerald-500/30",
    };
  }
  if (rel === "CONTRADICTS") {
    return {
      label: "CONTRADICTS CLAIM",
      icon: AlertTriangle,
      color: "bg-rose-500/15 text-rose-600 dark:text-rose-400 border-rose-500/30",
    };
  }
  return {
    label: "UNCERTAIN / NEUTRAL",
    icon: HelpCircle,
    color: "bg-amber-500/15 text-amber-600 dark:text-amber-400 border-amber-500/30",
  };
}

function NewVerification() {
  const search = Route.useSearch();
  const [claim, setClaim] = useState(search.claim || "");
  const [evidence, setEvidence] = useState(search.evidence || "");
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState("");
  const [uploadedCount, setUploadedCount] = useState(0);
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [result, setResult] = useState<VerificationResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [sourceFilter, setSourceFilter] = useState("all");
  const autoExecutedRef = useRef(false);

  const addFiles = (filesToAdd: FileList | File[]) => {
    const validFiles: File[] = [];
    const existingKeys = new Set(selectedFiles.map((f) => `${f.name}-${f.size}`));

    for (let i = 0; i < filesToAdd.length; i++) {
      const file = filesToAdd[i];
      const ext = `.${getFileExtension(file.name)}`;

      if (!SUPPORTED_EXTENSIONS.includes(ext)) {
        toast.error(`"${file.name}" is not supported. Please upload PDF, TXT, MD, CSV, or JSON.`);
        continue;
      }

      if (file.size > MAX_FILE_SIZE_BYTES) {
        toast.error(`"${file.name}" (${formatFileSize(file.size)}) exceeds 25MB limit.`);
        continue;
      }

      const key = `${file.name}-${file.size}`;
      if (existingKeys.has(key)) {
        toast.info(`"${file.name}" is already selected.`);
        continue;
      }

      existingKeys.add(key);
      validFiles.push(file);
    }

    if (validFiles.length > 0) {
      setSelectedFiles((prev) => [...prev, ...validFiles]);
      toast.success(`Added ${validFiles.length} document${validFiles.length > 1 ? "s" : ""}.`);
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      addFiles(e.target.files);
      e.target.value = "";
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      addFiles(e.dataTransfer.files);
    }
  };

  const removeFile = (index: number) => {
    setSelectedFiles((prev) => prev.filter((_, idx) => idx !== index));
  };

  const verify = async (targetClaim?: string, targetEvidence?: string) => {
    const claimToVerify = (targetClaim !== undefined ? targetClaim : claim).trim();
    const evidenceToVerify = (targetEvidence !== undefined ? targetEvidence : evidence).trim();

    if (!claimToVerify) {
      setError("Enter a scientific claim or statement to verify.");
      return;
    }

    setError("");
    setResult(null);

    // 1. Upload any selected documents first before running verification
    if (selectedFiles.length > 0) {
      setUploading(true);
      const totalToUpload = selectedFiles.length;
      let successCount = 0;

      for (let i = 0; i < selectedFiles.length; i++) {
        const file = selectedFiles[i];
        setUploadProgress(`Uploading documents (${i + 1} of ${totalToUpload}): ${file.name}...`);
        try {
          await api.uploadFile(file, file.name);
          successCount++;
        } catch (uploadErr) {
          const errMsg = uploadErr instanceof Error ? uploadErr.message : "Failed to upload document.";
          toast.error(`Error uploading "${file.name}": ${errMsg}`);
          setError(`Upload failed for "${file.name}": ${errMsg}. Please remove it or retry.`);
          setUploading(false);
          return;
        }
      }

      setUploadedCount((prev) => prev + successCount);
      toast.success(`✓ ${successCount} document${successCount > 1 ? "s" : ""} uploaded and indexed into evidence store.`);
      setSelectedFiles([]);
      setUploading(false);
    }

    // 2. Run scientific verification across multi-source evidence
    setLoading(true);
    try {
      const verification = await api.verify(claimToVerify, evidenceToVerify);
      setResult(verification);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Verification failed.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (search.claim && !autoExecutedRef.current) {
      autoExecutedRef.current = true;
      setClaim(search.claim);
      if (search.evidence) setEvidence(search.evidence);
      void verify(search.claim, search.evidence || "");
    }
  }, [search.claim, search.evidence]);

  const handleImagePaste = async (e: React.ClipboardEvent, targetField: "claim" | "evidence") => {
    if (e.clipboardData) {
      let imageFile: File | null = null;
      if (e.clipboardData.files && e.clipboardData.files.length > 0) {
        if (e.clipboardData.files[0].type.startsWith("image/")) {
          imageFile = e.clipboardData.files[0];
        }
      } else if (e.clipboardData.items) {
        for (let i = 0; i < e.clipboardData.items.length; i++) {
          const item = e.clipboardData.items[i];
          if (item.type.startsWith("image/")) {
            const blob = item.getAsFile();
            if (blob) {
              imageFile = blob;
              break;
            }
          }
        }
      }

      if (imageFile) {
        e.preventDefault();
        const toastId = toast.loading("Ingesting and extracting evidence from pasted image screenshot...");
        try {
          const res = await api.uploadFile(imageFile, `Pasted Screenshot ${new Date().toLocaleTimeString()}`);
          const extractedText =
            res.document.chunks?.map((c) => c.content).join("\n\n") ||
            res.document.raw_text_preview ||
            `Extracted evidence from image: ${res.document.title}`;

          if (targetField === "claim") {
            setClaim((prev) => (prev ? `${prev}\n${extractedText}` : extractedText));
          } else {
            setEvidence((prev) => (prev ? `${prev}\n\n${extractedText}` : extractedText));
          }
          toast.success("Image text extracted and inserted!", { id: toastId });
        } catch (err) {
          toast.error("Failed to parse pasted image.", { id: toastId });
        }
      }
    }
  };

  const filteredEvidence = useMemo(() => {
    if (!result?.evidence) return [];
    if (sourceFilter === "all") return result.evidence;
    if (sourceFilter === "uploads") {
      return result.evidence.filter(
        (item) =>
          item.source.toLowerCase().includes("upload") ||
          item.source.toLowerCase().includes("user") ||
          (item.source_type || "").toLowerCase().includes("upload")
      );
    }
    return result.evidence.filter((item) =>
      item.source.toLowerCase().includes(sourceFilter.toLowerCase())
    );
  }, [result?.evidence, sourceFilter]);

  const sourceCounts = useMemo(() => {
    if (!result?.evidence) return { all: 0, scifact: 0, pubmed: 0, wikipedia: 0, uploads: 0 };
    return {
      all: result.evidence.length,
      scifact: result.evidence.filter((e) => e.source.toLowerCase().includes("scifact")).length,
      pubmed: result.evidence.filter((e) => e.source.toLowerCase().includes("pubmed")).length,
      wikipedia: result.evidence.filter((e) => e.source.toLowerCase().includes("wikipedia")).length,
      uploads: result.evidence.filter(
        (e) =>
          e.source.toLowerCase().includes("upload") ||
          e.source.toLowerCase().includes("user") ||
          (e.source_type || "").toLowerCase().includes("upload")
      ).length,
    };
  }, [result?.evidence]);

  const statusBadge = getStatusBadge(result?.verification_status || result?.prediction);
  const riskBadge = getRiskBadge(result?.hallucination_risk);
  const qualityBadge = getQualityBadge(result?.evidence_quality);

  return (
    <AppShell>
      <PageHeader
        title="Scientific Claim Verification"
        description="Verify scientific and factual claims against multi-source biomedical literature (SciFact + PubMed + Wikipedia) and user-uploaded research documents."
      />

      {/* Claim and Custom Evidence Inputs */}
      <div className="grid gap-6 lg:grid-cols-2">
        <SectionCard title="Claim to Verify">
          <Textarea
            value={claim}
            onChange={(event) => setClaim(event.target.value)}
            onPaste={(e) => void handleImagePaste(e, "claim")}
            aria-label="Claim"
            placeholder="e.g., Smoking significantly increases the risk of lung cancer."
            className="min-h-32 resize-none rounded-xl bg-background text-sm"
          />
          <div className="mt-3 flex items-center justify-between text-xs text-muted-foreground">
            <span>Ctrl + V supports image screenshots and text.</span>
            <span>{claim.length}/2000 chars</span>
          </div>
        </SectionCard>

        <SectionCard title="Custom Evidence (Optional)">
          <Textarea
            value={evidence}
            onChange={(event) => setEvidence(event.target.value)}
            onPaste={(e) => void handleImagePaste(e, "evidence")}
            aria-label="Evidence"
            placeholder="Paste raw excerpts, study abstracts, or specific text to include as candidate evidence..."
            className="min-h-32 resize-none rounded-xl bg-background text-sm"
          />
          <p className="mt-3 text-xs text-muted-foreground">
            If provided, custom evidence or pasted image extracts are analyzed directly alongside indexed literature.
          </p>
        </SectionCard>
      </div>

      {/* Add Documents Section (Placed directly ABOVE Verify Claim) */}
      <div className="mt-6">
        <SectionCard
          title="Add Documents"
          description="Optionally attach research papers, articles, or data files. Uploaded documents are automatically chunked and indexed as grounded evidence for verification."
        >
          <div className="grid gap-6 lg:grid-cols-2">
            {/* Drag & Drop Upload Zone */}
            <div
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
              onClick={() => fileInputRef.current?.click()}
              className={cn(
                "relative flex flex-col items-center justify-center rounded-xl border-2 border-dashed p-6 text-center transition-all cursor-pointer",
                isDragging
                  ? "border-primary bg-primary/10 shadow-sm"
                  : "border-border/80 bg-background/50 hover:border-primary/50 hover:bg-muted/30",
                (loading || uploading) && "pointer-events-none opacity-60"
              )}
            >
              <input
                ref={fileInputRef}
                type="file"
                multiple
                accept=".pdf,.txt,.md,.markdown,.csv,.json"
                onChange={handleFileSelect}
                className="hidden"
                disabled={loading || uploading}
              />
              <div className="rounded-full bg-primary/10 p-3 text-primary ring-1 ring-primary/20">
                <FilePlus className="size-6" />
              </div>
              <p className="mt-3 text-sm font-semibold text-foreground">
                Drag &amp; drop files here or <span className="text-primary underline">browse</span>
              </p>
              <p className="mt-1 text-xs text-muted-foreground">
                Supported: PDF, TXT, MD, CSV, JSON (max 25MB each)
              </p>
            </div>

            {/* Selected Documents List */}
            <div className="flex flex-col justify-between rounded-xl border border-border/80 bg-background/40 p-4">
              <div className="flex items-center justify-between border-b border-border/60 pb-3">
                <div className="flex items-center gap-2">
                  <Files className="size-4 text-primary" />
                  <span className="text-sm font-semibold text-foreground">
                    Selected Documents ({selectedFiles.length})
                  </span>
                </div>
                {selectedFiles.length > 0 && !uploading && !loading && (
                  <button
                    type="button"
                    onClick={(e) => {
                      e.stopPropagation();
                      setSelectedFiles([]);
                    }}
                    className="text-xs text-muted-foreground hover:text-destructive transition-colors font-medium"
                  >
                    Clear All
                  </button>
                )}
              </div>

              {selectedFiles.length === 0 ? (
                <div className="flex flex-1 flex-col items-center justify-center py-6 text-center text-xs text-muted-foreground">
                  <BookOpen className="size-8 mb-2 opacity-30 text-muted-foreground" />
                  No documents selected yet.
                  <span className="mt-0.5 text-[11px] opacity-70">
                    Uploaded documents are automatically chunked &amp; indexed into multi-source retrieval.
                  </span>
                </div>
              ) : (
                <div className="mt-3 max-h-48 space-y-2 overflow-y-auto pr-1">
                  {selectedFiles.map((file, index) => {
                    const ext = getFileExtension(file.name);
                    const sizeStr = formatFileSize(file.size);
                    return (
                      <div
                        key={`${file.name}-${file.size}-${index}`}
                        className="flex items-center justify-between rounded-lg border border-border bg-card/80 p-2.5 text-xs transition-colors hover:border-border/80"
                      >
                        <div className="flex items-center gap-2.5 min-w-0 pr-2">
                          <div className="grid size-7 place-items-center rounded bg-primary/10 text-primary font-bold text-[10px] shrink-0 uppercase">
                            {ext}
                          </div>
                          <div className="min-w-0">
                            <p className="truncate font-medium text-foreground text-xs" title={file.name}>
                              {file.name}
                            </p>
                            <p className="text-[10px] text-muted-foreground">
                              <span className="uppercase font-semibold">{ext}</span> • {sizeStr}
                            </p>
                          </div>
                        </div>
                        <button
                          type="button"
                          onClick={(e) => {
                            e.stopPropagation();
                            removeFile(index);
                          }}
                          disabled={uploading || loading}
                          className="grid size-6 place-items-center rounded text-muted-foreground hover:bg-destructive/15 hover:text-destructive transition-colors shrink-0 disabled:opacity-50"
                          title={`Remove ${file.name}`}
                        >
                          <X className="size-3.5" />
                        </button>
                      </div>
                    );
                  })}
                </div>
              )}

              {uploadedCount > 0 && selectedFiles.length === 0 && (
                <div className="mt-2 flex items-center gap-1.5 rounded-lg bg-emerald-500/10 border border-emerald-500/20 px-3 py-2 text-xs text-emerald-600 dark:text-emerald-400 font-medium">
                  <CheckCircle2 className="size-4 shrink-0" />
                  <span>✓ {uploadedCount} document{uploadedCount > 1 ? "s" : ""} uploaded &amp; indexed as evidence</span>
                </div>
              )}
            </div>
          </div>
        </SectionCard>
      </div>

      {/* Verify Claim Action Button */}
      <div className="mt-6 flex items-center gap-3">
        <Button
          className="h-12 rounded-xl px-7 font-medium shadow-sm"
          disabled={loading || uploading}
          onClick={() => void verify()}
        >
          {uploading ? (
            <>
              <Loader2 className="size-4 mr-2 animate-spin" /> {uploadProgress || "Uploading documents..."}
            </>
          ) : loading ? (
            <>
              <Loader2 className="size-4 mr-2 animate-spin" /> Verifying Multi-Source Evidence...
            </>
          ) : (
            <>
              Verify Claim <ArrowRight className="size-4 ml-2" />
            </>
          )}
        </Button>
      </div>

      {error && (
        <div role="alert" className="mt-4 rounded-xl border border-destructive/30 bg-destructive/10 p-4 text-sm text-destructive flex items-center gap-2">
          <AlertTriangle className="size-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {result && (
        <div className="mt-8 space-y-6">
          {/* Main Verification Dashboard Card */}
          <div className="rounded-2xl border border-border bg-card p-6 shadow-sm">
            <div className="flex flex-wrap items-center justify-between gap-4 border-b border-border pb-6">
              <div>
                <span className="text-xs font-semibold tracking-wider text-muted-foreground uppercase">
                  Verification Verdict
                </span>
                <div className="mt-2 flex items-center gap-3">
                  <div className={`inline-flex items-center gap-2 rounded-xl border px-4 py-2 font-bold tracking-wide ${statusBadge.color}`}>
                    <statusBadge.icon className="size-5" />
                    <span className="text-lg">{statusBadge.label}</span>
                  </div>
                  <Badge variant="outline" className={`h-8 px-3 text-xs font-semibold ${riskBadge.color}`}>
                    {riskBadge.label}
                  </Badge>
                  <Badge variant="outline" className={`h-8 px-3 text-xs font-semibold ${qualityBadge.color}`}>
                    {qualityBadge.label}
                  </Badge>
                </div>
              </div>

              <div className="flex items-center gap-6">
                <div className="text-right">
                  <span className="text-xs text-muted-foreground">Model Confidence</span>
                  <p className="text-2xl font-bold tracking-tight text-foreground">
                    {result.confidence_available
                      ? `${(result.confidence_score * 100).toFixed(1)}%`
                      : "N/A"}
                  </p>
                </div>
              </div>
            </div>

            {/* Metrics Breakdown Grid */}
            <div className="mt-6 grid grid-cols-2 gap-4 sm:grid-cols-4">
              <div className="rounded-xl border border-border bg-muted/30 p-3">
                <div className="text-xs text-muted-foreground">Sources Retrieved</div>
                <div className="mt-1 text-xl font-bold">{result.evidence.length}</div>
              </div>
              <div className="rounded-xl border border-emerald-500/20 bg-emerald-500/5 p-3">
                <div className="text-xs text-emerald-600 dark:text-emerald-400">Supporting Evidence</div>
                <div className="mt-1 text-xl font-bold text-emerald-600 dark:text-emerald-400">
                  {result.supporting_evidence?.length ?? result.evidence.filter(e => e.relationship === "SUPPORTS").length}
                </div>
              </div>
              <div className="rounded-xl border border-rose-500/20 bg-rose-500/5 p-3">
                <div className="text-xs text-rose-600 dark:text-rose-400">Contradicting Evidence</div>
                <div className="mt-1 text-xl font-bold text-rose-600 dark:text-rose-400">
                  {result.contradicting_evidence?.length ?? result.evidence.filter(e => e.relationship === "CONTRADICTS").length}
                </div>
              </div>
              <div className="rounded-xl border border-amber-500/20 bg-amber-500/5 p-3">
                <div className="text-xs text-amber-600 dark:text-amber-400">Uncertain / Neutral</div>
                <div className="mt-1 text-xl font-bold text-amber-600 dark:text-amber-400">
                  {result.uncertain_evidence?.length ?? result.evidence.filter(e => e.relationship === "UNCERTAIN").length}
                </div>
              </div>
            </div>

            {/* Why This Result Explainability Section */}
            {result.explanation_bullets && result.explanation_bullets.length > 0 && (
              <div className="mt-6 rounded-xl border border-primary/20 bg-primary/5 p-4">
                <div className="flex items-center gap-2 text-sm font-semibold text-primary">
                  <Sparkles className="size-4" /> Why this result?
                </div>
                <ul className="mt-3 space-y-1.5 text-xs sm:text-sm text-foreground/90">
                  {result.explanation_bullets.map((bullet, idx) => (
                    <li key={idx} className="flex items-start gap-2">
                      <span className="text-primary">•</span>
                      <span>{bullet}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>

          {/* Evidence Passages with Source Filter Tabs */}
          <SectionCard
            title={`Evidence Passages (${result.evidence.length})`}
            action={
              <Tabs value={sourceFilter} onValueChange={setSourceFilter} className="w-auto">
                <TabsList className="h-8 bg-muted/60 p-0.5">
                  <TabsTrigger value="all" className="h-7 text-xs px-2.5">
                    All ({sourceCounts.all})
                  </TabsTrigger>
                  {sourceCounts.scifact > 0 && (
                    <TabsTrigger value="scifact" className="h-7 text-xs px-2.5">
                      SciFact ({sourceCounts.scifact})
                    </TabsTrigger>
                  )}
                  {sourceCounts.pubmed > 0 && (
                    <TabsTrigger value="pubmed" className="h-7 text-xs px-2.5">
                      PubMed ({sourceCounts.pubmed})
                    </TabsTrigger>
                  )}
                  {sourceCounts.wikipedia > 0 && (
                    <TabsTrigger value="wikipedia" className="h-7 text-xs px-2.5">
                      Wikipedia ({sourceCounts.wikipedia})
                    </TabsTrigger>
                  )}
                  {sourceCounts.uploads > 0 && (
                    <TabsTrigger value="uploads" className="h-7 text-xs px-2.5">
                      Uploads ({sourceCounts.uploads})
                    </TabsTrigger>
                  )}
                </TabsList>
              </Tabs>
            }
          >
            {filteredEvidence.length > 0 ? (
              <div className="space-y-4">
                {filteredEvidence.map((item, idx) => {
                  const rel = getRelationshipBadge(item.relationship);
                  return (
                    <div
                      key={`${item.source}-${item.title}-${idx}`}
                      className="rounded-xl border border-border bg-card p-4 transition-all hover:border-primary/40"
                    >
                      <div className="flex flex-wrap items-center justify-between gap-2">
                        <div className="flex flex-wrap items-center gap-2">
                          <span className={`inline-flex items-center rounded-md border px-2 py-0.5 text-xs font-semibold ${getSourceStyle(item.source)}`}>
                            {item.source}
                          </span>
                          <span className={`inline-flex items-center gap-1 rounded-md border px-2 py-0.5 text-xs font-semibold ${rel.color}`}>
                            <rel.icon className="size-3" />
                            {rel.label}
                          </span>
                        </div>
                        <div className="text-xs font-medium text-muted-foreground">
                          Relevance: {(item.similarity_score * 100).toFixed(1)}%
                        </div>
                      </div>

                      <h4 className="mt-2 text-sm font-semibold text-foreground">
                        {item.title}
                      </h4>

                      {item.authors && item.authors.length > 0 && (
                        <p className="mt-1 text-xs text-muted-foreground">
                          Authors: {item.authors.slice(0, 3).join(", ")}{item.authors.length > 3 ? " et al." : ""}
                          {item.publication_date ? ` • (${item.publication_date})` : ""}
                        </p>
                      )}

                      <p className="mt-2 text-xs leading-relaxed text-foreground/80 whitespace-pre-line">
                        {item.content}
                      </p>

                      <div className="mt-3 flex items-center gap-3 text-xs">
                        {item.pmid && (
                          <a
                            href={`https://pubmed.ncbi.nlm.nih.gov/${item.pmid}/`}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="inline-flex items-center gap-1 text-primary hover:underline font-medium"
                          >
                            PMID: {item.pmid} <ExternalLink className="size-3" />
                          </a>
                        )}
                        {item.doi && (
                          <a
                            href={`https://doi.org/${item.doi}`}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="inline-flex items-center gap-1 text-primary hover:underline font-medium"
                          >
                            DOI: {item.doi} <ExternalLink className="size-3" />
                          </a>
                        )}
                        {item.url && !item.pmid && (
                          <a
                            href={item.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="inline-flex items-center gap-1 text-primary hover:underline font-medium"
                          >
                            Source Link <ExternalLink className="size-3" />
                          </a>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            ) : (
              <p className="py-6 text-center text-sm text-muted-foreground">
                No evidence passages found matching the selected filter.
              </p>
            )}
          </SectionCard>
        </div>
      )}
    </AppShell>
  );
}
