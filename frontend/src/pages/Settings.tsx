import { useState } from "react";
import {
  Key,
  Github,
  Brain,
  Save,
  CheckCircle2,
  AlertCircle,
  Eye,
  EyeOff,
} from "lucide-react";
import { clsx } from "clsx";
import { api } from "../services/api";
import { useAppStore } from "../stores/appStore";

export function Settings() {
  const {
    llmApiKey,
    githubToken,
    sessionId,
    setLLMApiKey,
    setGithubToken,
    setSessionId,
  } = useAppStore();

  const [showLLMKey, setShowLLMKey] = useState(false);
  const [showGithubKey, setShowGithubKey] = useState(false);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState("");

  const [maxAttempts, setMaxAttempts] = useState(3);
  const [confidenceThreshold, setConfidenceThreshold] = useState(0.7);
  const [modelName, setModelName] = useState("gpt-4o");

  const handleSaveKeys = async () => {
    setSaving(true);
    setError("");
    setSaved(false);

    try {
      const result = await api.storeKeys(llmApiKey, githubToken);
      setSessionId(result.session_id);
      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
    } catch (err: any) {
      setError(err.message || "Failed to save keys");
    } finally {
      setSaving(false);
    }
  };

  const handleSaveConfig = async () => {
    try {
      await api.updateConfig({
        max_attempts: maxAttempts,
        confidence_threshold: confidenceThreshold,
        model_name: modelName,
      });
      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
    } catch (err: any) {
      setError(err.message || "Failed to save config");
    }
  };

  return (
    <div className="space-y-6 max-w-3xl mx-auto">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold gradient-text">Settings</h1>
        <p className="text-sm text-surface-400 mt-1">
          Configure your API keys and agent behavior
        </p>
      </div>

      {/* API Keys Section (BYOK) */}
      <div className="glass-card p-6 space-y-5">
        <div className="flex items-center gap-2">
          <Key className="w-4 h-4 text-primary-400" />
          <h2 className="text-sm font-semibold text-surface-200">
            Bring Your Own Keys (BYOK)
          </h2>
        </div>
        <p className="text-xs text-surface-500">
          Your keys are stored ephemerally in memory and never persisted to disk.
          They are cleared when your session ends.
        </p>

        <div className="space-y-4">
          {/* LLM API Key */}
          <div>
            <label className="block text-xs font-medium text-surface-400 mb-1.5 flex items-center gap-1.5">
              <Brain className="w-3.5 h-3.5" />
              LLM API Key (OpenAI / OpenRouter)
            </label>
            <div className="relative">
              <input
                type={showLLMKey ? "text" : "password"}
                value={llmApiKey}
                onChange={(e) => setLLMApiKey(e.target.value)}
                placeholder="sk-..."
                className="w-full bg-surface-800 border border-surface-700 rounded-lg pl-3 pr-10 py-2 text-sm text-surface-200 placeholder-surface-500 focus:outline-none focus:ring-2 focus:ring-primary-500/40 focus:border-primary-500/50 transition-all font-mono"
              />
              <button
                onClick={() => setShowLLMKey(!showLLMKey)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-surface-500 hover:text-surface-300"
              >
                {showLLMKey ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </button>
            </div>
          </div>

          {/* GitHub Token */}
          <div>
            <label className="block text-xs font-medium text-surface-400 mb-1.5 flex items-center gap-1.5">
              <Github className="w-3.5 h-3.5" />
              GitHub Personal Access Token
            </label>
            <div className="relative">
              <input
                type={showGithubKey ? "text" : "password"}
                value={githubToken}
                onChange={(e) => setGithubToken(e.target.value)}
                placeholder="ghp_..."
                className="w-full bg-surface-800 border border-surface-700 rounded-lg pl-3 pr-10 py-2 text-sm text-surface-200 placeholder-surface-500 focus:outline-none focus:ring-2 focus:ring-primary-500/40 focus:border-primary-500/50 transition-all font-mono"
              />
              <button
                onClick={() => setShowGithubKey(!showGithubKey)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-surface-500 hover:text-surface-300"
              >
                {showGithubKey ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </button>
            </div>
          </div>

          <button
            onClick={handleSaveKeys}
            disabled={saving}
            className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-semibold bg-primary-600 hover:bg-primary-500 text-white transition-colors disabled:opacity-50"
          >
            {saving ? "Saving..." : "Save Keys"}
          </button>

          {sessionId && (
            <p className="text-xs text-success flex items-center gap-1">
              <CheckCircle2 className="w-3 h-3" />
              Session active — keys stored in memory
            </p>
          )}
        </div>
      </div>

      {/* Agent Configuration */}
      <div className="glass-card p-6 space-y-5">
        <div className="flex items-center gap-2">
          <Brain className="w-4 h-4 text-accent-400" />
          <h2 className="text-sm font-semibold text-surface-200">
            Agent Configuration
          </h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-xs font-medium text-surface-400 mb-1.5">
              Max Fix Attempts
            </label>
            <input
              type="number"
              min={1}
              max={10}
              value={maxAttempts}
              onChange={(e) => setMaxAttempts(Number(e.target.value))}
              className="w-full bg-surface-800 border border-surface-700 rounded-lg px-3 py-2 text-sm text-surface-200 focus:outline-none focus:ring-2 focus:ring-primary-500/40"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-surface-400 mb-1.5">
              Confidence Threshold
            </label>
            <div className="flex items-center gap-2">
              <input
                type="range"
                min={0}
                max={100}
                value={confidenceThreshold * 100}
                onChange={(e) => setConfidenceThreshold(Number(e.target.value) / 100)}
                className="flex-1 accent-primary-500"
              />
              <span className="text-sm font-mono text-surface-300 w-10">
                {(confidenceThreshold * 100).toFixed(0)}%
              </span>
            </div>
          </div>

          <div>
            <label className="block text-xs font-medium text-surface-400 mb-1.5">
              Capable Model
            </label>
            <select
              value={modelName}
              onChange={(e) => setModelName(e.target.value)}
              className="w-full bg-surface-800 border border-surface-700 rounded-lg px-3 py-2 text-sm text-surface-200 focus:outline-none focus:ring-2 focus:ring-primary-500/40"
            >
              <option value="gpt-4o">GPT-4o</option>
              <option value="gpt-4o-mini">GPT-4o Mini</option>
              <option value="claude-3-opus-20240229">Claude 3 Opus</option>
              <option value="claude-3-sonnet-20240229">Claude 3 Sonnet</option>
              <option value="claude-3-haiku-20240307">Claude 3 Haiku</option>
            </select>
          </div>
        </div>

        <button
          onClick={handleSaveConfig}
          className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-semibold bg-surface-700 hover:bg-surface-600 text-surface-200 transition-colors"
        >
          <Save className="w-4 h-4" />
          Save Configuration
        </button>
      </div>

      {/* Status messages */}
      {saved && (
        <div className="flex items-center gap-2 text-sm text-success bg-success/10 px-4 py-3 rounded-lg border border-success/20">
          <CheckCircle2 className="w-4 h-4" />
          Settings saved successfully
        </div>
      )}
      {error && (
        <div className="flex items-center gap-2 text-sm text-danger bg-danger/10 px-4 py-3 rounded-lg border border-danger/20">
          <AlertCircle className="w-4 h-4" />
          {error}
        </div>
      )}
    </div>
  );
}
