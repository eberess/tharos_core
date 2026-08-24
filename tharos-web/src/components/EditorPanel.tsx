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
  onImportFile?: (file: File) => void;
}

export default function EditorPanel({
  sourceCode,
  onSourceChange,
  generatedCode,
  detectedLanguage,
  confidence,
  matchedPatterns,
  onImportFile,
}: EditorPanelProps) {
  const [split, setSplit] = useState(50);
  const [dragging, setDragging] = useState(false);
  const [fileHover, setFileHover] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);
  const detectTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

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
      // Note: copying functionality would be implemented in actual app
    } catch {
      /* clipboard unavailable */
    }
  }, [generatedCode]);

  const openFileSelector = useCallback(() => {
    fileInputRef.current?.click();
  }, []);

  const handleInputChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      e.target.value = "";
      if (file && onImportFile) onImportFile(file);
    },
    [onImportFile]
  );

  const onDragOver = useCallback(
    (e: React.DragEvent<HTMLDivElement>) => {
      if (!onImportFile) return;
      e.preventDefault();
      e.stopPropagation();
      setFileHover(true);
    },
    [onImportFile]
  );

  const onDragLeave = useCallback((e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setFileHover(false);
  }, []);

  const onDrop = useCallback(
    (e: React.DragEvent<HTMLDivElement>) => {
      if (!onImportFile) return;
      e.preventDefault();
      e.stopPropagation();
      setFileHover(false);
      const file = e.dataTransfer.files?.[0];
      if (file) onImportFile(file);
    },
    [onImportFile]
  );

  const isDetected = detectedLanguage === "windev" && matchedPatterns.length > 0;
  const langLabel = detectedLanguage === "windev" ? "WinDev" : "Inconnu";
  const pct = Math.round(confidence * 100);

  return (
    <div
      ref={containerRef}
      className="relative flex h-full w-full select-none overflow-hidden bg-zinc-950"
      onMouseMove={onMouseMove}
      onMouseUp={onMouseUp}
      onMouseLeave={onMouseUp}
    >
      {/* Left: Source */}
      <div
        className="relative flex h-full flex-col overflow-hidden"
        style={{ width: `${split}%` }}
        onDragOver={onDragOver}
        onDragLeave={onDragLeave}
        onDrop={onDrop}
      >
        <div className="flex h-11 shrink-0 items-center justify-between gap-2 border-b border-zinc-800 bg-zinc-900/60 px-4">
          <span className="text-xs font-medium text-zinc-300">
            Code Source WLanguage
          </span>
          <div className="flex items-center gap-2">
            {isDetected && (
              <span className="hidden items-center gap-1.5 rounded-full border border-emerald-500/30 bg-emerald-500/10 px-2.5 py-0.5 text-[11px] font-medium text-emerald-400 xl:inline-flex">
                <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 shadow-[0_0_6px_rgba(52,211,153,0.8)]" />
                {langLabel} ({pct}%)
              </span>
            )}
            <button
              onClick={openFileSelector}
              className="inline-flex items-center gap-1.5 rounded-md border border-indigo-500/40 bg-indigo-500/15 px-2.5 py-1 text-[11px] font-semibold text-indigo-300 shadow-sm shadow-indigo-950/40 transition hover:border-indigo-400 hover:bg-indigo-500/25 hover:text-indigo-200"
            >
              <span className="material-symbols-rounded text-[14px] leading-none">
                upload_file
              </span>
              Importer (.wdw, .wdg, .wda)
            </button>
            <input
              type="file"
              ref={fileInputRef}
              accept=".wdw,.wdg,.wda"
              onChange={handleInputChange}
              className="hidden"
            />
          </div>
        </div>
        <div className="flex-1 overflow-hidden">
          <CodeMirrorEditor
            value={sourceCode}
            onChange={handleSourceChange}
            language="plain"
          />
        </div>

        {/* Drag & drop overlay */}
        {fileHover && (
          <div className="pointer-events-none absolute inset-3 z-10 flex items-center justify-center rounded-xl border-2 border-dashed border-indigo-400/80 bg-indigo-950/80 backdrop-blur-sm">
            <div className="text-center">
              <span className="material-symbols-rounded mb-2 block text-[42px] leading-none text-indigo-300">
                upload_file
              </span>
              <p className="text-sm font-medium text-indigo-200">
                Déposez votre fichier ici
              </p>
              <p className="mt-1 text-xs text-indigo-300/70">
                Formats supportés : .wdw, .wdg, .wda
              </p>
            </div>
          </div>
        )}
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
              {generatedCode ? "content_copy" : "check"}
            </span>
            Copier
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