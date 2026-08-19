import { createFileRoute, Link } from "@tanstack/react-router";
import { motion } from "motion/react";
import {
  ArrowRight,
  BadgeAlert,
  CheckCircle2,
  FileSearch,
  MessagesSquare,
  ShieldCheck,
  ShieldQuestion,
  Share2,
  Sparkles,
  Upload,
} from "lucide-react";
import { useEffect, useState } from "react";

import { AppShell } from "@/components/app/app-shell";
import { SectionCard, ResultBadge } from "@/components/app/ui-kit";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { api, type Verification } from "@/lib/api";
import { mapHistoryRecord } from "@/lib/presentation";
import robot from "@/assets/robot.png";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "Dashboard — AI Hallucination Mitigation System" },
      {
        name: "description",
        content:
          "Track verifications, start a new claim check and review evidence-based answers from your dashboard.",
      },
      { property: "og:title", content: "Dashboard — AI Hallucination Mitigation System" },
      {
        property: "og:description",
        content: "Track verifications, start a new claim check and review evidence-based answers from your dashboard.",
      },
    ],
  }),
  component: Dashboard,
});

const overviewSteps = [
  { label: "Retrieve Information", icon: FileSearch },
  { label: "Build Knowledge Graph", icon: Share2 },
  { label: "Verify / Generate Answer", icon: ShieldCheck },
  { label: "Provide Result", icon: Sparkles },
];

function Dashboard() {
  const [claim, setClaim] = useState("");
  const [verifications, setVerifications] = useState<Verification[]>([]);
  const [loading, setLoading] = useState(true);
  const [historyError, setHistoryError] = useState("");
  useEffect(() => {
    api.history().then(({ history }) => setVerifications(history.map(mapHistoryRecord))).catch(() => { setVerifications([]); setHistoryError("Unable to load project history."); }).finally(() => setLoading(false));
  }, []);
  const counts = verifications.reduce((summary, item) => { summary[item.result] += 1; return summary; }, { supported: 0, refuted: 0, "not-enough-info": 0 } as Record<string, number>);
  const statCards = [
    { value: verifications.length, label: "Total Verifications", icon: MessagesSquare, tone: "bg-accent text-primary" },
    { value: counts.supported, label: "Supported", icon: CheckCircle2, tone: "bg-success-soft text-success" },
    { value: counts.refuted, label: "Refuted", icon: BadgeAlert, tone: "bg-danger-soft text-destructive" },
    { value: counts["not-enough-info"], label: "Not Enough Info", icon: ShieldQuestion, tone: "bg-warning-soft text-warning" },
  ];

  return (
    <AppShell>
      <div className="grid grid-cols-[minmax(0,1fr)_auto] items-center gap-4">
        <div className="min-w-0">
          <h1 className="text-2xl font-bold tracking-tight sm:text-3xl">
            Evidence workspace
          </h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Verify claims, ask questions and get evidence-based answers.
          </p>
        </div>
        <img
          src={robot}
          alt="Illustration of an AI assistant robot inspecting documents"
          width={768}
          height={640}
          className="hidden h-28 w-auto sm:block"
        />
      </div>

      <div className="mt-6 flex flex-col gap-6">
        <SectionCard
          title="Start New Verification"
          description="Type a claim/question or upload files to get accurate evidence-based answers."
        >
          <Input
            value={claim}
            onChange={(e) => setClaim(e.target.value)}
            placeholder="Enter your claim or question here..."
            aria-label="Claim or question"
            className="h-14 rounded-xl bg-background px-4 text-base"
          />
          <div className="mt-4 grid grid-cols-[minmax(0,1fr)_auto] items-center gap-4">
            <Link
              to="/new-verification"
              className="flex min-w-0 items-center gap-3 rounded-xl p-2 transition-colors hover:bg-muted focus-visible:ring-2 focus-visible:ring-ring focus-visible:outline-none"
            >
              <span className="grid size-10 shrink-0 place-items-center rounded-xl bg-accent text-primary">
                <Upload className="size-5" aria-hidden="true" />
              </span>
              <span className="min-w-0">
                <span className="block text-sm font-semibold">Upload Files</span>
                <span className="block truncate text-xs text-muted-foreground">
                  PDF, TXT, DOCX, CSV (Max 20MB)
                </span>
              </span>
            </Link>
            <Button asChild size="lg" className="rounded-xl">
              <Link to="/new-verification">
                Verify / Ask <ArrowRight className="size-4" />
              </Link>
            </Button>
          </div>
        </SectionCard>

        <div className="grid gap-6 sm:grid-cols-2 xl:grid-cols-4">
          {statCards.map((stat, i) => (
            <motion.article
              key={stat.label}
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3, delay: i * 0.06 }}
              whileHover={{ y: -6 }}
              className="card-soft flex items-center gap-4 p-5 transition-shadow hover:shadow-lift"
            >
              <span className={`grid size-11 shrink-0 place-items-center rounded-xl ${stat.tone}`}>
                <stat.icon className="size-5" aria-hidden="true" />
              </span>
              <span className="min-w-0">
                <span className="block text-2xl font-bold">{stat.value}</span>
                <span className="block truncate text-sm text-muted-foreground">{stat.label}</span>
              </span>
            </motion.article>
          ))}
        </div>

        <div className="grid gap-6 lg:grid-cols-2">
          <SectionCard
            title="Recent Verifications"
            action={
              <Link
                to="/history"
                className="text-sm font-semibold text-primary hover:underline focus-visible:ring-2 focus-visible:ring-ring focus-visible:outline-none"
              >
                View all
              </Link>
            }
            bodyClassName="p-0"
          >
            {loading && <p className="px-5 py-6 text-sm text-muted-foreground">Loading...</p>}
            {historyError && <p role="alert" className="px-5 py-6 text-sm text-destructive">{historyError}</p>}
            {!loading && !historyError && !verifications.length && <p className="px-5 py-6 text-sm text-muted-foreground">No data yet.</p>}
            {!loading && !historyError && verifications.length > 0 && <div className="overflow-x-auto px-5 pt-4 pb-5">
              <table className="w-full min-w-[420px] text-left text-sm">
                <thead>
                  <tr className="text-xs font-semibold text-muted-foreground">
                    <th scope="col" className="pb-3">
                      Claim / Question
                    </th>
                    <th scope="col" className="pb-3">
                      Result
                    </th>
                    <th scope="col" className="pb-3 text-right">
                      Date
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {verifications.slice(0, 4).map((v) => (
                    <tr key={v.id} className="border-t border-border/70">
                      <td className="max-w-[220px] truncate py-3 pr-4 font-medium">
                        <Link to="/answer/$id" params={{ id: v.id }} className="hover:text-primary">
                          {v.text}
                        </Link>
                      </td>
                      <td className="py-3 pr-4">
                        <ResultBadge result={v.result} />
                      </td>
                      <td className="py-3 text-right whitespace-nowrap text-muted-foreground">
                        {v.date}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>}
          </SectionCard>

          <SectionCard title="System Overview">
            <ol className="flex flex-wrap items-start justify-between gap-4">
              {overviewSteps.map((step, i) => (
                <li key={step.label} className="flex flex-1 items-start gap-3">
                  <div className="flex w-24 flex-col items-center gap-2 text-center">
                    <span className="grid size-14 place-items-center rounded-2xl bg-accent text-primary">
                      <step.icon className="size-6" aria-hidden="true" />
                    </span>
                    <span className="text-xs font-medium text-muted-foreground">{step.label}</span>
                  </div>
                  {i < overviewSteps.length - 1 && (
                    <ArrowRight className="mt-5 size-4 shrink-0 text-muted-foreground" aria-hidden="true" />
                  )}
                </li>
              ))}
            </ol>
          </SectionCard>
        </div>
      </div>
    </AppShell>
  );
}
