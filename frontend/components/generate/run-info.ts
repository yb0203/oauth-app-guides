import type { Guide, StageId } from "@/types/guide";

/** One line per stage on why it matters. Shown under every stage in the pipeline. */
export const STAGE_WHY: Record<StageId, string> = {
  resolve: "Works out which provider this is and whether Composio already covers it.",
  find_docs: "Picks the official pages about app registration, scopes and review.",
  research: "Reads those pages and notes every claim it will need to prove.",
  probe: "Opens the real developer console to see what a new developer hits first.",
  synthesize: "Writes the steps, limits and review path, each tied to a quote.",
  verify: "Re-checks every quote against the live page. Misses are downgraded.",
  publish: "Saves the guide at a permanent link you can share.",
};

/** What the agent is doing right now, in plain words, for the summary at the top. */
export const STAGE_NOW: Record<StageId, (app: string) => string> = {
  resolve: (app) => `Looking up ${app}`,
  find_docs: (app) => `Finding ${app}'s official developer docs`,
  research: () => "Reading the docs and noting claims to check",
  probe: () => "Opening the developer console to see what a new developer hits",
  synthesize: () => "Writing the guide from what it read",
  verify: () => "Re-checking every quote on the live pages",
  publish: () => "Publishing the guide",
};

export const TYPICAL_RUN = "2 to 4 minutes";
/** After this long a run is slower than the usual range; the summary says so instead of staying silent. */
export const SLOW_AFTER_MS = 5 * 60 * 1000;

/** A stage that has been running this long without finishing gets an explanation instead of silence. */
export const QUIET_AFTER_MS = 20 * 1000;

export function formatDuration(ms: number): string {
  const s = Math.max(0, ms) / 1000;
  if (s < 10) return `${s.toFixed(1)}s`;
  if (s < 60) return `${Math.round(s)}s`;
  const m = Math.floor(s / 60);
  return `${m}m ${String(Math.round(s % 60)).padStart(2, "0")}s`;
}

/** "n of m claims" for the badge, read from the guide so it matches what the reader sees below. */
export function verifiedClaims(guide: Guide): { n: number; total: number } {
  const v = guide.verification_summary;
  return { n: v.tested + v.docs_verified + v.docs_hidden, total: v.total };
}

export type SourceKind = "official" | "composio" | "community" | "observation" | "other";

export const SOURCE_KIND_LABEL: Record<SourceKind, string> = {
  official: "Official docs",
  composio: "Composio docs",
  community: "Community",
  observation: "Our observation",
  other: "Other",
};

const COMMUNITY_HOSTS = /(reddit|stackoverflow|stackexchange|medium|dev\.to|hashnode|news\.ycombinator|quora|discourse|forum|community|github\.com\/.+\/issues)/i;
const OFFICIAL_HINT = /^(docs?|developers?|developer|dev|api|support|help|learn|apidocs)\./i;

export function hostOf(url: string): string {
  try {
    return new URL(url).hostname.replace(/^www\./, "");
  } catch {
    return url;
  }
}

/** The stream carries only url and title, so source kind is inferred; the guide's own list has the exact kind. */
export function classifySource(url: string, title: string): SourceKind {
  if (/observation/i.test(title)) return "observation";
  const host = hostOf(url);
  if (/(^|\.)composio\.dev$/i.test(host)) return "composio";
  if (COMMUNITY_HOSTS.test(url)) return "community";
  if (OFFICIAL_HINT.test(host) || /\/(docs?|developers?|api)\b/i.test(url)) return "official";
  return "other";
}
