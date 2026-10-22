// Dev-only mock of POST /api/generate (CONTRACT §4). Enabled with NEXT_PUBLIC_USE_MOCK=1.
import { buildFixture } from "@/fixtures/stream";

export const dynamic = "force-dynamic";

function lastUserText(body: unknown): string {
  const b = body as { app?: string; messages?: { role: string; parts?: { type: string; text?: string }[] }[] };
  if (b?.app) return b.app;
  const last = [...(b?.messages ?? [])].reverse().find((m) => m.role === "user");
  return last?.parts?.filter((p) => p.type === "text").map((p) => p.text).join(" ") ?? "unknown app";
}

export async function POST(req: Request) {
  if (process.env.NEXT_PUBLIC_USE_MOCK !== "1") return new Response("mock disabled", { status: 404 });
  const app = lastUserText(await req.json().catch(() => ({})));
  const events = buildFixture(app);
  const enc = new TextEncoder();
  const stream = new ReadableStream({
    async start(controller) {
      for (const { delay, event } of events) {
        await new Promise((r) => setTimeout(r, delay));
        controller.enqueue(enc.encode(`data: ${event === "[DONE]" ? event : JSON.stringify(event)}\n\n`));
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
