"use client";

import { useState, useCallback, useEffect, useRef } from "react";
import EditorPanel from "@/components/EditorPanel";
import LogPanel from "@/components/LogPanel";
import ProjectMetadata from "@/components/ProjectMetadata";
import { detectLanguage, transpileCode, parseFile, generateUi } from "@/lib/api";
import type { AttemptInfo, ParseFileResponse, UIWindowStructure } from "@/types";

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

const WINDEV_FILE_RE = /\.(wdw|wdg|wda)$/i;

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
  const [loadedFiles, setLoadedFiles] = useState<{ filename: string; content: string }[] | null>(null);
  const [parsedData, setParsedData] = useState<ParseFileResponse | null>(null);
  const [currentFilename, setCurrentFilename] = useState<string | null>(null);
  const [currentContent, setCurrentContent] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [files, setFiles] = useState<{ filename: string; content: string }[] | null>(null);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [isParsing, setIsParsing] = useState(false);
  /* v0.4 — Vue composant React */
  const [reactView, setReactView] = useState(false);
  const [generatedReact, setGeneratedReact] = useState<{ component_name: string; tsx_code: string } | null>(null);
  const [uiStructure, setUiStructure] = useState<UIWindowStructure | null>(null);
  const [isGeneratingReact, setIsGeneratingReact] = useState(false);
  const [reactError, setReactError] = useState<string | null>(null);
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

  const loadFile = useCallback(async (file: File) => {
    if (!WINDEV_FILE_RE.test(file.name)) {
      setError("Format invalide — choisissez un fichier WinDev (.wdw, .wdg ou .wda)");
      return;
    }

    setIsParsing(true);
    setError(null);

    try {
      const content = await file.text();
      setSourceCode(content);

      const parsed = await parseFile(file.name, content);
      setParsedData(parsed);
      setCurrentFilename(file.name);
      setCurrentContent(content);
      
      // Update files list with the loaded file
      setLoadedFiles([{ filename: file.name, content }]);

      // Show notification toast
      if (parsed.procedures.length > 0) {
        setError(`Fichier analysé : ${parsed.procedures.length} procédures détectées, ${parsed.hfsql_queries.length} requêtes HFSQL`);
      }
      
      if (parsed.procedures.length > 0) {
        setProcedureName(parsed.procedures[0].name);
        // Load the first procedure into source editor
        // This would normally come from the procedures parsing
      }
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Erreur lors de l'analyse du fichier"
      );
    } finally {
      setIsParsing(false);
    }
  }, []);

  const handleHeaderFileChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      e.target.value = "";
      if (file) void loadFile(file);
    },
    [loadFile]
  );

  const handleSelectProcedure = useCallback((name: string) => {
    setProcedureName(name);
    // In a real app, this would update the editor with the procedure content
    // For now, we'll just log that user selected a procedure
    console.log("Selected procedure:", name);
  }, []);

  const resetFile = useCallback(() => {
    setParsedData(null);
    setSourceCode(SAMPLE_CODE);
    setProcedureName("CalculerTVA");
    setError(null);
    setGeneratedCode("");
    setCurrentFilename(null);
    setCurrentContent(null);
    setLoadedFiles(null);
    setGeneratedReact(null);
    setUiStructure(null);
    setReactError(null);
  }, []);

  /* v0.4 — Génération du composant React (IHM) via /api/v1/generate-ui */
  const runGenerateReact = useCallback(async () => {
    setIsGeneratingReact(true);
    setReactError(null);
    try {
      const res = await generateUi(currentFilename ?? "fenetre.wdw", sourceCode);
      if (res.success) {
        setGeneratedReact({ component_name: res.component_name, tsx_code: res.tsx_code });
        setUiStructure(res.ui_structure);
      } else {
        setReactError(res.error ?? "Échec de la génération du composant React");
      }
    } catch (e) {
      setReactError(e instanceof Error ? e.message : "Erreur réseau lors de la génération UI");
    } finally {
      setIsGeneratingReact(false);
    }
  }, [currentFilename, sourceCode]);

  const handleToggleReactView = useCallback(() => setReactView((v) => !v), []);

  // Invalide le cache : l'effet ci-dessous relance la génération.
  const handleRegenerateReact = useCallback(() => {
    setGeneratedReact(null);
    setUiStructure(null);
  }, []);

  useEffect(() => {
    if (reactView && !generatedReact && !isGeneratingReact) {
      void runGenerateReact();
    }
    // Dépendances volontairement restreintes : pas de re-génération à chaque frappe,
    // le bouton « Régénérer » pilote explicitement le rafraîchissement.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [reactView, generatedReact]);

  // Keyboard shortcut for toggling sidebar (Ctrl+B or Cmd+B)
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Check for Ctrl+B or Cmd+B combination
      if ((e.ctrlKey || e.metaKey) && e.key === 'b') {
        e.preventDefault();
        setSidebarOpen(!sidebarOpen);
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [sidebarOpen]);

  // Empêche le navigateur d'ouvrir le fichier si le drop a lieu hors zone.
  useEffect(() => {
    const prevent = (e: DragEvent) => e.preventDefault();
    window.addEventListener("dragover", prevent);
    window.addEventListener("drop", prevent);
    return () => {
      window.removeEventListener("dragover", prevent);
      window.removeEventListener("drop", prevent);
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
          <button 
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="flex items-center justify-center rounded-md p-1.5 text-zinc-400 transition-colors hover:bg-zinc-800 hover:text-indigo-300"
            title="Afficher l'inspecteur de projet"
          >
            <span className="material-symbols-rounded text-[20px] leading-none">
              view_sidebar
            </span>
          </button>
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
          <input
            type="file"
            ref={fileInputRef}
            accept=".wdw,.wdg,.wda"
            onChange={handleHeaderFileChange}
            className="hidden"
          />
          <button
            onClick={() => fileInputRef.current?.click()}
            disabled={isParsing}
            className="inline-flex items-center gap-2 rounded-lg border border-zinc-700 bg-zinc-900 px-3 py-1.5 text-xs text-zinc-300 transition hover:border-indigo-500 hover:bg-zinc-800/60 focus:outline-none focus:ring-1 focus:ring-ind-indigo-500/40 disabled:opacity-50"
          >
            <span className="material-symbols-rounded text-[16px] leading-none">
              {isParsing ? "progress_activity" : "file_upload"}
            </span>
            {isParsing ? "Analyse…" : "Importer un fichier"}
          </button>

          {parsedData && (
            <button
              onClick={resetFile}
              className="inline-flex items-center gap-2 rounded-lg border border-zinc-700 bg-zinc-900 px-3 py-1.5 text-xs text-zinc-300 transition hover:border-indigo-500 hover:bg-zinc-800/60"
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
              {parsedData ? (
                parsedData.procedures.map((proc) => (
                  <option key={proc.name} value={proc.name}>
                    {proc.name}
                  </option>
                ))
              ) : (
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

      {/* Three-pane layout */}
      <div className="flex min-h-0 flex-1 overflow-hidden">
        {/* Left Panel: Project Explorer - 280px width */}
        <div 
          className={`flex h-full w-80 shrink-0 border-r border-zinc-800 bg-zinc-950 transition-all duration-200 ${sidebarOpen ? 'block' : 'hidden'}`}
        >
          <ProjectMetadata
            parsedData={parsedData}
            activeProcedureName={procedureName}
            onSelectProcedure={handleSelectProcedure}
            open={sidebarOpen}
            onToggle={() => setSidebarOpen(!sidebarOpen)}
            files={loadedFiles}
            currentFilename={currentFilename}
            currentContent={currentContent}
          />
        </div>

        {/* Middle Panel: Editor */}
        <main className="flex min-h-0 flex-1 flex-col gap-4 p-4">
          <section className="min-h-0 flex-1 overflow-hidden rounded-xl border border-zinc-800 bg-zinc-900 shadow-sm">
            <EditorPanel
              sourceCode={sourceCode}
              onSourceChange={handleSourceChange}
              generatedCode={generatedCode}
              detectedLanguage={detectedLanguage}
              confidence={confidence}
              matchedPatterns={matchedPatterns}
              onImportFile={loadFile}
              reactView={reactView}
              onToggleReactView={handleToggleReactView}
              generatedReact={generatedReact}
              uiStructure={uiStructure}
              isGeneratingReact={isGeneratingReact}
              reactError={reactError}
              onRegenerateReact={handleRegenerateReact}
            />
          </section>

          {/* Bottom Panel: Console/Output */}
          <section className="h-72 shrink-0 overflow-hidden rounded-xl border border-zinc-800 bg-zinc-900 shadow-sm">
            <LogPanel attempts={attempts} isRunning={isRunning} success={success} />
          </section>
        </main>
      </div>

      {/* Floating toggle button when sidebar is closed */}
      {!sidebarOpen && (
        <button
          onClick={() => setSidebarOpen(!sidebarOpen)}
          className="fixed left-0 top-1/2 flex h-8 w-6 items-center justify-center rounded-r-md border border-zinc-700 bg-zinc-900/80 text-zinc-400 transition-colors hover:bg-zinc-800 hover:text-indigo-300"
          title="Ouvrir l'inspecteur de projet"
        >
          <span className="material-symbols-rounded text-[16px] leading-none">
            chevron_right
          </span>
        </button>
      )}
    </div>
  );
}