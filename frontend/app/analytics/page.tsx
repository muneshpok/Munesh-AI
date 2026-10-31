"use client";

import { useEffect, useState } from "react";

interface Funnel {
  total: number;
  stages: Record<string, { count: number; percentage: number }>;
  conversion_rate: number;
}

interface Insights {
  funnel: Funnel;
  engagement: {
    messages_sent: number;
    messages_received: number;
    total_messages: number;
    active_conversations: number;
    period_days: number;
  };
  agent_performance: {
    breakdown: Record<string, number>;
    total_decisions: number;
    period_days: number;
  };
  stale_leads: Array<{
    phone: string;
    name: string;
    status: string;
    hours_since_activity: number;
    lead_score: number;
  }>;
  top_leads: Array<{
    phone: string;
    name: string;
    status: string;
    lead_score: number;
  }>;
  recommendations: string[];
}

interface DailyReport {
  id: number;
  report_date: string;
  total_leads: number;
  new_leads: number;
  contacted_leads: number;
  demo_booked: number;
  closed_leads: number;
  lost_leads: number;
  conversion_rate: number;
  messages_sent: number;
  messages_received: number;
  active_conversations: number;
  agent_breakdown: Record<string, number> | null;
  insights: string[] | null;
  actions_taken: string[] | null;
  stale_leads_count: number;
  follow_ups_sent: number;
  leads_scored: number;
  created_at: string | null;
}

interface AutomationLog {
  id: number;
  action_type: string;
  phone: string | null;
  description: string;
  status: string;
  created_at: string | null;
}

const STAGE_COLORS: Record<string, string> = {
  new: "bg-green-500",
  contacted: "bg-blue-500",
  demo_booked: "bg-purple-500",
  follow_up: "bg-yellow-500",
  closed: "bg-gray-500",
  lost: "bg-red-500",
};

const ACTION_COLORS: Record<string, string> = {
  follow_up: "bg-orange-100 text-orange-800",
  nurture: "bg-green-100 text-green-800",
  score: "bg-blue-100 text-blue-800",
  escalate: "bg-red-100 text-red-800",
};

export default function AnalyticsPage() {
  const [insights, setInsights] = useState<Insights | null>(null);
  const [report, setReport] = useState<DailyReport | null>(null);
  const [logs, setLogs] = useState<AutomationLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [tab, setTab] = useState<"insights" | "reports" | "logs">("insights");

  const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

  const loadData = async () => {
    try {
      const [insightsRes, reportRes, logsRes] = await Promise.all([
        fetch(`${API_BASE}/api/analytics/insights`),
        fetch(`${API_BASE}/api/analytics/daily-report`),
        fetch(`${API_BASE}/api/analytics/automation-logs?limit=20`),
      ]);

      if (insightsRes.ok) setInsights(await insightsRes.json());
      if (reportRes.ok) {
        const data = await reportRes.json();
        setReport(data);
      }
      if (logsRes.ok) setLogs(await logsRes.json());
      setError(null);
    } catch {
      setError("Unable to connect to backend.");
    } finally {
      setLoading(false);
    }
  };

  const runLoop = async () => {
    setRunning(true);
    try {
      const res = await fetch(`${API_BASE}/api/analytics/run-loop`, {
        method: "POST",
      });
      if (res.ok) {
        const newReport = await res.json();
        setReport(newReport);
        await loadData();
      }
    } catch {
      setError("Failed to run daily loop.");
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
        <div className="text-gray-500">Loading analytics...</div>
      </div>
    );
  }

  return (
    <div>
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Analytics</h2>
          <p className="text-gray-500 mt-1">
            Daily Loop: Data → Analyze → Decide → Improve → Deploy → Repeat
          </p>
        </div>
        <button
          onClick={runLoop}
          disabled={running}
          className={`px-4 py-2 rounded-md text-sm font-medium ${
            running
              ? "bg-gray-300 text-gray-500 cursor-not-allowed"
              : "bg-primary-600 text-white hover:bg-primary-700"
          }`}
        >
          {running ? "Running Loop..." : "▶ Run Daily Loop Now"}
        </button>
      </div>

      {error && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-4">
          <p className="text-yellow-700">{error}</p>
        </div>
      )}

      {/* Tabs */}
      <div className="flex gap-1 mb-6 bg-gray-100 rounded-lg p-1 w-fit">
        {(["insights", "reports", "logs"] as const).map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`px-4 py-2 rounded-md text-sm font-medium capitalize ${
              tab === t
                ? "bg-white text-gray-900 shadow-sm"
                : "text-gray-600 hover:text-gray-900"
            }`}
          >
            {t === "logs" ? "Automation Logs" : t === "reports" ? "Daily Reports" : "Live Insights"}
          </button>
        ))}
      </div>

      {/* Live Insights Tab */}
      {tab === "insights" && insights && (
        <div className="space-y-6">
          {/* Funnel */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Lead Funnel</h3>
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4 mb-4">
              {Object.entries(insights.funnel.stages).map(([stage, data]) => (
                <div key={stage} className="text-center">
                  <div className={`w-3 h-3 rounded-full ${STAGE_COLORS[stage] || "bg-gray-400"} mx-auto mb-1`}></div>
                  <div className="text-2xl font-bold text-gray-900">{data.count}</div>
                  <div className="text-xs text-gray-500 capitalize">{stage.replace("_", " ")}</div>
                  <div className="text-xs text-gray-400">{data.percentage}%</div>
                </div>
              ))}
            </div>
            {/* Funnel bar */}
            <div className="flex h-4 rounded-full overflow-hidden bg-gray-100">
              {Object.entries(insights.funnel.stages).map(([stage, data]) => (
                data.percentage > 0 && (
                  <div
                    key={stage}
                    className={`${STAGE_COLORS[stage] || "bg-gray-400"}`}
                    style={{ width: `${data.percentage}%` }}
                    title={`${stage}: ${data.percentage}%`}
                  ></div>
                )
              ))}
            </div>
            <div className="mt-3 text-sm text-gray-600">
              Conversion Rate: <span className="font-bold text-gray-900">{insights.funnel.conversion_rate}%</span>
              {" · "}Total Leads: <span className="font-bold">{insights.funnel.total}</span>
            </div>
          </div>

          {/* Engagement + Agent Performance row */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Engagement (24h)</h3>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <div className="text-3xl font-bold text-blue-600">{insights.engagement.messages_received}</div>
                  <div className="text-sm text-gray-500">Received</div>
                </div>
                <div>
                  <div className="text-3xl font-bold text-green-600">{insights.engagement.messages_sent}</div>
                  <div className="text-sm text-gray-500">Sent</div>
                </div>
                <div>
                  <div className="text-3xl font-bold text-purple-600">{insights.engagement.total_messages}</div>
                  <div className="text-sm text-gray-500">Total Messages</div>
                </div>
                <div>
                  <div className="text-3xl font-bold text-orange-600">{insights.engagement.active_conversations}</div>
                  <div className="text-sm text-gray-500">Active Chats</div>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Agent Performance (24h)</h3>
              {Object.keys(insights.agent_performance.breakdown).length > 0 ? (
                <div className="space-y-3">
                  {Object.entries(insights.agent_performance.breakdown).map(([agent, count]) => {
                    const pct = insights.agent_performance.total_decisions > 0
                      ? Math.round((count / insights.agent_performance.total_decisions) * 100)
                      : 0;
                    return (
                      <div key={agent}>
                        <div className="flex justify-between text-sm mb-1">
                          <span className="capitalize font-medium">{agent}</span>
                          <span className="text-gray-500">{count} ({pct}%)</span>
                        </div>
                        <div className="h-2 bg-gray-100 rounded-full">
                          <div className="h-2 bg-primary-500 rounded-full" style={{ width: `${pct}%` }}></div>
                        </div>
                      </div>
                    );
                  })}
                  <div className="text-sm text-gray-500 mt-2">
                    Total: {insights.agent_performance.total_decisions} decisions
                  </div>
                </div>
              ) : (
                <p className="text-gray-500 text-sm">No agent activity in the last 24 hours.</p>
              )}
            </div>
          </div>

          {/* Recommendations */}
          {insights.recommendations.length > 0 && (
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Recommendations</h3>
              <ul className="space-y-2">
                {insights.recommendations.map((rec, i) => (
                  <li key={i} className="flex items-start gap-2 text-sm">
                    <span className="text-primary-600 mt-0.5">→</span>
                    <span className="text-gray-700">{rec}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Top Leads + Stale Leads row */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {insights.top_leads.length > 0 && (
              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Top Leads by Score</h3>
                <div className="space-y-2">
                  {insights.top_leads.map((lead, i) => (
                    <div key={i} className="flex items-center justify-between py-2 border-b border-gray-100 last:border-0">
                      <div>
                        <span className="text-sm font-medium text-gray-900">{lead.name}</span>
                        <span className="text-xs text-gray-400 ml-2">{lead.phone}</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="text-xs capitalize text-gray-500">{lead.status.replace("_", " ")}</span>
                        <span className={`px-2 py-0.5 rounded-full text-xs font-bold ${
                          lead.lead_score >= 70 ? "bg-green-100 text-green-800" :
                          lead.lead_score >= 40 ? "bg-yellow-100 text-yellow-800" :
                          "bg-gray-100 text-gray-800"
                        }`}>
                          {lead.lead_score}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {insights.stale_leads.length > 0 && (
              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">
                  Stale Leads
                  <span className="ml-2 text-sm font-normal text-red-500">({insights.stale_leads.length} need attention)</span>
                </h3>
                <div className="space-y-2">
                  {insights.stale_leads.slice(0, 5).map((lead, i) => (
                    <div key={i} className="flex items-center justify-between py-2 border-b border-gray-100 last:border-0">
                      <div>
                        <span className="text-sm font-medium text-gray-900">{lead.name}</span>
                        <span className="text-xs text-gray-400 ml-2">{lead.phone}</span>
                      </div>
                      <span className="text-xs text-red-600">{lead.hours_since_activity}h inactive</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Daily Reports Tab */}
      {tab === "reports" && (
        <div className="space-y-6">
          {report ? (
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-gray-900">
                  Report: {report.report_date}
                </h3>
                <span className="text-xs text-gray-400">
                  {report.created_at ? new Date(report.created_at).toLocaleString() : ""}
                </span>
              </div>

              {/* Metrics grid */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                <div className="bg-gray-50 rounded-lg p-3 text-center">
                  <div className="text-xl font-bold">{report.total_leads}</div>
                  <div className="text-xs text-gray-500">Total Leads</div>
                </div>
                <div className="bg-gray-50 rounded-lg p-3 text-center">
                  <div className="text-xl font-bold">{report.conversion_rate}%</div>
                  <div className="text-xs text-gray-500">Conversion</div>
                </div>
                <div className="bg-gray-50 rounded-lg p-3 text-center">
                  <div className="text-xl font-bold">{report.messages_sent + report.messages_received}</div>
                  <div className="text-xs text-gray-500">Messages</div>
                </div>
                <div className="bg-gray-50 rounded-lg p-3 text-center">
                  <div className="text-xl font-bold">{report.active_conversations}</div>
                  <div className="text-xs text-gray-500">Active Chats</div>
                </div>
              </div>

              {/* Insights */}
              {report.insights && report.insights.length > 0 && (
                <div className="mb-4">
                  <h4 className="text-sm font-semibold text-gray-700 mb-2">Insights & Recommendations</h4>
                  <ul className="space-y-1">
                    {report.insights.map((insight, i) => (
                      <li key={i} className="text-sm text-gray-600 flex items-start gap-2">
                        <span className="text-primary-500 mt-0.5">•</span>
                        {insight}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Actions taken */}
              {report.actions_taken && report.actions_taken.length > 0 && (
                <div className="mb-4">
                  <h4 className="text-sm font-semibold text-gray-700 mb-2">Actions Taken</h4>
                  <div className="flex flex-wrap gap-2">
                    {report.actions_taken.map((action, i) => (
                      <span key={i} className="px-3 py-1 bg-green-50 text-green-700 rounded-full text-xs font-medium">
                        {action}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Summary stats */}
              <div className="grid grid-cols-3 gap-4 mt-4 pt-4 border-t border-gray-200">
                <div className="text-center">
                  <div className="text-lg font-bold text-orange-600">{report.stale_leads_count}</div>
                  <div className="text-xs text-gray-500">Stale Leads</div>
                </div>
                <div className="text-center">
                  <div className="text-lg font-bold text-blue-600">{report.follow_ups_sent}</div>
                  <div className="text-xs text-gray-500">Follow-ups Sent</div>
                </div>
                <div className="text-center">
                  <div className="text-lg font-bold text-green-600">{report.leads_scored}</div>
                  <div className="text-xs text-gray-500">Leads Scored</div>
                </div>
              </div>
            </div>
          ) : (
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-12 text-center">
              <p className="text-gray-500 mb-4">No daily reports yet.</p>
              <button
                onClick={runLoop}
                disabled={running}
                className="px-4 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700 text-sm font-medium"
              >
                Run First Daily Loop
              </button>
            </div>
          )}
        </div>
      )}

      {/* Automation Logs Tab */}
      {tab === "logs" && (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
          {logs.length > 0 ? (
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Type</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Phone</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Description</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Time</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {logs.map((log) => (
                  <tr key={log.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                        ACTION_COLORS[log.action_type] || "bg-gray-100 text-gray-800"
                      }`}>
                        {log.action_type}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                      {log.phone || "—"}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-700 max-w-md truncate">
                      {log.description}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      <span className={`${log.status === "completed" ? "text-green-600" : "text-red-600"}`}>
                        {log.status}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-400">
                      {log.created_at ? new Date(log.created_at).toLocaleString() : "—"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <div className="p-12 text-center">
              <p className="text-gray-500">No automation logs yet. Run the Daily Loop to generate actions.</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
