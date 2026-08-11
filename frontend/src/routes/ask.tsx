import { createFileRoute, Link } from "@tanstack/react-router";
import { useEffect, useRef, useState } from "react";
import { motion } from "motion/react";
import { Bot, Plus, Send, User } from "lucide-react";

import { AppShell } from "@/components/app/app-shell";
import { PageHeader } from "@/components/app/ui-kit";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { initialChat, answerDetail, answerEvidence, type ChatMessage } from "@/data/mock";

export const Route = createFileRoute("/ask")({
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
  const [messages, setMessages] = useState<ChatMessage[]>(initialChat);
  const [draft, setDraft] = useState("");
  const [typing, setTyping] = useState(false);
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, typing]);

  const send = () => {
    const value = draft.trim();
    if (!value) return;
    setMessages((m) => [...m, { id: crypto.randomUUID(), role: "user", text: value, time: now() }]);
    setDraft("");
    setTyping(true);
    setTimeout(() => {
      setTyping(false);
      setMessages((m) => [
        ...m,
        {
          id: crypto.randomUUID(),
          role: "assistant",
          text: answerDetail.answer,
          time: now(),
          sources: answerEvidence.map((e) => e.source),
        },
      ]);
    }, 1400);
  };

  return (
    <AppShell>
      <PageHeader
        title="Ask a Question"
        description="Ask anything and get evidence-based answers."
        action={
          <Button
            variant="outline"
            className="rounded-xl"
            onClick={() => setMessages([])}
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
                    <p className="text-sm leading-relaxed">{m.text}</p>
                    <p className="mt-1 text-[11px] text-muted-foreground">{m.time}</p>
                    {m.sources && (
                      <div className="mt-4 rounded-xl bg-muted/60 p-4">
                        <p className="text-sm font-semibold">Sources ({m.sources.length})</p>
                        <ol className="mt-2 list-decimal space-y-1 pl-5 text-sm text-muted-foreground">
                          {m.sources.map((s) => (
                            <li key={s}>{s}</li>
                          ))}
                        </ol>
                        <Button asChild variant="secondary" size="sm" className="mt-3 rounded-lg">
                          <Link to="/answer/$id" params={{ id: "v2" }}>
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
              onClick={send}
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
