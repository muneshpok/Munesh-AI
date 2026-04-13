"use client";

import { useState, useEffect } from "react";

interface PerformanceMetrics {
  total_leads: number;
  status_breakdown: Record<string, number>;
  booked: number;
  closed: number;
  lost: number;
  conversion_rate: number;
  close_rate: number;
  loss_rate: number;
  total_messages: number;
  inbound_messages: number;
  outbound_messages: number;
  avg_messages_per_lead: number;
  analyzed_at: string;
}

interface AnalysisResult {
  metrics: PerformanceMetrics;
  suggestions: string;
  log: {
    timestamp: string;
    status: string;
  };
}

export default function PerformancePage() {
  const [metrics, setMetrics] = useState<PerformanceMetrics | null>(null);
  const [suggestions, setSuggestions] = useState<string | null>(null);
  const [analysis, setAnalysis] = useState<AnalysisResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [analyzing, setAnalyzing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

  const loadMetrics = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/performance/metrics`);
      if (res.ok) {
        setMetrics(await res.json());
        setError(null);
      }
    } catch {
      setError("Unable to connect to backend.");
    } finally {
      setLoading(false);
    }
  };

  const runAnalysis = async () => {
    setAnalyzing(true);
    try {
      const res = await fetch(`${API_BASE}/api/performance/analyze`, {
        method: "POST",
      });
      if (res.ok) {
        const result = await res.json();
        setAnalysis(result);
        setMetrics(result.metrics);
        setSuggestions(result.suggestions);
      }
    } catch {
      setError("Failed to run performance analysis.");
    } finally {
      setAnalyzing(false);
    }
  };

  useEffect(() => {
    loadMetrics();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-500">Loading performance data...</div>
      </div>
    );
  }

  return (
    <div>
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Performance Analyzer</h2>
          <p className="text-gray-500 mt-1">
            Quick performance snapshot with AI-powered improvement suggestions
          </p>
        </div>
        <button
          onClick={runAnalysis}
          disabled={analyzing}
          className={`px-4 py-2 rounded-md text-sm font-medium ${
            analyzing
              ? "bg-gray-300 text-gray-500 cursor-not-allowed"
              : "bg-indigo-600 text-white hover:bg-indigo-700"
          }`}
        >
          {analyzing ? "Analyzing..." : "📊 Run Analysis"}
        </button>
      </div>

      {error && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-4">
          <p className="text-yellow-700">{error}</p>
        </div>
      )}

      {metrics && (
        <>
          {/* Key Metrics Cards */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 text-center">
              <div className="text-3xl font-bold text-blue-600">{metrics.total_leads}</div>
              <div className="text-sm text-gray-500">Total Leads</div>
            </div>
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 text-center">
              <div className="text-3xl font-bold text-green-600">{metrics.conversion_rate}%</div>
              <div className="text-sm text-gray-500">Conversion Rate</div>
            </div>
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 text-center">
              <div className="text-3xl font-bold text-purple-600">{metrics.close_rate}%</div>
              <div className="text-sm text-gray-500">Close Rate</div>
            </div>
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 text-center">
              <div className="text-3xl font-bold text-orange-600">{metrics.total_messages}</div>
              <div className="text-sm text-gray-500">Total Messages</div>
            </div>
          </div>

          {/* Status Breakdown */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Lead Status Breakdown</h3>
              <div className="space-y-3">
                {Object.entries(metrics.status_breakdown).map(([status, count]) => {
                  const total = metrics.total_leads || 1;
                  const pct = ((count / total) * 100).toFixed(1);
                  const colors: Record<string, string> = {
                    new: "bg-blue-500",
                    contacted: "bg-yellow-500",
                    demo_booked: "bg-green-500",
                    follow_up: "bg-orange-500",
                    closed: "bg-emerald-600",
                    lost: "bg-red-500",
                  };
                  return (
                    <div key={status}>
                      <div className="flex justify-between text-sm mb-1">
                        <span className="capitalize font-medium text-gray-700">
                          {status.replace("_", " ")}
                        </span>
                        <span className="text-gray-500">
                          {count} ({pct}%)
                        </span>
                      </div>
                      <div className="w-full bg-gray-100 rounded-full h-2">
                        <div
                          className={`${colors[status] || "bg-gray-400"} h-2 rounded-full transition-all`}
                          style={{ width: `${Math.max(Number(pct), 1)}%` }}
                        />
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Message Activity</h3>
              <div className="space-y-4">
                <div className="flex items-center justify-between p-3 bg-blue-50 rounded-lg">
                  <span className="text-sm font-medium text-blue-800">📥 Inbound</span>
                  <span className="text-lg font-bold text-blue-600">{metrics.inbound_messages}</span>
                </div>
                <div className="flex items-center justify-between p-3 bg-green-50 rounded-lg">
                  <span className="text-sm font-medium text-green-800">📤 Outbound</span>
                  <span className="text-lg font-bold text-green-600">{metrics.outbound_messages}</span>
                </div>
                <div className="flex items-center justify-between p-3 bg-purple-50 rounded-lg">
                  <span className="text-sm font-medium text-purple-800">💬 Avg per Lead</span>
                  <span className="text-lg font-bold text-purple-600">{metrics.avg_messages_per_lead}</span>
                </div>
              </div>
              <div className="mt-4 text-xs text-gray-400">
                Last analyzed: {new Date(metrics.analyzed_at).toLocaleString()}
              </div>
            </div>
          </div>
        </>
      )}

      {/* AI Suggestions */}
      {suggestions && (
        <div className="bg-white rounded-lg shadow-sm border border-indigo-200 p-6 mb-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900">
              🤖 AI Improvement Suggestions
            </h3>
            {analysis?.log && (
              <span className="text-xs text-gray-400">
                Generated: {new Date(analysis.log.timestamp).toLocaleString()}
              </span>
            )}
          </div>
          <div className="prose prose-sm max-w-none">
            {suggestions.split("\n\n").map((block, i) => (
              <div key={i} className="mb-4 p-4 bg-gray-50 rounded-lg">
                <p className="text-sm text-gray-700 whitespace-pre-wrap">{block}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Empty state for suggestions */}
      {!suggestions && !analyzing && (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-12 text-center">
          <p className="text-gray-500 mb-4">
            Click &quot;Run Analysis&quot; to get AI-powered improvement suggestions based on your current performance.
          </p>
          <button
            onClick={runAnalysis}
            className="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 text-sm font-medium"
          >
            📊 Run Analysis
          </button>
        </div>
      )}
    </div>
  );
}
