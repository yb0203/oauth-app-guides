import { Bot, Shuffle, User } from "lucide-react";
import { cn } from "cn";
import type { HumanReason, StepActor } from "@/types/guide";

/** Plain-words reason a human has to do the step. */
export const HUMAN_REASON: Record<HumanReason, string> = {
  credential: "sign in",
  legal_acceptance: "accept terms",
  payment: "payment",
  identity: "identity check",
  real_account: "real account",
  submit: "submit",
  wait: "wait",
};

const HUMAN_REASON_LONG: Record<HumanReason, string> = {
  credential: "needs your login or credentials",
  legal_acceptance: "needs you to accept legal terms",
  payment: "needs a payment method",
  identity: "needs an identity check",
  real_account: "needs your real account",
  submit: "needs you to submit it",
  wait: "is a waiting period",
};

/**
 * Who does this step. Distinct by shape and icon as well as colour:
 * solid dark = you, tinted + bot icon = agent, dashed outline = either.
 */
export function ActorBadge({ actor, reason, className }: { actor: StepActor; reason: HumanReason | null; className?: string }) {
  const base = "inline-flex items-center gap-1.5 rounded-md border px-2 py-1 text-xs leading-none font-medium whitespace-nowrap";
  if (actor === "human") {
    return (
      <span
        className={cn(base, "keep-bg border-foreground bg-foreground text-background", className)}
        title={reason ? `You: this step ${HUMAN_REASON_LONG[reason] ?? reason}` : "You have to do this step"}
      >
        <User className="size-3.5" aria-hidden />
        <span>You</span>
        {reason && (
          <>
            <span aria-hidden className="opacity-50">
              ·
            </span>
            <span className="font-normal">{HUMAN_REASON[reason] ?? reason}</span>
          </>
        )}
      </span>
    );
  }
  if (actor === "agent") {
    return (
      <span className={cn(base, "border-brand/30 bg-brand-soft text-brand", className)} title="An agent can prepare or do this step">
        <Bot className="size-3.5" aria-hidden />
        Agent prepared
      </span>
    );
  }
  return (
    <span
      className={cn(base, "border-dashed border-muted-foreground/70 bg-transparent text-foreground", className)}
      title="Either you or an agent can do this step"
    >
      <Shuffle className="size-3.5" aria-hidden />
      Either
    </span>
  );
}
