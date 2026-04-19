"use client";

import { useEffect, useState } from "react";
import en from "@/i18n/messages/en.json";
import es from "@/i18n/messages/es.json";
import fr from "@/i18n/messages/fr.json";

const BUNDLES: Record<string, any> = { en, es, fr };

/** Lightweight i18n — no next-intl dep, just JSON bundles per locale. */
export function useT() {
  const [locale, setLocale] = useState<"en" | "es" | "fr">("en");

  useEffect(() => {
    if (typeof window === "undefined") return;
    const stored = (localStorage.getItem("ro-locale") || navigator.language.slice(0, 2)) as any;
    if (BUNDLES[stored]) setLocale(stored);
  }, []);

  function t(path: string): string {
    const keys = path.split(".");
    let cur: any = BUNDLES[locale];
    for (const k of keys) cur = cur?.[k];
    return typeof cur === "string" ? cur : path;
  }

  function setLang(l: "en" | "es" | "fr") {
    setLocale(l);
    localStorage.setItem("ro-locale", l);
  }

  return { t, locale, setLang, locales: Object.keys(BUNDLES) };
}
