"use client";

import { useState } from "react";
import type { AttemptInfo } from "@/types";

interface LogPanelProps {
  attempts: AttemptInfo[];
  isRunning: boolean;
  success: boolean | null;
}

export default function LogPanel({ attempts, isRunning, success }: LogPanelProps) {
  const [activeTab, setActiveTab] = useState("report");
  
  const tabs = [
    { id: "report", label: "Rapport de couverture" },
    { id: "pytest", label: "Logs Pytest" },
    { id: "history", label: "Historique des tentatives" }
  ];

  return (
    <div className="flex h-full flex-col">
      {/* Tab Navigation */}
      <div className="flex border-b border-zinc-800 bg-zinc-900/60">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`px-4 py-2 text-xs font-medium transition-colors ${
              activeTab === tab.id
                ? "border-b border-indigo-500 text-indigo-300"
                : "text-zinc-500 hover:text-zinc-300"
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      <div className="flex-1 overflow-auto p-4">
        {activeTab === "report" && (
          <div className="space-y-4 text-xs">
            <div className="rounded-lg border border-zinc-800 bg-zinc-900/60 p-3">
              <h4 className="font-medium text-zinc-200">Résumé de la couverture</h4>
              <div className="mt-2 space-y-1">
                <div className="flex justify-between">
                  <span className="text-zinc-500">Procédures détectées:</span>
                  <span className="text-zinc-200">32</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-zinc-500">Procédures transpilées:</span>
                  <span className="text-emerald-400">28 (87%)</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-zinc-500">Dépendances résolues:</span>
                  <span className="text-emerald-400">15/15</span>
                </div>
              </div>
            </div>

            <div className="rounded-lg border border-zinc-800 bg-zinc-900/60 p-3">
              <h4 className="font-medium text-zinc-200">Dépendances</h4>
              <ul className="mt-2 space-y-1 text-zinc-400">
                <li>Utilisation des bibliothèques standart Python (datetime, os)</li>
                <li>Compatibilité avec pandas pour traitement des données</li>
                <li>Mise à disposition du code dans un package PyPI</li>
              </ul>
            </div>

            <div className="rounded-lg border border-zinc-800 bg-zinc-900/60 p-3">
              <h4 className="font-medium text-zinc-200">Notes de migration</h4>
              <ul className="mt-2 space-y-1 text-zinc-400">
                <li>Certaines fonctionnalités WinDev nécessitent des adaptations</li>
                <li>Les dates doivent être converties au format ISO8601</li>
                <li>Les types de données doivent être vérifiés après transpilation</li>
              </ul>
            </div>
          </div>
        )}

        {activeTab === "pytest" && (
          <div className="space-y-4 text-xs">
            <div className="rounded-lg border border-zinc-800 bg-zinc-900/60 p-3">
              <h4 className="font-medium text-zinc-200">Tests unitaires</h4>
              <div className="mt-2 space-y-2">
                <div className="flex items-center gap-2">
                  <span className="inline-flex h-2 w-2 rounded-full bg-emerald-500"></span>
                  <span>test_procedure1.py: OK</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="inline-flex h-2 w-2 rounded-full bg-emerald-500"></span>
                  <span>test_procedure2.py: OK</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="inline-flex h-2 w-2 rounded-full bg-yellow-500"></span>
                  <span>test_procedure3.py: WARNING (type mismatch)</span>
                </div>
              </div>
            </div>

            <div className="rounded-lg border border-zinc-800 bg-zinc-900/60 p-3">
              <h4 className="font-medium text-zinc-200">Résumé des tests</h4>
              <div className="mt-2 space-y-1">
                <div className="flex justify-between">
                  <span className="text-zinc-500">Tests exécutés:</span>
                  <span className="text-zinc-200">28</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-zinc-500">Tests réussis:</span>
                  <span className="text-emerald-400">26</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-zinc-500">Tests avec avertissements:</span>
                  <span className="text-yellow-400">2</span>
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === "history" && (
          <div className="space-y-3 text-xs">
            {attempts.length > 0 ? (
              attempts.map((attempt, index) => (
                <div 
                  key={index} 
                  className="rounded-lg border border-zinc-800 bg-zinc-900/60 p-3"
                >
                  <div className="flex justify-between">
                    <h4 className="font-medium text-zinc-200">Tentative #{attempt.attempt}</h4>
                    <span className="text-zinc-500">
                      {new Date().toLocaleTimeString()}
                    </span>
                  </div>
                  <div className="mt-2 space-y-1">
                    <div className="flex justify-between">
                      <span className="text-zinc-500">Résultat:</span>
                      <span className={attempt.passed ? "text-emerald-400" : "text-red-400"}>
                        {attempt.passed ? "Réussie" : "Échouée"}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-zinc-500">Code de sortie:</span>
                      <span className="text-zinc-200">{attempt.exit_code}</span>
                    </div>
                    {attempt.logs && (
                      <div className="mt-2 rounded bg-zinc-800/40 p-2 text-zinc-300">
                        <p className="font-medium">Logs:</p>
                        <p className="whitespace-pre-wrap">{attempt.logs}</p>
                      </div>
                    )}
                  </div>
                </div>
              ))
            ) : (
              <div className="flex h-full items-center justify-center text-zinc-500">
                Aucune tentative de transpilation effectuée
              </div>
            )}
          </div>
        )}
      </div>

      {/* Status Bar */}
      <div className="flex items-center justify-between border-t border-zinc-800 bg-zinc-900/60 px-4 py-2 text-xs">
        <div className="flex items-center gap-2">
          {isRunning && (
            <span className="inline-flex h-2 w-2 rounded-full bg-yellow-500 animate-pulse"></span>
          )}
          <span className="text-zinc-400">
            {isRunning ? "Transpilation en cours…" : success === true ? "Transpilation réussie" : success === false ? "Transpilation échouée" : "Prêt"}
          </span>
        </div>
        <span className="text-zinc-500">
          Projet: {attempts.length > 0 ? "Projet de test" : "Sans nom"}
        </span>
      </div>
    </div>
  );
}