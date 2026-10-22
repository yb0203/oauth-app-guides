import type { CatalogEntry, Guide, GuideListEntry } from "@/types/guide";

export const API_URL = (process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000").replace(/\/$/, "");

// When NEXT_PUBLIC_USE_MOCK=1, generation streams from the in-app dev route instead of the backend.
export const USE_MOCK = process.env.NEXT_PUBLIC_USE_MOCK === "1";
export const GENERATE_URL = USE_MOCK ? "/api/dev-generate" : `${API_URL}/api/generate`;
/** Endpoint for the "Ask this guide" stream (CONTRACT section 4b). */
export const ASK_URL = (slug: string) =>
  USE_MOCK ? `/api/dev-ask/${encodeURIComponent(slug)}` : `${API_URL}/api/guides/${encodeURIComponent(slug)}/ask`;

async function getJson<T>(path: string): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, { cache: "no-store" });
  if (!res.ok) throw new Error(`${path} → ${res.status}`);
  return res.json() as Promise<T>;
}

// Mock mode falls back to fixtures when the backend is not running.
const MOCK_CATALOG: CatalogEntry[] = [
  { slug: "github", name: "GitHub", composio_status: "managed", tier_guess: "instant", has_guide: true, tier: "instant", guide_slug: "github" },
  { slug: "gmail", name: "Gmail", composio_status: "managed", tier_guess: "verify_to_scale", has_guide: true, tier: "review_required", guide_slug: "google-gmail" },
  { slug: "slack", name: "Slack", composio_status: "managed", tier_guess: "verify_to_scale", has_guide: false },
  { slug: "xero", name: "Xero", composio_status: "byo", tier_guess: "partner_only", has_guide: false },
];

export async function getCatalog(): Promise<CatalogEntry[]> {
  try {
    return await getJson<CatalogEntry[]>("/api/catalog");
  } catch (e) {
    if (USE_MOCK) return MOCK_CATALOG;
    throw e;
  }
}
export const getGuides = () => getJson<GuideListEntry[]>("/api/guides");

export async function getGuide(slug: string): Promise<Guide | null> {
  let res: Response;
  try {
    res = await fetch(`${API_URL}/api/guides/${encodeURIComponent(slug)}`, { cache: "no-store" });
  } catch (e) {
    if (USE_MOCK && slug === "github") return (await import("@/fixtures/github.json")).default as unknown as Guide;
    throw e;
  }
  if (res.status === 404) return null;
  if (!res.ok) throw new Error(`guide ${slug} → ${res.status}`);
  return res.json() as Promise<Guide>;
}

export const markdownUrl = (slug: string) => `${API_URL}/api/guides/${encodeURIComponent(slug)}/markdown`;
