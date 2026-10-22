"use client";

import { useState } from "react";
import { Eyebrow } from "@/components/guide/shared";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { configToQuery, type GenConfig, type ModelsInfo } from "@/lib/models";
import { SettingsPopover } from "./SettingsPopover";

/** Shown when /generate is opened without ?app=. A plain GET form (settings ride along as hidden fields), so it works without JS. */
export function TargetForm({ models, initialConfig }: { models: ModelsInfo | null; initialConfig: GenConfig }) {
  const [config, setConfig] = useState(initialConfig);
  return (
    <div className="mx-auto w-full max-w-xl px-4 py-12">
      <Eyebrow>Live generation</Eyebrow>
      <h1 className="mt-1 text-2xl font-semibold tracking-tight">Which app do you want a guide for?</h1>
      <p className="mt-1.5 text-sm text-muted-foreground">
        Enter an app name or its developer docs URL. The agent will research it live and show its work.
      </p>
      <form action="/generate" method="get" className="mt-5">
        <div className="flex gap-2">
          <label htmlFor="app" className="sr-only">
            App name or URL
          </label>
          <Input id="app" name="app" required autoFocus placeholder="Xero, or https://developer.xero.com" />
          <Button type="submit">Generate</Button>
        </div>
        {Object.entries(configToQuery(config)).map(([k, v]) => (
          <input key={k} type="hidden" name={k} value={v} />
        ))}
        <div className="mt-2.5">
          <SettingsPopover value={config} onChange={setConfig} models={models} />
        </div>
      </form>
    </div>
  );
}
