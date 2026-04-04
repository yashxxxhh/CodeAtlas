import { useState, useEffect, useCallback } from "react";

const STATUS_STYLES = {
  pending:  { dot: "bg-gray-500",   text: "text-gray-400",  label: "Pending" },
  cloned:   { dot: "bg-blue-500",   text: "text-blue-400",  label: "Cloned" },
  parsed:   { dot: "bg-yellow-500", text: "text-yellow-400",label: "Parsed" },
  embedded: { dot: "bg-orange-500", text: "text-orange-400",label: "Embedded" },
  indexed:  { dot: "bg-green-500",  text: "text-green-400", label: "Indexed ✓" },
  failed:   { dot: "bg-red-500",    text: "text-red-400",   label: "Failed" },
};

const PIPELINE_STEPS = ["pending", "cloned", "parsed", "embedded", "indexed"];

export default function RepoList({ apiBase }) {
  const [repos, setRepos] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [expanded, setExpanded] = useState(null);

  const fetchRepos = useCallback(async () => {
    try {
      const res = await fetch(`${apiBase}/repos`);
      if (!res.ok) throw new Error("Failed to fetch repos");
      const data = await res.json();
      setRepos(data);
      setError(null);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, [apiBase]);

  useEffect(() => {
    fetchRepos();
    // Poll every 5s to catch worker status updates
    const id = setInterval(fetchRepos, 5000);
    return () => clearInterval(id);
  }, [fetchRepos]);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-16 text-gray-600 text-sm gap-2">
        <span className="inline-block w-4 h-4 border-2 border-gray-700
                         border-t-gray-400 rounded-full animate-spin" />
        Loading repositories…
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-red-400 text-sm text-center py-8">{error}</div>
    );
  }

  if (repos.length === 0) {
    return (
      <div className="text-center py-16">
        <p className="text-gray-600 text-sm mb-2">No repositories yet.</p>
        <p className="text-gray-700 text-xs">
          Go to "Upload Repo" to add your first repository.
        </p>
      </div>
    );
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-gray-300 font-semibold text-sm">
          {repos.length} repositor{repos.length === 1 ? "y" : "ies"}
        </h2>
        <button
          onClick={fetchRepos}
          className="text-xs text-gray-600 hover:text-gray-400 transition-colors"
        >
          ↻ Refresh
        </button>
      </div>

      <div className="space-y-2">
        {repos.map((repo) => (
          <RepoCard
            key={repo.id}
            repo={repo}
            apiBase={apiBase}
            isExpanded={expanded === repo.id}
            onToggle={() => setExpanded(expanded === repo.id ? null : repo.id)}
          />
        ))}
      </div>
    </div>
  );
}

function RepoCard({ repo, apiBase, isExpanded, onToggle }) {
  const style = STATUS_STYLES[repo.status] || STATUS_STYLES.pending;
  const stepIndex = PIPELINE_STEPS.indexOf(repo.status);

  return (
    <div className="border border-gray-800 rounded-xl overflow-hidden bg-gray-900/40">
      {/* Main row */}
      <button
        onClick={onToggle}
        className="w-full text-left px-4 py-3 flex items-center gap-3 hover:bg-gray-900/60 transition-colors"
      >
        {/* Status dot */}
        <span className={`w-2 h-2 rounded-full flex-shrink-0 ${style.dot}`} />

        {/* Repo name */}
        <span className="text-gray-200 text-sm font-medium flex-1 truncate">
          {repo.name}
        </span>

        {/* Status label */}
        <span className={`text-xs flex-shrink-0 ${style.text}`}>
          {style.label}
        </span>

        {/* Chunk count */}
        {repo.chunk_count > 0 && (
          <span className="text-gray-600 text-xs flex-shrink-0">
            {repo.chunk_count} chunks
          </span>
        )}

        {/* Expand chevron */}
        <span className="text-gray-700 text-xs flex-shrink-0 transition-transform duration-200"
              style={{ transform: isExpanded ? "rotate(180deg)" : "none" }}>
          ▾
        </span>
      </button>

      {/* Expanded details */}
      {isExpanded && (
        <div className="px-4 pb-4 border-t border-gray-800/50 pt-3 space-y-3">
          {/* Pipeline progress */}
          <div>
            <p className="text-xs text-gray-600 mb-2">Pipeline progress</p>
            <div className="flex items-center gap-1">
              {PIPELINE_STEPS.map((step, i) => {
                const done = i <= stepIndex && repo.status !== "failed";
                const current = i === stepIndex;
                const failed = repo.status === "failed" && i === stepIndex;
                return (
                  <div key={step} className="flex items-center gap-1 flex-1">
                    <div className={`flex-1 h-1.5 rounded-full transition-colors ${
                      failed ? "bg-red-700" :
                      done   ? "bg-blue-600" :
                               "bg-gray-800"
                    }`} />
                    {i < PIPELINE_STEPS.length - 1 && (
                      <div className={`w-1 h-1 rounded-full ${
                        done && !failed ? "bg-blue-600" : "bg-gray-800"
                      }`} />
                    )}
                  </div>
                );
              })}
            </div>
            <div className="flex justify-between mt-1">
              {PIPELINE_STEPS.map((step) => (
                <span key={step} className="text-[9px] text-gray-700 capitalize">
                  {step}
                </span>
              ))}
            </div>
          </div>

          {/* Metadata */}
          <div className="grid grid-cols-2 gap-2 text-xs">
            <div>
              <span className="text-gray-600">Repo ID</span>
              <span className="text-gray-400 ml-2">#{repo.id}</span>
            </div>
            <div>
              <span className="text-gray-600">Chunks</span>
              <span className="text-gray-400 ml-2">{repo.chunk_count || 0}</span>
            </div>
            {repo.source_url && (
              <div className="col-span-2">
                <span className="text-gray-600">Git URL</span>
                <span className="text-gray-400 ml-2 font-mono text-[10px] break-all">
                  {repo.source_url}
                </span>
              </div>
            )}
            <div className="col-span-2">
              <span className="text-gray-600">Added</span>
              <span className="text-gray-400 ml-2">
                {new Date(repo.created_at).toLocaleString()}
              </span>
            </div>
          </div>

          {/* Error message */}
          {repo.status === "failed" && (
            <div className="rounded-lg bg-red-950/40 border border-red-900/40 px-3 py-2">
              <p className="text-red-400 text-xs font-semibold mb-0.5">Error</p>
              <p className="text-red-300/70 text-xs font-mono break-all">
                Check worker logs for details.
              </p>
            </div>
          )}

          {/* Next step hint */}
          {repo.status !== "indexed" && repo.status !== "failed" && (
            <NextStepHint status={repo.status} />
          )}
        </div>
      )}
    </div>
  );
}

function NextStepHint({ status }) {
  const hints = {
    pending:  "python workers/clone_worker.py",
    cloned:   "python workers/parser_worker.py",
    parsed:   "python workers/embedding_worker.py",
    embedded: "python workers/index_worker.py",
  };
  const cmd = hints[status];
  if (!cmd) return null;

  return (
    <div className="flex items-center gap-2 bg-gray-800/60 rounded-lg px-3 py-2">
      <span className="text-gray-600 text-[10px] flex-shrink-0">Next step:</span>
      <code className="text-blue-400 text-[10px] font-mono">{cmd}</code>
    </div>
  );
}
