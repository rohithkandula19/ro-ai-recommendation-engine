import type { ReactNode } from "react";
import { createElement, Fragment } from "react";

// Tiny markdown: **bold**, *italic*, `code`, [text](url), and auto-link bare URLs.
// Zero deps. Streams safely — trailing unmatched markers just render literally.
export function renderMarkdown(src: string): ReactNode {
  if (!src) return null;

  const lines = src.split(/\n/);
  return createElement(
    Fragment,
    null,
    ...lines.map((line, i) =>
      createElement(
        Fragment,
        { key: i },
        ...renderInline(line),
        i < lines.length - 1 ? createElement("br", { key: `br-${i}` }) : null,
      ),
    ),
  );
}

function renderInline(text: string): ReactNode[] {
  const parts: ReactNode[] = [];
  let rest = text;
  let key = 0;
  const patterns: { re: RegExp; render: (m: RegExpExecArray) => ReactNode }[] = [
    { re: /\[([^\]]+)\]\((https?:\/\/[^\s)]+)\)/, render: (m) => createElement("a", { key: key++, href: m[2], target: "_blank", rel: "noreferrer noopener", className: "text-brand underline hover:text-brand-dark" }, m[1]) },
    { re: /\*\*([^*]+)\*\*/, render: (m) => createElement("strong", { key: key++, className: "font-bold text-white" }, m[1]) },
    { re: /(^|[^*])\*([^*]+)\*/, render: (m) => createElement(Fragment, { key: key++ }, m[1], createElement("em", { key: key++, className: "italic text-white/90" }, m[2])) },
    { re: /`([^`]+)`/, render: (m) => createElement("code", { key: key++, className: "rounded bg-white/10 px-1.5 py-0.5 text-[0.9em] font-mono text-white/90" }, m[1]) },
    { re: /(https?:\/\/[^\s<)]+)/, render: (m) => createElement("a", { key: key++, href: m[1], target: "_blank", rel: "noreferrer noopener", className: "text-brand underline break-all" }, m[1]) },
  ];

  while (rest.length > 0) {
    let best: { idx: number; len: number; node: ReactNode; preface: string } | null = null;
    for (const p of patterns) {
      const m = p.re.exec(rest);
      if (!m) continue;
      const idx = m.index;
      if (!best || idx < best.idx) {
        best = { idx, len: m[0].length, node: p.render(m), preface: rest.slice(0, idx) };
      }
    }
    if (!best) {
      parts.push(rest);
      break;
    }
    if (best.preface) parts.push(best.preface);
    parts.push(best.node);
    rest = rest.slice(best.idx + best.len);
  }
  return parts;
}

export function extractCandidateTitles(text: string): string[] {
  const set = new Set<string>();
  const reItalic = /\*([^*]{2,60})\*/g;
  const reBold = /\*\*([^*]{2,60})\*\*/g;
  const reQuoted = /["“”]([^"“”]{2,60})["“”]/g;
  let m;
  while ((m = reItalic.exec(text))) set.add(m[1].trim());
  while ((m = reBold.exec(text))) set.add(m[1].trim());
  while ((m = reQuoted.exec(text))) set.add(m[1].trim());
  return Array.from(set).filter((t) => /[A-Za-z]/.test(t) && t.split(/\s+/).length <= 8);
}
