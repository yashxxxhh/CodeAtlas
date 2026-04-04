import { useState, useRef } from "react";

const EXAMPLES = [
  "functions that parse JWT tokens",
  "class that manages database connections",
  "recursive file system walker",
  "error handling middleware",
  "function that validates email addresses",
  "async HTTP request handler",
];

export default function SearchBar({ onSearch, loading }) {
  const [value, setValue] = useState("");
  const [showExamples, setShowExamples] = useState(false);
  const inputRef = useRef(null);

  function handleSubmit(e) {
    e.preventDefault();
    const q = value.trim();
    if (q) {
      onSearch(q);
      setShowExamples(false);
    }
  }

  function handleExample(ex) {
    setValue(ex);
    setShowExamples(false);
    onSearch(ex);
  }

  return (
    <div className="relative">
      <form onSubmit={handleSubmit} className="flex gap-2">
        {/* Search icon */}
        <div className="relative flex-1">
          <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500 text-sm select-none pointer-events-none">
            ⌕
          </span>
          <input
            ref={inputRef}
            type="text"
            value={value}
            onChange={(e) => setValue(e.target.value)}
            onFocus={() => setShowExamples(true)}
            onBlur={() => setTimeout(() => setShowExamples(false), 150)}
            placeholder="Describe what the code does..."
            autoComplete="off"
            spellCheck={false}
            className="w-full bg-gray-900 border border-gray-700 rounded-lg
                       pl-8 pr-4 py-3 text-sm text-gray-100 placeholder-gray-600
                       focus:outline-none focus:border-blue-500 focus:ring-1
                       focus:ring-blue-500/30 transition-all duration-150"
          />
        </div>

        <button
          type="submit"
          disabled={loading || !value.trim()}
          className="px-5 py-3 bg-blue-600 hover:bg-blue-500 active:bg-blue-700
                     disabled:opacity-40 disabled:cursor-not-allowed
                     rounded-lg text-sm font-medium transition-colors
                     whitespace-nowrap flex items-center gap-2"
        >
          {loading ? (
            <>
              <span className="inline-block w-3 h-3 border-2 border-white/40
                               border-t-white rounded-full animate-spin" />
              Searching
            </>
          ) : (
            "Search"
          )}
        </button>
      </form>

      {/* Example queries dropdown */}
      {showExamples && !value && (
        <div className="absolute top-full left-0 right-0 mt-1 bg-gray-900
                        border border-gray-700 rounded-lg shadow-xl z-20 overflow-hidden">
          <p className="px-3 py-2 text-xs text-gray-600 border-b border-gray-800">
            Example queries
          </p>
          {EXAMPLES.map((ex) => (
            <button
              key={ex}
              onMouseDown={() => handleExample(ex)}
              className="w-full text-left px-3 py-2 text-sm text-gray-400
                         hover:bg-gray-800 hover:text-gray-200 transition-colors"
            >
              <span className="text-gray-600 mr-2">⌕</span>
              {ex}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
