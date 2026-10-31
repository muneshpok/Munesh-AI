"use client";

import { useEffect, useState } from "react";

interface Lead {
  id: number;
  phone: string;
  name: string | null;
  email: string | null;
  status: string;
  notes: string | null;
  source: string;
  created_at: string | null;
  updated_at: string | null;
}

const STATUS_COLORS: Record<string, string> = {
  new: "bg-green-100 text-green-800",
  contacted: "bg-blue-100 text-blue-800",
  demo_booked: "bg-purple-100 text-purple-800",
  follow_up: "bg-yellow-100 text-yellow-800",
  closed: "bg-gray-100 text-gray-800",
  lost: "bg-red-100 text-red-800",
};

const STATUSES = ["all", "new", "contacted", "demo_booked", "follow_up", "closed", "lost"];

export default function LeadsPage() {
  const [leads, setLeads] = useState<Lead[]>([]);
  const [filter, setFilter] = useState("all");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadLeads = async (status?: string) => {
    try {
      const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const url = status && status !== "all"
        ? `${API_BASE}/api/leads?status=${status}`
        : `${API_BASE}/api/leads`;
      const res = await fetch(url);
      if (!res.ok) throw new Error("Failed to fetch");
      const data = await res.json();
      setLeads(data);
      setError(null);
    } catch {
      setError("Unable to connect to backend.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadLeads(filter);
  }, [filter]);

  const updateStatus = async (phone: string, newStatus: string) => {
    try {
      const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      await fetch(`${API_BASE}/api/update-status`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ phone, status: newStatus }),
      });
      loadLeads(filter);
    } catch {
      alert("Failed to update status");
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-500">Loading leads...</div>
      </div>
    );
  }

  return (
    <div>
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Leads</h2>
          <p className="text-gray-500 mt-1">Manage your WhatsApp leads</p>
        </div>
        <div className="text-sm text-gray-500">{leads.length} leads</div>
      </div>

      {/* Status Filters */}
      <div className="flex flex-wrap gap-2 mb-6">
        {STATUSES.map((status) => (
          <button
            key={status}
            onClick={() => setFilter(status)}
            className={`px-3 py-1.5 rounded-full text-sm font-medium capitalize ${
              filter === status
                ? "bg-primary-600 text-white"
                : "bg-gray-100 text-gray-700 hover:bg-gray-200"
            }`}
          >
            {status.replace("_", " ")}
          </button>
        ))}
      </div>

      {error && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-4">
          <p className="text-yellow-700">{error}</p>
        </div>
      )}

      {/* Leads Table */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Phone</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Name</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Source</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Created</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Actions</th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {leads.length === 0 ? (
              <tr>
                <td colSpan={6} className="px-6 py-12 text-center text-gray-500">
                  No leads found
                </td>
              </tr>
            ) : (
              leads.map((lead) => (
                <tr key={lead.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    <a href={`/messages?phone=${lead.phone}`} className="text-primary-600 hover:underline">
                      {lead.phone}
                    </a>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-700">
                    {lead.name || "—"}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`px-2.5 py-0.5 rounded-full text-xs font-medium ${STATUS_COLORS[lead.status] || "bg-gray-100 text-gray-800"}`}>
                      {lead.status.replace("_", " ")}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{lead.source}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {lead.created_at ? new Date(lead.created_at).toLocaleDateString() : "—"}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm">
                    <select
                      value={lead.status}
                      onChange={(e) => updateStatus(lead.phone, e.target.value)}
                      className="text-sm border border-gray-300 rounded-md px-2 py-1 focus:outline-none focus:ring-1 focus:ring-primary-500"
                    >
                      {STATUSES.filter((s) => s !== "all").map((s) => (
                        <option key={s} value={s}>
                          {s.replace("_", " ")}
                        </option>
                      ))}
                    </select>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
