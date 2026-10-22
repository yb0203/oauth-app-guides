"use client";

import { useEffect, useRef, useState } from "react";

/** Counts up to `value` over a short tween. Snaps straight to the value when the user prefers reduced motion. */
export function AnimatedNumber({ value, duration = 450 }: { value: number; duration?: number }) {
  const [shown, setShown] = useState(value);
  const from = useRef(value);

  useEffect(() => {
    const start = from.current;
    if (start === value) return;
    // Reduced motion: a zero-length tween lands on the final value in the first frame.
    const ms = window.matchMedia("(prefers-reduced-motion: reduce)").matches ? 0 : duration;
    const t0 = performance.now();
    let raf = 0;
    const tick = (t: number) => {
      const p = ms === 0 ? 1 : Math.min(1, (t - t0) / ms);
      const eased = 1 - Math.pow(1 - p, 3);
      const v = Math.round(start + (value - start) * eased);
      from.current = v;
      setShown(v);
      if (p < 1) raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [value, duration]);

  return <span className="tabular-nums">{shown}</span>;
}
