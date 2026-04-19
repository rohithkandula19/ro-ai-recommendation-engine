"use client";

import { useT } from "@/hooks/useT";

export function LocaleSwitcher() {
  const { locale, setLang, locales } = useT();
  return (
    <select value={locale} onChange={(e) => setLang(e.target.value as any)}
      aria-label="language"
      className="bg-transparent text-xs text-white/70 focus:outline-none cursor-pointer">
      {locales.map((l) => <option key={l} value={l} className="bg-black">{l.toUpperCase()}</option>)}
    </select>
  );
}
