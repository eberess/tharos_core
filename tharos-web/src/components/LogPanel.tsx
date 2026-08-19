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
    <div className="h-64 flex flex-col border-t border-neutral-700 bg-neutral-950">
      {/* Tab bar */}
      <div className="flex items-center border-b border-neutral-800 px-2 text-xs">
        <button
          onClick={() => setTab("attempts")}
          className={`px-3 py-1.5 border-b-2 transition-colors ${
            tab === "attempts"
              ? "border-blue-500 text-white"
              : "border-transparent text-neutral-500 hover:text-neutral-300"
          }`}
        >
          Tentatives
        </button>
        <button
          onClick={() => setTab("logs")}
          className={`px-3 py-1.5 border-b-2 transition-colors ${
            tab === "logs"
              ? "border-blue-500 text-white"
              : "border-transparent text-neutral-500 hover:text-neutral-300"
          }`}
        >
          Logs Pytest
        </button>

        <div className="ml-auto flex items-center gap-2 text-neutral-500">
          {isRunning && (
            <span className="flex items-center gap-1">
              <span className="w-1.5 h-1.5 rounded-full bg-yellow-400 animate-pulse" />
              Transpilation en cours...
            </span>
          )}
          {!isRunning && success === true && (
            <span className="text-emerald-400">PASS</span>
          )}
          {!isRunning && success === false && attempts.length > 0 && (
            <span className="text-red-400">FAIL</span>
          )}
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-auto">
        {tab === "attempts" && (
          <div className="p-2 flex flex-col gap-1">
            {attempts.length === 0 && (
              <span className="text-neutral-600 text-xs p-2">
                Aucune tentative pour le moment.
              </span>
            )}
            {attempts.map((a) => (
              <button
                key={a.attempt}
                onClick={() => {
                  setSelectedAttempt(a.attempt);
                  setTab("logs");
                }}
                className={`flex items-center gap-2 px-3 py-1.5 rounded text-xs text-left transition-colors ${
                  selectedAttempt === a.attempt
                    ? "bg-neutral-800 text-white"
                    : "hover:bg-neutral-900 text-neutral-400"
                }`}
              >
                <span
                  className={`w-2 h-2 rounded-full ${
                    a.passed ? "bg-emerald-400" : "bg-red-400"
                  }`}
                />
                <span>Tentative {a.attempt}</span>
                <span className="text-neutral-600 ml-auto">
                  exit {a.exit_code}
                </span>
              </button>
            ))}
          </div>
        )}

        {tab === "logs" && (
          <pre className="p-3 text-xs font-mono text-neutral-300 whitespace-pre-wrap break-all leading-relaxed">
            {activeLogs || (
              <span className="text-neutral-600">
                Aucun log disponible.
              </span>
            )}
          </pre>
        )}
      </div>
    </div>
  );
}
