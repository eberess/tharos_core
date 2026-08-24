"use client";

import type { ParseFileResponse } from "@/types";

interface ProjectMetadataProps {
  parsedData: ParseFileResponse | null;
  activeProcedureName: string | null;
  onSelectProcedure: (name: string) => void;
  open: boolean;
  onToggle: () => void;
}

function SectionTitle({ children }: { children: React.ReactNode }) {
  return (
    <h4 className="text-[11px] font-medium uppercase tracking-wider text-zinc-500">
      {children}
    </h4>
  );
}

export default function ProjectMetadata({
  parsedData,
  activeProcedureName,
  onSelectProcedure,
  open,
  onToggle,
}: ProjectMetadataProps) {
  if (!open) {
    return (
      <button
        onClick={onToggle}
        title="Afficher l'inspecteur de projet"
        className="flex h-full w-10 shrink-0 flex-col items-center gap-3 border-r border-zinc-800 bg-zinc-950 pt-4 text-zinc-500 transition-colors hover:bg-zinc-900 hover:text-indigo-300"
      >
        <span className="material-symbols-rounded text-[20px] leading-none">
          chevron_right
        </span>
        <span
          className="text-[11px] font-medium tracking-wide"
          style={{ writingMode: "vertical-rl" }}
        >
          Inspecteur
        </span>
        {parsedData && (
          <span className="mt-2 rounded-full bg-indigo-500/15 px-1.5 text-[11px] font-semibold text-indigo-300">
            {parsedData.procedures.length}
          </span>
        )}
      </button>
    );
  }

  return (
    <aside className="flex h-full w-80 shrink-0 flex-col border-r border-zinc-800 bg-zinc-950">
      <div className="flex h-11 shrink-0 items-center justify-between border-b border-zinc-800 bg-zinc-900/60 px-4">
        <span className="flex items-center gap-2 text-xs font-medium text-zinc-200">
          <span className="material-symbols-rounded text-[16px] leading-none text-indigo-400">
            data_object
          </span>
          Inspecteur de projet
        </span>
        <button
          onClick={onToggle}
          title="Réduire"
          className="rounded-md p-1 text-zinc-500 transition-colors hover:bg-zinc-800 hover:text-zinc-200"
        >
          <span className="material-symbols-rounded text-[18px] leading-none">
            chevron_left
          </span>
        </button>
      </div>

      {!parsedData ? (
        <div className="flex flex-1 flex-col items-center justify-center gap-3 p-6 text-center">
          <span className="material-symbols-rounded text-[36px] leading-none text-zinc-700">
            folder_open
          </span>
          <p className="text-xs leading-relaxed text-zinc-500">
            Importez un fichier WinDev pour afficher son analyse :
            procédures, variables globales et requêtes HFSQL.
          </p>
        </div>
      ) : (
        <div className="flex-1 space-y-5 overflow-y-auto p-4">
          <div className="space-y-1.5">
            <SectionTitle>Fichier</SectionTitle>
            <div className="truncate text-sm font-medium text-zinc-100">
              {parsedData.filename}
            </div>
            <div className="flex flex-wrap gap-1.5 pt-1">
              <span className="rounded-full border border-emerald-500/30 bg-emerald-500/10 px-2 py-0.5 text-[10px] font-medium text-emerald-300">
                {parsedData.procedures.length} procédure
                {parsedData.procedures.length > 1 ? "s" : ""}
              </span>
              <span className="rounded-full border border-sky-500/30 bg-sky-500/10 px-2 py-0.5 text-[10px] font-medium text-sky-300">
                {parsedData.global_variables.length} var. globale
                {parsedData.global_variables.length > 1 ? "s" : ""}
              </span>
              <span className="rounded-full border border-violet-500/30 bg-violet-500/10 px-2 py-0.5 text-[10px] font-medium text-violet-300">
                {parsedData.hfsql_queries.length} requête
                {parsedData.hfsql_queries.length > 1 ? "s" : ""}
              </span>
              <span className="rounded-full border border-zinc-700 bg-zinc-800/60 px-2 py-0.5 text-[10px] font-medium text-zinc-400">
                {parsedData.total_lines} lignes
              </span>
            </div>
          </div>

          <div className="space-y-1.5">
            <SectionTitle>Procédures extraites</SectionTitle>
            {parsedData.procedures.length === 0 ? (
              <p className="text-xs text-zinc-600">Aucune procédure détectée.</p>
            ) : (
              <ul className="space-y-1">
                {parsedData.procedures.map((proc) => {
                  const isActive = proc.name === activeProcedureName;
                  return (
                    <li key={proc.name}>
                      <button
                        onClick={() => onSelectProcedure(proc.name)}
                        className={`w-full rounded-lg border px-2.5 py-1.5 text-left transition-colors ${
                          isActive
                            ? "border-indigo-500/50 bg-indigo-500/15"
                            : "border-transparent hover:border-zinc-700 hover:bg-zinc-900"
                        }`}
                      >
                        <span
                          className={`block truncate font-mono text-xs ${
                            isActive ? "text-indigo-200" : "text-zinc-200"
                          }`}
                        >
                          {proc.name}
                        </span>
                        <span className="mt-0.5 block text-[10px] text-zinc-500">
                          ligne {proc.start_line} · {proc.parameters.length} param.
                          {proc.has_return ? " · retour" : ""}
                        </span>
                      </button>
                    </li>
                  );
                })}
              </ul>
            )}
          </div>

          <div className="space-y-1.5">
            <SectionTitle>Variables globales</SectionTitle>
            {parsedData.global_variables.length === 0 ? (
              <p className="text-xs text-zinc-600">Aucune variable globale.</p>
            ) : (
              <ul className="divide-y divide-zinc-800/70 overflow-hidden rounded-lg border border-zinc-800">
                {parsedData.global_variables.map((v) => (
                  <li
                    key={`${v.name}-${v.line}`}
                    className="flex items-center justify-between gap-2 px-2.5 py-1.5"
                  >
                    <span className="truncate font-mono text-xs text-zinc-200">
                      {v.name}
                    </span>
                    <span className="shrink-0 rounded bg-zinc-800/80 px-1.5 py-0.5 text-[10px] text-zinc-400">
                      {v.type}
                    </span>
                  </li>
                ))}
              </ul>
            )}
          </div>

          <div className="space-y-1.5">
            <SectionTitle>Requêtes HFSQL</SectionTitle>
            {parsedData.hfsql_queries.length === 0 ? (
              <p className="text-xs text-zinc-600">Aucune requête détectée.</p>
            ) : (
              <ul className="space-y-1.5">
                {parsedData.hfsql_queries.map((q, i) => (
                  <li key={`${q.line}-${i}`} className="rounded-lg border border-zinc-800 bg-zinc-900/60 p-2">
                    <div className="mb-1 flex items-center justify-between gap-2">
                      <span className="rounded bg-violet-500/15 px-1.5 py-0.5 text-[10px] font-semibold text-violet-300">
                        {q.type}
                      </span>
                      <span className="font-mono text-[10px] text-zinc-500">
                        {q.target_table} · L{q.line}
                      </span>
                    </div>
                    <code className="line-clamp-2 block break-all font-mono text-[10px] leading-relaxed text-zinc-400">
                      {q.sql}
                    </code>
                  </li>
                ))}
              </ul>
            )}
          </div>

          {parsedData.dependencies.length > 0 && (
            <div className="space-y-1.5">
              <SectionTitle>Dépendances internes</SectionTitle>
              <div className="flex flex-wrap gap-1">
                {parsedData.dependencies.map((dep) => (
                  <span
                    key={dep}
                    className="rounded-full border border-zinc-700 bg-zinc-800/60 px-2 py-0.5 font-mono text-[10px] text-zinc-300"
                  >
                    {dep}()
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </aside>
  );
}