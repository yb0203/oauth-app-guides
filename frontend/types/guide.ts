// Mirrors data/schema/guide.schema.json (schema_version "1"). Keep in sync; the schema is the source of truth.

export type Tier = "instant" | "verify_to_scale" | "review_required" | "partner_only" | "unknown";
export type EvidenceLabel = "TESTED" | "DOCS" | "COMMUNITY" | "UNCERTAIN";
export type FoundIn = "visible" | "hidden_section" | null;

export interface Evidence {
  label: EvidenceLabel;
  source_id: string | null;
  quote: string | null;
  found_in: FoundIn;
  note: string | null;
}

export interface Fact {
  text: string;
  evidence: Evidence;
}

export interface Verdict {
  tier: Tier;
  summary: string;
  effort_hours: { min: number; max: number };
  calendar: { min_days: number; max_days: number | null; label: string };
  calendar_basis: "official" | "community" | "estimate";
  confidence: "high" | "medium" | "low";
}

export interface SituationOption {
  id: string;
  label: string;
}
export interface SituationQuestion {
  id: string;
  text: string;
  options: SituationOption[];
}
export interface SituationVariant {
  when: Record<string, string>;
  tier: Tier;
  summary: string;
  calendar_label: string;
  notes: string[];
}

export interface Limit {
  what: string;
  value: number | null;
  unit: string;
  scope: string;
  evidence: Evidence;
}

export type StepActor = "agent" | "human" | "either";
export type HumanReason =
  | "credential"
  | "legal_acceptance"
  | "payment"
  | "identity"
  | "real_account"
  | "submit"
  | "wait";

export interface Step {
  n: number;
  title: string;
  detail: string;
  actor: StepActor;
  human_reason: HumanReason | null;
  irreversible: boolean;
  values: { label: string; value: string }[];
  evidence: Evidence;
}

export interface Review {
  required: "yes" | "no" | "conditional";
  trigger: string | null;
  submit: string[];
  reviewer: string | null;
  wait_official: string | null;
  wait_community: string | null;
  cost: string | null;
  evidence: Evidence[];
}

export interface Blocker {
  symptom: string;
  cause: string;
  fix: string;
  evidence: Evidence;
}

export interface PreparedScope {
  scope: string;
  why: string;
  review_class: "none" | "sensitive" | "restricted" | "unknown";
}
export interface Prepared {
  scopes: PreparedScope[];
  privacy_policy_outline: string[];
  consent_screen: Record<string, string>;
  review_text: string | null;
}

export interface WallProbe {
  console_url: string;
  final_url: string;
  redirect_chain: string[];
  outcome: "login_wall" | "console_reachable" | "blocked" | "error";
  wall_host: string | null;
  asks_for: string;
  bot_check: boolean;
  method: "http" | "browser";
  observed_at: string;
}

export interface Conflict {
  field: string;
  description: string;
  evidence: Evidence[];
}

export interface Source {
  id: string;
  url: string;
  title: string;
  accessed: string;
  kind: "official_docs" | "composio_docs" | "community" | "observation";
}

export interface VerificationSummary {
  total: number;
  tested: number;
  docs_verified: number;
  docs_hidden: number;
  community: number;
  uncertain: number;
}

export interface Guide {
  schema_version: "1";
  slug: string;
  app_name: string;
  guide_type: "curated" | "generated";
  last_verified: string;
  composio: {
    toolkit_slug: string | null;
    status: "managed" | "byo" | "not_in_catalog";
    callback_url: string;
    callback_note: string;
  };
  verdict: Verdict;
  situations: { questions: SituationQuestion[]; variants: SituationVariant[] };
  byo_advice: string | null;
  before_you_start: Fact[];
  limits: Limit[];
  steps: Step[];
  review: Review;
  customer_gates: Fact[];
  gotchas: Fact[];
  blockers: Blocker[];
  prepared: Prepared;
  open_questions: string[];
  wall_probe: WallProbe | null;
  conflicts: Conflict[];
  sources: Source[];
  verification_summary: VerificationSummary;
}

// ---- API shapes (CONTRACT §3) ----
export interface CatalogEntry {
  slug: string;
  name: string;
  composio_status: "managed" | "byo" | "not_in_catalog" | string;
  tier_guess: Tier | string | null;
  has_guide: boolean;
  /** verified tier from the guide, when one exists */
  tier?: Tier | null;
  /** slug of the guide to open (can differ from the catalog slug, e.g. gmail → google-gmail) */
  guide_slug?: string | null;
}

export interface GuideListEntry {
  slug: string;
  app_name: string;
  guide_type: "curated" | "generated";
  tier: Tier;
  last_verified: string;
}

// ---- Generation stream (CONTRACT §4) ----
export const STAGE_ORDER = [
  "resolve",
  "find_docs",
  "research",
  "probe",
  "synthesize",
  "verify",
  "publish",
] as const;
export type StageId = (typeof STAGE_ORDER)[number];

export interface StageData {
  stage: StageId;
  status: "running" | "done" | "error" | "skipped";
  label: string;
  detail?: string;
  counts?: Record<string, number>;
}

export interface VerificationProgress {
  checked: number;
  docs_verified: number;
  hidden: number;
  downgraded: number;
  total: number;
}

export interface GuideDataPart {
  slug: string;
  permalink: string;
  guide: Guide;
}
