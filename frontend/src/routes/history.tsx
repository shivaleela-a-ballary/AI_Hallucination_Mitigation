import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import {
  AlertCircle,
  AlertTriangle,
  ArrowRight,
  CheckCircle2,
  Clock,
  ExternalLink,
  Filter,
  History as HistoryIcon,
  Loader2,
  Search,
  ShieldAlert,
  ShieldCheck,
  Trash2,
  XCircle,
} from "lucide-react";

import { AppShell } from "@/components/app/app-shell";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { api, type AnswerRecord } from "@/lib/api";
import { toast } from "sonner";

export const Route = createFileRoute("/history")({
  component: HistoryPage,
});

function HistoryPage() {
  const navigate = useNavigate();
  const [historyItems, setHistoryItems] = useState<AnswerRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [filterStatus, setFilterStatus] = useState<string>("All");
  const [searchQuery, setSearchQuery] = useState("");
  const [deletingId, setDeletingId] = useState<string | null>(null);

  const loadHistory = async () => {
    try {
      setLoading(true);
      const res = await api.history();
      setHistoryItems(res.history || []);
    } catch (err: unknown) {
      toast.error("Failed to load verification history.");
      setHistoryItems([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void loadHistory();
  }, []);

  const handleDelete = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      setDeletingId(id);
      await api.deleteHistoryItem(id);
      setHistoryItems((prev) => prev.filter((item) => item.id !== id));
      toast.success("Record deleted.");
    } catch {
      toast.error("Failed to delete record.");
    } finally {
      setDeletingId(null);
    }
  };

  const handleClearAll = async () => {
    if (!confirm("Are you sure you want to clear all verification history?")) return;
    try {
      await api.clearHistory();
      setHistoryItems([]);
      toast.success("All verification history cleared.");
    } catch {
      toast.error("Failed to clear history.");
    }
  };

  const filteredItems = historyItems.filter((item) => {
    const status = (item.verification_status || "").toUpperCase();
    if (filterStatus === "SUPPORTED" && status !== "SUPPORTED") return false;
    if (filterStatus === "REFUTED" && status !== "REFUTED") return false;
    if (filterStatus === "UNCERTAIN" && !status.includes("UNCERTAIN") && status !== "PARTIALLY_VERIFIED") return false;

    const queryText = item.query || (item as unknown as { user_query?: string }).user_query || "";
    if (searchQuery && !queryText.toLowerCase().includes(searchQuery.toLowerCase())) {
      return false;
    }
    return true;
  });

  return (
    <AppShell>
      <div className="space-y-7 max-w-6xl mx-auto">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-[#162340] pb-5">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <div className="size-8 rounded-lg bg-indigo-500/10 border border-indigo-500/30 flex items-center justify-center text-indigo-400">
                <HistoryIcon className="size-4.5" />
              </div>
              <h1 className="text-2xl font-extrabold text-white tracking-tight">
                Verification History
              </h1>
            </div>
            <p className="text-xs sm:text-sm text-slate-400">
              Audit trail of previous factual inquiries, claim deconstructions, and scientific verifications.
            </p>
          </div>

          <div className="flex items-center gap-2">
            {historyItems.length > 0 && (
              <Button
                variant="outline"
                size="sm"
                onClick={handleClearAll}
                className="rounded-xl border-rose-500/30 text-rose-400 hover:bg-rose-500/10 text-xs"
              >
                <Trash2 className="size-3.5 mr-1.5" /> Clear All History
              </Button>
            )}
          </div>
        </div>

        {/* Search & Filter Bar */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-[#091124] border border-[#172545] p-4 rounded-2xl">
          <div className="flex items-center gap-1.5 flex-wrap">
            <span className="text-xs font-semibold text-slate-400 mr-1 flex items-center gap-1">
              <Filter className="size-3.5" /> Filter:
            </span>
            {["All", "SUPPORTED", "REFUTED", "UNCERTAIN"].map((s) => (
              <button
                key={s}
                type="button"
                onClick={() => setFilterStatus(s)}
                className={`text-xs px-3 py-1.5 rounded-xl font-semibold transition-colors ${
                  filterStatus === s
                    ? "bg-indigo-600 text-white shadow"
                    : "text-slate-400 hover:text-slate-200 bg-[#0c1630]"
                }`}
              >
                {s === "All" ? "All Records" : s}
              </button>
            ))}
          </div>

          <div className="w-full sm:w-72">
            <Input
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search past queries..."
              className="h-9 rounded-xl bg-[#060c1d] border-[#1c2c54] text-xs text-slate-200 placeholder:text-slate-500"
            />
          </div>
        </div>

        {/* History List */}
        {loading ? (
          <div className="py-16 text-center text-slate-400 text-xs flex flex-col items-center justify-center gap-2">
            <Loader2 className="size-6 animate-spin text-indigo-400" />
            <span>Loading verification records...</span>
          </div>
        ) : filteredItems.length === 0 ? (
          <div className="py-16 text-center rounded-2xl border border-dashed border-[#172545] bg-[#091124] text-slate-400 space-y-2">
            <Clock className="size-8 text-slate-500 mx-auto mb-1" />
            <p className="text-sm font-semibold text-slate-300">No verification records found.</p>
            <p className="text-xs text-slate-500">
              Start by checking an AI answer or asking a question from the dashboard.
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            {filteredItems.map((item) => {
              const status = (item.verification_status || "").toUpperCase();
              const isSupported = status === "SUPPORTED";
              const isRefuted = status === "REFUTED";
              const dateStr = item.created_at ? new Date(item.created_at).toLocaleString() : "Recent";
              const queryText = item.query || (item as unknown as { user_query?: string }).user_query || "Verification Query";
              const answerText = item.answer || (item as unknown as { response?: string }).response || "";
              const sourcesCount = (item.sources || item.evidence || []).length;
              const conf = Math.round((item.confidence_score ?? (item as unknown as { confidence?: number }).confidence ?? 0) * 100);

              return (
                <div
                  key={item.id}
                  className="rounded-2xl border border-[#172545] bg-[#091124] p-5 space-y-3 hover:border-indigo-500/40 transition-colors"
                >
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                    <div className="flex items-center gap-2 flex-wrap">
                      <Badge
                        className={
                          isSupported
                            ? "bg-emerald-500/20 text-emerald-400 border-emerald-500/40 text-xs font-bold"
                            : isRefuted
                            ? "bg-rose-500/20 text-rose-400 border-rose-500/40 text-xs font-bold"
                            : "bg-amber-500/20 text-amber-400 border-amber-500/40 text-xs font-bold"
                        }
                      >
                        {status || "VERIFIED"}
                      </Badge>
                      <span className="text-xs text-slate-500 flex items-center gap-1">
                        <Clock className="size-3" /> {dateStr}
                      </span>
                    </div>

                    <div className="flex items-center gap-3 text-xs text-slate-400">
                      {conf > 0 && (
                        <span>Confidence: <strong className="text-slate-200">{conf}%</strong></span>
                      )}
                      <span>Evidence: <strong className="text-slate-200">{sourcesCount} sources</strong></span>
                      <button
                        type="button"
                        onClick={(e) => handleDelete(item.id, e)}
                        disabled={deletingId === item.id}
                        className="text-slate-500 hover:text-rose-400 p-1 transition-colors"
                        title="Delete record"
                      >
                        <Trash2 className="size-3.5" />
                      </button>
                    </div>
                  </div>

                  <div>
                    <h3 className="text-sm font-bold text-slate-100 leading-snug">
                      "{queryText}"
                    </h3>
                    {answerText && (
                      <p className="mt-1.5 text-xs text-slate-400 line-clamp-2 leading-relaxed">
                        {answerText}
                      </p>
                    )}
                  </div>

                  <div className="pt-2 flex items-center justify-between border-t border-[#121c33] text-xs">
                    <span className="text-slate-500 text-[11px]">
                      {(item.claims || []).length > 0 ? `${item.claims.length} claim(s) extracted` : "Direct inquiry"}
                    </span>

                    <div className="flex items-center gap-2">
                      <Button
                        onClick={() => navigate({ to: "/before-after" })}
                        variant="ghost"
                        size="sm"
                        className="text-xs text-indigo-400 hover:text-indigo-300"
                      >
                        Inspect Before/After <ExternalLink className="size-3 ml-1" />
                      </Button>
                      <Link
                        to="/answer/$id"
                        params={{ id: item.id }}
                        className="text-xs font-semibold text-slate-200 hover:text-white bg-[#0f1b38] hover:bg-indigo-600 px-3 py-1 rounded-lg border border-[#1b2f61] transition-colors"
                      >
                        View Full Details
                      </Link>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </AppShell>
  );
}
