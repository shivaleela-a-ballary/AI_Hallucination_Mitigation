import { createFileRoute, Link } from "@tanstack/react-router";
import { useEffect, useMemo, useState } from "react";
import {
  Eye,
  Filter,
  MessageCircleQuestion,
  Search,
  ShieldCheck,
  Trash2,
  RefreshCw,
  Database,
} from "lucide-react";

import { AppShell } from "@/components/app/app-shell";
import { PageHeader, ResultBadge } from "@/components/app/ui-kit";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Button } from "@/components/ui/button";
import { api, type Verification } from "@/lib/api";
import { mapHistoryRecord } from "@/lib/presentation";
import { useAuth } from "@/lib/auth-context";
import { toast } from "sonner";

export const Route = createFileRoute("/history")({
  head: () => ({
    meta: [
      { title: "Verification History — AI Hallucination Mitigation System" },
      {
        name: "description",
        content: "Track and review all your past claim verifications and questions with confidence scores.",
      },
      { property: "og:title", content: "Verification History — AI Hallucination Mitigation System" },
      { property: "og:description", content: "Review past verifications and confidence scores." },
    ],
  }),
  component: HistoryPage,
});

const PAGE_SIZE = 6;

function HistoryPage() {
  const { isAuthenticated } = useAuth();
  const [query, setQuery] = useState("");
  const [filter, setFilter] = useState("all");
  const [page, setPage] = useState(1);
  const [verifications, setVerifications] = useState<Verification[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [deletingId, setDeletingId] = useState<string | null>(null);

  const loadHistory = async () => {
    try {
      setError("");
      setLoading(true);
      const { history } = await api.history();
      setVerifications(history.map(mapHistoryRecord));
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Unable to load history.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void loadHistory();
  }, []);

  const handleDeleteItem = async (id: string, text: string) => {
    if (!confirm(`Delete verification record for "${text.slice(0, 40)}..."?`)) return;
    setDeletingId(id);
    try {
      if (isAuthenticated) {
        await api.user.deleteHistoryItem(id);
      }
      setVerifications((prev) => prev.filter((item) => item.id !== id));
      toast.success("Record deleted successfully.");
    } catch (cause) {
      toast.error(cause instanceof Error ? cause.message : "Failed to delete record.");
    } finally {
      setDeletingId(null);
    }
  };

  const handleClearAll = async () => {
    if (!confirm("Are you sure you want to clear your verification history? This cannot be undone.")) return;
    try {
      if (isAuthenticated) {
        await api.user.clearHistory();
      }
      setVerifications([]);
      toast.success("Verification history cleared.");
    } catch (cause) {
      toast.error(cause instanceof Error ? cause.message : "Failed to clear history.");
    }
  };

  const filtered = useMemo(
    () =>
      verifications.filter(
        (v) =>
          v.text.toLowerCase().includes(query.toLowerCase()) &&
          (filter === "all" || v.result === filter),
      ),
    [verifications, query, filter],
  );

  const pages = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE));
  const current = Math.min(page, pages);
  const rows = filtered.slice((current - 1) * PAGE_SIZE, current * PAGE_SIZE);

  return (
    <AppShell>
      <PageHeader
        title="Verification History"
        description="Review all past claim verifications, evidence citations, and confidence scores synced to MongoDB."
        action={
          verifications.length > 0 ? (
            <Button
              variant="outline"
              size="sm"
              onClick={() => void handleClearAll()}
              className="rounded-xl text-destructive hover:bg-destructive/10 hover:text-destructive"
            >
              <Trash2 className="size-4 mr-1.5" /> Clear All History
            </Button>
          ) : undefined
        }
      />

      <div className="card-soft p-5">
        <div className="grid gap-3 sm:grid-cols-[minmax(0,1fr)_auto_auto]">
          <div className="relative min-w-0">
            <Search
              className="absolute top-1/2 left-3 size-4 -translate-y-1/2 text-muted-foreground"
              aria-hidden="true"
            />
            <Input
              value={query}
              onChange={(e) => {
                setQuery(e.target.value);
                setPage(1);
              }}
              placeholder="Search history..."
              aria-label="Search history"
              className="h-11 rounded-xl pl-9"
            />
          </div>
          <Select
            value={filter}
            onValueChange={(v) => {
              setFilter(v);
              setPage(1);
            }}
          >
            <SelectTrigger className="h-11 w-full rounded-xl sm:w-44">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Results</SelectItem>
              <SelectItem value="supported">Supported</SelectItem>
              <SelectItem value="refuted">Refuted</SelectItem>
              <SelectItem value="not-enough-info">Not Enough Info</SelectItem>
            </SelectContent>
          </Select>
          <Button
            variant="outline"
            size="icon"
            aria-label="Refresh history"
            className="size-11 rounded-xl"
            onClick={() => void loadHistory()}
          >
            <RefreshCw className={`size-4 ${loading ? "animate-spin" : ""}`} />
          </Button>
        </div>

        {loading && <p className="mt-3 text-sm text-muted-foreground">Loading history from MongoDB...</p>}
        {error && <p role="alert" className="mt-3 text-sm text-destructive">{error}</p>}

        <div className="mt-5 overflow-x-auto">
          <table className="w-full min-w-[720px] text-left text-sm">
            <thead>
              <tr className="text-xs font-semibold text-muted-foreground">
                <th scope="col" className="pb-3">
                  Type
                </th>
                <th scope="col" className="pb-3">
                  Claim / Question
                </th>
                <th scope="col" className="pb-3">
                  Result
                </th>
                <th scope="col" className="pb-3">
                  Confidence
                </th>
                <th scope="col" className="pb-3">Sources</th>
                <th scope="col" className="pb-3">
                  Date
                </th>
                <th scope="col" className="pb-3 text-right">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody>
              {rows.map((v) => (
                <tr key={v.id} className="border-t border-border/70 group">
                  <td className="py-4 pr-4">
                    <span className="grid size-9 place-items-center rounded-xl bg-accent text-primary">
                      {v.type === "claim" ? (
                        <ShieldCheck className="size-4" aria-hidden="true" />
                      ) : (
                        <MessageCircleQuestion className="size-4" aria-hidden="true" />
                      )}
                      <span className="sr-only">{v.type}</span>
                    </span>
                  </td>
                  <td className="max-w-[260px] py-4 pr-4 font-medium">
                    <span className="line-clamp-2">{v.text}</span>
                  </td>
                  <td className="py-4 pr-4">
                    <ResultBadge result={v.result} />
                  </td>
                  <td className="py-4 pr-4 tabular-nums">
                    {v.confidenceAvailable ? `${(v.confidence * 100).toFixed(1)}%` : "Not available"}
                  </td>
                  <td className="py-4 pr-4 text-muted-foreground">{v.sourceCount}</td>
                  <td className="py-4 pr-4 text-muted-foreground">
                    <span className="block whitespace-nowrap">{v.date}</span>
                    <span className="block text-xs">{v.time}</span>
                  </td>
                  <td className="py-4 text-right">
                    <div className="flex items-center justify-end gap-1">
                      <Link
                        to="/answer/$id"
                        params={{ id: v.id }}
                        aria-label={`View details for ${v.text}`}
                        className="inline-grid size-8 place-items-center rounded-lg text-muted-foreground transition-colors hover:bg-muted hover:text-primary"
                      >
                        <Eye className="size-4" />
                      </Link>
                      <button
                        type="button"
                        onClick={() => void handleDeleteItem(v.id, v.text)}
                        disabled={deletingId === v.id}
                        aria-label="Delete item"
                        className="inline-grid size-8 place-items-center rounded-lg text-muted-foreground transition-colors hover:bg-destructive/10 hover:text-destructive"
                      >
                        <Trash2 className="size-4" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
              {rows.length === 0 && !loading && (
                <tr>
                  <td colSpan={7} className="py-12 text-center text-muted-foreground">
                    <div className="flex flex-col items-center justify-center space-y-2">
                      <Database className="size-8 text-muted-foreground/50" />
                      <p className="font-medium">No verification records found</p>
                      <p className="text-xs">Run a claim check in New Verification or ask a question in Chat.</p>
                    </div>
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        {pages > 1 && (
          <nav aria-label="Pagination" className="mt-6 flex items-center justify-center gap-2">
            <Button
              variant="outline"
              size="icon"
              className="size-9 rounded-lg"
              aria-label="Previous page"
              disabled={current === 1}
              onClick={() => setPage(current - 1)}
            >
              ‹
            </Button>
            {Array.from({ length: pages }).map((_, i) => (
              <Button
                key={i}
                variant={current === i + 1 ? "default" : "outline"}
                size="icon"
                className="size-9 rounded-lg"
                aria-current={current === i + 1 ? "page" : undefined}
                onClick={() => setPage(i + 1)}
              >
                {i + 1}
              </Button>
            ))}
            <Button
              variant="outline"
              size="icon"
              className="size-9 rounded-lg"
              aria-label="Next page"
              disabled={current === pages}
              onClick={() => setPage(current + 1)}
            >
              ›
            </Button>
          </nav>
        )}
      </div>
    </AppShell>
  );
}
