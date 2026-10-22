import { Loader2Icon } from "lucide-react";
import type { RunStatus } from "./useRunRecovery";
import { STAGE_SHORT_NAME } from "@/lib/chat-types";
import type { StageId } from "@/types/guide";

/** Calm, honest notice while the stream is silent and the client is asking the server how the run is doing. */
export function RecoveryNotice({ status, canPoll }: { status: RunStatus | null; canPoll: boolean }) {
  const stage = status?.stage && status.stage in STAGE_SHORT_NAME ? STAGE_SHORT_NAME[status.stage as StageId].toLowerCase() : status?.stage;
  return (
    <div role="status" className="mt-4 flex items-start gap-2.5 rounded-xl border border-info-border bg-info-soft px-4 py-3 text-sm text-info print:hidden">
      <Loader2Icon className="mt-0.5 size-4 shrink-0 animate-spin motion-reduce:animate-none" aria-hidden />
      <div className="min-w-0">
        <p className="font-semibold">Connection went quiet. {canPoll ? "Checking on the run…" : "Waiting for the run to start…"}</p>
        <p className="mt-0.5 text-info/85">
          {canPoll
            ? status
              ? `The server says the run is ${status.status}${stage ? ` (${stage})` : ""}. It keeps working even when the live view drops, and the guide will appear here when it is published.`
              : "The run keeps going on the server even when the live view drops. Asking it for an update every few seconds."
            : "Nothing has arrived from the server yet. You can stop and retry if this lasts."}
        </p>
      </div>
    </div>
  );
}
