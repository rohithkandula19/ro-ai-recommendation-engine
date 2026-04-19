"use client";

import { useTheme } from "@/hooks/useTheme";

export function ThemeToggle() {
  const { theme, toggle } = useTheme();
  return (
    <button onClick={toggle} aria-label="toggle theme"
      className="text-white/60 hover:text-white text-sm px-2">
      {theme === "dark" ? "☀️" : "🌙"}
    </button>
  );
}
