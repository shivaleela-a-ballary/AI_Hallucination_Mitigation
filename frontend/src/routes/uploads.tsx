import { createFileRoute } from "@tanstack/react-router";
import { useRef, useState } from "react";
import { CloudUpload, Eye, FileText, Trash2 } from "lucide-react";
import { motion } from "motion/react";
import { toast } from "sonner";

import { AppShell } from "@/components/app/app-shell";
import { PageHeader } from "@/components/app/ui-kit";
import { Button } from "@/components/ui/button";
import { uploads as seedUploads, type UploadedFile } from "@/data/mock";
import { cn } from "@/lib/utils";

export const Route = createFileRoute("/uploads")({
  head: () => ({
    meta: [
      { title: "Uploads — AI Hallucination Mitigation System" },
      {
        name: "description",
        content: "Upload PDFs, reports and datasets so verifications can cite your own private evidence.",
      },
      { property: "og:title", content: "Uploads — AI Hallucination Mitigation System" },
      { property: "og:description", content: "Manage the documents indexed for your verifications." },
    ],
  }),
  component: UploadsPage,
});

const statusStyles: Record<UploadedFile["status"], string> = {
  indexed: "bg-success-soft text-success",
  processing: "bg-warning-soft text-warning",
  failed: "bg-danger-soft text-destructive",
};

function UploadsPage() {
  const [files, setFiles] = useState<UploadedFile[]>(seedUploads);
  const [dragging, setDragging] = useState(false);
  const [progress, setProgress] = useState<number | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleFiles = (list: FileList | null) => {
    if (!list?.length) return;
    setProgress(8);
    const timer = setInterval(() => {
      setProgress((p) => {
        if (p === null) return null;
        if (p >= 100) {
          clearInterval(timer);
          return null;
        }
        return p + 12;
      });
    }, 140);

    setTimeout(() => {
      setFiles((prev) => [
        ...Array.from(list).map((f, i) => ({
          id: `new-${Date.now()}-${i}`,
          name: f.name,
          type: (f.name.split(".").pop() ?? "FILE").toUpperCase(),
          uploaded: new Date().toLocaleDateString("en-GB", {
            day: "2-digit",
            month: "short",
            year: "numeric",
          }),
          status: "indexed" as const,
          size: `${(f.size / 1024).toFixed(0)} KB`,
        })),
        ...prev,
      ]);
      toast.success("Upload complete");
    }, 1300);
  };

  return (
    <AppShell>
      <PageHeader
        title="Uploads"
        description="Manage the documents indexed as private evidence."
        action={
          <Button className="rounded-xl" onClick={() => inputRef.current?.click()}>
            <CloudUpload className="size-4" /> Upload
          </Button>
        }
      />

      <div
        onDragOver={(e) => {
          e.preventDefault();
          setDragging(true);
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={(e) => {
          e.preventDefault();
          setDragging(false);
          handleFiles(e.dataTransfer.files);
        }}
        className={cn(
          "flex flex-col items-center gap-3 rounded-2xl border-2 border-dashed p-10 text-center transition-colors",
          dragging ? "border-primary bg-accent" : "border-primary/30 bg-accent/40",
        )}
      >
        <CloudUpload className="size-8 text-primary" aria-hidden="true" />
        <p className="text-sm font-medium">Drag &amp; drop files here</p>
        <p className="text-xs text-muted-foreground">PDF, TXT, DOCX, CSV (Max 20MB)</p>
        <Button variant="secondary" className="rounded-lg" onClick={() => inputRef.current?.click()}>
          Browse Files
        </Button>
        <input
          ref={inputRef}
          type="file"
          multiple
          className="sr-only"
          aria-label="Upload documents"
          onChange={(e) => handleFiles(e.target.files)}
        />
        {progress !== null && (
          <div className="mt-2 h-2 w-full max-w-sm overflow-hidden rounded-full bg-muted">
            <motion.div
              animate={{ width: `${Math.min(progress, 100)}%` }}
              className="h-full rounded-full bg-primary"
            />
          </div>
        )}
      </div>

      <div className="card-soft mt-6 p-5">
        <div className="overflow-x-auto">
          <table className="w-full min-w-[720px] text-left text-sm">
            <thead>
              <tr className="text-xs font-semibold text-muted-foreground">
                <th scope="col" className="pb-3">
                  Filename
                </th>
                <th scope="col" className="pb-3">
                  Type
                </th>
                <th scope="col" className="pb-3">
                  Uploaded
                </th>
                <th scope="col" className="pb-3">
                  Status
                </th>
                <th scope="col" className="pb-3">
                  Size
                </th>
                <th scope="col" className="pb-3 text-right">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody>
              {files.map((f) => (
                <tr key={f.id} className="border-t border-border/70">
                  <td className="max-w-[260px] py-4 pr-4">
                    <span className="flex min-w-0 items-center gap-3">
                      <FileText className="size-4 shrink-0 text-muted-foreground" aria-hidden="true" />
                      <span className="truncate font-medium">{f.name}</span>
                    </span>
                  </td>
                  <td className="py-4 pr-4 text-muted-foreground">{f.type}</td>
                  <td className="py-4 pr-4 whitespace-nowrap text-muted-foreground">{f.uploaded}</td>
                  <td className="py-4 pr-4">
                    <span
                      className={cn(
                        "inline-flex rounded-md px-2 py-1 text-xs font-semibold capitalize",
                        statusStyles[f.status],
                      )}
                    >
                      {f.status}
                    </span>
                  </td>
                  <td className="py-4 pr-4 text-muted-foreground">{f.size}</td>
                  <td className="py-4 text-right">
                    <span className="inline-flex gap-1">
                      <button
                        type="button"
                        aria-label={`Preview ${f.name}`}
                        onClick={() => toast(`Preview: ${f.name}`)}
                        className="grid size-9 place-items-center rounded-xl text-muted-foreground transition-colors hover:bg-muted hover:text-primary"
                      >
                        <Eye className="size-4" />
                      </button>
                      <button
                        type="button"
                        aria-label={`Delete ${f.name}`}
                        onClick={() => {
                          setFiles((prev) => prev.filter((x) => x.id !== f.id));
                          toast.success("File removed");
                        }}
                        className="grid size-9 place-items-center rounded-xl text-muted-foreground transition-colors hover:bg-muted hover:text-destructive"
                      >
                        <Trash2 className="size-4" />
                      </button>
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </AppShell>
  );
}
