"use client";

import { useCallback, useEffect, useRef, useState } from "react";

const STORAGE_KEY = "lds-sound";
const AUDIO_SRC = "/children.mp3";
const VOLUME = 0.32;

function VolumeOnIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" aria-hidden="true">
      <path d="M11 5 6 9H3v6h3l5 4V5z" />
      <path d="M15.54 8.46a5 5 0 0 1 0 7.07M19.07 4.93a10 10 0 0 1 0 14.14" />
    </svg>
  );
}

function VolumeOffIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" aria-hidden="true">
      <path d="M11 5 6 9H3v6h3l5 4V5z" />
      <path d="m22 9-6 6M16 9l6 6" />
    </svg>
  );
}

export function SoundToggle() {
  const audioRef = useRef<HTMLAudioElement>(null);
  const [enabled, setEnabled] = useState(false);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    const stored = localStorage.getItem(STORAGE_KEY);
    const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    setEnabled(stored === "on" && !reducedMotion);
    setReady(true);
  }, []);

  useEffect(() => {
    if (!ready) return;
    const audio = audioRef.current;
    if (!audio) return;

    audio.volume = VOLUME;

    if (enabled) {
      void audio.play().catch(() => setEnabled(false));
    } else {
      audio.pause();
    }

    localStorage.setItem(STORAGE_KEY, enabled ? "on" : "off");
  }, [enabled, ready]);

  const toggle = useCallback(() => {
    setEnabled((on) => !on);
  }, []);

  return (
    <>
      <audio ref={audioRef} src={AUDIO_SRC} loop preload="metadata" />
      <button
        type="button"
        className={`sound-toggle${enabled ? " sound-toggle--on" : ""}`}
        onClick={toggle}
        aria-pressed={enabled}
        aria-label={enabled ? "Turn background music off" : "Turn background music on"}
        title={enabled ? "Sound off" : "Sound on"}
      >
        {enabled ? <VolumeOnIcon /> : <VolumeOffIcon />}
      </button>
    </>
  );
}
