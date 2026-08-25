"use client";

import type { UIControl, UIWindowStructure } from "@/types";

interface UiPreviewProps {
  structure: UIWindowStructure | null;
}

const TYPE_BADGE: Record<UIControl["control_type"], { text: string; cls: string }> = {
  input: { text: "Input", cls: "border-sky-500/30 bg-sky-500/10 text-sky-300" },
  button: { text: "Button", cls: "border-indigo-500/30 bg-indigo-500/10 text-indigo-300" },
  table: { text: "Table", cls: "border-violet-500/30 bg-violet-500/10 text-violet-300" },
  label: { text: "Label", cls: "border-zinc-600 bg-zinc-800/60 text-zinc-300" },
  checkbox: { text: "Checkbox", cls: "border-emerald-500/30 bg-emerald-500/10 text-emerald-300" },
  select: { text: "Select", cls: "border-amber-500/30 bg-amber-500/10 text-amber-300" },
};

export default function UiPreview({ structure }: UiPreviewProps) {
  if (!structure) {
    return (
      <div className="flex h-full items-center justify-center p-4 text-xs text-zinc-500">
        Importez une fenêtre .wdw puis générez le composant pour voir l'aperçu.
      </div>
    );
  }

  const { title, controls } = structure;
  const buttons = controls.filter((c) => c.control_type === "button");

  return (
    <div className="h-full overflow-auto p-4">
      {/* Carte fenêtre simulée */}
      <div className="mx-auto max-w-md overflow-hidden rounded-xl border border-zinc-700 bg-zinc-900 shadow-lg">
        {/* Barre de titre */}
        <div className="flex items-center gap-2 border-b border-zinc-800 bg-gradient-to-r from-indigo-950/80 to-violet-950/60 px-4 py-2.5">
          <span className="flex gap-1.5">
            <span className="h-2.5 w-2.5 rounded-full bg-red-500/70" />
            <span className="h-2.5 w-2.5 rounded-full bg-yellow-500/70" />
            <span className="h-2.5 w-2.5 rounded-full bg-green-500/70" />
          </span>
          <span className="truncate text-xs font-medium text-zinc-200">
            {title ?? "Fenêtre WinDev"}
          </span>
        </div>

        {/* Corps */}
        <div className="flex flex-col gap-4 p-5">
          {controls
            .filter((c) => c.control_type === "label")
            .map((c) => (
              <p key={c.name} className="text-sm font-medium text-zinc-200">
                {c.label ?? c.default_value ?? c.name}
              </p>
            ))}

          {controls
            .filter((c) => c.control_type === "input")
            .map((c) => (
              <div key={c.name} className="flex flex-col gap-1.5">
                <label className="text-xs font-medium text-zinc-400">
                  {c.label ?? c.name}
                  <span className={`ml-2 rounded border px-1 py-px align-middle text-[9px] ${TYPE_BADGE.input.cls}`}>
                    SAI_
                  </span>
                </label>
                <input
                  readOnly
                  type={c.wtype === "entier" || c.wtype === "reel" || c.wtype === "monetaire" ? "number" : "text"}
                  placeholder={c.default_value ?? ""}
                  className="h-8 w-full cursor-default rounded-md border border-zinc-700 bg-zinc-800/60 px-2.5 text-xs text-zinc-300 placeholder:text-zinc-600 focus:outline-none"
                />
              </div>
            ))}

          {controls
            .filter((c) => c.control_type === "checkbox")
            .map((c) => (
              <label key={c.name} className="flex items-center gap-2 text-xs text-zinc-300">
                <input
                  type="checkbox"
                  defaultChecked={(c.default_value ?? "").toLowerCase() === "vrai"}
                  disabled
                  className="h-3.5 w-3.5 accent-indigo-500"
                />
                {c.label ?? c.name}
                <span className={`rounded border px-1 py-px text-[9px] ${TYPE_BADGE.checkbox.cls}`}>INT_</span>
              </label>
            ))}

          {controls
            .filter((c) => c.control_type === "select")
            .map((c) => (
              <div key={c.name} className="flex flex-col gap-1.5">
                <label className="text-xs font-medium text-zinc-400">
                  {c.label ?? c.name}
                  <span className={`ml-2 rounded border px-1 py-px align-middle text-[9px] ${TYPE_BADGE.select.cls}`}>
                    COMBO_
                  </span>
                </label>
                <select
                  disabled
                  className="h-8 w-full cursor-default rounded-md border border-zinc-700 bg-zinc-800/60 px-2 text-xs text-zinc-500"
                >
                  <option>{c.label ?? "Sélection…"}…</option>
                </select>
              </div>
            ))}

          {controls
            .filter((c) => c.control_type === "table")
            .map((c) => (
              <div key={c.name} className="flex flex-col gap-1.5">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-medium text-zinc-300">{c.label ?? c.name}</span>
                  <span className={`rounded border px-1 py-px text-[9px] ${TYPE_BADGE.table.cls}`}>
                    TABLE_ · shadcn
                  </span>
                </div>
                <div className="overflow-hidden rounded-lg border border-zinc-700">
                  <table className="w-full text-left text-[11px]">
                    <thead className="bg-zinc-800/80 text-zinc-400">
                      <tr>
                        {(c.columns.length ? c.columns : ["Colonne 1", "Colonne 2"]).map((col, i) => (
                          <th key={i} className="px-2.5 py-1.5 font-medium">
                            {col}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      <tr className="border-t border-zinc-800">
                        <td colSpan={Math.max(c.columns.length, 1)} className="px-2.5 py-3 text-center text-zinc-600">
                          Aucune ligne — branchée sur GET /api/{c.name.toLowerCase().replace("table_", "")}
                        </td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>
            ))}

          {buttons.length > 0 && (
            <div className="mt-1 flex items-center justify-end gap-2.5 border-t border-zinc-800 pt-4">
              {buttons.map((b, i) => (
                <button
                  key={b.name}
                  type="button"
                  disabled
                  className={
                    i === 0
                      ? "inline-flex h-8 items-center rounded-md bg-gradient-to-r from-indigo-600 to-violet-600 px-3.5 text-xs font-medium text-white opacity-90"
                      : "inline-flex h-8 items-center rounded-md border border-zinc-700 px-3.5 text-xs text-zinc-300 opacity-90"
                  }
                >
                  {b.label ?? b.name.split("_")[1]}
                </button>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Légende mapping WinDev → React */}
      <div className="mx-auto mt-4 max-w-md rounded-lg border border-zinc-800 bg-zinc-900/50 p-3">
        <p className="mb-2 text-[10px] font-semibold uppercase tracking-wider text-zinc-500">
          Mapping appliqué
        </p>
        <div className="flex flex-wrap gap-1.5">
          {Object.entries(TYPE_BADGE).map(([k, v]) => (
            <span key={k} className={`rounded border px-1.5 py-0.5 text-[9px] font-medium ${v.cls}`}>
              {v.text}
            </span>
          ))}
        </div>
      </div>
    </div>
  );
}
