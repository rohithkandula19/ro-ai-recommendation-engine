"use client";

import { ChangeEvent } from "react";

interface Props {
  playing: boolean;
  progress: number;
  duration: number;
  volume: number;
  onTogglePlay: () => void;
  onSeek: (v: number) => void;
  onVolume: (v: number) => void;
  onFullscreen: () => void;
}

function fmt(s: number) {
  if (!isFinite(s) || s < 0) return "0:00";
  const m = Math.floor(s / 60);
  const sec = Math.floor(s % 60).toString().padStart(2, "0");
  return `${m}:${sec}`;
}

export function PlayerControls({
  playing, progress, duration, volume,
  onTogglePlay, onSeek, onVolume, onFullscreen,
}: Props) {
  return (
    <div className="absolute inset-x-0 bottom-0 bg-gradient-to-t from-black/90 to-transparent p-4">
      <input
        type="range" min={0} max={duration || 0} step={0.1}
        value={progress}
        onChange={(e: ChangeEvent<HTMLInputElement>) => onSeek(Number(e.target.value))}
        className="w-full accent-brand"
      />
      <div className="mt-2 flex items-center gap-4 text-sm">
        <button onClick={onTogglePlay} aria-label="play-pause" className="px-3 py-1 rounded bg-white/10 hover:bg-white/20">
          {playing ? "⏸" : "▶"}
        </button>
        <span>{fmt(progress)} / {fmt(duration)}</span>
        <label className="ml-auto flex items-center gap-2 text-xs">
          Vol
          <input type="range" min={0} max={1} step={0.05} value={volume}
            onChange={(e) => onVolume(Number(e.target.value))} className="accent-white" />
        </label>
        <button onClick={onFullscreen} className="px-3 py-1 rounded bg-white/10 hover:bg-white/20">⛶</button>
      </div>
    </div>
  );
}
