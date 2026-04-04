import { useState, useRef } from "react";

export default function UploadRepo({ apiBase, onDone }) {
  const [mode, setMode] = useState("zip");          // "zip" | "git"
  const [file, setFile] = useState(null);
  const [gitUrl, setGitUrl] = useState("");
  const [repoName, setRepoName] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState(null);       // { ok, message, repo_id }
  const [dragOver, setDragOver] = useState(false);
  const fileInputRef = useRef(null);

  function handleDrop(e) {
    e.preventDefault();
    setDragOver(false);
    const dropped = e.dataTransfer.files[0];
    if (dropped && dropped.name.endsWith(".zip")) {
      setFile(dropped);
      if (!repoName) setRepoName(dropped.name.replace(".zip", ""));
    }
  }

  async function handleSubmit() {
    if (!repoName.trim()) return alert("Please enter a repository name.");
    setSubmitting(true);
    setResult(null);

    try {
      let res, data;

      if (mode === "zip") {
        if (!file) return alert("Please select a .zip file.");
        const form = new FormData();
        form.append("file", file);
        form.append("repo_name", repoName.trim());
        res = await fetch(`${apiBase}/upload`, { method: "POST", body: form });
      } else {
        if (!gitUrl.trim()) return alert("Please enter a Git URL.");
        const form = new FormData();
        form.append("repo_name", repoName.trim());
        form.append("git_url", gitUrl.trim());
        res = await fetch(`${apiBase}/register-git`, { method: "POST", body: form });
      }

      data = await res.json();
      setResult({ ok: res.ok, ...data });
    } catch (err) {
      setResult({ ok: false, message: err.message });
    } finally {
      setSubmitting(false);
    }
  }

  function handleReset() {
    setFile(null);
    setGitUrl("");
    setRepoName("");
    setResult(null);
  }

  if (result?.ok) {
    return (
      <SuccessCard
        repoId={result.repo_id}
        repoName={repoName}
        mode={mode}
        onAddAnother={handleReset}
        onViewRepos={onDone}
      />
    );
  }

  return (
    <div className="max-w-lg mx-auto">
      <div className="mb-6">
        <h2 className="text-gray-200 font-semibold text-base mb-1">
          Add a repository
        </h2>
        <p className="text-gray-600 text-xs">
          Upload a .zip file or provide a public Git URL. After submitting, run
          the 4 worker scripts to index the code.
        </p>
      </div>

      {/* Mode selector */}
      <div className="flex gap-1 mb-5 bg-gray-900 p-1 rounded-lg border border-gray-800">
        {[
          { id: "zip", label: "ZIP Upload", icon: "↑" },
          { id: "git", label: "Git URL", icon: "⎇" },
        ].map((m) => (
          <button
            key={m.id}
            onClick={() => setMode(m.id)}
            className={`flex-1 flex items-center justify-center gap-1.5 py-2 rounded
                        text-xs font-medium transition-all ${
              mode === m.id
                ? "bg-gray-800 text-gray-100 shadow-sm"
                : "text-gray-500 hover:text-gray-300"
            }`}
          >
            <span>{m.icon}</span>
            {m.label}
          </button>
        ))}
      </div>

      {/* Repo name */}
      <div className="mb-4">
        <label className="block text-xs text-gray-500 mb-1.5">
          Repository name
        </label>
        <input
          type="text"
          value={repoName}
          onChange={(e) => setRepoName(e.target.value)}
          placeholder="my-project"
          className="w-full bg-gray-900 border border-gray-700 rounded-lg px-3 py-2.5
                     text-sm text-gray-100 placeholder-gray-600 focus:outline-none
                     focus:border-blue-500 transition-colors"
        />
      </div>

      {/* ZIP drop zone */}
      {mode === "zip" && (
        <div
          onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
          onDragLeave={() => setDragOver(false)}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current?.click()}
          className={`mb-4 border-2 border-dashed rounded-xl p-8 text-center cursor-pointer
                      transition-all duration-150 ${
            dragOver
              ? "border-blue-500 bg-blue-950/20"
              : file
              ? "border-green-700/60 bg-green-950/20"
              : "border-gray-700 hover:border-gray-600 hover:bg-gray-900/50"
          }`}
        >
          <input
            ref={fileInputRef}
            type="file"
            accept=".zip"
            onChange={(e) => {
              const f = e.target.files?.[0];
              if (f) {
                setFile(f);
                if (!repoName) setRepoName(f.name.replace(".zip", ""));
              }
            }}
            className="hidden"
          />
          {file ? (
            <div>
              <p className="text-green-400 text-sm font-medium">✓ {file.name}</p>
              <p className="text-gray-600 text-xs mt-1">
                {(file.size / 1024 / 1024).toFixed(2)} MB · Click to change
              </p>
            </div>
          ) : (
            <div>
              <p className="text-3xl mb-2 text-gray-700">↑</p>
              <p className="text-gray-400 text-sm">
                Drop a .zip file here or click to browse
              </p>
              <p className="text-gray-700 text-xs mt-1">ZIP archives only</p>
            </div>
          )}
        </div>
      )}

      {/* Git URL input */}
      {mode === "git" && (
        <div className="mb-4">
          <label className="block text-xs text-gray-500 mb-1.5">
            Git URL (public repos only)
          </label>
          <input
            type="url"
            value={gitUrl}
            onChange={(e) => setGitUrl(e.target.value)}
            placeholder="https://github.com/user/repo.git"
            className="w-full bg-gray-900 border border-gray-700 rounded-lg px-3 py-2.5
                       text-sm text-gray-100 placeholder-gray-600 focus:outline-none
                       focus:border-blue-500 transition-colors font-mono"
          />
        </div>
      )}

      {/* Error */}
      {result && !result.ok && (
        <div className="mb-4 rounded-lg bg-red-900/30 border border-red-800/50
                        px-4 py-3 text-red-400 text-sm">
          ✗ {result.detail || result.message || "Upload failed"}
        </div>
      )}

      {/* Submit */}
      <button
        onClick={handleSubmit}
        disabled={submitting}
        className="w-full py-3 bg-blue-600 hover:bg-blue-500 active:bg-blue-700
                   disabled:opacity-40 disabled:cursor-not-allowed rounded-lg
                   text-sm font-medium transition-colors flex items-center
                   justify-center gap-2"
      >
        {submitting ? (
          <>
            <span className="inline-block w-3.5 h-3.5 border-2 border-white/30
                             border-t-white rounded-full animate-spin" />
            Submitting…
          </>
        ) : (
          "Submit Repository"
        )}
      </button>
    </div>
  );
}

function SuccessCard({ repoId, repoName, mode, onAddAnother, onViewRepos }) {
  const steps = [
    { cmd: "python workers/clone_worker.py",     label: "Clone / extract repo" },
    { cmd: "python workers/parser_worker.py",    label: "Parse Python files" },
    { cmd: "python workers/embedding_worker.py", label: "Generate embeddings" },
    { cmd: "python workers/index_worker.py",     label: "Build FAISS index" },
  ];

  return (
    <div className="max-w-lg mx-auto">
      <div className="rounded-xl border border-green-800/40 bg-green-950/20 p-6 mb-5">
        <p className="text-green-400 font-semibold text-sm mb-1">
          ✓ Repository submitted!
        </p>
        <p className="text-gray-400 text-xs">
          <span className="text-gray-200">{repoName}</span> was registered
          {mode === "git" ? " (Git URL)" : " (ZIP)"} as repo #{repoId}.
        </p>
      </div>

      <p className="text-gray-400 text-xs mb-3 font-semibold uppercase tracking-wider">
        Next — run these 4 commands in order:
      </p>
      <div className="space-y-2 mb-6">
        {steps.map((s, i) => (
          <div key={i} className="flex items-center gap-3 bg-gray-900 border
                                  border-gray-800 rounded-lg px-3 py-2.5">
            <span className="text-gray-700 text-xs w-4 text-right flex-shrink-0">
              {i + 1}
            </span>
            <code className="text-blue-300 text-xs flex-1 font-mono">{s.cmd}</code>
            <span className="text-gray-600 text-[10px] flex-shrink-0">
              {s.label}
            </span>
          </div>
        ))}
      </div>

      <div className="flex gap-2">
        <button
          onClick={onAddAnother}
          className="flex-1 py-2 rounded-lg border border-gray-700 text-gray-400
                     hover:text-gray-200 hover:border-gray-600 text-sm transition-colors"
        >
          Add another
        </button>
        <button
          onClick={onViewRepos}
          className="flex-1 py-2 rounded-lg bg-blue-600 hover:bg-blue-500
                     text-sm font-medium transition-colors"
        >
          View my repos
        </button>
      </div>
    </div>
  );
}
