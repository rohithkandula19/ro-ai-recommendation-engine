export interface ParsedCommand {
  cmd: string;
  args: string;
  raw: string;
}

export const SLASH_COMMANDS: { cmd: string; hint: string; desc: string }[] = [
  { cmd: "/decisive", hint: "context", desc: "Just pick one for me." },
  { cmd: "/surprise", hint: "", desc: "Random high-match pick." },
  { cmd: "/mood", hint: "tense|chill|light|thoughtful", desc: "Bias recs toward a mood." },
  { cmd: "/stats", hint: "", desc: "Describe my taste DNA." },
  { cmd: "/new", hint: "", desc: "Start a fresh thread." },
  { cmd: "/export", hint: "", desc: "Download this conversation as markdown." },
  { cmd: "/clear", hint: "", desc: "Wipe chat memory." },
];

export function parseSlash(input: string): ParsedCommand | null {
  const m = input.match(/^\s*(\/[a-zA-Z]+)\b\s*(.*)$/);
  if (!m) return null;
  return { cmd: m[1].toLowerCase(), args: m[2].trim(), raw: input };
}
