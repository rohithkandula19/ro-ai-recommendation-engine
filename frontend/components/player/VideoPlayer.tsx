"use client";

import { useEffect, useRef, useState } from "react";
import { PlayerControls } from "./PlayerControls";
import { useEventTracker } from "@/hooks/useEventTracker";

interface Props {
  contentId: string;
  src: string;
  poster?: string;
}

export function VideoPlayer({ contentId, src, poster }: Props) {
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const containerRef = useRef<HTMLDivElement | null>(null);
  const [playing, setPlaying] = useState(false);
  const [progress, setProgress] = useState(0);
  const [duration, setDuration] = useState(0);
  const [volume, setVolume] = useState(1);
  const lastReportedProgress = useRef<number>(-1);
  const { track } = useEventTracker();

  useEffect(() => {
    const v = videoRef.current;
    if (!v) return;

    function onTime() {
      if (!v) return;
      setProgress(v.currentTime);
      if (v.duration > 0) {
        const pct = v.currentTime / v.duration;
        const bucket = Math.floor(pct * 10);
        if (bucket > lastReportedProgress.current && bucket < 10) {
          lastReportedProgress.current = bucket;
          track("progress", contentId, pct);
        }
      }
    }

    function onMeta() { if (v) setDuration(v.duration || 0); }
    function onPlay() { setPlaying(true); track("play", contentId); }
    function onPause() { setPlaying(false); track("pause", contentId, v?.currentTime); }
    function onEnded() { setPlaying(false); track("complete", contentId, 1); }

    v.addEventListener("timeupdate", onTime);
    v.addEventListener("loadedmetadata", onMeta);
    v.addEventListener("play", onPlay);
    v.addEventListener("pause", onPause);
    v.addEventListener("ended", onEnded);
    return () => {
      v.removeEventListener("timeupdate", onTime);
      v.removeEventListener("loadedmetadata", onMeta);
      v.removeEventListener("play", onPlay);
      v.removeEventListener("pause", onPause);
      v.removeEventListener("ended", onEnded);
    };
  }, [contentId, track]);

  function toggle() {
    const v = videoRef.current;
    if (!v) return;
    if (v.paused) v.play(); else v.pause();
  }

  function seek(t: number) { if (videoRef.current) videoRef.current.currentTime = t; }
  function setVol(v: number) {
    setVolume(v);
    if (videoRef.current) videoRef.current.volume = v;
  }
  function fullscreen() {
    const el = containerRef.current;
    if (!el) return;
    if (document.fullscreenElement) document.exitFullscreen();
    else el.requestFullscreen();
  }

  return (
    <div ref={containerRef} className="relative bg-black aspect-video w-full">
      <video
        ref={videoRef}
        src={src}
        poster={poster}
        className="h-full w-full"
        onClick={toggle}
        playsInline
      />
      <PlayerControls
        playing={playing} progress={progress} duration={duration} volume={volume}
        onTogglePlay={toggle} onSeek={seek} onVolume={setVol} onFullscreen={fullscreen}
      />
    </div>
  );
}
