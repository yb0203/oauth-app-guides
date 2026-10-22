// Dev-only fixture following CONTRACT §4. Replayed by app/api/dev-generate/route.ts.
import github from "./github.json";
import type { Guide } from "@/types/guide";

export type FixtureEvent = { delay: number; event: Record<string, unknown> | "[DONE]" };

const guide = github as unknown as Guide;
let n = 0;
const text = (delay: number, body: string): FixtureEvent[] => {
  const id = `t${++n}`;
  return [
    { delay, event: { type: "text-start", id } },
    { delay: 60, event: { type: "text-delta", id, delta: body } },
    { delay: 20, event: { type: "text-end", id } },
  ];
};
const stage = (
  delay: number,
  s: string,
  status: string,
  label: string,
  detail?: string,
  counts?: Record<string, number>,
): FixtureEvent => ({
  delay,
  event: { type: "data-stage", id: s, data: { stage: s, status, label, detail, counts, replay: true } },
});
const src = (delay: number, id: string, url: string, title: string): FixtureEvent => ({
  delay,
  event: { type: "source-url", sourceId: id, url, title },
});

export function buildFixture(app: string): FixtureEvent[] {
  n = 0;
  const g: Guide = { ...guide, guide_type: "generated" };
  return [
    { delay: 100, event: { type: "start", messageId: "run-dev-1" } },
    stage(100, "resolve", "running", "Resolving the app"),
    ...text(500, `Demo replay: recorded GitHub run, not research for ${app}`),
    stage(400, "resolve", "done", "Resolved to GitHub (github.com)", "Composio toolkit: github (managed)"),
    stage(200, "find_docs", "running", "Finding official docs"),
    src(600, "s1", "https://docs.github.com/en/apps/oauth-apps/building-oauth-apps/creating-an-oauth-app", "Creating an OAuth app"),
    ...text(300, "Found 5 candidate docs pages on docs.github.com."),
    src(500, "s2", "https://docs.github.com/en/apps/oauth-apps/building-oauth-apps/authorizing-oauth-apps", "Authorizing OAuth apps"),
    stage(300, "find_docs", "done", "Found 5 docs pages", undefined, { pages: 5 }),
    stage(200, "research", "running", "Reading docs and community reports"),
    src(700, "s3", "https://docs.github.com/en/organizations/managing-oauth-access-to-your-organizations-data", "Managing OAuth access to your organization's data"),
    ...text(300, "Organizations restrict third-party OAuth apps by default. Checking how owners approve them."),
    src(600, "s4", "https://docs.composio.dev/docs/toolkits/github", "Composio: GitHub toolkit"),
    stage(300, "research", "done", "Read 4 pages", undefined, { pages: 4 }),
    stage(200, "probe", "running", "Probing the developer console"),
    ...text(500, "Opening github.com/settings/applications/new without credentials to see where it leads."),
    {
      delay: 900,
      event: {
        type: "data-wall",
        id: "wall",
        data: {
          console_url: "https://github.com/settings/applications/new",
          final_url: "https://github.com/login?return_to=%2Fsettings%2Fapplications%2Fnew",
          redirect_chain: [
            "https://github.com/settings/applications/new",
            "https://github.com/login?return_to=%2Fsettings%2Fapplications%2Fnew",
          ],
          outcome: "login_wall",
          wall_host: "github.com",
          asks_for: "Sign in with password, Google, Apple or a passkey",
          bot_check: false,
          method: "http",
          observed_at: new Date().toISOString(),
        },
      },
    },
    stage(200, "probe", "done", "Console is behind a sign-in wall"),
    stage(200, "synthesize", "running", "Drafting the guide"),
    ...text(700, "Drafting steps, limits and the review path from the collected evidence."),
    stage(800, "synthesize", "done", "Guide drafted"),
    stage(200, "verify", "running", "Re-checking every quote against the live pages"),
    ...[4, 9, 14, 17].map((c, i) => ({
      delay: 450,
      event: {
        type: "data-verification",
        id: "verification",
        data: { checked: c, docs_verified: Math.max(0, c - 4 - i), hidden: i > 1 ? 1 : 0, downgraded: i > 2 ? 1 : 0, total: 17 },
      },
    })),
    stage(300, "verify", "done", "17 claims checked"),
    stage(200, "publish", "running", "Publishing"),
    stage(400, "publish", "done", "Published"),
    {
      delay: 200,
      event: { type: "data-guide", id: "guide", data: { slug: g.slug, permalink: `/guides/${g.slug}`, guide: g, replay: true } },
    },
    { delay: 50, event: { type: "finish" } },
    { delay: 10, event: "[DONE]" },
  ];
}
