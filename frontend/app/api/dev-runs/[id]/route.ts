// Dev-only mock of GET /api/runs/{run_id} (CONTRACT section 3). Enabled with NEXT_PUBLIC_USE_MOCK=1.
// Runs started by the dev-generate "!silent" input report `running` for 12 s, then `done` with the github guide.
import { devRuns } from "../../dev-generate/runs";

export const dynamic = "force-dynamic";

export async function GET(_req: Request, ctx: { params: Promise<{ id: string }> }) {
  if (process.env.NEXT_PUBLIC_USE_MOCK !== "1") return new Response("mock disabled", { status: 404 });
  const { id } = await ctx.params;
  const started = devRuns.get(id);
  if (started === undefined) return Response.json({ detail: "Unknown run" }, { status: 404 });
  const age = Date.now() - started;
  const done = age > 12_000;
  return Response.json({
    run_id: id,
    status: done ? "done" : "running",
    stage: done ? "publish" : "synthesize",
    slug: done ? "github" : null,
    permalink: done ? "/guides/github" : null,
    error: null,
    updated_at: new Date().toISOString(),
  });
}
