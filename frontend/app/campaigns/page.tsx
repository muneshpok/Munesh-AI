"use client";

import { useState, useEffect } from "react";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface CampaignMetrics {
  total_targeted: number;
  sent: number;
  delivered: number;
  responded: number;
  converted: number;
  response_rate: number;
  conversion_rate: number;
}

interface CampaignMessage {
  phone: string;
  name: string;
  message: string;
  status: string;
  sent_at?: string;
  error?: string;
}

interface Campaign {
  id: number;
  name: string;
  template_type: string;
  description: string;
  goal: string;
  message_style: string;
  audience_filter: string;
  custom_message?: string;
  status: string;
  created_at: string;
  completed_at?: string;
  audience: { phone: string; name: string; status: string; score: number }[];
  messages: CampaignMessage[];
  metrics: CampaignMetrics;
  optimization_notes: string[];
}

interface Template {
  name: string;
  description: string;
  goal: string;
  default_audience: string;
  message_style: string;
  suggested_timing: string;
}

interface AudienceFilter {
  name: string;
  description: string;
}

export default function CampaignsPage() {
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [templates, setTemplates] = useState<Record<string, Template>>({});
  const [audienceFilters, setAudienceFilters] = useState<
    Record<string, AudienceFilter>
  >({});
  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState(false);
  const [activeTab, setActiveTab] = useState<"create" | "campaigns" | "pipeline">("create");

  // Create form state
  const [selectedTemplate, setSelectedTemplate] = useState("demo_push");
  const [customName, setCustomName] = useState("");
  const [customMessage, setCustomMessage] = useState("");
  const [audienceFilter, setAudienceFilter] = useState("");

  useEffect(() => {
    Promise.all([
      fetch(`${API_URL}/api/campaigns/templates`).then((r) => r.json()),
      fetch(`${API_URL}/api/campaigns/audience-filters`).then((r) => r.json()),
      fetch(`${API_URL}/api/campaigns/`).then((r) => r.json()),
    ])
      .then(([t, a, c]) => {
        setTemplates(t);
        setAudienceFilters(a);
        setCampaigns(c);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const runPipeline = async () => {
    setRunning(true);
    try {
      const res = await fetch(`${API_URL}/api/campaigns/run`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          template_type: selectedTemplate,
          custom_name: customName || null,
          custom_message: customMessage || null,
          audience_filter: audienceFilter || null,
        }),
      });
      const campaign = await res.json();
      setCampaigns((prev) => [...prev, campaign]);
      setActiveTab("campaigns");
    } catch {
      // handled
    } finally {
      setRunning(false);
    }
  };

  const refreshCampaigns = async () => {
    try {
      const res = await fetch(`${API_URL}/api/campaigns/`);
      setCampaigns(await res.json());
    } catch {
      // handled
    }
  };

  const statusColor = (status: string) => {
    const map: Record<string, string> = {
      planned: "bg-gray-100 text-gray-800",
      audience_selected: "bg-blue-100 text-blue-800",
      messages_generated: "bg-purple-100 text-purple-800",
      scheduled: "bg-yellow-100 text-yellow-800",
      sending: "bg-orange-100 text-orange-800",
      completed: "bg-green-100 text-green-800",
    };
    return map[status] || "bg-gray-100 text-gray-800";
  };

  const goalIcon = (goal: string) => {
    const map: Record<string, string> = {
      awareness: "📢",
      reactivation: "🔄",
      conversion: "🎯",
      revenue: "💰",
      custom: "⚙️",
    };
    return map[goal] || "📋";
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-500">Loading Campaign System...</div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">
            Campaign System
          </h1>
          <p className="text-gray-500 mt-1">
            AI CEO → Planner → Audience → Messages → Schedule → Send → Metrics → Optimize
          </p>
        </div>
        <button
          onClick={refreshCampaigns}
          className="px-4 py-2 text-sm bg-gray-100 hover:bg-gray-200 rounded-lg"
        >
          Refresh
        </button>
      </div>

      {/* Pipeline Visualization */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4">
        <div className="flex items-center justify-between overflow-x-auto">
          {[
            { step: "AI CEO", icon: "🧠", desc: "Strategy" },
            { step: "Planner", icon: "📋", desc: "Campaign Plan" },
            { step: "Audience", icon: "👥", desc: "Target Selection" },
            { step: "Generator", icon: "✍️", desc: "Message Creation" },
            { step: "Scheduler", icon: "📅", desc: "Send Timing" },
            { step: "Sender", icon: "📲", desc: "WhatsApp API" },
            { step: "Metrics", icon: "📊", desc: "Track Results" },
            { step: "Optimize", icon: "🔁", desc: "Self-Improve" },
          ].map((s, i) => (
            <div key={s.step} className="flex items-center">
              <div className="flex flex-col items-center min-w-[80px]">
                <div className="text-2xl mb-1">{s.icon}</div>
                <div className="text-xs font-semibold text-gray-700">
                  {s.step}
                </div>
                <div className="text-[10px] text-gray-400">{s.desc}</div>
              </div>
              {i < 7 && (
                <div className="text-gray-300 mx-1 text-lg">→</div>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Tabs */}
      <div className="flex space-x-1 bg-gray-100 rounded-lg p-1">
        {(
          [
            { key: "create", label: "Create Campaign" },
            { key: "campaigns", label: `Campaigns (${campaigns.length})` },
            { key: "pipeline", label: "Pipeline Steps" },
          ] as const
        ).map((tab) => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key)}
            className={`flex-1 py-2 px-4 rounded-md text-sm font-medium transition ${
              activeTab === tab.key
                ? "bg-white shadow text-gray-900"
                : "text-gray-500 hover:text-gray-700"
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Create Campaign Tab */}
      {activeTab === "create" && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <h2 className="text-lg font-semibold mb-4">
            Launch a New Campaign
          </h2>

          {/* Template Selection */}
          <div className="mb-6">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Campaign Template
            </label>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
              {Object.entries(templates).map(([key, t]) => (
                <button
                  key={key}
                  onClick={() => {
                    setSelectedTemplate(key);
                    setAudienceFilter(t.default_audience);
                  }}
                  className={`p-3 rounded-lg border text-left transition ${
                    selectedTemplate === key
                      ? "border-blue-500 bg-blue-50 ring-2 ring-blue-200"
                      : "border-gray-200 hover:border-gray-300"
                  }`}
                >
                  <div className="flex items-center gap-2">
                    <span>{goalIcon(t.goal)}</span>
                    <span className="font-medium text-sm">{t.name}</span>
                  </div>
                  <p className="text-xs text-gray-500 mt-1">
                    {t.description}
                  </p>
                  <div className="flex items-center gap-2 mt-2">
                    <span className="text-[10px] bg-gray-100 px-2 py-0.5 rounded">
                      {t.goal}
                    </span>
                    <span className="text-[10px] text-gray-400">
                      Best at {t.suggested_timing}
                    </span>
                  </div>
                </button>
              ))}
            </div>
          </div>

          {/* Audience Filter */}
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Target Audience
            </label>
            <select
              value={audienceFilter}
              onChange={(e) => setAudienceFilter(e.target.value)}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm"
            >
              <option value="">Use template default</option>
              {Object.entries(audienceFilters).map(([key, f]) => (
                <option key={key} value={key}>
                  {f.name} — {f.description}
                </option>
              ))}
            </select>
          </div>

          {/* Custom Name */}
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Campaign Name (optional)
            </label>
            <input
              type="text"
              value={customName}
              onChange={(e) => setCustomName(e.target.value)}
              placeholder="e.g. April Demo Push"
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm"
            />
          </div>

          {/* Custom Message */}
          <div className="mb-6">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Custom Message (optional — AI generates if blank)
            </label>
            <textarea
              value={customMessage}
              onChange={(e) => setCustomMessage(e.target.value)}
              placeholder="Hi {name}! We have an exciting update..."
              rows={3}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm"
            />
            <p className="text-xs text-gray-400 mt-1">
              Use {"{name}"} to personalize. Leave blank for AI-generated messages.
            </p>
          </div>

          {/* Launch Button */}
          <button
            onClick={runPipeline}
            disabled={running}
            className={`w-full py-3 rounded-lg font-semibold text-white transition ${
              running
                ? "bg-gray-400 cursor-not-allowed"
                : "bg-blue-600 hover:bg-blue-700"
            }`}
          >
            {running
              ? "Running Pipeline..."
              : "Launch Campaign (Full Pipeline)"}
          </button>
        </div>
      )}

      {/* Campaigns List Tab */}
      {activeTab === "campaigns" && (
        <div className="space-y-4">
          {campaigns.length === 0 ? (
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-8 text-center text-gray-500">
              No campaigns yet. Create your first one!
            </div>
          ) : (
            campaigns.map((c) => (
              <div
                key={c.id}
                className="bg-white rounded-xl shadow-sm border border-gray-200 p-5"
              >
                <div className="flex items-start justify-between">
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="text-lg">
                        {goalIcon(c.goal)}
                      </span>
                      <h3 className="font-semibold text-gray-900">
                        {c.name}
                      </h3>
                      <span
                        className={`px-2 py-0.5 rounded-full text-xs font-medium ${statusColor(
                          c.status
                        )}`}
                      >
                        {c.status.replace(/_/g, " ")}
                      </span>
                    </div>
                    <p className="text-sm text-gray-500 mt-1">
                      {c.description}
                    </p>
                  </div>
                  <div className="text-xs text-gray-400">
                    {new Date(c.created_at).toLocaleString()}
                  </div>
                </div>

                {/* Metrics Grid */}
                <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-3 mt-4">
                  {[
                    {
                      label: "Targeted",
                      value: c.metrics.total_targeted,
                      color: "text-gray-700",
                    },
                    {
                      label: "Sent",
                      value: c.metrics.sent,
                      color: "text-blue-600",
                    },
                    {
                      label: "Delivered",
                      value: c.metrics.delivered,
                      color: "text-green-600",
                    },
                    {
                      label: "Responded",
                      value: c.metrics.responded,
                      color: "text-purple-600",
                    },
                    {
                      label: "Converted",
                      value: c.metrics.converted,
                      color: "text-orange-600",
                    },
                    {
                      label: "Response %",
                      value: `${c.metrics.response_rate}%`,
                      color: "text-indigo-600",
                    },
                    {
                      label: "Convert %",
                      value: `${c.metrics.conversion_rate}%`,
                      color: "text-emerald-600",
                    },
                  ].map((m) => (
                    <div
                      key={m.label}
                      className="bg-gray-50 rounded-lg p-2 text-center"
                    >
                      <div className={`text-lg font-bold ${m.color}`}>
                        {m.value}
                      </div>
                      <div className="text-[10px] text-gray-500">
                        {m.label}
                      </div>
                    </div>
                  ))}
                </div>

                {/* Optimization Notes */}
                {c.optimization_notes.length > 0 && (
                  <div className="mt-4 bg-yellow-50 rounded-lg p-3">
                    <div className="text-xs font-semibold text-yellow-800 mb-1">
                      Optimization Suggestions
                    </div>
                    <ul className="space-y-1">
                      {c.optimization_notes.map((note, i) => (
                        <li
                          key={i}
                          className="text-xs text-yellow-700"
                        >
                          • {note}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Messages Preview */}
                {c.messages.length > 0 && (
                  <details className="mt-3">
                    <summary className="text-xs text-gray-500 cursor-pointer hover:text-gray-700">
                      View {c.messages.length} messages
                    </summary>
                    <div className="mt-2 space-y-2 max-h-48 overflow-y-auto">
                      {c.messages.map((m, i) => (
                        <div
                          key={i}
                          className="flex items-start gap-2 text-xs bg-gray-50 rounded p-2"
                        >
                          <span
                            className={`px-1.5 py-0.5 rounded text-[10px] font-medium ${
                              m.status === "sent"
                                ? "bg-green-100 text-green-700"
                                : m.status === "responded"
                                ? "bg-purple-100 text-purple-700"
                                : m.status === "failed"
                                ? "bg-red-100 text-red-700"
                                : "bg-gray-100 text-gray-600"
                            }`}
                          >
                            {m.status}
                          </span>
                          <span className="font-medium">{m.name}</span>
                          <span className="text-gray-400 truncate flex-1">
                            {m.message.slice(0, 80)}...
                          </span>
                        </div>
                      ))}
                    </div>
                  </details>
                )}
              </div>
            ))
          )}
        </div>
      )}

      {/* Pipeline Steps Tab */}
      {activeTab === "pipeline" && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <h2 className="text-lg font-semibold mb-4">
            Pipeline Step-by-Step API
          </h2>
          <p className="text-sm text-gray-500 mb-6">
            You can also run each step individually via the API:
          </p>
          <div className="space-y-4">
            {[
              {
                step: 1,
                name: "Plan",
                method: "POST",
                endpoint: "/api/campaigns/plan",
                desc: "Create a campaign from a template",
              },
              {
                step: 2,
                name: "Select Audience",
                method: "POST",
                endpoint: "/api/campaigns/{id}/select-audience",
                desc: "Filter CRM leads into target audience",
              },
              {
                step: 3,
                name: "Generate Messages",
                method: "POST",
                endpoint: "/api/campaigns/{id}/generate-messages",
                desc: "AI-generate personalized WhatsApp messages",
              },
              {
                step: 4,
                name: "Schedule",
                method: "POST",
                endpoint: "/api/campaigns/{id}/schedule",
                desc: "Set send timing (immediate or delayed)",
              },
              {
                step: 5,
                name: "Execute",
                method: "POST",
                endpoint: "/api/campaigns/{id}/execute",
                desc: "Send messages via WhatsApp Cloud API",
              },
              {
                step: 6,
                name: "Metrics",
                method: "GET",
                endpoint: "/api/campaigns/{id}/metrics",
                desc: "Track delivery, response, and conversion rates",
              },
              {
                step: 7,
                name: "Optimize",
                method: "POST",
                endpoint: "/api/campaigns/{id}/optimize",
                desc: "Get AI-powered optimization suggestions",
              },
            ].map((s) => (
              <div
                key={s.step}
                className="flex items-start gap-4 p-3 rounded-lg bg-gray-50"
              >
                <div className="flex-shrink-0 w-8 h-8 rounded-full bg-blue-100 text-blue-700 flex items-center justify-center text-sm font-bold">
                  {s.step}
                </div>
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <span className="font-medium text-sm">{s.name}</span>
                    <code className="text-xs bg-gray-200 px-2 py-0.5 rounded">
                      {s.method} {s.endpoint}
                    </code>
                  </div>
                  <p className="text-xs text-gray-500 mt-0.5">{s.desc}</p>
                </div>
              </div>
            ))}
            <div className="flex items-start gap-4 p-3 rounded-lg bg-blue-50 border border-blue-200">
              <div className="flex-shrink-0 w-8 h-8 rounded-full bg-blue-500 text-white flex items-center justify-center text-sm font-bold">
                *
              </div>
              <div className="flex-1">
                <div className="flex items-center gap-2">
                  <span className="font-medium text-sm">
                    Full Pipeline (All Steps)
                  </span>
                  <code className="text-xs bg-blue-100 text-blue-700 px-2 py-0.5 rounded">
                    POST /api/campaigns/run
                  </code>
                </div>
                <p className="text-xs text-gray-600 mt-0.5">
                  Runs all 7 steps end-to-end in a single call
                </p>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
