"use client";

import { useEffect, useState } from "react";

/** A non-2xx answer from the backend, turned into plain language. `message` is safe to show as-is. */
export class ApiError extends Error {
  constructor(
    message: string,
    readonly status: number,
    /** seconds from a Retry-After header, when present */
    readonly retryAfter: number | null,
  ) {
    super(message);
    this.name = "ApiError";
  }
  get rateLimited() {
    return this.status === 429;
  }
}

function parseRetryAfter(h: string | null): number | null {
  if (!h) return null;
  const n = Number(h);
  if (Number.isFinite(n) && n >= 0) return Math.ceil(n);
  const d = Date.parse(h);
  return Number.isNaN(d) ? null : Math.max(0, Math.ceil((d - Date.now()) / 1000));
}

/** FastAPI errors are {"detail": "text"} or {"detail": [{msg}, ...]}; fall back to a short status line. */
async function detailOf(res: Response): Promise<string> {
  const raw = await res.text().catch(() => "");
  try {
    const j = JSON.parse(raw) as { detail?: unknown };
    if (typeof j.detail === "string") return j.detail;
    if (Array.isArray(j.detail)) {
      const msgs = j.detail.map((d) => (d && typeof d === "object" && "msg" in d ? String((d as { msg: unknown }).msg) : "")).filter(Boolean);
      if (msgs.length) return msgs.join("; ");
    }
  } catch {
    /* not JSON */
  }
  const t = raw.trim();
  return t && t.length < 200 && !t.startsWith("<") ? t : "";
}

/**
 * fetch for the chat transports: non-2xx responses become an ApiError with a readable message.
 * `what` is how a 429 is phrased: "guides" (generation) or "questions" (ask).
 */
export function apiFetch(what: "guides" | "questions"): typeof fetch {
  return async (input, init) => {
    const res = await fetch(input, init);
    if (res.ok) return res;
    const detail = await detailOf(res);
    const retryAfter = parseRetryAfter(res.headers.get("retry-after"));
    let message: string;
    if (res.status === 429) {
      message = `You've started several ${what} in a few minutes. Wait a minute and retry.`;
    } else if (res.status === 404) {
      message = detail || "That guide or endpoint wasn't found.";
    } else if (res.status >= 500) {
      message = detail ? `The service had a problem: ${detail}` : "The service had a problem. Try again in a moment.";
    } else {
      message = detail || `The request was rejected (HTTP ${res.status}).`;
    }
    throw new ApiError(message, res.status, retryAfter);
  };
}

/** Seconds left, counting down from `from` (null/0 = nothing to wait). Remount to restart the countdown. */
export function useCountdown(from: number | null | undefined): number {
  const [t0] = useState(() => Date.now());
  const [now, setNow] = useState(t0);
  useEffect(() => {
    if (!from) return;
    const t = setInterval(() => setNow(Date.now()), 500);
    return () => clearInterval(t);
  }, [from]);
  return from ? Math.max(0, from - Math.floor((now - t0) / 1000)) : 0;
}
