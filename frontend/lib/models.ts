import { API_URL, USE_MOCK } from "@/lib/api";

// Model choice and run settings for generation (CONTRACT section 3: GET /api/models, POST /api/generate `config`).

export interface ModelInfo {
  id: string;
  label: string;
  free: boolean;
  /** tokens, when the backend says */
  contextLength: number | null;
  notes: string | null;
  recommended: boolean;
  /** false = the backend could not call it at last check: shown disabled, sorted last */
  available: boolean;
}

export interface ModelsInfo {
  models: ModelInfo[];
  defaultModel: string | null;
  pageOptions: number[];
}

export interface GenConfig {
  /** undefined = let the backend pick its default */
  model?: string;
  /** docs depth: how many pages the agent reads */
  pages: number;
  probe: boolean;
}

export const DEFAULT_PAGES = 5;
export const DEFAULT_PAGE_OPTIONS = [3, 5, 8];
export const DEFAULT_CONFIG: GenConfig = { pages: DEFAULT_PAGES, probe: true };

const MOCK_MODELS: ModelsInfo = {
  defaultModel: "meta-llama/llama-3.3-70b-instruct:free",
  pageOptions: DEFAULT_PAGE_OPTIONS,
  models: [
    { id: "meta-llama/llama-3.3-70b-instruct:free", label: "Llama 3.3 70B Instruct", free: true, contextLength: 131072, notes: "best balance", recommended: true, available: true },
    { id: "google/gemma-3-27b-it:free", label: "Gemma 3 27B", free: true, contextLength: 96000, notes: "fastest", recommended: false, available: true },
    { id: "deepseek/deepseek-r1:free", label: "DeepSeek R1", free: true, contextLength: 163840, notes: "slower, reasons more", recommended: false, available: true },
  ],
};

const str = (v: unknown): string | null => (typeof v === "string" && v ? v : null);
const num = (v: unknown): number | null => (typeof v === "number" && Number.isFinite(v) ? v : null);

/** Tolerant of an array or {models, default, options}; ignores anything it can't read. */
export function normalizeModels(json: unknown): ModelsInfo | null {
  const obj = (json && typeof json === "object" ? json : {}) as Record<string, unknown>;
  const list = Array.isArray(json) ? json : Array.isArray(obj.models) ? obj.models : null;
  if (!list) return null;
  const defaultId = str(obj.default) ?? str(obj.default_model) ?? str(obj.defaultModel);
  const models: ModelInfo[] = [];
  for (const raw of list) {
    if (typeof raw === "string") {
      models.push({ id: raw, label: raw.replace(/:free$/, ""), free: /:free$/.test(raw), contextLength: null, notes: null, recommended: raw === defaultId, available: true });
      continue;
    }
    const m = (raw ?? {}) as Record<string, unknown>;
    const id = str(m.id);
    if (!id) continue;
    models.push({
      id,
      label: str(m.label) ?? str(m.name) ?? id,
      free: typeof m.free === "boolean" ? m.free : /:free$/.test(id),
      contextLength: num(m.context_length) ?? num(m.contextLength) ?? num(m.context),
      notes: str(m.notes) ?? str(m.note) ?? str(m.hint),
      recommended: m.recommended === true || id === defaultId,
      available: m.tested !== false,
    });
  }
  if (models.length === 0) return null;
  const opts = (obj.options ?? {}) as Record<string, unknown>;
  // options.max_pages is {default, choices:[…]} (CONTRACT section 3); an array of numbers is accepted too.
  const mp = opts.max_pages as unknown;
  const rawChoices = Array.isArray(mp) ? mp : mp && typeof mp === "object" && Array.isArray((mp as { choices?: unknown }).choices) ? (mp as { choices: unknown[] }).choices : [];
  const pages = rawChoices.filter((n): n is number => typeof n === "number");
  const usable = models.filter((m) => m.available);
  const defaultModel =
    defaultId && usable.some((m) => m.id === defaultId) ? defaultId : (usable.find((m) => m.recommended)?.id ?? usable[0]?.id ?? models[0].id);
  // recommended default first, unavailable models last (Array.sort is stable)
  const rank = (m: ModelInfo) => (m.id === defaultModel ? 0 : m.available ? 1 : 2);
  models.sort((a, b) => rank(a) - rank(b));
  return { models, defaultModel, pageOptions: pages.length ? pages : DEFAULT_PAGE_OPTIONS };
}

/** null when the backend has no /api/models (older backend): the model picker is then hidden. */
export async function getModels(): Promise<ModelsInfo | null> {
  try {
    const res = await fetch(`${API_URL}/api/models`, { cache: "no-store" });
    if (res.ok) return normalizeModels(await res.json());
  } catch {
    /* fall through */
  }
  return USE_MOCK ? MOCK_MODELS : null;
}

const first = (v: string | string[] | undefined) => (Array.isArray(v) ? v[0] : v);

/** ?model=…&pages=5&probe=1 (probe=0 turns it off). Missing values mean defaults. */
export function parseConfig(sp: Record<string, string | string[] | undefined>): GenConfig {
  const pages = Number(first(sp.pages));
  const probe = first(sp.probe);
  return {
    model: first(sp.model)?.trim() || undefined,
    pages: Number.isInteger(pages) && pages >= 1 && pages <= 20 ? pages : DEFAULT_PAGES,
    probe: probe === undefined ? true : !/^(0|false|off|no)$/i.test(probe),
  };
}

export function configToQuery(c: GenConfig): Record<string, string> {
  const q: Record<string, string> = {};
  if (c.model) q.model = c.model;
  q.pages = String(c.pages);
  q.probe = c.probe ? "1" : "0";
  return q;
}

export function configToBody(c: GenConfig) {
  return { ...(c.model ? { model: c.model } : {}), max_pages: c.pages, probe_console: c.probe };
}

export const sameConfig = (a: GenConfig, b: GenConfig) => a.model === b.model && a.pages === b.pages && a.probe === b.probe;

export function formatContext(n: number | null): string | null {
  if (!n) return null;
  return n >= 1000 ? `${Math.round(n / 1000)}k context` : `${n} context`;
}

export function modelLabel(info: ModelsInfo | null, id: string | undefined): string {
  if (!id) return info?.defaultModel ? (info.models.find((m) => m.id === info.defaultModel)?.label ?? "Default model") : "Default model";
  return info?.models.find((m) => m.id === id)?.label ?? id;
}
