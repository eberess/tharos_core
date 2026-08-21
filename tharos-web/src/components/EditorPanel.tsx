"use client";

import { useState, useCallback, useRef } from "react";
import CodeMirrorEditor from "./CodeMirrorEditor";
import { detectLanguage } from "@/lib/api";

interface EditorPanelProps {
  sourceCode: string;
  onSourceChange: (code: string) => void;
  generatedCode: string;
  detectedLanguage: string;
  confidence: number;
  matchedPatterns: string[];
}

export default function EditorPanel({
  sourceCode,
  onSourceChange,
  generatedCode,
  detectedLanguage,
  confidence,
  matchedPatterns,
}: EditorPanelProps) {
  const [dragging, setDragging] = useState(false);
  const [split, setSplit] = useState(50);
  const [copied, setCopied] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);
  const detectTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const handleSourceChange = useCallback(
    (value: string) => {
      onSourceChange(value);
      if (detectTimerRef.current) clearTimeout(detectTimerRef.current);
      detectTimerRef.current = setTimeout(() => {
        detectLanguage("file.wdw", value).catch(() => {});
      }, 800);
    },
    [onSourceChange]
  );

  const onMouseDown = useCallback(() => setDragging(true), []);

  const onMouseMove = useCallback(
    (e: React.MouseEvent) => {
      if (!dragging || !containerRef.current) return;
      const rect = containerRef.current.getBoundingClientRect();
      const pct = ((e.clientX - rect.left) / rect.width) * 100;
      setSplit(Math.max(20, Math.min(80, pct)));
    },
    [dragging]
  );

  const onMouseUp = useCallback(() => setDragging(false), []);

  const handleCopy = useCallback(async () => {
    if (!generatedCode) return;
    try {
      await navigator.clipboard.writeText(generatedCode);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch {
      /* clipboard unavailable */
    }
  }, [generatedCode]);

  const isDetected = detectedLanguage === "windev" && matchedPatterns.length > 0;
  const langLabel = detectedLanguage === "windev" ? "WinDev" : "Inconnu";
  const pct = Math.round(confidence * 100);

  return (
    <div
      ref={containerRef}
      className="flex h-full w-full overflow-hidden relative select-none bg-zinc-950"
      onMouseMove={onMouseMove}
      onMouseUp={onMouseUp}
      onMouseLeave={onMouseUp}
    >
      {/* Left: Source */}
      <div
        className="flex h-full flex-col overflow-hidden"
        style={{ width: `${split}%` }}
      >
        <div className="flex h-11 shrink-0 items-center justify-between border-b border-zinc-800 bg-zinc-900/60 px-4">
          <span className="text-xs font-medium text-zinc-300">
            Code Source WLanguage
          </span>
          {isDetected ? (
            <span className="inline-flex items-center gap-1.5 rounded-full border border-emerald-500/30 bg-emerald-500/10 px-2.5 py-0.5 text-[11px] font-medium text-emerald-400">
              <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 shadow-[0_0_6px_rgba(52,211,153,0.8)]" />
              {langLabel} ({pct}%)
            </span>
          ) : (
            <span className="inline-flex items-center rounded-full border border-zinc-700 bg-zinc-800/50 px-2.5 py-0.5 text-[11px] font-medium text-zinc-500">
              En attente…
            </span>
          )}
        </div>
        <div className="flex-1 overflow-hidden">
          <CodeMirrorEditor
            value={sourceCode}
            onChange={handleSourceChange}
            language="plain"
          />
        </div>
      </div>

      {/* Drag handle */}
      <div
        className="group relative w-1 shrink-0 cursor-col-resize bg-zinc-800 transition-colors hover:bg-indigo-500"
        onMouseDown={onMouseDown}
      >
        <div className="absolute inset-y-0 -left-1.5 -right-1.5" />
      </div>

      {/* Right: Generated */}
      <div className="flex h-full flex-1 flex-col overflow-hidden">
        <div className="flex h-11 shrink-0 items-center justify-between border-b border-zinc-800 bg-zinc-900/60 px-4">
          <span className="text-xs font-medium text-zinc-300">
            Code Python Transpilé
          </span>
          <button
            onClick={handleCopy}
            disabled={!generatedCode}
            className="inline-flex items-center gap-1.5 rounded-md border border-zinc-700 bg-zinc-800/60 px-2.5 py-1 text-[11px] font-medium text-zinc-300 transition hover:border-zinc-600 hover:bg-zinc-700/60 hover:text-white disabled:cursor-not-allowed disabled:opacity-40"
          >
            <span className="material-symbols-rounded text-[16px] leading-none">
              {copied ? "check" : "content_copy"}
            </span>
            {copied ? "Copié !" : "Copier"}
          </button>
        </div>
        <div className="flex-1 overflow-hidden">
          <CodeMirrorEditor
            value={generatedCode}
            readOnly
            language="python"
          />
        </div>
      </div>
    </div>
  );
}
