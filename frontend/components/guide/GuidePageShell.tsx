"use client";

import { AskLauncher } from "@/components/ask/AskLauncher";
import { AskPanel } from "@/components/ask/AskPanel";
import { useAsk } from "@/components/ask/useAsk";
import type { Answers } from "@/components/guide/situation";
import { SituationProvider } from "@/components/guide/situation";
import { GuideView } from "@/components/guide/GuideView";
import type { Guide } from "@/types/guide";

function Shell({ guide }: { guide: Guide }) {
  const ask = useAsk(guide);
  return (
    <div className="mx-auto w-full max-w-[1200px] px-4 sm:px-6 xl:flex xl:items-start xl:gap-10 print:block print:max-w-none print:p-0">
      <div className="min-w-0 flex-1 pt-8 pb-24 xl:pb-12 print:p-0">
        <div className="max-w-[760px]">
          <GuideView guide={guide} />
        </div>
      </div>
      <aside className="hidden w-[380px] shrink-0 xl:sticky xl:top-16 xl:mt-8 xl:block print:hidden">
        <div className="h-[calc(100vh-6rem)] overflow-hidden rounded-xl border bg-card shadow-xs">
          <AskPanel ask={ask} />
        </div>
      </aside>
      <AskLauncher ask={ask} />
    </div>
  );
}

export function GuidePageShell({ guide, initialAnswers }: { guide: Guide; initialAnswers?: Answers }) {
  return (
    <SituationProvider guide={guide} initialAnswers={initialAnswers} syncUrl>
      <Shell guide={guide} />
    </SituationProvider>
  );
}
