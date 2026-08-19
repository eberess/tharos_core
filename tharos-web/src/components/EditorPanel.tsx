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

  return (
    <div
      ref={containerRef}
      className="flex-1 flex overflow-hidden relative select-none"
      onMouseMove={onMouseMove}
      onMouseUp={onMouseUp}
      onMouseLeave={onMouseUp}
    >
      {/* Left: Source */}
      <div
        className="flex flex-col overflow-hidden border-r border-neutral-700"
        style={{ width: `${split}%` }}
      >
        <div className="flex items-center justify-between px-3 py-1.5 bg-neutral-900 border-b border-neutral-700 text-xs">
          <span className="font-mono text-neutral-400">WLanguage Source</span>
          <div className="flex items-center gap-2">
            {matchedPatterns.length > 0 && (
              <span className="text-emerald-400">
                {detectedLanguage.toUpperCase()}{" "}
                {Math.round(confidence * 100)}%
              </span>
            )}
          </div>
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
        className="w-1 cursor-col-resize bg-neutral-700 hover:bg-blue-500 transition-colors z-10"
        onMouseDown={onMouseDown}
      />

      {/* Right: Generated */}
      <div className="flex flex-col overflow-hidden flex-1">
        <div className="flex items-center px-3 py-1.5 bg-neutral-900 border-b border-neutral-700 text-xs">
          <span className="font-mono text-neutral-400">
            Python Generated
          </span>
          {matchedPatterns.length > 0 && (
            <div className="ml-auto flex gap-1">
              {matchedPatterns.map((p) => (
                <span
                  key={p}
                  className="px-1.5 py-0.5 rounded bg-neutral-800 text-neutral-500 text-[10px]"
                >
                  {p}
                </span>
              ))}
            </div>
          )}
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
