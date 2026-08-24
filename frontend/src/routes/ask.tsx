import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { useEffect, useRef, useState } from "react";
import { motion, AnimatePresence } from "motion/react";
import {
  Bot,
  Plus,
  Send,
  User,
  Copy,
  Check,
  ExternalLink,
  BookOpen,
  Sparkles,
  RefreshCw,
  AlertCircle,
  HelpCircle,
  ChevronRight,
} from "lucide-react";
import { toast } from "sonner";

import { AppShell } from "@/components/app/app-shell";
import { PageHeader, ResultBadge } from "@/components/app/ui-kit";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { api, type AnswerRecord } from "@/lib/api";
import { answerParagraphs, confidenceLabel, shortExcerpt, statusExplanation, resultFor } from "@/lib/presentation";

type ChatMessage = {
  id: string;
  role: "user" | "assistant";
  text: string;
  time: string;
  result?: AnswerRecord;
  error?: boolean;
};

const SUGGESTED_QUESTIONS = [
  "Does regular cardiovascular exercise improve cognitive memory?",
  "How does mRNA vaccine technology stimulate an immune response?",
  "Does low-dose aspirin reduce the risk of secondary heart attacks?",
  "What causes antimicrobial resistance in bacterial infections?",
];

export const Route = createFileRoute("/ask")({
  validateSearch: (search: Record<string, unknown>) => ({
    q: (search.q as string) || "",
  }),
  head: () => ({
    meta: [
      { title: "Ask a Question — AI Hallucination Mitigation System" },
      {
        name: "description",
        content: "Ask anything and get grounded, evidence-based answers with citations you can inspect.",
      },
      { property: "og:title", content: "Ask a Question — AI Hallucination Mitigation System" },
      { property: "og:description", content: "Grounded answers with inspectable citations." },
    ],
  }),
  component: AskPage,
});

function now() {
  return new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

function AskPage() {
  const search = Route.useSearch();
  const navigate = useNavigate();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [draft, setDraft] = useState("");
  const [typing, setTyping] = useState(false);
  const [error, setError] = useState("");
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const endRef = useRef<HTMLDivElement>(null);
  const autoExecutedRef = useRef(false);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, typing]);

  const handleCopy = (id: string, text: string) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    toast.success("Answer copied to clipboard");
    setTimeout(() => setCopiedId(null), 2000);
  };

  const send = async (customValue?: string) => {
    const value = (customValue !== undefined ? customValue : draft).trim();
    if (!value || typing) {
      if (!value) setError("Please enter a question.");
      return;
    }

    setError("");
    const userMsgId = `user-${Date.now()}`;
    setMessages((m) => [...m, { id: userMsgId, role: "user", text: value, time: now() }]);
    setDraft("");
    setTyping(true);

    try {
      const result = await api.ask(value);
      setTyping(false);

      const recordId = result.id || `ans-${Date.now()}`;
      const answerText = result.answer || "Answer generated successfully.";

      setMessages((m) => [
        ...m,
        {
          id: recordId,
          role: "assistant",
          text: answerText,
          time: now(),
          result: {
            ...result,
            id: recordId,
            evidence: result.evidence || [],
            sources: result.sources || [],
            claims: result.claims || [],
          },
        },
      ]);
    } catch (cause) {
      setTyping(false);
      const errMsg = cause instanceof Error ? cause.message : "Unable to connect to verification backend.";
      setError(errMsg);
      setMessages((m) => [
        ...m,
        {
          id: `err-${Date.now()}`,
          role: "assistant",
          text: `Error processing question: ${errMsg}`,
          time: now(),
          error: true,
        },
      ]);
    }
  };

  useEffect(() => {
    if (search.q && !autoExecutedRef.current) {
      autoExecutedRef.current = true;
      void send(search.q);
    }
  }, [search.q]);

  return (
    <AppShell>
      <PageHeader
        title="Ask a Question"
        description="Ask anything and get grounded, evidence-backed answers with verifiable scientific citations."
        action={
          <Button
            variant="outline"
            className="rounded-xl transition-colors hover:bg-muted"
            onClick={() => {
              setMessages([]);
              setError("");
            }}
          >
            <Plus className="size-4 mr-1" /> New Chat
          </Button>
        }
      />

      <div className="card-soft flex h-[calc(100vh-14rem)] min-h-[560px] flex-col rounded-2xl border border-border bg-card shadow-sm overflow-hidden">
        {/* Messages Container */}
        <div className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-6">
          {messages.length === 0 && (
            <div className="flex flex-col items-center justify-center py-12 px-4 text-center">
              <div className="grid size-14 place-items-center rounded-2xl bg-primary/10 text-primary mb-4 shadow-soft">
                <Sparkles className="size-7" />
              </div>
              <h3 className="text-base font-semibold text-foreground">
                Ask any question with Hallucination Mitigation
              </h3>
              <p className="mt-1 text-xs text-muted-foreground max-w-md">
                Every query is retrieved through multi-source evidence indexes, cross-referenced with
                the SciFact fact-checking pipeline, and scored for factual confidence.
              </p>

              <div className="mt-8 w-full max-w-xl text-left">
                <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-3">
                  Suggested Questions
                </p>
                <div className="grid gap-2">
                  {SUGGESTED_QUESTIONS.map((question) => (
                    <button
                      key={question}
                      type="button"
                      onClick={() => void send(question)}
                      className="group flex items-center justify-between rounded-xl border border-border/80 bg-background/60 p-3 text-xs font-medium text-foreground transition-all duration-200 hover:border-primary/50 hover:bg-primary/[0.04] hover:shadow-xs text-left"
                    >
                      <span className="truncate pr-2">{question}</span>
                      <ChevronRight className="size-4 shrink-0 text-muted-foreground group-hover:text-primary transition-transform group-hover:translate-x-0.5" />
                    </button>
                  ))}
                </div>
              </div>
            </div>
          )}

          <ul className="flex flex-col gap-6">
            <AnimatePresence initial={false}>
              {messages.map((m) => (
                <motion.li
                  key={m.id}
                  initial={{ opacity: 0, y: 12 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.25 }}
                  className={`flex items-start gap-3.5 ${m.role === "user" ? "flex-row-reverse" : ""}`}
                >
                  <span
                    className={`grid size-9 shrink-0 place-items-center rounded-xl shadow-xs ${
                      m.role === "user"
                        ? "bg-primary text-primary-foreground"
                        : m.error
                        ? "bg-destructive/10 text-destructive border border-destructive/20"
                        : "bg-primary/10 text-primary border border-primary/20"
                    }`}
                  >
                    {m.role === "user" ? (
                      <User className="size-4" aria-hidden="true" />
                    ) : m.error ? (
                      <AlertCircle className="size-4" aria-hidden="true" />
                    ) : (
                      <Bot className="size-4" aria-hidden="true" />
                    )}
                  </span>

                  {m.role === "user" ? (
                    <div className="max-w-[80%] rounded-2xl rounded-tr-xs bg-primary px-4 py-3 text-primary-foreground shadow-sm">
                      <p className="text-sm font-medium leading-relaxed">{m.text}</p>
                      <p className="mt-1.5 text-right text-[10px] text-primary-foreground/75">{m.time}</p>
                    </div>
                  ) : (
                    <div className="max-w-[88%] w-full rounded-2xl rounded-tl-xs border border-border bg-card p-4 sm:p-5 shadow-sm space-y-4">
                      {m.result ? (
                        <>
                          {/* Status & Confidence Header */}
                          <div className="flex flex-wrap items-center justify-between gap-2 border-b border-border/50 pb-3">
                            <div className="flex items-center gap-2">
                              <ResultBadge result={resultFor(m.result.verification_status)} />
                              <span className="text-xs text-muted-foreground font-medium">
                                {statusExplanation(m.result.verification_status)}
                              </span>
                            </div>

                            <div className="flex items-center gap-2">
                              <span className="rounded-md bg-muted px-2 py-0.5 text-[11px] font-semibold text-muted-foreground">
                                Confidence: {confidenceLabel(m.result)}
                              </span>
                              <button
                                type="button"
                                onClick={() => handleCopy(m.id, m.result?.answer || m.text)}
                                title="Copy answer"
                                className="grid size-7 place-items-center rounded-lg border border-border/80 text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
                              >
                                {copiedId === m.id ? (
                                  <Check className="size-3.5 text-emerald-600" />
                                ) : (
                                  <Copy className="size-3.5" />
                                )}
                              </button>
                            </div>
                          </div>

                          {/* Answer Body */}
                          <div className="space-y-2.5 text-sm leading-relaxed text-foreground">
                            {answerParagraphs(m.result.answer).length > 0 ? (
                              answerParagraphs(m.result.answer).map((paragraph, idx) => (
                                <p key={idx}>{paragraph}</p>
                              ))
                            ) : (
                              <p>{m.result.answer || m.text}</p>
                            )}
                          </div>

                          {/* Evidence & Citations Section */}
                          {(m.result.sources?.length > 0 || m.result.evidence?.length > 0) && (
                            <div className="rounded-xl border border-border/60 bg-muted/40 p-4 space-y-3">
                              <div className="flex items-center justify-between">
                                <span className="flex items-center gap-1.5 text-xs font-semibold text-foreground uppercase tracking-wider">
                                  <BookOpen className="size-3.5 text-primary" />
                                  Evidence &amp; Grounding Sources
                                </span>
                                <span className="text-[11px] text-muted-foreground font-medium">
                                  {(m.result.sources?.length || 0) + (m.result.evidence?.length || 0)} references
                                </span>
                              </div>

                              {m.result.evidence && m.result.evidence.length > 0 && (
                                <div className="rounded-lg bg-background/80 p-2.5 border border-border/40 text-xs">
                                  <p className="font-medium text-foreground mb-1">
                                    Primary SciFact Evidence: {m.result.evidence[0].title}
                                  </p>
                                  <p className="text-muted-foreground line-clamp-2">
                                    {shortExcerpt(m.result.evidence[0].content, 180)}
                                  </p>
                                </div>
                              )}

                              {m.result.sources && m.result.sources.length > 0 && (
                                <ol className="list-decimal space-y-1.5 pl-4 text-xs text-muted-foreground">
                                  {m.result.sources.map((s, idx) => (
                                    <li key={`${s.title}-${idx}`}>
                                      {s.url ? (
                                        <a
                                          href={s.url}
                                          target="_blank"
                                          rel="noreferrer"
                                          className="inline-flex items-center gap-1 text-primary hover:underline font-medium"
                                        >
                                          {s.title}
                                          <ExternalLink className="size-2.5" />
                                        </a>
                                      ) : (
                                        <span className="font-medium text-foreground">{s.title}</span>
                                      )}
                                      {s.similarity_score ? (
                                        <span className="ml-1.5 text-[10px] text-muted-foreground">
                                          ({Math.round(s.similarity_score * 100)}% match)
                                        </span>
                                      ) : null}
                                    </li>
                                  ))}
                                </ol>
                              )}

                              {/* Interactive Actions */}
                              <div className="flex flex-wrap items-center gap-2 pt-1">
                                <Button
                                  asChild
                                  variant="secondary"
                                  size="sm"
                                  className="h-8 rounded-lg text-xs font-medium"
                                >
                                  <Link to="/answer/$id" params={{ id: m.id }}>
                                    View Full Verification Record
                                  </Link>
                                </Button>
                              </div>
                            </div>
                          )}

                          <div className="flex items-center justify-between text-[10px] text-muted-foreground pt-1">
                            <span>{m.result.confidence_explanation || "Grounding complete"}</span>
                            <span>{m.time}</span>
                          </div>
                        </>
                      ) : (
                        <div className="space-y-2">
                          <p className="text-sm leading-relaxed text-foreground">{m.text}</p>
                          <p className="text-[10px] text-muted-foreground text-right">{m.time}</p>
                        </div>
                      )}
                    </div>
                  )}
                </motion.li>
              ))}
            </AnimatePresence>

            {typing && (
              <motion.li
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                className="flex items-center gap-3.5"
                aria-live="polite"
              >
                <span className="grid size-9 place-items-center rounded-xl bg-primary/10 text-primary border border-primary/20">
                  <Bot className="size-4 animate-pulse" aria-hidden="true" />
                </span>
                <div className="flex items-center gap-2 rounded-2xl border border-border bg-card px-4 py-3 shadow-xs">
                  <span className="text-xs text-muted-foreground mr-1">Retrieving evidence &amp; verifying</span>
                  {[0, 1, 2].map((i) => (
                    <motion.span
                      key={i}
                      animate={{ opacity: [0.2, 1, 0.2], scale: [0.8, 1.1, 0.8] }}
                      transition={{ duration: 1.2, repeat: Infinity, delay: i * 0.2 }}
                      className="size-2 rounded-full bg-primary"
                    />
                  ))}
                </div>
              </motion.li>
            )}

            {error && (
              <li
                role="alert"
                className="flex items-center justify-between rounded-xl border border-destructive/30 bg-destructive/10 p-3.5 text-xs text-destructive"
              >
                <div className="flex items-center gap-2">
                  <AlertCircle className="size-4 shrink-0" />
                  <span>{error}</span>
                </div>
                <button
                  type="button"
                  onClick={() => setError("")}
                  className="font-medium underline hover:opacity-80 ml-2"
                >
                  Dismiss
                </button>
              </li>
            )}
          </ul>
          <div ref={endRef} />
        </div>

        {/* Input Bar */}
        <div className="border-t border-border p-3 sm:p-4 bg-muted/20">
          <div className="grid grid-cols-[minmax(0,1fr)_auto] items-end gap-2.5">
            <Textarea
              value={draft}
              onChange={(e) => setDraft(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  void send();
                }
              }}
              placeholder="Ask a question (e.g., 'How does mRNA vaccine technology work?')..."
              aria-label="Question prompt"
              className="max-h-32 min-h-11 resize-none rounded-xl bg-background text-sm leading-relaxed border-border/80 focus-visible:ring-2 focus-visible:ring-primary/40"
            />
            <Button
              size="icon"
              disabled={typing || !draft.trim()}
              onClick={() => void send()}
              aria-label="Send question"
              className="size-11 shrink-0 rounded-xl bg-primary text-primary-foreground shadow-soft hover:bg-primary/90 transition-all disabled:opacity-50"
            >
              {typing ? (
                <RefreshCw className="size-4 animate-spin" />
              ) : (
                <Send className="size-4" />
              )}
            </Button>
          </div>
        </div>
      </div>
    </AppShell>
  );
}
