import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useEffect, useState, useRef } from "react";
import {
  UploadCloud,
  FileText,
  FileCode,
  FileCheck2,
  Trash2,
  ExternalLink,
  Loader2,
  AlertTriangle,
  CheckCircle2,
  Sparkles,
  Search,
  Eye,
  FileUp,
  Layers,
  ShieldCheck,
  BookOpen,
  Image as ImageIcon,
  ClipboardPaste,
  X,
} from "lucide-react";
import { toast } from "sonner";

import { AppShell } from "@/components/app/app-shell";
import { PageHeader, SectionCard } from "@/components/app/ui-kit";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";
import { api, type UploadedDocument } from "@/lib/api";

export const Route = createFileRoute("/uploads")({
  head: () => ({ meta: [{ title: "Uploads & Image Ingestion — AI Hallucination Mitigation System" }] }),
  component: UploadsPage,
});

function formatBytes(bytes: number): string {
  if (bytes === 0) return "0 B";
  const k = 1024;
  const sizes = ["B", "KB", "MB", "GB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${(bytes / Math.pow(k, i)).toFixed(1)} ${sizes[i]}`;
}

function getFileTypeBadge(type: string) {
  const t = type.toLowerCase();
  if (t.includes("pdf")) return { label: "PDF", color: "bg-rose-500/15 text-rose-600 dark:text-rose-400 border-rose-500/30" };
  if (t.includes("json")) return { label: "JSON", color: "bg-amber-500/15 text-amber-600 dark:text-amber-400 border-amber-500/30" };
  if (t.includes("csv")) return { label: "CSV", color: "bg-emerald-500/15 text-emerald-600 dark:text-emerald-400 border-emerald-500/30" };
  if (t.includes("md")) return { label: "MD", color: "bg-blue-500/15 text-blue-600 dark:text-blue-400 border-blue-500/30" };
  if (t.includes("png") || t.includes("jpg") || t.includes("jpeg") || t.includes("webp") || t.includes("image")) {
    return { label: "IMAGE", color: "bg-cyan-500/15 text-cyan-600 dark:text-cyan-400 border-cyan-500/30" };
  }
  return { label: "TXT", color: "bg-purple-500/15 text-purple-600 dark:text-purple-400 border-purple-500/30" };
}

function UploadsPage() {
  const navigate = useNavigate();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [activeTab, setActiveTab] = useState<"file" | "text">("file");
  const [documents, setDocuments] = useState<UploadedDocument[]>([]);
  const [loadingDocs, setLoadingDocs] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");

  // File & Image Upload State
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [imagePreviewUrl, setImagePreviewUrl] = useState<string | null>(null);
  const [fileTitle, setFileTitle] = useState("");
  const [isUploading, setIsUploading] = useState(false);
  const [dragOver, setDragOver] = useState(false);

  // Text Ingestion State
  const [rawTitle, setRawTitle] = useState("");
  const [rawContent, setRawContent] = useState("");
  const [isSubmittingText, setIsSubmittingText] = useState(false);

  // Preview Modal
  const [previewDoc, setPreviewDoc] = useState<UploadedDocument | null>(null);

  const loadDocuments = async () => {
    setLoadingDocs(true);
    try {
      const res = await api.getUploads();
      setDocuments(res.documents || []);
    } catch (err) {
      console.warn("Failed loading uploaded documents:", err);
    } finally {
      setLoadingDocs(false);
    }
  };

  useEffect(() => {
    void loadDocuments();
  }, []);

  // Cleanup blob URLs on unmount or file change
  useEffect(() => {
    return () => {
      if (imagePreviewUrl) {
        URL.revokeObjectURL(imagePreviewUrl);
      }
    };
  }, [imagePreviewUrl]);

  // Global Ctrl + V Paste Listener for Images & Documents
  useEffect(() => {
    const handlePaste = (e: ClipboardEvent) => {
      const target = e.target as HTMLElement | null;
      const isTextInput = target && (target.tagName === "INPUT" || target.tagName === "TEXTAREA");

      if (e.clipboardData) {
        // 1. Check for files / images in clipboard
        let capturedFile: File | null = null;

        if (e.clipboardData.files && e.clipboardData.files.length > 0) {
          capturedFile = e.clipboardData.files[0];
        } else if (e.clipboardData.items) {
          for (let i = 0; i < e.clipboardData.items.length; i++) {
            const item = e.clipboardData.items[i];
            if (item.type.startsWith("image/") || item.kind === "file") {
              const blob = item.getAsFile();
              if (blob) {
                capturedFile = blob;
                break;
              }
            }
          }
        }

        if (capturedFile) {
          e.preventDefault();
          const ext = capturedFile.type.split("/")[1] || "png";
          const fileName =
            capturedFile.name && capturedFile.name !== "image.png"
              ? capturedFile.name
              : `pasted_screenshot_${Date.now()}.${ext}`;

          const namedFile = new File([capturedFile], fileName, {
            type: capturedFile.type || "image/png",
          });

          setSelectedFile(namedFile);
          if (namedFile.type.startsWith("image/")) {
            if (imagePreviewUrl) URL.revokeObjectURL(imagePreviewUrl);
            setImagePreviewUrl(URL.createObjectURL(namedFile));
          } else {
            setImagePreviewUrl(null);
          }

          setFileTitle(namedFile.name.replace(/\.[^/.]+$/, ""));
          setActiveTab("file");
          toast.success(`Image captured from clipboard (Ctrl+V): ${namedFile.name}`);
          return;
        }

        // 2. If plain text and user is not already focused in an input
        if (!isTextInput) {
          const text = e.clipboardData.getData("text");
          if (text && text.trim().length > 10) {
            setActiveTab("text");
            setRawContent((prev) => (prev ? `${prev}\n\n${text}` : text));
            if (!rawTitle) {
              setRawTitle(`Pasted Note (${new Date().toLocaleTimeString()})`);
            }
            toast.info("Pasted text into raw text ingestion form.");
          }
        }
      }
    };

    window.addEventListener("paste", handlePaste);
    return () => window.removeEventListener("paste", handlePaste);
  }, [imagePreviewUrl, rawTitle]);

  const handleProcessFile = (file: File) => {
    setSelectedFile(file);
    if (file.type.startsWith("image/")) {
      if (imagePreviewUrl) URL.revokeObjectURL(imagePreviewUrl);
      setImagePreviewUrl(URL.createObjectURL(file));
    } else {
      setImagePreviewUrl(null);
    }
    if (!fileTitle) {
      setFileTitle(file.name.replace(/\.[^/.]+$/, ""));
    }
  };

  const handleFileDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleProcessFile(e.dataTransfer.files[0]);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      handleProcessFile(e.target.files[0]);
    }
  };

  const handleClearSelectedFile = (e?: React.MouseEvent) => {
    if (e) e.stopPropagation();
    setSelectedFile(null);
    if (imagePreviewUrl) {
      URL.revokeObjectURL(imagePreviewUrl);
      setImagePreviewUrl(null);
    }
    setFileTitle("");
    if (fileInputRef.current) fileInputRef.current.value = "";
  };

  const handleUploadSubmit = async () => {
    if (!selectedFile) {
      toast.error("Please select or paste an image/file to upload.");
      return;
    }

    setIsUploading(true);
    try {
      const res = await api.uploadFile(selectedFile, fileTitle.trim() || undefined);
      toast.success(res.message || "Document uploaded and indexed successfully!");
      handleClearSelectedFile();
      await loadDocuments();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Failed to upload document.");
    } finally {
      setIsUploading(false);
    }
  };

  const handleTextSubmit = async () => {
    if (!rawTitle.trim() || !rawContent.trim()) {
      toast.error("Please provide both a document title and text content.");
      return;
    }

    setIsSubmittingText(true);
    try {
      const res = await api.uploadText(rawTitle.trim(), rawContent.trim());
      toast.success(res.message || "Text passage ingested successfully!");
      setRawTitle("");
      setRawContent("");
      await loadDocuments();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Failed to ingest text.");
    } finally {
      setIsSubmittingText(false);
    }
  };

  const handleDelete = async (doc: UploadedDocument) => {
    if (!confirm(`Delete "${doc.title || doc.filename}" from the evidence store?`)) return;

    try {
      await api.deleteUpload(doc.id);
      toast.info(`Deleted "${doc.title || doc.filename}".`);
      setDocuments((prev) => prev.filter((d) => d.id !== doc.id));
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Failed to delete document.");
    }
  };

  const filteredDocs = documents.filter((doc) => {
    const q = searchQuery.toLowerCase().trim();
    if (!q) return true;
    return (
      (doc.title && doc.title.toLowerCase().includes(q)) ||
      (doc.filename && doc.filename.toLowerCase().includes(q)) ||
      (doc.raw_text_preview && doc.raw_text_preview.toLowerCase().includes(q))
    );
  });

  return (
    <AppShell>
      <PageHeader
        title="Document & Image Ingestion"
        description="Ingest research papers, clinical trial PDFs, images/screenshots (Ctrl+V supported), and study articles into the active evidence store for claim verification and RAG grounding."
      />

      {/* Upload Methods Card */}
      <div className="rounded-2xl border border-border bg-card p-6 shadow-sm">
        <Tabs value={activeTab} onValueChange={(v) => setActiveTab(v as "file" | "text")} className="w-full">
          <div className="flex flex-wrap items-center justify-between gap-3 mb-6">
            <TabsList className="grid w-full max-w-xs grid-cols-2 rounded-xl bg-muted/60 p-1">
              <TabsTrigger value="file" className="rounded-lg text-xs font-semibold">
                <FileUp className="size-3.5 mr-1.5" /> Upload File / Image
              </TabsTrigger>
              <TabsTrigger value="text" className="rounded-lg text-xs font-semibold">
                <FileText className="size-3.5 mr-1.5" /> Paste Raw Text
              </TabsTrigger>
            </TabsList>

            <div className="inline-flex items-center gap-1.5 rounded-full border border-primary/25 bg-primary/10 px-3 py-1 text-xs font-semibold text-primary">
              <ClipboardPaste className="size-3.5" />
              <span>Press <kbd className="rounded border border-primary/30 bg-background/80 px-1 py-0.5 font-mono text-[10px]">Ctrl + V</kbd> to paste images directly</span>
            </div>
          </div>

          {/* Tab 1: File & Image Upload */}
          <TabsContent value="file" className="space-y-4">
            <div
              onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
              onDragLeave={() => setDragOver(false)}
              onDrop={handleFileDrop}
              onClick={() => fileInputRef.current?.click()}
              className={`relative flex flex-col items-center justify-center rounded-2xl border-2 border-dashed p-8 text-center transition-all cursor-pointer ${
                dragOver
                  ? "border-primary bg-primary/10 scale-[0.99]"
                  : "border-border/80 bg-background/50 hover:border-primary/50 hover:bg-accent/40"
              }`}
            >
              <input
                ref={fileInputRef}
                type="file"
                accept=".pdf,.txt,.md,.json,.csv,.png,.jpg,.jpeg,.webp,.bmp,.tiff,.gif"
                onChange={handleFileChange}
                className="hidden"
              />

              {imagePreviewUrl ? (
                <div className="flex flex-col items-center space-y-3">
                  <div className="relative group">
                    <img
                      src={imagePreviewUrl}
                      alt="Pasted/Selected Preview"
                      className="max-h-48 max-w-full rounded-xl border border-border shadow-md object-contain bg-background"
                    />
                    <button
                      type="button"
                      onClick={handleClearSelectedFile}
                      className="absolute -top-2 -right-2 rounded-full bg-destructive text-destructive-foreground p-1 shadow-md hover:scale-110 transition-transform"
                      title="Remove image"
                    >
                      <X className="size-3.5" />
                    </button>
                  </div>
                  <div className="inline-flex items-center gap-2 rounded-full border border-primary/30 bg-primary/10 px-3 py-1 text-xs font-medium text-primary">
                    <ImageIcon className="size-3.5" />
                    <span>{selectedFile?.name} ({formatBytes(selectedFile?.size || 0)})</span>
                  </div>
                </div>
              ) : (
                <>
                  <div className="grid size-12 place-items-center rounded-2xl bg-primary/10 text-primary">
                    <UploadCloud className="size-6" />
                  </div>
                  <p className="mt-3 text-sm font-semibold text-foreground">
                    {selectedFile ? selectedFile.name : "Click to browse, drag and drop, or press Ctrl + V"}
                  </p>
                  <p className="mt-1 text-xs text-muted-foreground">
                    Supports Images (PNG, JPG, WEBP, BMP), PDF, Plain Text (.txt), Markdown (.md), JSON, and CSV (up to 25MB)
                  </p>
                  {selectedFile && (
                    <div className="mt-3 inline-flex items-center gap-2 rounded-full border border-primary/30 bg-primary/10 px-3 py-1 text-xs font-medium text-primary">
                      <CheckCircle2 className="size-3" /> Ready: {formatBytes(selectedFile.size)}
                    </div>
                  )}
                </>
              )}
            </div>

            {selectedFile && (
              <div className="grid gap-3 sm:grid-cols-[1fr_auto]">
                <Input
                  value={fileTitle}
                  onChange={(e) => setFileTitle(e.target.value)}
                  placeholder="Document / Image Title (Optional)..."
                  className="rounded-xl bg-background"
                />
                <Button
                  onClick={() => void handleUploadSubmit()}
                  disabled={isUploading}
                  className="rounded-xl px-6 font-semibold"
                >
                  {isUploading ? (
                    <>
                      <Loader2 className="size-4 mr-2 animate-spin" /> Ingesting & Extracting...
                    </>
                  ) : (
                    <>
                      <FileCheck2 className="size-4 mr-2" /> Ingest Evidence
                    </>
                  )}
                </Button>
              </div>
            )}
          </TabsContent>

          {/* Tab 2: Raw Text Ingestion */}
          <TabsContent value="text" className="space-y-4">
            <Input
              value={rawTitle}
              onChange={(e) => setRawTitle(e.target.value)}
              placeholder="Document Title (e.g. 'Clinical Trial Phase III Results on Pembrolizumab')..."
              className="rounded-xl bg-background text-sm font-medium"
            />
            <Textarea
              value={rawContent}
              onChange={(e) => setRawContent(e.target.value)}
              placeholder="Paste study abstract, medical literature excerpt, or reference text here (or press Ctrl + V)..."
              className="min-h-40 resize-none rounded-xl bg-background text-sm leading-relaxed"
            />
            <div className="flex items-center justify-between">
              <span className="text-xs text-muted-foreground">
                {rawContent.split(/\s+/).filter(Boolean).length} words • {rawContent.length} characters
              </span>
              <Button
                onClick={() => void handleTextSubmit()}
                disabled={isSubmittingText}
                className="rounded-xl px-6 font-semibold"
              >
                {isSubmittingText ? (
                  <>
                    <Loader2 className="size-4 mr-2 animate-spin" /> Ingesting Text...
                  </>
                ) : (
                  <>
                    <FileCheck2 className="size-4 mr-2" /> Ingest Text Passage
                  </>
                )}
              </Button>
            </div>
          </TabsContent>
        </Tabs>
      </div>

      {/* Indexed Document Library Section */}
      <div className="mt-8 space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h3 className="text-lg font-bold tracking-tight text-foreground flex items-center gap-2">
              <BookOpen className="size-5 text-primary" /> Active Evidence Knowledge Base ({documents.length})
            </h3>
            <p className="text-xs text-muted-foreground">
              These documents and image assets are actively indexed and retrieved during AI claim verification and chat queries.
            </p>
          </div>

          <div className="relative w-full sm:w-64">
            <Search className="absolute left-3 top-2.5 size-4 text-muted-foreground" />
            <Input
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search documents..."
              className="pl-9 h-9 rounded-xl text-xs bg-card"
            />
          </div>
        </div>

        {loadingDocs ? (
          <div className="py-12 text-center text-muted-foreground flex flex-col items-center gap-2">
            <Loader2 className="size-6 animate-spin text-primary" />
            <span className="text-sm">Loading ingested documents...</span>
          </div>
        ) : filteredDocs.length > 0 ? (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {filteredDocs.map((doc) => {
              const badge = getFileTypeBadge(doc.file_type || "txt");
              return (
                <div
                  key={doc.id}
                  className="flex flex-col justify-between rounded-2xl border border-border bg-card p-5 shadow-sm transition-all hover:border-primary/40 hover:shadow-md"
                >
                  <div>
                    <div className="flex items-center justify-between gap-2">
                      <span className={`inline-flex items-center rounded-md border px-2 py-0.5 text-xs font-bold ${badge.color}`}>
                        {badge.label}
                      </span>
                      <span className="text-xs text-muted-foreground">
                        {formatBytes(doc.file_size)}
                      </span>
                    </div>

                    <h4 className="mt-3 text-sm font-bold text-foreground line-clamp-1">
                      {doc.title || doc.filename}
                    </h4>
                    <p className="mt-0.5 text-xs text-muted-foreground truncate">
                      {doc.filename}
                    </p>

                    <div className="mt-3 flex items-center gap-2">
                      <Badge variant="outline" className="text-xs font-semibold bg-primary/5 text-primary border-primary/20">
                        <Layers className="size-3 mr-1" /> {doc.chunk_count} Chunks Indexed
                      </Badge>
                    </div>

                    {doc.raw_text_preview && (
                      <p className="mt-3 text-xs text-foreground/75 line-clamp-3 leading-relaxed bg-muted/30 p-2 rounded-lg border border-border/50">
                        {doc.raw_text_preview}
                      </p>
                    )}
                  </div>

                  <div className="mt-4 pt-3 border-t border-border/60 flex items-center justify-between gap-2">
                    <button
                      type="button"
                      onClick={() => setPreviewDoc(doc)}
                      className="inline-flex items-center gap-1 text-xs font-semibold text-primary hover:underline"
                    >
                      <Eye className="size-3.5" /> View Passages
                    </button>

                    <div className="flex items-center gap-1">
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={() => {
                          const evidenceSample = doc.chunks?.[0]?.content || doc.raw_text_preview || "";
                          navigate({
                            to: "/new-verification",
                            search: {
                              claim: doc.title,
                              evidence: evidenceSample,
                            },
                          });
                        }}
                        title="Verify claim using this document"
                        className="size-8 text-muted-foreground hover:text-primary"
                      >
                        <ShieldCheck className="size-4" />
                      </Button>

                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={() => void handleDelete(doc)}
                        title="Delete document"
                        className="size-8 text-muted-foreground hover:text-destructive"
                      >
                        <Trash2 className="size-4" />
                      </Button>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        ) : (
          <div className="rounded-2xl border border-dashed border-border p-12 text-center">
            <BookOpen className="mx-auto size-10 text-muted-foreground/50" />
            <h4 className="mt-3 text-sm font-semibold text-foreground">No documents or images ingested yet</h4>
            <p className="mt-1 text-xs text-muted-foreground max-w-sm mx-auto">
              Upload a biomedical PDF, image screenshot (or press Ctrl + V), text document, or paste a study excerpt above to expand the ground-truth evidence store.
            </p>
          </div>
        )}
      </div>

      {/* Extracted Chunks Preview Modal */}
      {previewDoc && (
        <Dialog open={!!previewDoc} onOpenChange={(open) => !open && setPreviewDoc(null)}>
          <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto border-border bg-background p-6 rounded-2xl">
            <DialogHeader>
              <DialogTitle className="text-lg font-bold flex items-center gap-2">
                <Layers className="size-5 text-primary" /> {previewDoc.title || previewDoc.filename}
              </DialogTitle>
              <DialogDescription className="text-xs text-muted-foreground">
                Showing {previewDoc.chunks?.length || 0} parsed evidence chunk(s) indexed for semantic retrieval.
              </DialogDescription>
            </DialogHeader>

            <div className="mt-4 space-y-3">
              {previewDoc.chunks && previewDoc.chunks.length > 0 ? (
                previewDoc.chunks.map((chunk, idx) => (
                  <div key={idx} className="rounded-xl border border-border bg-card p-3.5">
                    <div className="text-xs font-bold text-primary mb-1">
                      {chunk.title || `Passage #${idx + 1}`}
                    </div>
                    <p className="text-xs leading-relaxed text-foreground/85 whitespace-pre-line">
                      {chunk.content}
                    </p>
                  </div>
                ))
              ) : (
                <p className="text-xs text-muted-foreground">No parsed chunks available.</p>
              )}
            </div>
          </DialogContent>
        </Dialog>
      )}
    </AppShell>
  );
}
