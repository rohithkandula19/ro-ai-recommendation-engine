"use client";

import { ChangeEvent } from "react";

interface Props {
  value: string;
  onChange: (v: string) => void;
  placeholder?: string;
}

export function SearchBar({ value, onChange, placeholder = "Search…" }: Props) {
  return (
    <input
      value={value}
      onChange={(e: ChangeEvent<HTMLInputElement>) => onChange(e.target.value)}
      placeholder={placeholder}
      className="w-full rounded-md bg-black/60 px-4 py-3 text-base outline-none ring-1 ring-white/10 focus:ring-white/30"
    />
  );
}
