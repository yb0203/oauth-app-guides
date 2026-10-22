import { FlaskConicalIcon } from "lucide-react";

/**
 * Shown for the whole run whenever the backend says the stream is a recorded replay (fake mode).
 * The recording is always GitHub's, whatever was typed, so nothing below may read as research for `app`.
 */
export function ReplayBanner({ app }: { app: string }) {
  return (
    <section
      aria-label="Demo replay notice"
      className="mt-4 flex items-start gap-3 rounded-xl border border-warning-border bg-warning-soft px-4 py-3 text-warning"
    >
      <FlaskConicalIcon className="mt-0.5 size-4 shrink-0" aria-hidden />
      <div className="min-w-0 text-sm">
        <p className="font-semibold">Demo replay: recorded GitHub run, not research for {app}</p>
        <p className="mt-0.5 text-warning/85">
          This environment is not calling the live agent, so every stage, source, console probe and claim below is a
          recording of the GitHub run. None of it is evidence about {app}.
        </p>
      </div>
    </section>
  );
}
