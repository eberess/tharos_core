"use client";

import { useState, useEffect } from "react";
import type { ParseFileResponse } from "@/types";
import { getDependencyGraph } from "@/lib/api";

interface DependencyGraphTabProps {
  parsedData: ParseFileResponse | null;
  files: { filename: string; content: string }[] | null;
}

export default function DependencyGraphTab({ parsedData, files }: DependencyGraphTabProps) {
  const [dependencyData, setDependencyData] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!files || !parsedData) return;

    const loadDependencyGraph = async () => {
      try {
        setLoading(true);
        // We'll fetch the graph with all parsed files
        const res = await getDependencyGraph(files);
        setDependencyData(res);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Erreur lors du chargement du graphe");
      } finally {
        setLoading(false);
      }
    };

    loadDependencyGraph();
  }, [files, parsedData]);

  if (!parsedData || !files) {
    return (
      <div className="text-center text-xs text-zinc-600 py-4">
        Aucun fichier chargé pour le graphe de dépendances
      </div>
    );
  }

  if (loading) {
    return (
      <div className="text-center text-xs text-zinc-600 py-4 flex items-center justify-center">
        <span className="material-symbols-rounded animate-spin">sync</span>
        <span className="ml-2">Chargement du graphe de dépendances...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-xs text-red-400 py-4">
        Erreur: {error}
      </div>
    );
  }

  if (!dependencyData) {
    return (
      <div className="text-center text-xs text-zinc-600 py-4">
        Aucune donnée disponible
      </div>
    );
  }

  return (
    <div className="space-y-4 p-4">
      {dependencyData.has_cycles ? (
        <div className="rounded-lg border border-yellow-500/30 bg-yellow-500/10 p-3">
          <h4 className="font-medium text-yellow-300">Dépendances circulaires détectées</h4>
          <p className="mt-1 text-xs text-yellow-400">
            Le projet contient des dépendances circulaires qui peuvent poser problème.
          </p>
        </div>
      ) : (
        <div className="rounded-lg border border-emerald-500/30 bg-emerald-500/10 p-3">
          <h4 className="font-medium text-emerald-300">Aucune dépendance circulaire</h4>
          <p className="mt-1 text-xs text-emerald-400">
            Les dépendances sont résolues sans circularité.
          </p>
        </div>
      )}

      <div>
        <h4 className="text-[11px] font-medium uppercase tracking-wider text-zinc-500 mb-2">
          Ordre de transpilation recommandé
        </h4>
        <ol className="space-y-2">
          {dependencyData.transpilation_order.map((file: string, index: number) => (
            <li 
              key={index} 
              className="flex items-center gap-3 rounded-lg border border-zinc-800 bg-zinc-900/60 p-3 transition-colors hover:bg-zinc-800/40"
            >
              <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-indigo-500/15 text-[10px] font-medium text-indigo-300">
                {index + 1}
              </span>
              <div className="truncate flex-1 text-sm font-mono text-zinc-200">
                {file}
              </div>
            </li>
          ))}
        </ol>
      </div>

      <div>
        <h4 className="text-[11px] font-medium uppercase tracking-wider text-zinc-500 mb-2">
          Structure des dépendances
        </h4>
        <div className="space-y-3">
          <div className="rounded-lg border border-zinc-800 bg-zinc-900/60 p-3">
            <div className="flex items-center gap-2 mb-2">
              <span className="material-symbols-rounded text-indigo-400 text-sm">source</span>
              <span className="text-xs font-medium text-zinc-200">Dépendances internes</span>
            </div>
            {Object.keys(dependencyData.dependencies || {}).length > 0 ? (
              <ul className="space-y-1.5">
                {Object.entries(dependencyData.dependencies).map(([file, deps]) => (
                  <li key={file} className="text-xs text-zinc-400">
                    <span className="font-mono text-indigo-300">{file}</span>
                    <span className="mx-1">→</span>
                    {Array.isArray(deps) && deps.length > 0 ? (
                      <span>{deps.join(", ")}</span>
                    ) : (
                      <span className="text-zinc-500">aucune dépendance</span>
                    )}
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-xs text-zinc-500">Aucune dépendance détectée</p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}