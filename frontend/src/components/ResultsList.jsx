import { useState } from "react";
import CodePreview from "./CodePreview.jsx";

export default function ResultsList({ results }) {
  const [selected, setSelected] = useState(results[0] || null);

  // Reset selection when results change
  if (results.length > 0 && selected && !results.find((r) => r.chunk_id === selected.chunk_id)) {
    setSelected(results[0]);
  }

  return (
    <div className="flex gap-4 h-[calc(100vh-220px)] min-h-[400px]">
      {/* ── Left: result cards ──────────────────────────────── */}
      <div className="w-80 flex-shrink-0 overflow-y-auto space-y-1.5 pr-1">
        {results.map((r, i) => (
          <ResultCard
            key={r.chunk_id}
            result={r}
            index={i}
            isSelected={selected?.chunk_id === r.chunk_id}
            onClick={() => setSelected(r)}
          />
        ))}
      </div>

      {/* ── Right: code preview ─────────────────────────────── */}
      <div className="flex-1 overflow-hidden rounded-lg border border-gray-800">
        {selected ? (
          <CodePreview chunk={selected} />
        ) : (
          <div className="h-full flex items-center justify-center text-gray-700 text-sm">
            Select a result to preview
          </div>
        )}
      </div>
    </div>
  );
}

function ResultCard({ result, index, isSelected, onClick }) {
  const score = Math.round(result.score * 100);
  const isFunction = result.chunk_type === "function";

  return (
    <button
      onClick={onClick}
      className={`w-full text-left rounded-lg border px-3 py-2.5 transition-all
                  duration-100 group ${
        isSelected
          ? "border-blue-500/70 bg-blue-950/40 shadow-sm shadow-blue-900/20"
          : "border-gray-800 bg-gray-900/60 hover:border-gray-700 hover:bg-gray-900"
      }`}
    >
      {/* Top row: type badge + name + score */}
      <div className="flex items-center gap-2 mb-1">
        <span
          className={`text-[10px] px-1.5 py-0.5 rounded font-medium flex-shrink-0 ${
            isFunction
              ? "bg-blue-900/70 text-blue-300 border border-blue-800/50"
              : "bg-purple-900/70 text-purple-300 border border-purple-800/50"
          }`}
        >
          {isFunction ? "fn" : "cls"}
        </span>

        <span className="text-gray-100 text-xs font-medium truncate flex-1">
          {result.name}
        </span>

        <ScorePill score={score} />
      </div>

      {/* Repo + file path */}
      <p className="text-gray-600 text-[10px] truncate leading-tight">
        <span className="text-gray-500">{result.repo_name}</span>
        <span className="mx-1 text-gray-700">·</span>
        <span>{result.file_path}</span>
        {result.start_line && (
          <span className="text-gray-700">:{result.start_line}</span>
        )}
      </p>
    </button>
  );
}

function ScorePill({ score }) {
  const color =
    score >= 80
      ? "text-green-400"
      : score >= 60
      ? "text-yellow-400"
      : "text-gray-500";

  return (
    <span className={`text-[10px] font-mono flex-shrink-0 ${color}`}>
      {score}%
    </span>
  );
}
