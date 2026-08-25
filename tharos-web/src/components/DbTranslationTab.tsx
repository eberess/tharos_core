"use client";

import { useState, useEffect } from "react";
import type { ParseFileResponse } from "@/types";
import { translateDbQueries } from "@/lib/api";

interface DbTranslationTabProps {
  parsedData: ParseFileResponse | null;
  filename: string | null;
  content: string | null;
}

export default function DbTranslationTab({ parsedData, filename, content }: DbTranslationTabProps) {
  const [translationData, setTranslationData] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!filename || !content) return;

    const loadTranslations = async () => {
      try {
        setLoading(true);
        // We'll translate all HFSQL queries in the current file
        const res = await translateDbQueries(filename, content);
        setTranslationData(res);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Erreur lors de la traduction");
      } finally {
        setLoading(false);
      }
    };

    loadTranslations();
  }, [filename, content]);

  if (!parsedData || !content || !filename) {
    return (
      <div className="text-center text-xs text-zinc-600 py-4">
        Aucun fichier sélectionné pour la traduction
      </div>
    );
  }

  if (loading) {
    return (
      <div className="text-center text-xs text-zinc-600 py-4 flex items-center justify-center">
        <span className="material-symbols-rounded animate-spin">sync</span>
        <span className="ml-2">Traduction des requêtes HFSQL...</span>
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

  if (!translationData || !translationData.translations) {
    return (
      <div className="text-center text-xs text-zinc-600 py-4">
        Aucune traduction disponible
      </div>
    );
  }

  const translations = Object.entries(translationData.translations);

  return (
    <div className="space-y-4 p-4">
      {translations.length === 0 ? (
        <div className="text-center text-xs text-zinc-600 py-4">
          Aucune requête HFSQL à traduire dans ce fichier
        </div>
      ) : (
        <div className="space-y-3">
          <h4 className="text-[11px] font-medium uppercase tracking-wider text-zinc-500 mb-2">
            Traductions de requêtes HFSQL
          </h4>
          {translations.map(([procName, translation]: [string, any]) => (
            <div 
              key={procName} 
              className="rounded-lg border border-zinc-800 bg-zinc-900/60 p-3"
            >
              <div className="flex items-start justify-between gap-2 mb-3">
                <h5 className="font-medium text-zinc-200 text-sm">{procName}</h5>
                {translation.warnings && translation.warnings.length > 0 && (
                  <span className="inline-flex h-4 w-4 rounded-full bg-yellow-500/15 p-0.5">
                    <span className="material-symbols-rounded text-[12px] leading-none text-yellow-400">
                      warning
                    </span>
                  </span>
                )}
              </div>
              
              {/* Original query */}
              <div className="mb-2">
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-[10px] font-medium text-zinc-500">Original</span>
                  <span className="text-xs bg-zinc-800/60 rounded px-2 py-0.5 text-zinc-400">
                    {translation.original_query}
                  </span>
                </div>
                <pre className="text-[10px] text-zinc-400 bg-zinc-900/60 border border-zinc-800 rounded-lg p-2 overflow-auto max-h-32 whitespace-pre-wrap">
                  {translation.original_query}
                </pre>
              </div>

              {/* Translated code */}
              <div className="mb-2">
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-[10px] font-medium text-zinc-500">Traduit</span>
                  <span className="text-xs bg-emerald-500/15 rounded px-2 py-0.5 text-emerald-300">
                    SQLAlchemy 2.0
                  </span>
                </div>
                <pre className="text-xs text-green-400 bg-zinc-900/60 border border-zinc-800 rounded-lg p-2 overflow-auto max-h-32 whitespace-pre-wrap">
                  {translation.translated_code}
                </pre>
              </div>

              {/* Warnings if any */}
              {translation.warnings && translation.warnings.length > 0 && (
                <div className="mt-2 text-xs text-yellow-400">
                  <div className="flex items-start gap-2">
                    <span className="material-symbols-rounded text-[16px] leading-none mt-0.5">
                      warning
                    </span>
                    <ul className="list-disc pl-4 space-y-1">
                      {translation.warnings.map((warning: string, i: number) => (
                        <li key={i}>{warning}</li>
                      ))}
                    </ul>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}