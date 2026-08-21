"use client";

import { useState, useCallback, useEffect, useRef } from "react";
import EditorPanel from "@/components/EditorPanel";
import LogPanel from "@/components/LogPanel";
import ProjectMetadata from "@/components/ProjectMetadata";
import { detectLanguage, transpileCode, parseFile } from "@/lib/api";
import type { AttemptInfo, ParseFileResponse } from "@/types";

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
  const [maxAttempts, setMaxAttempts] = useState(3);
  const [error, setError] = useState<string | null>(null);
  const [parsedData, setParsedData] = useState<ParseFileResponse | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleSourceChange = useCallback(async (code: string) => {
    setSourceCode(code);
    try {
      const res = await detectLanguage("file.wdw", code);
      setDetectedLanguage(res.detected_language);
      setConfidence(res.confidence);
      setMatchedPatterns(res.matched_patterns);
    } catch {
      /* silent */
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
        maxAttempts
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
  }, [sourceCode, procedureName, maxAttempts]);

  const handleFileChange = useCallback(async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      const file = e.target.files[0];
      
      // Check file extension
      if (!file.name.match(/\.(wdw|wdg|wda)$/i)) {
        setError("Veuillez sélectionner un fichier WinDev (.wdw, .wdg ou .wda)");
        return;
      }
      
      try {
        const content = await file.text();
        setSourceCode(content);
        
        // Parse the file
        const parsed = await parseFile(file.name, content);
        setParsedData(parsed);
        
        // Set procedure dropdown to first procedure
        if (parsed.procedures.length > 0) {
          setProcedureName(parsed.procedures[0].name);
        }
        
        setError(null);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Erreur lors de l'analyse du fichier");
      }
    }
  }, []);

  const handleDragOver = useCallback((e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback(() => {
    setIsDragging(false);
  }, []);

  const openFileSelector = useCallback(() => {
    fileInputRef.current?.click();
  }, []);

  const handleDrop = useCallback(async (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      const file = e.dataTransfer.files[0];
      
      // Check file extension
      if (!file.name.match(/\.(wdw|wdg|wda)$/i)) {
        setError("Veuillez sélectionner un fichier WinDev (.wdw, .wdg ou .wda)");
        return;
      }
      
      try {
        const content = await file.text();
        setSourceCode(content);
        
        // Parse the file
        const parsed = await parseFile(file.name, content);
        setParsedData(parsed);
        
        // Set procedure dropdown to first procedure
        if (parsed.procedures.length > 0) {
          setProcedureName(parsed.procedures[0].name);
        }
        
        setError(null);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Erreur lors de l'analyse du fichier");
      }
    }
  }, []);

  const handleSelectProcedure = useCallback((name: string) => {
    setProcedureName(name);
  }, []);

  const resetFile = useCallback(() => {
    setParsedData(null);
    setSourceCode(SAMPLE_CODE);
    setProcedureName("CalculerTVA");
    setError(null);
  }, []);

  // Set up global drag events
  useEffect(() => {
    const handleGlobalDragOver = (e: DragEvent) => {
      e.preventDefault();
    };

    window.addEventListener('dragover', handleGlobalDragOver);
    return () => {
      window.removeEventListener('dragover', handleGlobalDragOver);
    };
  }, []);

  return (
    <div className="flex h-screen flex-col bg-zinc-950 text-zinc-100">
      {/* Header + Action bar */}
      <header className="sticky top-0 z-20 flex flex-wrap items-center justify-between gap-3 border-b border-zinc-800 bg-zinc-950/80 px-6 py-3 backdrop-blur">
        <div className="flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-indigo-500 to-violet-600 text-base font-bold text-white shadow-lg shadow-indigo-500/20">
            T
          </div>
          <div className="flex items-center gap-2">
            <span className="text-lg font-semibold tracking-tight text-zinc-100">
              THAROS
            </span>
            <span className="rounded-full border border-indigo-500/30 bg-gradient-to-r from-indigo-500/15 to-violet-500/15 px-2 py-0.5 text-[10px] font-medium text-indigo-300">
              SaaS Edition
            </span>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          {!parsedData && (
            <>
              <div className="relative">
                <input
                  type="file"
                  ref={fileInputRef}
                  onChange={handleFileChange}
                  accept=".wdw,.wdg,.wda"
                  className="hidden"
                />
                <button
                  onClick={openFileSelector}
                  className="inline-flex items-center gap-2 rounded-lg border border-zinc-700 bg-zinc-900 px-3 py-1.5 text-xs text-zinc-300 transition hover:border-indigo-500 hover:bg-zinc-800/60 focus:outline-none focus:ring-1 focus:ring-indigo-500/40"
                >
                  <span className="material-symbols-rounded text-[16px] leading-none">
                    file_upload
                  </span>
                  Importer un fichier
                </button>
              </div>
            </>
          )}
          
          {parsedData && (
            <button
              onClick={resetFile}
              className="inline-flex items-center gap-2 rounded-lg border border-zinc-700 bg-zinc-900 px-3 py-1.5 text-xs text-zinc-300 transition hover:border-indigo-500 hover:bg-zinc-800/60 focus:outline-none focus:ring-1 focus:ring-indigo-500/40"
            >
              <span className="material-symbols-rounded text-[16px] leading-none">
                refresh
              </span>
              Nouveau fichier
            </button>
          )}
          
          <div className="flex items-center gap-2">
            <label className="text-xs text-zinc-400">Procédure</label>
            <select
              value={procedureName}
              onChange={(e) => setProcedureName(e.target.value)}
              className="w-48 rounded-lg border border-zinc-800 bg-zinc-900 px-3 py-1.5 text-xs text-zinc-100 transition focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500/40"
            >
              {parsedData && parsedData.procedures.map((proc) => (
                <option key={proc.name} value={proc.name}>
                  {proc.name}
                </option>
              ))}
              {!parsedData && (
                <option value="CalculerTVA">CalculerTVA</option>
              )}
            </select>
          </div>

          <div className="flex items-center gap-2">
            <label className="text-xs text-zinc-400">Tentatives</label>
            <select
              value={maxAttempts}
              onChange={(e) => setMaxAttempts(Number(e.target.value))}
              className="rounded-lg border border-zinc-800 bg-zinc-900 px-3 py-1.5 text-xs text-zinc-100 transition focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500/40"
            >
              {[1, 2, 3, 4, 5].map((n) => (
                <option key={n} value={n}>
                  {n} tentative{n > 1 ? "s" : ""}
                </option>
              ))}
            </select>
          </div>

          <button
            onClick={handleTranspile}
            disabled={isRunning || !sourceCode.trim()}
            className="group inline-flex items-center gap-2 rounded-lg bg-gradient-to-r from-indigo-600 to-violet-600 px-4 py-1.5 text-sm font-medium text-white shadow-sm transition hover:from-indigo-500 hover:to-violet-500 disabled:cursor-not-allowed disabled:opacity-50"
          >
            <span className="material-symbols-rounded text-[18px] leading-none">
              {isRunning ? "sync" : "auto_fix_high"}
            </span>
            {isRunning ? "Transpilation…" : "Transpiler"}
          </button>
        </div>
      </header>

      {/* Error banner */}
      {error && (
        <div className="flex items-center gap-2 border-b border-red-900/50 bg-red-950/40 px-6 py-2.5 text-xs text-red-300">
          <span className="material-symbols-rounded text-[16px] leading-none">
            error
          </span>
          {error}
        </div>
      )}

      {/* Main layout with sidebar */}
      <div className="flex flex-1 overflow-hidden">
        {/* Sidebar - Project Metadata */}
        {parsedData && (
          <div className="w-80 border-r border-zinc-800 bg-zinc-950/80 p-4 overflow-y-auto">
            <ProjectMetadata 
              parsedData={parsedData} 
              onSelectProcedure={handleSelectProcedure}
              onFileLoad={() => {}}
            />
          </div>
        )}

        {/* Main content area */}
        <div className="flex-1 flex flex-col">
          {/* Editor container with drag & drop support */}
          <div 
            className="flex-1 overflow-hidden relative"
            onDrop={handleDrop}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
          >
            {/* Drag overlay */}
            {isDragging && !parsedData && (
              <div className="absolute inset-0 z-10 flex items-center justify-center bg-black/50 backdrop-blur-sm">
                <div className="rounded-xl border-2 border-dashed border-indigo-500/30 bg-indigo-950/30 p-8 text-center text-indigo-300">
                  <span className="material-symbols-rounded text-[48px] leading-none mb-3">upload_file</span>
                  <p className="text-lg font-medium">Déposez votre fichier WinDev ici</p>
                  <p className="text-sm mt-2">Formats supportés : .wdw, .wdg, .wda</p>
                </div>
              </div>
            )}

            <section className="min-h-0 flex-1 overflow-hidden rounded-xl border border-zinc-800 bg-zinc-900 shadow-sm m-4">
              <EditorPanel
                sourceCode={sourceCode}
                onSourceChange={handleSourceChange}
                generatedCode={generatedCode}
                detectedLanguage={detectedLanguage}
                confidence={confidence}
                matchedPatterns={matchedPatterns}
              />
            </section>
          </div>

          {/* Log panel */}
          <section className="h-72 shrink-0 overflow-hidden rounded-xl border border-zinc-800 bg-zinc-900 shadow-sm m-4">
            <LogPanel
              attempts={attempts}
              isRunning={isRunning}
              success={success}
            />
          </section>
        </div>
      </div>
    </div>
  );
}