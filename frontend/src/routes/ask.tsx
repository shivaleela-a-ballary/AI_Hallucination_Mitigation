import { createFileRoute, Link } from "@tanstack/react-router";
import { useEffect, useRef, useState } from "react";
import { motion } from "motion/react";
import { Bot, Plus, Send, User } from "lucide-react";

import { AppShell } from "@/components/app/app-shell";
import { PageHeader, ResultBadge } from "@/components/app/ui-kit";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { api, type AnswerRecord } from "@/lib/api";
import { answerParagraphs, confidenceLabel, shortExcerpt, statusExplanation, resultFor } from "@/lib/presentation";

type ChatMessage = { id: string; role: "user" | "assistant"; text: string; time: string; result?: AnswerRecord };

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
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [draft, setDraft] = useState("");
  const [typing, setTyping] = useState(false);
  const [error, setError] = useState("");
  const endRef = useRef<HTMLDivElement>(null);
  const autoExecutedRef = useRef(false);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, typing]);

  const send = async (customValue?: string) => {
    const value = (customValue !== undefined ? customValue : draft).trim();
    if (!value || typing) {
      if (!value) setError("Enter a question first.");
      return;
    }
    setError("");
    setMessages((m) => [...m, { id: crypto.randomUUID(), role: "user", text: value, time: now() }]);
    setDraft("");
    setTyping(true);
    try {
      const result = await api.ask(value);
      setTyping(false);
      setMessages((m) => [
        ...m,
        {
          id: result.id,
          role: "assistant",
          text: result.answer,
          time: now(),
          result,
        },
      ]);
    } catch (cause) {
      setTyping(false);
      setError(cause instanceof Error ? cause.message : "Unable to process the question.");
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
        description="Ask anything and get evidence-based answers."
        action={
          <Button
            variant="outline"
            className="rounded-xl"
            onClick={() => { setMessages([]); setError(""); }}
          >
            <Plus className="size-4" /> New Chat
          </Button>
        }
      />

      <div className="card-soft flex h-[calc(100vh-14rem)] min-h-[520px] flex-col">
        <div className="flex-1 overflow-y-auto p-5">
          {messages.length === 0 && (
            <p className="mt-20 text-center text-sm text-muted-foreground">
              Start a new conversation by asking a question below.
            </p>
          )}
          <ul className="flex flex-col gap-5">
            {messages.map((m) => (
              <motion.li
                key={m.id}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className={`flex items-start gap-3 ${m.role === "user" ? "flex-row-reverse" : ""}`}
              >
                <span
                  className={`grid size-9 shrink-0 place-items-center rounded-full ${
                    m.role === "user" ? "bg-primary text-primary-foreground" : "bg-accent text-primary"
                  }`}
                >
                  {m.role === "user" ? (
                    <User className="size-4" aria-hidden="true" />
                  ) : (
                    <Bot className="size-4" aria-hidden="true" />
                  )}
                </span>

                {m.role === "user" ? (
                  <div className="max-w-[75%] rounded-2xl rounded-tr-sm bg-primary px-4 py-3 text-primary-foreground">
                    <p className="text-sm">{m.text}</p>
                    <p className="mt-1 text-right text-[11px] opacity-80">{m.time}</p>
                  </div>
                ) : (
                  <div className="max-w-[85%] rounded-2xl rounded-tl-sm border border-border bg-card px-4 py-3">
                    {m.result ? <>
                      <div className="flex flex-wrap items-center gap-2">
                        <ResultBadge result={resultFor(m.result.verification_status)} />
                        <span className="text-xs text-muted-foreground">{statusExplanation(m.result.verification_status)}</span>
                      </div>
                      <div className="mt-3 space-y-2 text-sm leading-relaxed">
                        {answerParagraphs(m.result.answer).map((paragraph) => <p key={paragraph}>{paragraph}</p>)}
                      </div>
                      <p className="mt-3 text-xs font-semibold">Confidence: {confidenceLabel(m.result)}</p>
                      <p className="mt-1 text-xs text-muted-foreground">{m.result.created_at ? new Date(m.result.created_at).toLocaleString() : m.time}</p>
                    </> : <p className="text-sm leading-relaxed">{m.text}</p>}
                    {m.result && (
                      <div className="mt-4 rounded-xl bg-muted/60 p-4">
                        <p className="text-sm font-semibold">Evidence &amp; Sources</p>
                        {m.result.evidence.length > 0 && <p className="mt-2 text-xs text-muted-foreground">{shortExcerpt(m.result.evidence[0].content)}</p>}
                        <ol className="mt-2 list-decimal space-y-1 pl-5 text-sm text-muted-foreground">
                          {m.result.sources.map((s) => (
                            <li key={`${s.source}:${s.title}`}>{s.url ? <a href={s.url} target="_blank" rel="noreferrer" className="hover:text-primary hover:underline">{s.title}</a> : s.title}</li>
                          ))}
                        </ol>
                        <Button asChild variant="secondary" size="sm" className="mt-3 rounded-lg">
                          <Link to="/answer/$id" params={{ id: m.id }}>
                            View Sources
                          </Link>
                        </Button>
                      </div>
                    )}
                  </div>
                )}
              </motion.li>
            ))}
            {typing && (
              <li className="flex items-center gap-3" aria-live="polite">
                <span className="grid size-9 place-items-center rounded-full bg-accent text-primary">
                  <Bot className="size-4" aria-hidden="true" />
                </span>
                <span className="flex gap-1 rounded-2xl border border-border bg-card px-4 py-4">
                  {[0, 1, 2].map((i) => (
                    <motion.span
                      key={i}
                      animate={{ opacity: [0.3, 1, 0.3] }}
                      transition={{ duration: 1.1, repeat: Infinity, delay: i * 0.18 }}
                      className="size-2 rounded-full bg-primary"
                    />
                  ))}
                </span>
              </li>
            )}
            {error && <li role="alert" className="rounded-xl bg-danger-soft p-3 text-sm text-destructive">{error}</li>}
          </ul>
          <div ref={endRef} />
        </div>

        <div className="border-t border-border p-4">
          <div className="grid grid-cols-[minmax(0,1fr)_auto] items-end gap-3">
            <Textarea
              value={draft}
              onChange={(e) => setDraft(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  send();
                }
              }}
              placeholder="Ask another question..."
              aria-label="Message"
              className="max-h-32 min-h-12 resize-none rounded-xl bg-background"
            />
            <Button
              size="icon"
              onClick={() => void send()}
              aria-label="Send message"
              className="size-12 shrink-0 rounded-full"
            >
              <Send className="size-4" />
            </Button>
          </div>
        </div>
      </div>
    </AppShell>
  );
}
