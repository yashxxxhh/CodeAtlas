import { useState } from "react";

export default function CodePreview({ chunk }) {
  const [copied, setCopied] = useState(false);

  function handleCopy() {
    navigator.clipboard.writeText(chunk.code).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  }

  const lines = chunk.code.split("\n");

  return (
    <div className="h-full flex flex-col bg-gray-900">
      {/* ── Header bar ──────────────────────────────────────── */}
      <div className="flex items-center justify-between px-4 py-2.5
                      border-b border-gray-800 flex-shrink-0 gap-3">
        <div className="flex items-center gap-2 min-w-0">
          {/* Type badge */}
          <span
            className={`text-[10px] px-1.5 py-0.5 rounded font-medium flex-shrink-0 ${
              chunk.chunk_type === "function"
                ? "bg-blue-900/70 text-blue-300 border border-blue-800/50"
                : "bg-purple-900/70 text-purple-300 border border-purple-800/50"
            }`}
          >
            {chunk.chunk_type === "function" ? "function" : "class"}
          </span>

          {/* Function/class name */}
          <span className="text-blue-300 text-sm font-semibold truncate">
            {chunk.name}
          </span>
        </div>

        <div className="flex items-center gap-3 flex-shrink-0">
          {/* Score */}
          <span className="text-gray-600 text-xs">
            {Math.round(chunk.score * 100)}% match
          </span>

          {/* Copy button */}
          <button
            onClick={handleCopy}
            className="text-xs text-gray-500 hover:text-gray-300
                       transition-colors flex items-center gap-1"
          >
            {copied ? (
              <span className="text-green-400">✓ Copied</span>
            ) : (
              <>
                <span>⎘</span>
                <span>Copy</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* ── File path breadcrumb ─────────────────────────────── */}
      <div className="px-4 py-1.5 border-b border-gray-800/50 flex-shrink-0
                      flex items-center gap-2">
        <span className="text-gray-600 text-[10px]">
          {chunk.repo_name}
        </span>
        <span className="text-gray-700 text-[10px]">/</span>
        <span className="text-gray-500 text-[10px] font-mono truncate">
          {chunk.file_path}
        </span>
        {chunk.start_line && (
          <>
            <span className="text-gray-700 text-[10px]">·</span>
            <span className="text-gray-600 text-[10px]">
              line {chunk.start_line}
            </span>
          </>
        )}
      </div>

      {/* ── Code block with line numbers ─────────────────────── */}
      <div className="flex-1 overflow-auto">
        <table className="w-full border-collapse text-xs">
          <tbody>
            {lines.map((line, i) => {
              const lineNum = (chunk.start_line || 1) + i;
              return (
                <tr key={i} className="hover:bg-gray-800/30 group">
                  {/* Line number */}
                  <td className="select-none text-right pr-4 pl-4 py-0 text-gray-700
                                 w-12 align-top leading-6 group-hover:text-gray-500
                                 border-r border-gray-800/50 font-mono">
                    {lineNum}
                  </td>
                  {/* Code */}
                  <td className="pl-4 pr-4 py-0 leading-6 whitespace-pre font-mono
                                 text-gray-300 align-top">
                    <CodeLine text={line} />
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* ── Footer meta ─────────────────────────────────────── */}
      <div className="flex items-center gap-4 px-4 py-2 border-t border-gray-800
                      flex-shrink-0 text-[10px] text-gray-700">
        <span>Python</span>
        <span>·</span>
        <span>{lines.length} lines</span>
        <span>·</span>
        <span>chunk #{chunk.chunk_id}</span>
      </div>
    </div>
  );
}

/**
 * Minimal syntax coloring for Python without a library.
 * Handles: keywords, strings, comments, numbers, decorators.
 */
function CodeLine({ text }) {
  // Simple tokenizer — good enough for readable previews
  const parts = tokenize(text);
  return (
    <>
      {parts.map((p, i) => (
        <span key={i} className={TOKEN_COLORS[p.type] || "text-gray-300"}>
          {p.text}
        </span>
      ))}
    </>
  );
}

const PY_KEYWORDS = new Set([
  "def","class","return","import","from","if","else","elif","for","while",
  "try","except","finally","with","as","pass","break","continue","raise",
  "yield","lambda","not","and","or","in","is","None","True","False",
  "async","await","global","nonlocal","del","assert",
]);

const TOKEN_COLORS = {
  keyword:   "text-purple-400",
  string:    "text-green-400",
  comment:   "text-gray-600 italic",
  number:    "text-amber-400",
  decorator: "text-blue-400",
  builtin:   "text-cyan-400",
  plain:     "text-gray-300",
};

function tokenize(text) {
  const tokens = [];
  let i = 0;

  while (i < text.length) {
    // Comment
    if (text[i] === "#") {
      tokens.push({ type: "comment", text: text.slice(i) });
      break;
    }
    // Decorator
    if (text[i] === "@" && (i === 0 || /\s/.test(text[i - 1]))) {
      const end = text.slice(i).search(/[\s(]|$/);
      tokens.push({ type: "decorator", text: text.slice(i, i + (end === -1 ? text.length : end)) });
      i += end === -1 ? text.length - i : end;
      continue;
    }
    // String (single or double quote, single line)
    if (text[i] === '"' || text[i] === "'") {
      const q = text[i];
      const triple = text.slice(i, i + 3) === q.repeat(3);
      const delim = triple ? q.repeat(3) : q;
      let j = i + delim.length;
      while (j < text.length) {
        if (text[j] === "\\") { j += 2; continue; }
        if (text.slice(j, j + delim.length) === delim) { j += delim.length; break; }
        j++;
      }
      tokens.push({ type: "string", text: text.slice(i, j) });
      i = j;
      continue;
    }
    // Number
    if (/[0-9]/.test(text[i]) && (i === 0 || /\W/.test(text[i - 1]))) {
      const m = text.slice(i).match(/^[0-9._xXbBoO]+/);
      if (m) {
        tokens.push({ type: "number", text: m[0] });
        i += m[0].length;
        continue;
      }
    }
    // Word (keyword or plain)
    if (/[a-zA-Z_]/.test(text[i])) {
      const m = text.slice(i).match(/^[a-zA-Z_][a-zA-Z0-9_]*/);
      if (m) {
        const word = m[0];
        tokens.push({ type: PY_KEYWORDS.has(word) ? "keyword" : "plain", text: word });
        i += word.length;
        continue;
      }
    }
    // Anything else — grab a run of non-word chars
    const m = text.slice(i).match(/^[^a-zA-Z0-9_"'#@]+/);
    if (m) {
      tokens.push({ type: "plain", text: m[0] });
      i += m[0].length;
    } else {
      tokens.push({ type: "plain", text: text[i] });
      i++;
    }
  }

  return tokens;
}
