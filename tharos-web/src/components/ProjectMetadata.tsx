"use client";

import { useState, useEffect } from "react";
import type { ParseFileResponse } from "@/types";

interface ProjectMetadataProps {
  parsedData: ParseFileResponse | null;
  onSelectProcedure: (name: string) => void;
  onFileLoad: () => void;
}

export default function ProjectMetadata({
  parsedData,
  onSelectProcedure,
  onFileLoad
}: ProjectMetadataProps) {
  const [isOpen, setIsOpen] = useState(false);

  useEffect(() => {
    if (parsedData) {
      setIsOpen(true);
    }
  }, [parsedData]);

  if (!parsedData) {
    return null;
  }

  return (
    <div className="fixed inset-y-0 left-0 z-30 flex w-80 flex-col border-r border-zinc-800 bg-zinc-950/80 backdrop-blur-md">
      <div className="flex items-center justify-between border-b border-zinc-800 p-4">
        <h3 className="text-sm font-semibold text-zinc-200">Métadonnées du projet</h3>
        <button
          onClick={() => setIsOpen(false)}
          className="rounded-md p-1 text-zinc-500 hover:bg-zinc-800 hover:text-zinc-200"
        >
          <span className="material-symbols-rounded text-[18px]">close</span>
        </button>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        <div className="space-y-2">
          <h4 className="text-xs font-medium text-zinc-400 uppercase tracking-wider">Fichier</h4>
          <div className="text-sm text-zinc-200">{parsedData.filename}</div>
          <div className="text-xs text-zinc-500">{parsedData.total_lines} lignes</div>
        </div>

        <div className="space-y-2">
          <h4 className="text-xs font-medium text-zinc-400 uppercase tracking-wider">Variables globales</h4>
          {parsedData.global_variables.length > 0 ? (
            <div className="space-y-1">
              {parsedData.global_variables.map((varItem, index) => (
                <div key={index} className="text-sm text-zinc-200 flex justify-between">
                  <span>{varItem.name}</span>
                  <span className="text-zinc-500">{varItem.type}</span>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-xs text-zinc-500">Aucune variable globale</div>
          )}
        </div>

        <div className="space-y-2">
          <h4 className="text-xs font-medium text-zinc-400 uppercase tracking-wider">Procédures détectées</h4>
          {parsedData.procedures.length > 0 ? (
            <div className="space-y-1">
              {parsedData.procedures.map((proc, index) => (
                <button
                  key={index}
                  onClick={() => onSelectProcedure(proc.name)}
                  className="w-full text-left text-sm text-zinc-200 hover:bg-zinc-800/50 p-2 rounded-md transition-colors"
                >
                  {proc.name}
                </button>
              ))}
            </div>
          ) : (
            <div className="text-xs text-zinc-500">Aucune procédure détectée</div>
          )}
        </div>

        <div className="space-y-2">
          <h4 className="text-xs font-medium text-zinc-400 uppercase tracking-wider">Requêtes HFSQL</h4>
          {parsedData.hfsql_queries.length > 0 ? (
            <div className="space-y-2">
              {parsedData.hfsql_queries.map((query, index) => (
                <div key={index} className="text-xs bg-zinc-800/50 p-2 rounded-md">
                  <div className="font-mono text-zinc-300">{query.sql}</div>
                  <div className="text-[10px] text-zinc-500 mt-1">
                    Table: {query.target_table} | Type: {query.type}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-xs text-zinc-500">Aucune requête HFSQL</div>
          )}
        </div>

        <div className="space-y-2">
          <h4 className="text-xs font-medium text-zinc-400 uppercase tracking-wider">Dépendances</h4>
          {parsedData.dependencies.length > 0 ? (
            <div className="flex flex-wrap gap-1">
              {parsedData.dependencies.map((dep, index) => (
                <span 
                  key={index} 
                  className="inline-flex items-center rounded-full border border-zinc-700 bg-zinc-800/50 px-2 py-1 text-xs text-zinc-300"
                >
                  {dep}
                </span>
              ))}
            </div>
          ) : (
            <div className="text-xs text-zinc-500">Aucune dépendance</div>
          )}
        </div>
      </div>

      <div className="border-t border-zinc-800 p-4">
        <button
          onClick={() => {
            onFileLoad();
            setIsOpen(false);
          }}
          className="w-full rounded-md bg-indigo-600/15 py-2 px-3 text-sm font-medium text-indigo-400 hover:bg-indigo-600/20 transition-colors"
        >
          Charger le fichier dans l'éditeur
        </button>
      </div>
    </div>
  );
}