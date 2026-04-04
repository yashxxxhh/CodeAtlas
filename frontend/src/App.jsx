import { useState, useCallback } from "react";
import UploadRepo from "./components/UploadRepo.jsx";
import SearchBar from "./components/SearchBar.jsx";
import ResultsList from "./components/ResultsList.jsx";
import RepoList from "./components/RepoList.jsx";

const API_BASE = "/api";

export default function App() {
  const [tab, setTab] = useState("search"); // "search" | "upload" | "repos"
  const [results, setResults] = useState([]);
  const [searching, setSearching] = useState(false);
  const [searchError, setSearchError] = useState(null);
  const [lastQuery, setLastQuery] = useState("");
  const [hasSearched, setHasSearched] = useState(false);

  const handleSearch = useCallback(async (query) => {
    setLastQuery(query);
    setSearching(true);
    setSearchError(null);
    setHasSearched(true);

    try {
      const res = await fetch(
        `${API_BASE}/search?query=${encodeURIComponent(query)}&top_k=10`
      );
      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.detail || "Search failed");
      }

      setResults(data.results || []);
    } catch (err) {
      setSearchError(err.message);
      setResults([]);
    } finally {
      setSearching(false);
    }
  }, []);

  const tabs = [
    { id: "search", label: "Search", icon: "⌕" },
    { id: "upload", label: "Upload Repo", icon: "↑" },
    { id: "repos",  label: "My Repos",   icon: "◫" },
  ];

  return (
    <div className="min-h-screen bg-gray-950 flex flex-col">
      {/* ── Header ─────────────────────────────────────────────── */}
      <header className="border-b border-gray-800 bg-gray-950 sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6">
          <div className="flex items-center justify-between h-14">
            {/* Logo */}
            <div className="flex items-center gap-3">
              <span className="text-blue-400 text-2xl select-none">⬡</span>
              <div className="flex flex-col leading-none">
                <span className="text-white font-semibold text-sm tracking-wide">
                  CodeAtlas
                </span>
                <span className="text-gray-500 text-xs">
                  Semantic code search
                </span>
              </div>
            </div>

            {/* Nav tabs */}
            <nav className="flex items-center gap-1">
              {tabs.map((t) => (
                <button
                  key={t.id}
                  onClick={() => setTab(t.id)}
                  className={`flex items-center gap-1.5 px-3 py-1.5 rounded text-xs
                    font-medium transition-all duration-150 ${
                    tab === t.id
                      ? "bg-blue-600 text-white"
                      : "text-gray-400 hover:text-gray-200 hover:bg-gray-800"
                  }`}
                >
                  <span className="text-sm">{t.icon}</span>
                  <span className="hidden sm:inline">{t.label}</span>
                </button>
              ))}
            </nav>
          </div>
        </div>
      </header>

      {/* ── Main ───────────────────────────────────────────────── */}
      <main className="flex-1 max-w-7xl mx-auto w-full px-4 sm:px-6 py-6">
        {tab === "upload" && (
          <UploadRepo apiBase={API_BASE} onDone={() => setTab("repos")} />
        )}

        {tab === "repos" && (
          <RepoList apiBase={API_BASE} />
        )}

        {tab === "search" && (
          <div className="space-y-5">
            {/* Hero line — only show when no search yet */}
            {!hasSearched && (
              <div className="text-center py-10">
                <p className="text-gray-600 text-sm mb-1">
                  Search your indexed repositories with plain English
                </p>
                <p className="text-gray-700 text-xs">
                  e.g. "functions that handle JWT auth" · "class that manages database
                  connections" · "recursive file walker"
                </p>
              </div>
            )}

            <SearchBar onSearch={handleSearch} loading={searching} />

            {searchError && (
              <div className="rounded-lg bg-red-900/30 border border-red-800/50 px-4 py-3 text-red-400 text-sm">
                {searchError.includes("FAISS index not found")
                  ? "No indexed repos yet. Upload a repo and run the 4 workers first."
                  : `Error: ${searchError}`}
              </div>
            )}

            {hasSearched && !searching && !searchError && (
              <p className="text-gray-600 text-xs">
                {results.length === 0
                  ? `No results for "${lastQuery}"`
                  : `${results.length} result${results.length !== 1 ? "s" : ""} for `}
                {results.length > 0 && (
                  <span className="text-blue-400">"{lastQuery}"</span>
                )}
              </p>
            )}

            {results.length > 0 && <ResultsList results={results} />}
          </div>
        )}
      </main>

      {/* ── Footer ─────────────────────────────────────────────── */}
      <footer className="border-t border-gray-900 py-3 text-center text-gray-700 text-xs">
        CodeAtlas · semantic code search · powered by sentence-transformers + FAISS
      </footer>
    </div>
  );
}
