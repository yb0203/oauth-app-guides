"use client";

import { Eyebrow } from "@/components/guide/shared";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

/** Shown when /generate is opened without ?app=. A plain GET form, so it works without JS. */
export function TargetForm() {
  return (
    <div className="mx-auto w-full max-w-xl px-4 py-12">
      <Eyebrow>Live generation</Eyebrow>
      <h1 className="mt-1 text-2xl font-semibold tracking-tight">Which app do you want a guide for?</h1>
      <p className="mt-1.5 text-sm text-muted-foreground">
        Enter an app name or its developer docs URL. The agent will research it live and show its work.
      </p>
      <form action="/generate" method="get" className="mt-5 flex gap-2">
        <label htmlFor="app" className="sr-only">
          App name or URL
        </label>
        <Input id="app" name="app" required autoFocus placeholder="Xero, or https://developer.xero.com" />
        <Button type="submit">Generate</Button>
      </form>
    </div>
  );
}
