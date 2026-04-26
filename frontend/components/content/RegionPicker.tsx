"use client";

import { REGIONS, useRegion } from "@/lib/region";

export function RegionPicker() {
  const { region, setRegion } = useRegion();
  const current = REGIONS.find((r) => r.code === region) ?? REGIONS[0];
  return (
    <label className="inline-flex items-center gap-2 text-xs text-white/60">
      <span>Region</span>
      <div className="relative">
        <select
          value={region}
          onChange={(e) => setRegion(e.target.value)}
          className="appearance-none rounded-md bg-white/10 ring-1 ring-white/15 px-2.5 py-1 pr-7 text-sm text-white/90 hover:bg-white/15 focus:outline-none focus:ring-2 focus:ring-brand cursor-pointer"
        >
          {REGIONS.map((r) => (
            <option key={r.code} value={r.code} className="bg-[#14141a]">
              {r.flag} {r.label}
            </option>
          ))}
        </select>
        <span className="pointer-events-none absolute right-1.5 top-1/2 -translate-y-1/2 text-white/50 text-xs">▾</span>
      </div>
      <span className="text-base">{current.flag}</span>
    </label>
  );
}
