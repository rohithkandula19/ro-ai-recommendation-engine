"use client";

import { useEffect, useState } from "react";

export const REGIONS: { code: string; label: string; flag: string }[] = [
  { code: "US", label: "United States", flag: "🇺🇸" },
  { code: "GB", label: "United Kingdom", flag: "🇬🇧" },
  { code: "CA", label: "Canada", flag: "🇨🇦" },
  { code: "AU", label: "Australia", flag: "🇦🇺" },
  { code: "IN", label: "India", flag: "🇮🇳" },
  { code: "DE", label: "Germany", flag: "🇩🇪" },
  { code: "FR", label: "France", flag: "🇫🇷" },
  { code: "JP", label: "Japan", flag: "🇯🇵" },
];

const KEY = "ro:region";

export function useRegion() {
  const [region, setRegion] = useState("US");
  useEffect(() => {
    const stored = typeof window !== "undefined" ? window.localStorage.getItem(KEY) : null;
    if (stored) setRegion(stored);
  }, []);
  function update(code: string) {
    setRegion(code);
    try { window.localStorage.setItem(KEY, code); } catch {}
  }
  return { region, setRegion: update };
}
