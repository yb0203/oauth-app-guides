// Dev-only: start times of mock runs, shared by dev-generate and dev-runs.
export const devRuns: Map<string, number> = ((globalThis as unknown as { __devRuns?: Map<string, number> }).__devRuns ??= new Map());
