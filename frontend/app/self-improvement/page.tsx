"use client";

import { useEffect, useState } from "react";

interface PromptVersion {
  id: number;
  agent_type: string;
  version: number;
  prompt_text: string;
  is_active: number;
  performance_score: number | null;
  reason: string | null;
  created_at: string | null;
}

interface ImprovementLog {
  id: number;
  improvement_type: string;
  target: string;
  description: string;
  old_value: string | null;
  new_value: string | null;
  rationale: string | null;
  impact_metrics: Record<string, number> | null;
  status: string;
  created_at: string | null;
}

interface StrategyConfig {
  id: number;
  config_key: string;
  config_value: string;
  config_type: string;
  category: string;
  description: string | null;
  updated_by: string;
  updated_at: string | null;
}

interface SIReport {
  cycle_id: string;
  timestamp: string;
  improvements_made: Array<{
    type: string;
    target: string;
    description: string;
    reason: string;
  }>;
  prompts_updated: number;
  keywords_updated: number;
  strategies_updated: number;
  follow_ups_optimized: number;
  insights: string[];
  next_recommendations: string[];
}

const IMPROVEMENT_COLORS: Record<string, string> = {
  prompt: "bg-purple-100 text-purple-800",
  keyword: "bg-blue-100 text-blue-800",
  follow_up: "bg-orange-100 text-orange-800",
  strategy: "bg-green-100 text-green-800",
};

const CATEGORY_COLORS: Record<string, string> = {
  keywords: "bg-blue-50 text-blue-700",
  timing: "bg-orange-50 text-orange-700",
  thresholds: "bg-red-50 text-red-700",
  templates: "bg-green-50 text-green-700",
};

export default function SelfImprovementPage() {
  const [prompts, setPrompts] = useState<PromptVersion[]>([]);
  const [improvements, setImprovements] = useState<ImprovementLog[]>([]);
  const [strategy, setStrategy] = useState<StrategyConfig[]>([]);
  const [lastReport, setLastReport] = useState<SIReport | null>(null);
  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [tab, setTab] = useState<"overview" | "prompts" | "strategy" | "history">("overview");

  const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

  const loadData = async () => {
    try {
      const [promptsRes, improvementsRes, strategyRes] = await Promise.all([
        fetch(`${API_BASE}/api/self-improvement/prompts/active`),
        fetch(`${API_BASE}/api/self-improvement/improvements?limit=20`),
        fetch(`${API_BASE}/api/self-improvement/strategy`),
      ]);

      if (promptsRes.ok) setPrompts(await promptsRes.json());
      if (improvementsRes.ok) setImprovements(await improvementsRes.json());
      if (strategyRes.ok) setStrategy(await strategyRes.json());
      setError(null);
    } catch {
      setError("Unable to connect to backend.");
    } finally {
      setLoading(false);
    }
  };

  const runCycle = async () => {
    setRunning(true);
    try {
      const res = await fetch(`${API_BASE}/api/self-improvement/run`, {
        method: "POST",
      });
      if (res.ok) {
        const report = await res.json();
        setLastReport(report);
        await loadData();
      }
    } catch {
      setError("Failed to run self-improvement cycle.");
    } finally {
      setRunning(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-500">Loading self-improvement data...</div>
      </div>
    );
  }

  return (
    <div>
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Self-Improvement Agent</h2>
          <p className="text-gray-500 mt-1">
            Autonomous system that analyzes interactions and improves prompts, responses, follow-ups & strategy
          </p>
        </div>
        <button
          onClick={runCycle}
          disabled={running}
          className={`px-4 py-2 rounded-md text-sm font-medium ${
            running
              ? "bg-gray-300 text-gray-500 cursor-not-allowed"
              : "bg-purple-600 text-white hover:bg-purple-700"
          }`}
        >
          {running ? "Running Cycle..." : "🧠 Run Improvement Cycle"}
        </button>
      </div>

      {error && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-4">
          <p className="text-yellow-700">{error}</p>
        </div>
      )}

      {/* Tabs */}
      <div className="flex gap-1 mb-6 bg-gray-100 rounded-lg p-1 w-fit">
        {(["overview", "prompts", "strategy", "history"] as const).map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`px-4 py-2 rounded-md text-sm font-medium capitalize ${
              tab === t
                ? "bg-white text-gray-900 shadow-sm"
                : "text-gray-600 hover:text-gray-900"
            }`}
          >
            {t === "overview" ? "Overview" : t === "prompts" ? "Agent Prompts" : t === "strategy" ? "Strategy Config" : "Improvement History"}
          </button>
        ))}
      </div>

      {/* Overview Tab */}
      {tab === "overview" && (
        <div className="space-y-6">
          {/* Flow diagram */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">How It Works</h3>
            <div className="flex items-center justify-center gap-2 flex-wrap">
              {[
                { label: "User Messages", icon: "💬", color: "bg-blue-100" },
                { label: "→", icon: "", color: "" },
                { label: "WhatsApp AI", icon: "🤖", color: "bg-green-100" },
                { label: "→", icon: "", color: "" },
                { label: "Logs + CRM", icon: "📊", color: "bg-yellow-100" },
                { label: "→", icon: "", color: "" },
                { label: "Self-Improvement", icon: "🧠", color: "bg-purple-100" },
                { label: "→", icon: "", color: "" },
                { label: "Updates", icon: "🚀", color: "bg-red-100" },
              ].map((step, i) =>
                step.icon ? (
                  <div key={i} className={`${step.color} rounded-lg px-4 py-3 text-center`}>
                    <div className="text-2xl">{step.icon}</div>
                    <div className="text-xs font-medium text-gray-700 mt-1">{step.label}</div>
                  </div>
                ) : (
                  <span key={i} className="text-gray-400 text-xl font-bold">{step.label}</span>
                )
              )}
            </div>
          </div>

          {/* Stats cards */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 text-center">
              <div className="text-3xl font-bold text-purple-600">{prompts.length}</div>
              <div className="text-sm text-gray-500">Active Prompts</div>
            </div>
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 text-center">
              <div className="text-3xl font-bold text-blue-600">
                {strategy.filter(s => s.category === "keywords").length}
              </div>
              <div className="text-sm text-gray-500">Keyword Lists</div>
            </div>
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 text-center">
              <div className="text-3xl font-bold text-orange-600">{strategy.length}</div>
              <div className="text-sm text-gray-500">Strategy Configs</div>
            </div>
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 text-center">
              <div className="text-3xl font-bold text-green-600">{improvements.length}</div>
              <div className="text-sm text-gray-500">Improvements Made</div>
            </div>
          </div>

          {/* Last Report */}
          {lastReport && (
            <div className="bg-white rounded-lg shadow-sm border border-purple-200 p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-gray-900">
                  Latest Improvement Cycle
                </h3>
                <span className="text-xs text-gray-400">
                  Cycle {lastReport.cycle_id} · {lastReport.timestamp}
                </span>
              </div>

              {/* Summary stats */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
                <div className="bg-purple-50 rounded p-2 text-center">
                  <div className="text-lg font-bold text-purple-700">{lastReport.prompts_updated}</div>
                  <div className="text-xs text-gray-500">Prompts Updated</div>
                </div>
                <div className="bg-blue-50 rounded p-2 text-center">
                  <div className="text-lg font-bold text-blue-700">{lastReport.keywords_updated}</div>
                  <div className="text-xs text-gray-500">Keywords Updated</div>
                </div>
                <div className="bg-green-50 rounded p-2 text-center">
                  <div className="text-lg font-bold text-green-700">{lastReport.strategies_updated}</div>
                  <div className="text-xs text-gray-500">Strategies Updated</div>
                </div>
                <div className="bg-orange-50 rounded p-2 text-center">
                  <div className="text-lg font-bold text-orange-700">{lastReport.follow_ups_optimized}</div>
                  <div className="text-xs text-gray-500">Follow-ups Optimized</div>
                </div>
              </div>

              {/* Insights */}
              {lastReport.insights.length > 0 && (
                <div className="mb-4">
                  <h4 className="text-sm font-semibold text-gray-700 mb-2">Insights</h4>
                  <ul className="space-y-1">
                    {lastReport.insights.map((insight, i) => (
                      <li key={i} className="text-sm text-gray-600 flex items-start gap-2">
                        <span className="text-purple-500 mt-0.5">•</span>
                        {insight}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Improvements */}
              {lastReport.improvements_made.length > 0 && (
                <div className="mb-4">
                  <h4 className="text-sm font-semibold text-gray-700 mb-2">Changes Applied</h4>
                  <div className="space-y-2">
                    {lastReport.improvements_made.map((imp, i) => (
                      <div key={i} className="flex items-center gap-3 text-sm">
                        <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                          IMPROVEMENT_COLORS[imp.type] || "bg-gray-100 text-gray-800"
                        }`}>
                          {imp.type}
                        </span>
                        <span className="text-gray-700">{imp.description}</span>
                        <span className="text-gray-400 text-xs ml-auto">{imp.reason}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Recommendations */}
              {lastReport.next_recommendations.length > 0 && (
                <div>
                  <h4 className="text-sm font-semibold text-gray-700 mb-2">Next Cycle Recommendations</h4>
                  <ul className="space-y-1">
                    {lastReport.next_recommendations.map((rec, i) => (
                      <li key={i} className="text-sm text-gray-600 flex items-start gap-2">
                        <span className="text-green-500 mt-0.5">→</span>
                        {rec}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}

          {/* What gets updated */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">What Gets Updated</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="border border-purple-200 rounded-lg p-4">
                <h4 className="font-medium text-purple-800 mb-2">📝 Prompts</h4>
                <p className="text-sm text-gray-600">
                  Agent system prompts are analyzed based on conversation outcomes and improved
                  to increase conversion rates and response quality.
                </p>
              </div>
              <div className="border border-blue-200 rounded-lg p-4">
                <h4 className="font-medium text-blue-800 mb-2">🔑 Keywords</h4>
                <p className="text-sm text-gray-600">
                  Intent classification keywords are expanded by analyzing messages that fall
                  through to the default chat agent.
                </p>
              </div>
              <div className="border border-orange-200 rounded-lg p-4">
                <h4 className="font-medium text-orange-800 mb-2">📬 Follow-ups</h4>
                <p className="text-sm text-gray-600">
                  Follow-up timing and message templates are optimized based on response rates
                  and lead conversion patterns.
                </p>
              </div>
              <div className="border border-green-200 rounded-lg p-4">
                <h4 className="font-medium text-green-800 mb-2">🎯 Strategy</h4>
                <p className="text-sm text-gray-600">
                  Scoring thresholds, escalation rules, and automation parameters are tuned
                  based on actual performance data.
                </p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Agent Prompts Tab */}
      {tab === "prompts" && (
        <div className="space-y-4">
          {prompts.length > 0 ? (
            prompts.map((prompt) => (
              <div key={prompt.id} className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-3">
                    <h3 className="text-lg font-semibold text-gray-900 capitalize">
                      {prompt.agent_type} Agent
                    </h3>
                    <span className="px-2 py-0.5 bg-green-100 text-green-800 rounded-full text-xs font-medium">
                      v{prompt.version}
                    </span>
                    {prompt.is_active === 1 && (
                      <span className="px-2 py-0.5 bg-blue-100 text-blue-800 rounded-full text-xs font-medium">
                        Active
                      </span>
                    )}
                  </div>
                  {prompt.performance_score !== null && (
                    <span className="text-sm text-gray-500">
                      Score: <span className="font-medium">{prompt.performance_score.toFixed(0)}%</span>
                    </span>
                  )}
                </div>
                <pre className="bg-gray-50 rounded-lg p-4 text-sm text-gray-700 whitespace-pre-wrap font-mono overflow-auto max-h-48">
                  {prompt.prompt_text}
                </pre>
                {prompt.reason && (
                  <div className="mt-3 text-xs text-gray-500">
                    Reason: {prompt.reason}
                  </div>
                )}
                {prompt.created_at && (
                  <div className="mt-1 text-xs text-gray-400">
                    Created: {new Date(prompt.created_at).toLocaleString()}
                  </div>
                )}
              </div>
            ))
          ) : (
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-12 text-center">
              <p className="text-gray-500 mb-4">No prompts initialized yet.</p>
              <button
                onClick={runCycle}
                disabled={running}
                className="px-4 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700 text-sm font-medium"
              >
                Initialize & Run First Cycle
              </button>
            </div>
          )}
        </div>
      )}

      {/* Strategy Config Tab */}
      {tab === "strategy" && (
        <div className="space-y-6">
          {Object.entries(
            strategy.reduce((acc, s) => {
              if (!acc[s.category]) acc[s.category] = [];
              acc[s.category].push(s);
              return acc;
            }, {} as Record<string, StrategyConfig[]>)
          ).map(([category, configs]) => (
            <div key={category} className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <h3 className="text-lg font-semibold text-gray-900 capitalize mb-4">
                <span className={`px-2 py-0.5 rounded text-xs font-medium mr-2 ${
                  CATEGORY_COLORS[category] || "bg-gray-50 text-gray-700"
                }`}>
                  {category}
                </span>
                Configuration
              </h3>
              <div className="space-y-3">
                {configs.map((config) => (
                  <div key={config.id} className="border border-gray-100 rounded-lg p-3">
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-sm font-medium text-gray-800">{config.config_key}</span>
                      <span className="text-xs text-gray-400">
                        Updated by: {config.updated_by}
                      </span>
                    </div>
                    {config.description && (
                      <p className="text-xs text-gray-500 mb-2">{config.description}</p>
                    )}
                    <div className="bg-gray-50 rounded p-2">
                      <code className="text-xs text-gray-700 break-all">
                        {config.config_value.length > 200
                          ? config.config_value.substring(0, 200) + "..."
                          : config.config_value}
                      </code>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ))}
          {strategy.length === 0 && (
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-12 text-center">
              <p className="text-gray-500">No strategy configs yet. Run an improvement cycle to initialize.</p>
            </div>
          )}
        </div>
      )}

      {/* Improvement History Tab */}
      {tab === "history" && (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
          {improvements.length > 0 ? (
            <div className="divide-y divide-gray-200">
              {improvements.map((log) => (
                <div key={log.id} className="p-4 hover:bg-gray-50">
                  <div className="flex items-center gap-3 mb-2">
                    <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                      IMPROVEMENT_COLORS[log.improvement_type] || "bg-gray-100 text-gray-800"
                    }`}>
                      {log.improvement_type}
                    </span>
                    <span className="text-sm font-medium text-gray-900">{log.target}</span>
                    <span className={`ml-auto text-xs px-2 py-0.5 rounded ${
                      log.status === "applied" ? "bg-green-100 text-green-700" :
                      log.status === "reverted" ? "bg-red-100 text-red-700" :
                      "bg-yellow-100 text-yellow-700"
                    }`}>
                      {log.status}
                    </span>
                    <span className="text-xs text-gray-400">
                      {log.created_at ? new Date(log.created_at).toLocaleString() : "—"}
                    </span>
                  </div>
                  <p className="text-sm text-gray-700 mb-2">{log.description}</p>
                  {log.rationale && (
                    <p className="text-xs text-gray-500 mb-2">
                      <span className="font-medium">Rationale:</span> {log.rationale}
                    </p>
                  )}
                  {log.old_value && log.new_value && (
                    <div className="grid grid-cols-2 gap-2 mt-2">
                      <div className="bg-red-50 rounded p-2">
                        <div className="text-xs font-medium text-red-700 mb-1">Before</div>
                        <code className="text-xs text-red-600 break-all">
                          {log.old_value.length > 150 ? log.old_value.substring(0, 150) + "..." : log.old_value}
                        </code>
                      </div>
                      <div className="bg-green-50 rounded p-2">
                        <div className="text-xs font-medium text-green-700 mb-1">After</div>
                        <code className="text-xs text-green-600 break-all">
                          {log.new_value.length > 150 ? log.new_value.substring(0, 150) + "..." : log.new_value}
                        </code>
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <div className="p-12 text-center">
              <p className="text-gray-500">No improvements made yet. Run an improvement cycle to start optimizing.</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
