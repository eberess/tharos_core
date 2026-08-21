"use client";

import { useState } from "react";
import type { AttemptInfo } from "@/types";

interface LogPanelProps {
  attempts: AttemptInfo[];
  isRunning: boolean;
  success: boolean | null;
}

type Tab = "attempts" | "logs";

export default function LogPanel({
  attempts,
  isRunning,
  success,
}: LogPanelProps) {
  const [tab, setTab] = useState<Tab>("attempts");
  const [selectedAttempt, setSelectedAttempt] = useState<number | null>(null);

  const activeLogs =
    selectedAttempt !== null
      ? attempts.find((a) => a.attempt === selectedAttempt)?.logs ?? ""
      : attempts.length > 0
        ? attempts[attempts.length - 1].logs
        : "";

  return (
    <div className="flex h-full flex-col overflow-hidden bg-zinc-900">
      {/* Tab bar */}
      <div className="flex h-11 shrink-0 items-center border-b border-zinc-800 px-3">
        {(["attempts", "logs"] as Tab[]).map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`relative px-4 py-2.5 text-xs font-medium transition-colors ${
              tab === t
                ? "text-zinc-100"
                : "text-zinc-500 hover:text-zinc-300"
            }`}
          >
            {t === "attempts" ? "Tentatives" : "Logs Pytest"}
            {tab === t && (
              <span className="absolute inset-x-3 -bottom-px h-0.5 rounded-full bg-indigo-500" />
            )}
          </button>
        ))}

        <div className="ml-auto flex items-center gap-2 pr-1 text-xs">
          {isRunning && (
            <span className="flex items-center gap-1.5 text-zinc-400">
              <span className="material-symbols-rounded animate-spin text-[16px] leading-none">
                sync
              </span>
              Transpilation en cours…
            </span>
          )}
          {!isRunning && success === true && (
            <span className="inline-flex items-center gap-1.5 rounded-full bg-emerald-500/10 px-2.5 py-0.5 text-[11px] font-medium text-emerald-400 ring-1 ring-emerald-500/30">
              <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 shadow-[0_0_6px_rgba(52,211,153,0.8)]" />
              Succès
            </span>
          )}
          {!isRunning && success === false && attempts.length > 0 && (
            <span className="inline-flex items-center gap-1.5 rounded-full bg-red-500/10 px-2.5 py-0.5 text-[11px] font-medium text-red-400 ring-1 ring-red-500/30">
              <span className="h-1.5 w-1.5 rounded-full bg-red-400" />
              Échec
            </span>
          )}
        </div>
      </div>

      {/* Content */}
      <div className="min-h-0 flex-1 overflow-hidden p-3">
        {tab === "attempts" ? (
          <div className="flex h-full flex-col gap-2 overflow-auto pr-1">
            {attempts.length === 0 && (
              <div className="flex h-full items-center justify-center text-xs text-zinc-600">
                {isRunning
                  ? "Transpilation en cours…"
                  : "Aucune tentative pour le moment."}
              </div>
            )}
            {attempts.map((a) => (
              <button
                key={a.attempt}
                onClick={() => {
                  setSelectedAttempt(a.attempt);
                  setTab("logs");
                }}
                className={`flex items-center justify-between rounded-lg border px-3 py-2.5 text-left text-xs transition ${
                  selectedAttempt === a.attempt
                    ? "border-indigo-500/50 bg-indigo-500/5"
                    : "border-zinc-800 bg-zinc-950/40 hover:border-zinc-700 hover:bg-zinc-900"
                }`}
              >
                <span className="flex items-center gap-2.5">
                  <span
                    className={`flex h-6 w-6 items-center justify-center rounded-md text-[11px] font-semibold ${
                      a.passed
                        ? "bg-emerald-500/15 text-emerald-400"
                        : "bg-red-500/15 text-red-400"
                    }`}
                  >
                    {a.attempt}
                  </span>
                  <span className="font-medium text-zinc-200">
                    Tentative {a.attempt}
                  </span>
                </span>
                <span
                  className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-[11px] font-semibold ${
                    a.passed
                      ? "bg-emerald-500/10 text-emerald-400 ring-1 ring-emerald-500/30"
                      : "bg-red-500/10 text-red-400 ring-1 ring-red-500/30"
                  }`}
                >
                  {a.passed ? "PASS" : "FAIL"}
                  <span className="opacity-60">· Exit {a.exit_code}</span>
                </span>
              </button>
            ))}
          </div>
        ) : (
          <div className="h-full overflow-auto rounded-lg border border-zinc-800 bg-black/80 p-4 font-mono text-xs leading-relaxed text-zinc-300 shadow-inner">
            <pre className="whitespace-pre-wrap break-words">
              {activeLogs || (
                <span className="text-zinc-600">Aucun log disponible.</span>
              )}
            </pre>
          </div>
        )}
      </div>
    </div>
  );
}
