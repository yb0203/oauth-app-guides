"use client";

import { useEffect, useRef, useState, type FormEvent, type KeyboardEvent } from "react";
import { ArrowUpIcon, Loader2Icon, MessageSquareTextIcon, RotateCcwIcon, SquareIcon, TriangleAlertIcon } from "lucide-react";
import { Conversation, ConversationContent, ConversationScrollButton } from "@/components/ai-elements/conversation";
import { Button } from "@/components/ui/button";
import { messageText } from "@/lib/ask-types";
import { cn } from "@/lib/utils";
import { AnswerBody } from "./AnswerBody";
import { starterQuestions } from "./starters";
import type { AskState } from "./useAsk";

/** Honest wait: live answers take 10 to 40 s on the free models, so say so and show time passing. */
function Thinking({ onStop }: { onStop: () => void }) {
  const [secs, setSecs] = useState(0);
  useEffect(() => {
    const t0 = Date.now();
    const t = setInterval(() => setSecs(Math.floor((Date.now() - t0) / 1000)), 1000);
    return () => clearInterval(t);
  }, []);
  const slow = secs >= 45;
  return (
    <div role="status" className="flex items-start gap-2.5 py-1 text-sm text-muted-foreground">
      <Loader2Icon className="mt-0.5 size-4 shrink-0 animate-spin text-brand motion-reduce:animate-none" aria-hidden />
      <div className="min-w-0">
        <p>
          <span className="font-medium text-foreground">{slow ? "Still working" : "Reading the guide"}</span>
          <span className="font-mono tabular-nums"> · {secs}s</span>
        </p>
        <p className="mt-0.5 text-xs">
          {slow
            ? "This is slower than usual. Free models can be slow; you can wait, or stop and ask again."
            : "Thinking, usually 10–30 s. The answer appears all at once."}
        </p>
        {slow && (
          <Button variant="outline" size="xs" className="mt-2 bg-background" onClick={onStop}>
            Stop
          </Button>
        )}
      </div>
    </div>
  );
}

function EmptyState({ ask }: { ask: AskState }) {
  const starters = starterQuestions(ask.guide);
  return (
    <div className="flex-1 overflow-y-auto px-4 pt-6 pb-4">
      <div className="flex size-8 items-center justify-center rounded-lg bg-brand-soft text-brand">
        <MessageSquareTextIcon className="size-4" />
      </div>
      <h2 className="mt-3 text-sm font-semibold tracking-tight">Ask this guide</h2>
      <p className="mt-1 text-sm text-muted-foreground">
        Answers come only from this guide&apos;s evidence, with the exact quote.
      </p>
      {starters.length > 0 && (
        <div className="mt-5">
          <p className="mb-2 text-xs font-medium text-muted-foreground">Try asking</p>
          <ul className="space-y-1.5">
            {starters.map((q) => (
              <li key={q}>
                <button
                  type="button"
                  onClick={() => ask.send(q)}
                  className="w-full cursor-pointer rounded-lg border bg-background px-3 py-2 text-left text-sm text-foreground/90 transition-colors outline-none hover:border-brand/40 hover:bg-brand-soft focus-visible:ring-3 focus-visible:ring-ring/50"
                >
                  {q}
                </button>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

function ErrorNotice({ ask }: { ask: AskState }) {
  return (
    <div role="alert" className="rounded-lg border border-danger-border bg-danger-soft px-3 py-2.5 text-sm text-danger">
      <div className="flex items-start gap-2">
        <TriangleAlertIcon className="mt-0.5 size-4 shrink-0" />
        <div className="min-w-0">
          <p className="font-medium">Couldn&apos;t get an answer</p>
          <p className="mt-0.5 text-xs break-words opacity-80">
            The guide service didn&apos;t respond{ask.error?.message ? ` (${ask.error.message.slice(0, 120)})` : ""}.
          </p>
          <Button variant="outline" size="xs" className="mt-2 bg-background" onClick={ask.retry}>
            <RotateCcwIcon /> Retry
          </Button>
        </div>
      </div>
    </div>
  );
}

function Composer({ ask }: { ask: AskState }) {
  const ref = useRef<HTMLTextAreaElement>(null);
  const wasBusy = useRef(false);

  // Hand focus back after an answer finishes, but never pop a touch keyboard open.
  useEffect(() => {
    if (wasBusy.current && !ask.busy && window.matchMedia("(pointer: fine)").matches) ref.current?.focus();
    wasBusy.current = ask.busy;
  }, [ask.busy]);

  const submit = (e?: FormEvent) => {
    e?.preventDefault();
    ask.send(ask.draft);
  };
  const onKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey && !e.nativeEvent.isComposing) {
      e.preventDefault();
      submit();
    }
  };
  const canSend = ask.draft.trim().length > 0 && !ask.busy;

  return (
    <form onSubmit={submit} className="border-t px-3 pt-3 pb-3">
      <div className="flex items-end gap-2 rounded-xl border bg-background p-1.5 pl-3 transition-colors focus-within:border-ring focus-within:ring-3 focus-within:ring-ring/30">
        <textarea
          ref={ref}
          rows={1}
          value={ask.draft}
          disabled={ask.busy}
          onChange={(e) => ask.setDraft(e.target.value)}
          onKeyDown={onKeyDown}
          placeholder="Ask about scopes, limits, review..."
          aria-label="Ask this guide a question"
          className="field-sizing-content max-h-36 min-h-7 flex-1 resize-none bg-transparent py-1 text-base outline-none md:text-sm placeholder:text-muted-foreground disabled:cursor-not-allowed disabled:opacity-60"
        />
        {ask.busy ? (
          <Button type="button" size="icon" variant="outline" onClick={() => ask.stop()} aria-label="Stop answering">
            <SquareIcon className="size-3 fill-current" />
          </Button>
        ) : (
          <Button
            type="submit"
            size="icon"
            disabled={!canSend}
            aria-label="Send question"
            className="bg-brand text-background hover:bg-brand/90"
          >
            <ArrowUpIcon />
          </Button>
        )}
      </div>
      <p className="mt-2 text-center text-[11px] text-muted-foreground">Grounded in this guide only. No web access.</p>
    </form>
  );
}

export function AskPanel({ ask, inSheet = false }: { ask: AskState; inSheet?: boolean }) {
  const { messages, status, error } = ask;
  const started = messages.length > 0;
  const last = messages[messages.length - 1];
  const waiting = ask.busy && (last?.role === "user" || (last?.role === "assistant" && !messageText(last).trim()));

  return (
    <section
      aria-label="Ask this guide"
      className={cn("flex h-full min-h-0 flex-col bg-card", inSheet ? "mx-auto w-full max-w-2xl" : "")}
    >
      {(started || error) && (
        <header className={cn("flex h-11 shrink-0 items-center justify-between border-b px-4", inSheet && "pr-12")}>
          <div className="flex items-center gap-2 text-sm font-medium">
            <MessageSquareTextIcon className="size-4 text-brand" />
            Ask this guide
          </div>
          <Button variant="ghost" size="xs" onClick={ask.reset} className="text-muted-foreground">
            <RotateCcwIcon /> New chat
          </Button>
        </header>
      )}

      {started ? (
        <Conversation className="min-h-0 flex-1">
          <ConversationContent className="gap-5 p-4">
            {messages.map((m, i) =>
              m.role === "user" ? (
                <div key={m.id} className="flex justify-end">
                  <p className="max-w-[88%] rounded-2xl rounded-br-md bg-muted px-3 py-2 text-sm break-words whitespace-pre-wrap">
                    {messageText(m)}
                  </p>
                </div>
              ) : (
                <AnswerBody
                  key={m.id}
                  message={m}
                  streaming={ask.busy && i === messages.length - 1}
                  appName={ask.guide.app_name}
                />
              ),
            )}
            {waiting && <Thinking onStop={() => ask.stop()} />}
            {status === "error" && error && <ErrorNotice ask={ask} />}
          </ConversationContent>
          <ConversationScrollButton />
        </Conversation>
      ) : (
        <EmptyState ask={ask} />
      )}

      <Composer ask={ask} />
    </section>
  );
}
