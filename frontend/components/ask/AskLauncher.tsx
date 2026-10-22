"use client";

import { useEffect, useState } from "react";
import { MessageSquareTextIcon } from "lucide-react";
import { Sheet, SheetContent, SheetTitle } from "@/components/ui/sheet";
import { AskPanel } from "./AskPanel";
import type { AskState } from "./useAsk";

/** Below xl: a floating button that opens the same panel in a bottom sheet. The state lives in `ask`, above the sheet. */
export function AskLauncher({ ask }: { ask: AskState }) {
  const [open, setOpen] = useState(false);

  // The docked column takes over at xl, so close the sheet if the window grows past it.
  useEffect(() => {
    const mq = window.matchMedia("(min-width: 1280px)");
    const onChange = () => mq.matches && setOpen(false);
    mq.addEventListener("change", onChange);
    return () => mq.removeEventListener("change", onChange);
  }, []);

  return (
    <div className="print:hidden xl:hidden">
      <button
        type="button"
        onClick={() => setOpen(true)}
        className="fixed right-4 bottom-4 z-40 inline-flex h-10 cursor-pointer items-center gap-2 rounded-full bg-brand px-4 text-sm font-medium text-background shadow-lg transition-opacity outline-none hover:opacity-90 focus-visible:ring-3 focus-visible:ring-ring/50"
      >
        <MessageSquareTextIcon className="size-4" />
        Ask this guide
        {ask.messages.length > 0 && <span className="size-1.5 rounded-full bg-background/80" aria-hidden />}
      </button>
      <Sheet open={open} onOpenChange={setOpen}>
        <SheetContent side="bottom" className="h-[85dvh] gap-0 rounded-t-2xl p-0">
          <SheetTitle className="sr-only">Ask this guide</SheetTitle>
          <AskPanel ask={ask} inSheet />
        </SheetContent>
      </Sheet>
    </div>
  );
}
