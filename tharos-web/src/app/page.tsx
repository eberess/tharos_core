"use client";

import { useState, useCallback } from "react";
import EditorPanel from "@/components/EditorPanel";
import LogPanel from "@/components/LogPanel";
import { detectLanguage, transpileCode } from "@/lib/api";
import type { AttemptInfo } from "@/types";

const SAMPLE_CODE = `PROCEDURE CalculerTVA(nMontantHT est un monétaire, sCodeTVA est une chaîne) LOCAL
    nTVA est un monétaire
    nTauxTVA est un réel

    SI sCodeTVA = "TX20" ALORS
        nTauxTVA = 0.20
    SINON SI sCodeTVA = "TX10" ALORS
        nTauxTVA = 0.10
    SINON
        nTauxTVA = 0.00
    FIN

    nTVA = nMontantHT * nTauxTVA
    RENVOYER nTVA
`;

export default function Home() {
  const [sourceCode, setSourceCode] = useState(SAMPLE_CODE);
  const [generatedCode, setGeneratedCode] = useState("");
  const [detectedLanguage, setDetectedLanguage] = useState("");
  const [confidence, setConfidence] = useState(0);
  const [matchedPatterns, setMatchedPatterns] = useState<string[]>([]);
  const [attempts, setAttempts] = useState<AttemptInfo[]>([]);
  const [isRunning, setIsRunning] = useState(false);
  const [success, setSuccess] = useState<boolean | null>(null);
  const [procedureName, setProcedureName] = useState("CalculerTVA");
  const [error, setError] = useState<string | null>(null);

  const handleSourceChange = useCallback(async (code: string) => {
    setSourceCode(code);
    try {
      const res = await detectLanguage("file.wdw", code);
      setDetectedLanguage(res.detected_language);
      setConfidence(res.confidence);
      setMatchedPatterns(res.matched_patterns);
    } catch {
      // silent
    }
  }, []);

  const handleTranspile = useCallback(async () => {
    setIsRunning(true);
    setSuccess(null);
    setAttempts([]);
    setError(null);
    setGeneratedCode("");

    try {
      const res = await transpileCode(
        "source.wdw",
        sourceCode,
        procedureName,
        3
      );
      setGeneratedCode(res.generated_code);
      setAttempts(res.history);
      setSuccess(res.success);
      if (res.error) setError(res.error);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erreur inconnue");
      setSuccess(false);
    } finally {
      setIsRunning(false);
    }
  }, [sourceCode, procedureName]);

  return (
    <div className="h-screen flex flex-col bg-neutral-950 text-white">
      {/* Header */}
      <header className="flex items-center justify-between px-4 py-2 border-b border-neutral-800 bg-neutral-950">
        <div className="flex items-center gap-3">
          <h1 className="text-sm font-bold tracking-tight">
            <span className="text-blue-400">Tharos</span>
            <span className="text-neutral-500 ml-1">Core</span>
          </h1>
          <span className="text-[10px] text-neutral-600 bg-neutral-800 px-1.5 py-0.5 rounded">
            v0.1.0
          </span>
        </div>

        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <label className="text-xs text-neutral-500">Procédure:</label>
            <input
              type="text"
              value={procedureName}
              onChange={(e) => setProcedureName(e.target.value)}
              className="bg-neutral-900 border border-neutral-700 rounded px-2 py-1 text-xs font-mono w-44 focus:outline-none focus:border-blue-500"
              placeholder="Nom de la procédure"
            />
          </div>

          <button
            onClick={handleTranspile}
            disabled={isRunning || !sourceCode.trim()}
            className="px-3 py-1.5 bg-blue-600 hover:bg-blue-500 disabled:bg-neutral-700 disabled:text-neutral-500 rounded text-xs font-medium transition-colors"
          >
            {isRunning ? "Transpilation..." : "Transpiler"}
          </button>
        </div>
      </header>

      {/* Error banner */}
      {error && (
        <div className="px-4 py-2 bg-red-950 border-b border-red-800 text-red-300 text-xs">
          {error}
        </div>
      )}

      {/* Editor split */}
      <EditorPanel
        sourceCode={sourceCode}
        onSourceChange={handleSourceChange}
        generatedCode={generatedCode}
        detectedLanguage={detectedLanguage}
        confidence={confidence}
        matchedPatterns={matchedPatterns}
      />

      {/* Log panel */}
      <LogPanel
        attempts={attempts}
        isRunning={isRunning}
        success={success}
      />
    </div>
  );
}
