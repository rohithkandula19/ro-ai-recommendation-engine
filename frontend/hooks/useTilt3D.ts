"use client";

import { useCallback, useRef } from "react";

interface Options {
  max?: number;
  scale?: number;
  perspective?: number;
  disabled?: boolean;
}

export function useTilt3D<T extends HTMLElement>({ max = 8, scale = 1.03, perspective = 1000, disabled }: Options = {}) {
  const ref = useRef<T | null>(null);
  const rafRef = useRef<number | null>(null);

  const onMove = useCallback((e: React.PointerEvent<T>) => {
    if (disabled) return;
    const el = ref.current;
    if (!el) return;
    const rect = el.getBoundingClientRect();
    const mx = e.clientX - rect.left;
    const my = e.clientY - rect.top;
    const px = mx / rect.width;
    const py = my / rect.height;
    const rx = (py - 0.5) * -2 * max;
    const ry = (px - 0.5) * 2 * max;
    if (rafRef.current) cancelAnimationFrame(rafRef.current);
    rafRef.current = requestAnimationFrame(() => {
      el.style.transform = `perspective(${perspective}px) rotateX(${rx}deg) rotateY(${ry}deg) scale(${scale})`;
      el.style.setProperty("--mx", `${mx}px`);
      el.style.setProperty("--my", `${my}px`);
    });
  }, [max, scale, perspective, disabled]);

  const onLeave = useCallback(() => {
    const el = ref.current;
    if (!el) return;
    if (rafRef.current) cancelAnimationFrame(rafRef.current);
    el.style.transform = "";
  }, []);

  return { ref, onPointerMove: onMove, onPointerLeave: onLeave, onPointerCancel: onLeave };
}
