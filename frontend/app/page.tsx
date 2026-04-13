"use client";

import { useEffect, useState } from "react";

interface DashboardMetrics {
  total_leads: number;
  new_leads: number;
  contacted_leads: number;
  demo_booked: number;
  closed_leads: number;
  conversion_rate: number;
  messages_today: number;
  active_conversations: number;
}

function MetricCard({
  title,
  value,
  color,
}: {
  title: string;
  value: string | number;
  color: string;
}) {
  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
      <div className="flex items-center">
        <div className={`w-2 h-12 ${color} rounded-full mr-4`}></div>
        <div>
          <p className="text-sm font-medium text-gray-500">{title}</p>
          <p className="text-2xl font-bold text-gray-900">{value}</p>
        </div>
      </div>
    </div>
  );
}

export default function DashboardPage() {
  const [metrics, setMetrics] = useState<DashboardMetrics | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const loadMetrics = async () => {
    try {
      const API_BASE =
        process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const res = await fetch(`${API_BASE}/api/metrics`);
      if (!res.ok) throw new Error("Failed to fetch");
      const data = await res.json();
      setMetrics(data);
      setError(null);
    } catch {
      setError("Unable to connect to backend. Make sure the API server is running.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadMetrics();
    const interval = setInterval(loadMetrics, 10000);
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-500">Loading dashboard...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6">
        <h2 className="text-lg font-semibold text-yellow-800 mb-2">
          Connection Issue
        </h2>
        <p className="text-yellow-700">{error}</p>
        <button
          onClick={loadMetrics}
          className="mt-3 px-4 py-2 bg-yellow-100 text-yellow-800 rounded-md hover:bg-yellow-200 text-sm font-medium"
        >
          Retry
        </button>
      </div>
    );
  }

  return (
    <div>
      <div className="mb-8">
        <h2 className="text-2xl font-bold text-gray-900">Dashboard</h2>
        <p className="text-gray-500 mt-1">
          Real-time overview of your WhatsApp business automation
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <MetricCard
          title="Total Leads"
          value={metrics?.total_leads ?? 0}
          color="bg-blue-500"
        />
        <MetricCard
          title="New Leads"
          value={metrics?.new_leads ?? 0}
          color="bg-green-500"
        />
        <MetricCard
          title="Demo Booked"
          value={metrics?.demo_booked ?? 0}
          color="bg-purple-500"
        />
        <MetricCard
          title="Closed Deals"
          value={metrics?.closed_leads ?? 0}
          color="bg-orange-500"
        />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <MetricCard
          title="Contacted"
          value={metrics?.contacted_leads ?? 0}
          color="bg-cyan-500"
        />
        <MetricCard
          title="Conversion Rate"
          value={`${metrics?.conversion_rate ?? 0}%`}
          color="bg-emerald-500"
        />
        <MetricCard
          title="Messages Today"
          value={metrics?.messages_today ?? 0}
          color="bg-indigo-500"
        />
        <MetricCard
          title="Active Conversations"
          value={metrics?.active_conversations ?? 0}
          color="bg-rose-500"
        />
      </div>

      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">
          Quick Actions
        </h3>
        <div className="flex flex-wrap gap-3">
          <a
            href="/leads"
            className="px-4 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700 text-sm font-medium"
          >
            View All Leads
          </a>
          <a
            href="/messages"
            className="px-4 py-2 bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200 text-sm font-medium"
          >
            View Messages
          </a>
        </div>
      </div>
    </div>
  );
}
