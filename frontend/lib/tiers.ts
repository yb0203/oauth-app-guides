import type { Tier } from "@/types/guide";

// Semantic tokens live in app/globals.css (light + dark). Ladder order = difficulty.
export const TIER_LADDER: Tier[] = ["instant", "verify_to_scale", "review_required", "partner_only"];

// Colour of each ladder segment, by position (easy two = success, review = warning, partner only = danger).
export const TIER_LADDER_BG = ["bg-success", "bg-success", "bg-warning", "bg-danger"] as const;

export const TIER_META: Record<Tier, { label: string; short: string; hint: string; classes: string; dot: string; bar: string; text: string }> = {
  instant: {
    label: "Instant",
    short: "Instant",
    hint: "Self-serve, works immediately",
    classes: "bg-success-soft text-success border-success-border",
    dot: "bg-success",
    bar: "bg-success",
    text: "text-success",
  },
  verify_to_scale: {
    label: "Verify to scale",
    short: "Verify to scale",
    hint: "Works now; verification needed past a threshold",
    classes: "bg-success-soft text-success border-success-border",
    dot: "bg-success",
    bar: "bg-success",
    text: "text-success",
  },
  review_required: {
    label: "Review required",
    short: "Review",
    hint: "Provider review before it works for other users",
    classes: "bg-warning-soft text-warning border-warning-border",
    dot: "bg-warning",
    bar: "bg-warning",
    text: "text-warning",
  },
  partner_only: {
    label: "Partner only",
    short: "Partner only",
    hint: "Needs a partnership or approval program",
    classes: "bg-danger-soft text-danger border-danger-border",
    dot: "bg-danger",
    bar: "bg-danger",
    text: "text-danger",
  },
  unknown: {
    label: "Unknown",
    short: "Unknown",
    hint: "Not enough evidence to say",
    classes: "bg-muted text-muted-foreground border-border",
    dot: "bg-muted-foreground",
    bar: "bg-muted-foreground",
    text: "text-muted-foreground",
  },
};

export const tierMeta = (t: string | null | undefined) => TIER_META[(t as Tier) in TIER_META ? (t as Tier) : "unknown"];
