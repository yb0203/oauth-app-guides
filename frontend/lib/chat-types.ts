import type { UIMessage } from "ai";
import {
  STAGE_ORDER,
  type GuideDataPart,
  type StageData,
  type StageId,
  type VerificationProgress,
  type WallProbe,
} from "@/types/guide";

/** The typed message for the generation stream (CONTRACT section 4). */
export type GenerateMessage = UIMessage<
  never,
  {
    stage: StageData;
    wall: WallProbe;
    verification: VerificationProgress;
    guide: GuideDataPart;
  }
>;

export interface NarrationLine {
  id: string;
  text: string;
  streaming: boolean;
}

export interface RunSource {
  sourceId: string;
  url: string;
  title: string;
}

/** Everything the page renders, folded out of the message parts. */
export interface RunSnapshot {
  stages: Partial<Record<StageId, StageData>>;
  narration: NarrationLine[];
  sources: RunSource[];
  wall: WallProbe | null;
  verification: VerificationProgress | null;
  guide: GuideDataPart | null;
}

const isStageId = (s: string): s is StageId => (STAGE_ORDER as readonly string[]).includes(s);

/**
 * Fold message parts into a render snapshot. Data parts that share an id are
 * already reconciled by the client; this also de-duplicates defensively
 * (last write wins for stages, first write wins for sources).
 */
export function deriveRun(messages: GenerateMessage[]): RunSnapshot {
  const snap: RunSnapshot = {
    stages: {},
    narration: [],
    sources: [],
    wall: null,
    verification: null,
    guide: null,
  };
  const seenSources = new Set<string>();

  for (const m of messages) {
    if (m.role !== "assistant") continue;
    m.parts.forEach((p, i) => {
      switch (p.type) {
        case "data-stage":
          if (p.data && isStageId(p.data.stage)) snap.stages[p.data.stage] = p.data;
          break;
        case "data-wall":
          snap.wall = p.data;
          break;
        case "data-verification":
          snap.verification = p.data;
          break;
        case "data-guide":
          if (p.data?.guide) snap.guide = p.data;
          break;
        case "source-url":
          if (!seenSources.has(p.sourceId)) {
            seenSources.add(p.sourceId);
            snap.sources.push({ sourceId: p.sourceId, url: p.url, title: p.title || p.url });
          }
          break;
        case "text": {
          const text = p.text.trim();
          if (text) snap.narration.push({ id: `${m.id}:${i}`, text, streaming: p.state === "streaming" });
          break;
        }
      }
    });
  }
  return snap;
}

export const STAGE_DEFAULT_LABEL: Record<StageId, string> = {
  resolve: "Resolve the app",
  find_docs: "Find official docs",
  research: "Read docs and community reports",
  probe: "Probe the developer console",
  synthesize: "Draft the guide",
  verify: "Verify every claim",
  publish: "Publish",
};

export const STAGE_SHORT_NAME: Record<StageId, string> = {
  resolve: "Resolve",
  find_docs: "Find docs",
  research: "Research",
  probe: "Probe",
  synthesize: "Synthesize",
  verify: "Verify",
  publish: "Publish",
};
