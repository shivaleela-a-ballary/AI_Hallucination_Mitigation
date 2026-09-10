import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useEffect } from "react";
import { ArrowRight, Loader2, Sparkles } from "lucide-react";
import { AppShell } from "@/components/app/app-shell";
import { Button } from "@/components/ui/button";

export const Route = createFileRoute("/new-verification")({
  validateSearch: (search: Record<string, unknown>) => ({
    claim: typeof search.claim === "string" ? search.claim : "",
    evidence: typeof search.evidence === "string" ? search.evidence : "",
  }),
  component: NewVerificationRedirect,
});

function NewVerificationRedirect() {
  const navigate = useNavigate();
  const search = Route.useSearch();

  useEffect(() => {
    // Seamlessly forward to the consolidated Check AI Answer workspace
    const timer = setTimeout(() => {
      navigate({
        to: "/check-answer",
        search: search.claim ? { q: search.claim } : undefined,
      });
    }, 100);
    return () => clearTimeout(timer);
  }, [navigate, search]);

  return (
    <AppShell>
      <div className="flex min-h-[60vh] flex-col items-center justify-center text-center p-6">
        <div className="size-14 rounded-2xl bg-indigo-500/10 border border-indigo-500/30 flex items-center justify-center text-indigo-400 mb-4">
          <Sparkles className="size-7 animate-pulse" />
        </div>
        <h2 className="text-xl font-bold text-slate-100">Redirecting to Check AI Answer</h2>
        <p className="mt-2 text-sm text-slate-400 max-w-md">
          Claim verification is now consolidated into the unified Check AI Answer workspace.
        </p>
        <div className="mt-6">
          <Button
            onClick={() =>
              navigate({
                to: "/check-answer",
                search: search.claim ? { q: search.claim } : undefined,
              })
            }
            className="rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white"
          >
            Go to Check AI Answer <ArrowRight className="size-4 ml-2" />
          </Button>
        </div>
      </div>
    </AppShell>
  );
}
