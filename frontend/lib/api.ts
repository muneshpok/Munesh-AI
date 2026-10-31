const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface Lead {
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

export interface DashboardMetrics {
  total_leads: number;
  new_leads: number;
  contacted_leads: number;
  demo_booked: number;
  closed_leads: number;
  conversion_rate: number;
  messages_today: number;
  active_conversations: number;
}

export interface Message {
  id: number;
  phone: string;
  direction: string;
  content: string;
  message_type: string;
  agent_type: string | null;
  created_at: string | null;
}

export async function fetchMetrics(): Promise<DashboardMetrics> {
  const res = await fetch(`${API_BASE}/api/metrics`, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to fetch metrics");
  return res.json();
}

export async function fetchLeads(status?: string): Promise<Lead[]> {
  const url = status
    ? `${API_BASE}/api/leads?status=${status}`
    : `${API_BASE}/api/leads`;
  const res = await fetch(url, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to fetch leads");
  return res.json();
}

export async function fetchMessages(phone: string): Promise<Message[]> {
  const res = await fetch(`${API_BASE}/api/messages/${phone}`, {
    cache: "no-store",
  });
  if (!res.ok) throw new Error("Failed to fetch messages");
  return res.json();
}

export async function updateLeadStatus(
  phone: string,
  status: string
): Promise<Lead> {
  const res = await fetch(`${API_BASE}/api/update-status`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ phone, status }),
  });
  if (!res.ok) throw new Error("Failed to update lead status");
  return res.json();
}
