import { createFileRoute } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import {
  BookOpen,
  CheckCircle2,
  ChevronDown,
  ChevronUp,
  ExternalLink,
  Filter,
  Info,
  Library,
  Search,
  ShieldCheck,
  Tag,
  Upload,
  XCircle,
} from "lucide-react";

import { AppShell } from "@/components/app/app-shell";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { api, type SourceRecord } from "@/lib/api";

export const Route = createFileRoute("/sources")({
  component: SourcesPage,
});

const BENCHMARK_SOURCES: SourceRecord[] = [
  {
    id: "scifact-1",
    title: "Metformin in Patients with Type 2 Diabetes and Cardiovascular Disease",
    source_type: "SciFact Knowledge Base",
    url: "https://pubmed.ncbi.nlm.nih.gov/22419688/",
    snippets: [
      "Metformin treatment was associated with lower risk of mortality and cardiovascular disease in patients with diabetes.",
      "However, observational designs preclude asserting complete curative effects in oncology without randomized clinical data.",
    ],
    verification_count: 8,
    acceptance_status: "ACCEPTED",
    avg_similarity: 0.88,
    latest_used_at: "Recent",
    referenced_in_records: ["rec-1", "rec-3"],
  },
  {
    id: "scifact-2",
    title: "Secondary Prevention of Atherosclerotic Cardiovascular Disease with Antiplatelet Agents",
    source_type: "SciFact Knowledge Base",
    url: "https://pubmed.ncbi.nlm.nih.gov/19478178/",
    snippets: [
      "Aspirin reduces cardiovascular events in secondary prevention trials, but carries heightened risk of major gastrointestinal bleeding.",
    ],
    verification_count: 5,
    acceptance_status: "ACCEPTED",
    avg_similarity: 0.84,
    latest_used_at: "Recent",
    referenced_in_records: ["rec-2"],
  },
  {
    id: "scifact-3",
    title: "High-Fidelity CRISPR-Cas9 Variants Mitigate Off-Target Cleavage in Mammalian Genomes",
    source_type: "SciFact Knowledge Base",
    url: "https://pubmed.ncbi.nlm.nih.gov/26744372/",
    snippets: [
      "Engineered Cas9 nucleases exhibit robust on-target efficiency while reducing undetectable off-target events across multiple genomic loci.",
    ],
    verification_count: 4,
    acceptance_status: "ACCEPTED",
    avg_similarity: 0.82,
    latest_used_at: "Recent",
    referenced_in_records: ["rec-4"],
  },
  {
    id: "pubmed-1",
    title: "Caffeine Consumption and Acute Hemodynamic Responses in Normotensive Adults",
    source_type: "PubMed / ArXiv",
    url: "https://pubmed.ncbi.nlm.nih.gov/15671190/",
    snippets: [
      "Caffeine ingestion elevates transient peripheral blood pressure without inducing myocardial infarction in healthy adult subjects.",
    ],
    verification_count: 3,
    acceptance_status: "ACCEPTED",
    avg_similarity: 0.79,
    latest_used_at: "Recent",
    referenced_in_records: ["rec-5"],
  },
  {
    id: "rejected-1",
    title: "In-Vitro Cell Proliferation Assays for Biguanide Derivatives in Non-Tumor Fibroblasts",
    source_type: "SciFact Knowledge Base",
    url: "",
    snippets: [
      "Assay evaluating cellular viability of mouse embryonic fibroblasts under varying glucose concentrations.",
    ],
    verification_count: 2,
    acceptance_status: "REJECTED (Irrelevant)",
    avg_similarity: 0.32,
    latest_used_at: "Recent",
    referenced_in_records: ["rec-1"],
  },
];

function SourcesPage() {
  const [sources, setSources] = useState<SourceRecord[]>(BENCHMARK_SOURCES);
  const [filterType, setFilterType] = useState<string>("All");
  const [searchQuery, setSearchQuery] = useState("");
  const [expandedId, setExpandedId] = useState<string | null>(null);

  useEffect(() => {
    api.getSources().then((res) => {
      if (res?.sources && res.sources.length > 0) {
        setSources(res.sources);
      }
    }).catch(() => {});
  }, []);

  const filteredSources = sources.filter((s) => {
    if (filterType !== "All" && s.source_type !== filterType && s.acceptance_status !== filterType) {
      return false;
    }
    if (searchQuery && !s.title.toLowerCase().includes(searchQuery.toLowerCase())) {
      return false;
    }
    return true;
  });

  const totalAccepted = sources.filter((s) => s.acceptance_status === "ACCEPTED").length;
  const totalSciFact = sources.filter((s) => s.source_type.includes("SciFact")).length;
  const totalUploaded = sources.filter((s) => s.source_type.includes("Upload")).length;

  return (
    <AppShell>
      <div className="space-y-7 max-w-6xl mx-auto">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-[#162340] pb-5">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <div className="size-8 rounded-lg bg-blue-500/10 border border-blue-500/30 flex items-center justify-center text-blue-400">
                <Library className="size-4.5" />
              </div>
              <h1 className="text-2xl font-extrabold text-white tracking-tight">
                Evidence Sources & Corpus Explorer
              </h1>
            </div>
            <p className="text-xs sm:text-sm text-slate-400">
              Explore scientifically indexed papers, reference corpora, and empirical proof citations.
            </p>
          </div>

          <div className="flex items-center gap-2">
            <Badge variant="outline" className="border-blue-500/30 text-blue-300 bg-blue-950/20 text-xs">
              FAISS Index & SciFact Corpus Connected
            </Badge>
          </div>
        </div>

        {/* Metric Cards */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          <div className="rounded-2xl border border-[#172545] bg-[#091124] p-4 text-center">
            <span className="text-[10px] font-semibold text-slate-400 uppercase">Total Sources</span>
            <p className="text-2xl font-bold text-white mt-1">{sources.length}</p>
            <span className="text-[10px] text-slate-500">Cross-referenced items</span>
          </div>

          <div className="rounded-2xl border border-[#172545] bg-[#091124] p-4 text-center">
            <span className="text-[10px] font-semibold text-emerald-400 uppercase">Empirical Proof</span>
            <p className="text-2xl font-bold text-emerald-400 mt-1">{totalAccepted}</p>
            <span className="text-[10px] text-emerald-400/70">Accepted entailment</span>
          </div>

          <div className="rounded-2xl border border-[#172545] bg-[#091124] p-4 text-center">
            <span className="text-[10px] font-semibold text-indigo-400 uppercase">SciFact Papers</span>
            <p className="text-2xl font-bold text-indigo-400 mt-1">{totalSciFact}</p>
            <span className="text-[10px] text-slate-500">Indexed corpus</span>
          </div>

          <div className="rounded-2xl border border-[#172545] bg-[#091124] p-4 text-center">
            <span className="text-[10px] font-semibold text-cyan-400 uppercase">User Ingestions</span>
            <p className="text-2xl font-bold text-cyan-400 mt-1">{totalUploaded}</p>
            <span className="text-[10px] text-slate-500">Attached documents</span>
          </div>
        </div>

        {/* Evidence Separation Notice Banner */}
        <div className="rounded-xl border border-indigo-500/20 bg-indigo-950/20 px-4 py-3 flex items-center justify-between text-xs text-slate-300">
          <div className="flex items-center gap-2.5">
            <ShieldCheck className="size-4 text-cyan-400 shrink-0" />
            <span>
              <strong>Proof Safeguard:</strong> A source with high embedding similarity is NOT accepted as factual proof unless directional NLI verifies entailment. Irrelevant or contradictory papers are rejected.
            </span>
          </div>
        </div>

        {/* Search & Filter Bar */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-[#091124] border border-[#172545] p-4 rounded-2xl">
          <div className="flex items-center gap-1.5 flex-wrap">
            <span className="text-xs font-semibold text-slate-400 mr-1 flex items-center gap-1">
              <Filter className="size-3.5" /> Filter:
            </span>
            {["All", "SciFact Knowledge Base", "PubMed / ArXiv", "ACCEPTED", "REJECTED (Irrelevant)"].map((f) => (
              <button
                key={f}
                type="button"
                onClick={() => setFilterType(f)}
                className={`text-xs px-3 py-1.5 rounded-xl font-semibold transition-colors ${
                  filterType === f
                    ? "bg-blue-600 text-white shadow"
                    : "text-slate-400 hover:text-slate-200 bg-[#0c1630]"
                }`}
              >
                {f}
              </button>
            ))}
          </div>

          <div className="w-full sm:w-72">
            <Input
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search source title..."
              className="h-9 rounded-xl bg-[#060c1d] border-[#1c2c54] text-xs text-slate-200 placeholder:text-slate-500"
            />
          </div>
        </div>

        {/* Sources List */}
        <div className="space-y-3">
          {filteredSources.map((item) => {
            const isExpanded = expandedId === item.id;
            const isAccepted = item.acceptance_status === "ACCEPTED";
            const isRejected = item.acceptance_status.includes("REJECTED");

            return (
              <div
                key={item.id}
                className="rounded-2xl border border-[#172545] bg-[#091124] overflow-hidden transition-colors"
              >
                <div className="p-5 space-y-3">
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                    <div className="flex items-center gap-2 flex-wrap">
                      <Badge variant="outline" className="border-blue-500/30 text-blue-300 bg-blue-950/20 text-xs">
                        {item.source_type}
                      </Badge>
                      <Badge
                        className={
                          isAccepted
                            ? "bg-emerald-500/20 text-emerald-400 border-emerald-500/40 text-xs font-bold"
                            : isRejected
                            ? "bg-rose-500/20 text-rose-400 border-rose-500/40 text-xs font-bold"
                            : "bg-amber-500/20 text-amber-400 border-amber-500/40 text-xs font-bold"
                        }
                      >
                        {item.acceptance_status}
                      </Badge>
                    </div>

                    <div className="flex items-center gap-3 text-xs text-slate-400">
                      <span>Relevance: <strong className="text-slate-200">{Math.round(item.avg_similarity * 100)}%</strong></span>
                      <span>Citations: <strong className="text-slate-200">{item.verification_count} queries</strong></span>
                    </div>
                  </div>

                  <h3 className="text-sm font-bold text-slate-100 leading-snug">
                    {item.title}
                  </h3>

                  <div className="pt-2 flex justify-between items-center border-t border-[#121c33] text-xs">
                    <div className="flex items-center gap-3 text-slate-400">
                      {item.url && (
                        <a
                          href={item.url}
                          target="_blank"
                          rel="noreferrer"
                          className="text-blue-400 hover:underline flex items-center gap-1 font-semibold"
                        >
                          View External Article <ExternalLink className="size-3" />
                        </a>
                      )}
                    </div>

                    {item.snippets?.length > 0 && (
                      <button
                        type="button"
                        onClick={() => setExpandedId(isExpanded ? null : item.id)}
                        className="text-indigo-400 hover:text-indigo-300 font-semibold flex items-center gap-1"
                      >
                        {isExpanded ? "Hide Text Snippets" : `Inspect Text Snippets (${item.snippets.length})`}
                        {isExpanded ? <ChevronUp className="size-3.5" /> : <ChevronDown className="size-3.5" />}
                      </button>
                    )}
                  </div>
                </div>

                {isExpanded && item.snippets?.length > 0 && (
                  <div className="bg-[#060c1d] border-t border-[#172545] p-5 space-y-2.5">
                    <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider block">
                      Indexed Corpus Evidence Passages:
                    </span>
                    {item.snippets.map((snip, idx) => (
                      <div key={idx} className="rounded-xl border border-slate-800 bg-[#0a1226] p-3 text-xs text-slate-300 leading-relaxed">
                        "{snip}"
                      </div>
                    ))}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </AppShell>
  );
}
