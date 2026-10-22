"use client";

import { useCallback, useMemo, useState } from "react";
import { useChat } from "@ai-sdk/react";
import { DefaultChatTransport } from "ai";
import { useSituation } from "@/components/guide/situation";
import { ASK_URL } from "@/lib/api";
import { apiFetch } from "@/lib/http-error";
import { messageText, type AskMessage } from "@/lib/ask-types";
import type { Guide } from "@/types/guide";

const HISTORY_TURNS = 6;

/**
 * All state for the "Ask this guide" conversation. It lives above both the desktop column and the mobile
 * sheet, so closing the sheet never loses the conversation. Must be used inside <SituationProvider>.
 *
 * The request body is {question, situation, history} (CONTRACT section 3). The situation is passed as a
 * per-request `body` option from the callbacks below, which are rebuilt whenever the answers change, so
 * it is always the answers at send time.
 */
export function useAsk(guide: Guide) {
  const { answers } = useSituation();

  const transport = useMemo(
    () =>
      new DefaultChatTransport<AskMessage>({
        api: ASK_URL(guide.slug),
        fetch: apiFetch("questions"),
        prepareSendMessagesRequest: ({ messages, body }) => {
          const last = messages[messages.length - 1];
          const question = last && last.role === "user" ? messageText(last).trim() : "";
          const history = messages
            .slice(0, -1)
            .map((m) => ({ role: m.role, text: messageText(m).trim() }))
            .filter((m) => m.text)
            .slice(-HISTORY_TURNS);
          return { body: { question, situation: body?.situation ?? {}, history } };
        },
      }),
    [guide.slug],
  );

  const chat = useChat<AskMessage>({ transport });
  const { messages, status, error, sendMessage, regenerate, stop, setMessages, clearError } = chat;
  const [draft, setDraft] = useState("");

  const busy = status === "submitted" || status === "streaming";

  const send = useCallback(
    (text: string) => {
      const t = text.trim();
      if (!t || busy) return;
      setDraft("");
      void sendMessage({ text: t }, { body: { situation: answers } });
    },
    [busy, sendMessage, answers],
  );

  const retry = useCallback(() => {
    clearError();
    void regenerate({ body: { situation: answers } });
  }, [clearError, regenerate, answers]);

  const reset = useCallback(() => {
    void stop();
    clearError();
    setMessages([]);
    setDraft("");
  }, [stop, clearError, setMessages]);

  return { guide, messages, status, error, busy, draft, setDraft, send, retry, stop, reset };
}

export type AskState = ReturnType<typeof useAsk>;
