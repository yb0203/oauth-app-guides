// Dev-only mock of POST /api/guides/{slug}/ask (CONTRACT section 4b). Enabled with NEXT_PUBLIC_USE_MOCK=1.
// Reads the guide JSON from ../data/guides/<slug>.json and answers with deterministic keyword retrieval.
import { readFile } from "node:fs/promises";
import path from "node:path";
import { buildAskEvents, type AskRequestBody } from "@/fixtures/ask";
import type { Guide } from "@/types/guide";

export const dynamic = "force-dynamic";

type RawBody = {
  question?: string;
  situation?: Record<string, string>;
  history?: AskRequestBody["history"];
  messages?: { role: string; parts?: { type: string; text?: string }[] }[];
};

function normalise(b: RawBody): AskRequestBody {
  let question = typeof b.question === "string" ? b.question : "";
  if (!question) {
    const last = [...(b.messages ?? [])].reverse().find((m) => m.role === "user");
    question = last?.parts?.filter((p) => p.type === "text").map((p) => p.text ?? "").join(" ") ?? "";
  }
  return { question, situation: b.situation ?? {}, history: Array.isArray(b.history) ? b.history : [] };
}

export async function POST(req: Request, ctx: { params: Promise<{ slug: string }> }) {
  if (process.env.NEXT_PUBLIC_USE_MOCK !== "1") return new Response("mock disabled", { status: 404 });
  const { slug } = await ctx.params;
  if (!/^[a-z0-9-]+$/.test(slug)) return new Response("bad slug", { status: 400 });

  let guide: Guide;
  try {
    guide = JSON.parse(await readFile(path.join(process.cwd(), "..", "data", "guides", `${slug}.json`), "utf8")) as Guide;
  } catch {
    return new Response("guide not found", { status: 404 });
  }

  const body = normalise((await req.json().catch(() => ({}))) as RawBody);
  const events = buildAskEvents(guide, body);
  const enc = new TextEncoder();
  const stream = new ReadableStream({
    async start(controller) {
      for (const { delay, event } of events) {
        await new Promise((r) => setTimeout(r, delay));
        try {
          controller.enqueue(enc.encode(`data: ${event === "[DONE]" ? event : JSON.stringify(event)}\n\n`));
        } catch {
          return; // client aborted
        }
      }
      controller.close();
    },
  });
  return new Response(stream, {
    headers: {
      "content-type": "text/event-stream",
      "cache-control": "no-cache",
      "x-vercel-ai-ui-message-stream": "v1",
    },
  });
}
