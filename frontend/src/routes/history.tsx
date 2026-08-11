import { createFileRoute, Link } from "@tanstack/react-router";
import { useMemo, useState } from "react";
import { Eye, Filter, MessageCircleQuestion, Search, ShieldCheck } from "lucide-react";

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
import { verifications } from "@/data/mock";

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
  const [query, setQuery] = useState("");
  const [filter, setFilter] = useState("all");
  const [page, setPage] = useState(1);

  const filtered = useMemo(
    () =>
      verifications.filter(
        (v) =>
          v.text.toLowerCase().includes(query.toLowerCase()) &&
          (filter === "all" || v.result === filter),
      ),
    [query, filter],
  );

  const pages = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE));
  const current = Math.min(page, pages);
  const rows = filtered.slice((current - 1) * PAGE_SIZE, current * PAGE_SIZE);

  return (
    <AppShell>
      <PageHeader
        title="Verification History"
        description="Track and review all your verifications and questions."
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
          <Button variant="outline" size="icon" aria-label="More filters" className="size-11 rounded-xl">
            <Filter className="size-4" />
          </Button>
        </div>

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
                <th scope="col" className="pb-3">
                  Date
                </th>
                <th scope="col" className="pb-3 text-right">
                  Action
                </th>
              </tr>
            </thead>
            <tbody>
              {rows.map((v) => (
                <tr key={v.id} className="border-t border-border/70">
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
                  <td className="py-4 pr-4 tabular-nums">{v.confidence.toFixed(2)}</td>
                  <td className="py-4 pr-4 text-muted-foreground">
                    <span className="block whitespace-nowrap">{v.date}</span>
                    <span className="block text-xs">{v.time}</span>
                  </td>
                  <td className="py-4 text-right">
                    <Link
                      to="/answer/$id"
                      params={{ id: v.id }}
                      aria-label={`View details for ${v.text}`}
                      className="inline-grid size-9 place-items-center rounded-xl text-muted-foreground transition-colors hover:bg-muted hover:text-primary"
                    >
                      <Eye className="size-4" />
                    </Link>
                  </td>
                </tr>
              ))}
              {rows.length === 0 && (
                <tr>
                  <td colSpan={6} className="py-10 text-center text-muted-foreground">
                    No verifications match your filters.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

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
      </div>
    </AppShell>
  );
}
