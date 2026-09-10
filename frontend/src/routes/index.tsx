import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import {
  Activity,
  AlertTriangle,
  ArrowRight,
  BrainCircuit,
  CheckCircle2,
  FileCheck,
  FileSearch,
  Library,
  Scale,
  ShieldAlert,
  ShieldCheck,
  Sparkles,
  TrendingUp,
  XCircle,
  HelpCircle,
  Clock,
  ExternalLink,
} from "lucide-react";
import { motion } from "motion/react";

import { AppShell } from "@/components/app/app-shell";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { api, type DashboardStats, type AnswerRecord } from "@/lib/api";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "Dashboard — AI Hallucination Mitigation Platform" },
      {
        name: "description",
        content: "Real-time AI hallucination detection, claim risk analysis, and factual verification workspace.",
      },
    ],
  }),
  component: DashboardPage,
});

function DashboardPage() {
  const navigate = useNavigate();
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [recentRecords, setRecentRecords] = useState<AnswerRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadData() {
      try {
        setLoading(true);
        const [statsRes, historyRes] = await Promise.all([
          api.getDashboardStats().catch(() => null),
          api.history().catch(() => ({ history: [] })),
        ]);
        if (statsRes) setStats(statsRes);
        if (historyRes?.history) setRecentRecords(historyRes.history.slice(0, 8));
      } catch (err: unknown) {
        setError("Failed to load dashboard metrics");
      } finally {
        setLoading(false);
      }
    }
    void loadData();
  }, []);
  const totalVerifications = stats?.total_verifications ?? recentRecords.length;
  const totalClaims = stats?.total_claims ?? 0;
  const hallucinationRate = stats?.hallucination_rate ?? 0;
  const avgConfidence = stats?.avg_confidence ?? 0;

  const quickActions = [
    {
      title: "Check AI Answer",
      description: "Decompose any AI response into claims, verify against scientific evidence, and produce grounded corrections.",
      to: "/check-answer",
      icon: FileCheck,
      color: "from-indigo-600/20 to-blue-600/20 text-indigo-400 border-indigo-500/30",
      buttonText: "Verify Answer",
    },
    {
      title: "Hallucination Forensics",
      description: "Perform deep linguistic & semantic forensic inspection to detect 12 distinct hallucination patterns.",
      to: "/forensics",
      icon: Activity,
      color: "from-purple-600/20 to-pink-600/20 text-purple-400 border-purple-500/30",
      buttonText: "Inspect Forensics",
    },
    {
      title: "Claim Risk Heatmap",
      description: "Visualize density, risk tiers (High/Moderate/Low), and NLI entailment distribution across claims.",
      to: "/risk-heatmap",
      icon: ShieldAlert,
      color: "from-amber-600/20 to-orange-600/20 text-amber-400 border-amber-500/30",
      buttonText: "View Heatmap",
    },
    {
      title: "Before / After Analysis",
      description: "Compare hallucinated AI text directly with verified, empirically grounded corrected text.",
      to: "/before-after",
      icon: Scale,
      color: "from-emerald-600/20 to-teal-600/20 text-emerald-400 border-emerald-500/30",
      buttonText: "Compare Outputs",
    },
    {
      title: "Research Paper Auditor",
      description: "Upload PDF research papers to audit claims across Abstract, Methods, and Results against citations.",
      to: "/research-paper-auditor",
      icon: FileSearch,
      color: "from-cyan-600/20 to-sky-600/20 text-cyan-400 border-cyan-500/30",
      buttonText: "Audit Paper",
    },
    {
      title: "Evidence Sources",
      description: "Explore verified SciFact corpus papers, uploaded documents, and real-time biomedical sources.",
      to: "/sources",
      icon: Library,
      color: "from-blue-600/20 to-indigo-600/20 text-blue-400 border-blue-500/30",
      buttonText: "Browse Sources",
    },
  ];

  return (
    <AppShell>
      <div className="space-y-7">
        {/* Executive Header Banner */}
        <div className="relative overflow-hidden rounded-2xl border border-[#1b2a4d] bg-gradient-to-br from-[#0c1633] via-[#091126] to-[#060c1d] p-6 sm:p-8 shadow-xl">
          <div className="relative z-10 flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
            <div className="space-y-2 max-w-2xl">
              <div className="inline-flex items-center gap-2 rounded-full border border-indigo-500/30 bg-indigo-500/10 px-3 py-1 text-xs font-semibold text-indigo-300">
                <Sparkles className="size-3.5 text-cyan-400" />
                Empirical Evidence Verification Engine
              </div>
              <h1 className="text-2xl sm:text-3xl lg:text-4xl font-extrabold tracking-tight text-white">
                AI Hallucination Mitigation Platform
              </h1>
              <p className="text-sm sm:text-base text-slate-300 leading-relaxed">
                Autonomous multi-source evidence retrieval, 12-pattern forensic diagnosis, claim risk quantification, and empirical fact-grounding.
              </p>
            </div>

            <div className="flex flex-wrap gap-3">
              <Button
                onClick={() => navigate({ to: "/check-answer" })}
                className="rounded-xl bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 text-white font-semibold shadow-lg shadow-indigo-500/25 px-5 py-2.5"
              >
                <FileCheck className="size-4 mr-2" /> Check AI Answer
              </Button>
              <Button
                onClick={() => navigate({ to: "/ask" })}
                variant="outline"
                className="rounded-xl border-[#233561] bg-[#0c152d]/80 hover:bg-[#132044] text-slate-200"
              >
                Ask Question
              </Button>
            </div>
          </div>
          {/* Subtle glow background */}
          <div className="pointer-events-none absolute -right-20 -top-20 size-80 rounded-full bg-indigo-500/10 blur-3xl" />
        </div>

        {/* Real-time Metric Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="rounded-2xl border border-[#172545] bg-[#091124] p-5 relative overflow-hidden">
            <div className="flex items-center justify-between text-slate-400 text-xs font-semibold uppercase tracking-wider">
              <span>Total Verifications</span>
              <Activity className="size-4 text-indigo-400" />
            </div>
            <div className="mt-3 flex items-baseline gap-2">
              <span className="text-3xl font-bold text-white tracking-tight">
                {loading ? "..." : totalVerifications}
              </span>
              <span className="text-xs text-slate-400">sessions</span>
            </div>
            <p className="mt-1 text-xs text-slate-400">Analyzed across all queries</p>
          </div>

          <div className="rounded-2xl border border-[#172545] bg-[#091124] p-5 relative overflow-hidden">
            <div className="flex items-center justify-between text-slate-400 text-xs font-semibold uppercase tracking-wider">
              <span>Hallucination Rate</span>
              <AlertTriangle className="size-4 text-rose-400" />
            </div>
            <div className="mt-3 flex items-baseline gap-2">
              <span className="text-3xl font-bold text-rose-400 tracking-tight">
                {loading ? "..." : `${hallucinationRate}%`}
              </span>
              <span className="text-xs text-rose-400/80">detected</span>
            </div>
            <p className="mt-1 text-xs text-slate-400">Claims contradicting evidence</p>
          </div>

          <div className="rounded-2xl border border-[#172545] bg-[#091124] p-5 relative overflow-hidden">
            <div className="flex items-center justify-between text-slate-400 text-xs font-semibold uppercase tracking-wider">
              <span>Avg Confidence</span>
              <ShieldCheck className="size-4 text-emerald-400" />
            </div>
            <div className="mt-3 flex items-baseline gap-2">
              <span className="text-3xl font-bold text-emerald-400 tracking-tight">
                {loading ? "..." : `${Math.round(avgConfidence * 100)}%`}
              </span>
              <span className="text-xs text-emerald-400/80">NLI score</span>
            </div>
            <p className="mt-1 text-xs text-slate-400">Mean entailment probability</p>
          </div>

          <div className="rounded-2xl border border-[#172545] bg-[#091124] p-5 relative overflow-hidden">
            <div className="flex items-center justify-between text-slate-400 text-xs font-semibold uppercase tracking-wider">
              <span>Claims Audited</span>
              <CheckCircle2 className="size-4 text-cyan-400" />
            </div>
            <div className="mt-3 flex items-baseline gap-2">
              <span className="text-3xl font-bold text-cyan-400 tracking-tight">
                {loading ? "..." : totalClaims}
              </span>
              <span className="text-xs text-slate-400">atomic claims</span>
            </div>
            <p className="mt-1 text-xs text-slate-400">
              {stats ? `${stats.supported_claims} supported · ${stats.refuted_claims} refuted` : "Atomic factual claims"}
            </p>
          </div>
        </div>

        {/* Claim Risk Breakdown & Forensics Pattern Distribution */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Claim Risk Level Distribution */}
          <div className="rounded-2xl border border-[#172545] bg-[#091124] p-6 space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-base font-bold text-white">Claim Risk Distribution</h3>
                <p className="text-xs text-slate-400">Risk stratification of verified claims</p>
              </div>
              <Link to="/risk-heatmap" className="text-xs text-indigo-400 hover:text-indigo-300 font-semibold flex items-center gap-1">
                Full Heatmap <ArrowRight className="size-3" />
              </Link>
            </div>

            <div className="space-y-3 pt-2">
              {/* Low Risk */}
              <div className="space-y-1.5">
                <div className="flex justify-between text-xs">
                  <span className="font-semibold text-emerald-400 flex items-center gap-1.5">
                    <span className="size-2 rounded-full bg-emerald-400" /> Low Risk (Empirically Supported)
                  </span>
                  <span className="text-slate-300 font-medium">{stats?.risk_distribution.low ?? 0} claims</span>
                </div>
                <div className="h-2 rounded-full bg-slate-800 overflow-hidden">
                  <div
                    className="h-full bg-emerald-500 rounded-full transition-all duration-500"
                    style={{
                      width: `${totalClaims > 0 ? ((stats?.risk_distribution.low ?? 0) / totalClaims) * 100 : 0}%`,
                    }}
                  />
                </div>
              </div>

              {/* Moderate Risk */}
              <div className="space-y-1.5">
                <div className="flex justify-between text-xs">
                  <span className="font-semibold text-amber-400 flex items-center gap-1.5">
                    <span className="size-2 rounded-full bg-amber-400" /> Moderate Risk (Uncertain / Insufficient)
                  </span>
                  <span className="text-slate-300 font-medium">{stats?.risk_distribution.moderate ?? 0} claims</span>
                </div>
                <div className="h-2 rounded-full bg-slate-800 overflow-hidden">
                  <div
                    className="h-full bg-amber-500 rounded-full transition-all duration-500"
                    style={{
                      width: `${totalClaims > 0 ? ((stats?.risk_distribution.moderate ?? 0) / totalClaims) * 100 : 0}%`,
                    }}
                  />
                </div>
              </div>

              {/* High Risk */}
              <div className="space-y-1.5">
                <div className="flex justify-between text-xs">
                  <span className="font-semibold text-rose-400 flex items-center gap-1.5">
                    <span className="size-2 rounded-full bg-rose-400" /> High Risk (Contradicted / Hallucinated)
                  </span>
                  <span className="text-slate-300 font-medium">{stats?.risk_distribution.high ?? 0} claims</span>
                </div>
                <div className="h-2 rounded-full bg-slate-800 overflow-hidden">
                  <div
                    className="h-full bg-rose-500 rounded-full transition-all duration-500"
                    style={{
                      width: `${totalClaims > 0 ? ((stats?.risk_distribution.high ?? 0) / totalClaims) * 100 : 0}%`,
                    }}
                  />
                </div>
              </div>
            </div>
          </div>

          {/* Top Detected Hallucination Patterns */}
          <div className="rounded-2xl border border-[#172545] bg-[#091124] p-6 space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-base font-bold text-white">Top Forensics Patterns</h3>
                <p className="text-xs text-slate-400">Most frequent linguistic & factual distortions</p>
              </div>
              <Link to="/forensics" className="text-xs text-indigo-400 hover:text-indigo-300 font-semibold flex items-center gap-1">
                Pattern Catalog <ArrowRight className="size-3" />
              </Link>
            </div>

            <div className="space-y-2.5 pt-1">
              {stats?.top_patterns && stats.top_patterns.length > 0 ? (
                stats.top_patterns.map((item, idx) => (
                  <div
                    key={item.pattern}
                    className="flex items-center justify-between rounded-xl bg-[#0c1630] border border-[#1b2b52] px-3.5 py-2.5 text-xs"
                  >
                    <div className="flex items-center gap-2.5 min-w-0">
                      <span className="size-5 rounded-md bg-rose-500/10 text-rose-400 flex items-center justify-center font-bold text-[11px]">
                        {idx + 1}
                      </span>
                      <span className="font-semibold text-slate-200 truncate">{item.pattern}</span>
                    </div>
                    <Badge variant="outline" className="border-rose-500/30 text-rose-400 font-mono text-[11px]">
                      {item.count} occurrences
                    </Badge>
                  </div>
                ))
              ) : (
                <div className="space-y-2 text-xs text-slate-400">
                  <div className="p-3 rounded-xl bg-[#0c1630] border border-[#1b2b52] flex items-center justify-between">
                    <span>Overgeneralization</span>
                    <span className="text-slate-500">Monitored</span>
                  </div>
                  <div className="p-3 rounded-xl bg-[#0c1630] border border-[#1b2b52] flex items-center justify-between">
                    <span>Causal Overclaim</span>
                    <span className="text-slate-500">Monitored</span>
                  </div>
                  <div className="p-3 rounded-xl bg-[#0c1630] border border-[#1b2b52] flex items-center justify-between">
                    <span>Unsupported Numerical Claim</span>
                    <span className="text-slate-500">Monitored</span>
                  </div>
                  <div className="p-3 rounded-xl bg-[#0c1630] border border-[#1b2b52] flex items-center justify-between">
                    <span>Absolute Language</span>
                    <span className="text-slate-500">Monitored</span>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Feature Workspace Launchers */}
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-bold text-white tracking-tight">Modular Analysis Workspaces</h2>
            <span className="text-xs text-slate-400 font-medium">Select a specialized module</span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            {quickActions.map((action) => {
              const IconComp = action.icon;
              return (
                <div
                  key={action.title}
                  className="group rounded-2xl border border-[#182647] bg-[#091124] p-5 flex flex-col justify-between hover:border-indigo-500/50 hover:bg-[#0c1633] transition-all duration-200 shadow-md"
                >
                  <div className="space-y-3">
                    <div className={`size-11 rounded-xl border flex items-center justify-center bg-gradient-to-br ${action.color}`}>
                      <IconComp className="size-5.5" />
                    </div>
                    <div>
                      <h3 className="text-base font-bold text-white group-hover:text-indigo-300 transition-colors">
                        {action.title}
                      </h3>
                      <p className="mt-1.5 text-xs text-slate-400 leading-relaxed">
                        {action.description}
                      </p>
                    </div>
                  </div>
                  <div className="pt-5 mt-4 border-t border-[#14203d]">
                    <Button
                      onClick={() => navigate({ to: action.to })}
                      className="w-full justify-between rounded-xl bg-[#101b38] hover:bg-indigo-600 text-slate-200 hover:text-white border border-[#1e3059] text-xs font-semibold transition-colors"
                    >
                      {action.buttonText}
                      <ArrowRight className="size-3.5" />
                    </Button>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Recent Verifications Activity */}
        <div className="rounded-2xl border border-[#172545] bg-[#091124] p-6 space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-base font-bold text-white">Recent Verification Activity</h3>
              <p className="text-xs text-slate-400">Live feed of processed claims and answers</p>
            </div>
            <Link to="/history" className="text-xs text-indigo-400 hover:text-indigo-300 font-semibold flex items-center gap-1">
              View All History <ArrowRight className="size-3" />
            </Link>
          </div>

          {recentRecords.length === 0 ? (
            <div className="text-center py-10 rounded-xl bg-[#0b1328] border border-dashed border-[#1a294d] text-slate-400 text-xs">
              <Clock className="size-7 text-slate-500 mx-auto mb-2" />
              No verifications recorded yet. Start by checking an AI answer or asking a question.
            </div>
          ) : (
            <div className="divide-y divide-[#152240] overflow-hidden rounded-xl border border-[#152240]">
              {recentRecords.map((item) => {
                const status = (item.verification_status || "").toUpperCase();
                const isSupported = status === "SUPPORTED";
                const isRefuted = status === "REFUTED";
                const dateStr = item.created_at ? new Date(item.created_at).toLocaleDateString() : "Recent";
                const queryText = item.query || (item as unknown as { user_query?: string }).user_query || "Answer Check";

                return (
                  <div
                    key={item.id}
                    className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 p-4 bg-[#091124] hover:bg-[#0d1730] transition-colors"
                  >
                    <div className="min-w-0 space-y-1">
                      <div className="flex items-center gap-2">
                        <Badge
                          className={
                            isSupported
                              ? "bg-emerald-500/15 text-emerald-400 border-emerald-500/30 text-[10px]"
                              : isRefuted
                              ? "bg-rose-500/15 text-rose-400 border-rose-500/30 text-[10px]"
                              : "bg-amber-500/15 text-amber-400 border-amber-500/30 text-[10px]"
                          }
                        >
                          {status || "VERIFIED"}
                        </Badge>
                        <span className="text-[11px] text-slate-500">{dateStr}</span>
                        {item.confidence_score ? (
                          <span className="text-[11px] font-mono text-slate-400">
                            {Math.round(item.confidence_score * 100)}% conf
                          </span>
                        ) : null}
                      </div>
                      <p className="text-xs font-semibold text-slate-200 truncate max-w-xl">
                        {queryText}
                      </p>
                    </div>

                    <div className="flex items-center gap-2 shrink-0">
                      <Button
                        onClick={() => navigate({ to: "/before-after" })}
                        variant="ghost"
                        size="sm"
                        className="text-xs text-indigo-400 hover:text-indigo-300 hover:bg-indigo-500/10"
                      >
                        Compare <ExternalLink className="size-3 ml-1" />
                      </Button>
                      <Button
                        onClick={() => navigate({ to: "/history" })}
                        variant="ghost"
                        size="sm"
                        className="text-xs text-slate-400 hover:text-slate-200"
                      >
                        Details
                      </Button>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>
    </AppShell>
  );
}
