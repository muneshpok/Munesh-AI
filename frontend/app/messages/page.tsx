"use client";

import { useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";

interface Message {
  id: number;
  phone: string;
  direction: string;
  content: string;
  message_type: string;
  agent_type: string | null;
  created_at: string | null;
}

export default function MessagesPage() {
  const searchParams = useSearchParams();
  const initialPhone = searchParams.get("phone") || "";

  const [phone, setPhone] = useState(initialPhone);
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadMessages = async (phoneNumber: string) => {
    if (!phoneNumber) return;
    setLoading(true);
    try {
      const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const res = await fetch(`${API_BASE}/api/messages/${phoneNumber}`);
      if (!res.ok) throw new Error("Failed to fetch");
      const data = await res.json();
      setMessages(data);
      setError(null);
    } catch {
      setError("Unable to load messages.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (initialPhone) {
      loadMessages(initialPhone);
    }
  }, [initialPhone]);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    loadMessages(phone);
  };

  return (
    <div>
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-900">Messages</h2>
        <p className="text-gray-500 mt-1">View conversation history</p>
      </div>

      {/* Search */}
      <form onSubmit={handleSearch} className="flex gap-3 mb-6">
        <input
          type="text"
          value={phone}
          onChange={(e) => setPhone(e.target.value)}
          placeholder="Enter phone number..."
          className="flex-1 px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
        />
        <button
          type="submit"
          className="px-6 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700 font-medium"
        >
          Search
        </button>
      </form>

      {error && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-4">
          <p className="text-yellow-700">{error}</p>
        </div>
      )}

      {loading && (
        <div className="flex items-center justify-center h-32">
          <div className="text-gray-500">Loading messages...</div>
        </div>
      )}

      {/* Messages */}
      {!loading && messages.length > 0 && (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="space-y-4">
            {messages.map((msg) => (
              <div
                key={msg.id}
                className={`flex ${msg.direction === "outbound" ? "justify-end" : "justify-start"}`}
              >
                <div
                  className={`max-w-lg rounded-lg px-4 py-3 ${
                    msg.direction === "outbound"
                      ? "bg-primary-600 text-white"
                      : "bg-gray-100 text-gray-900"
                  }`}
                >
                  <p className="text-sm">{msg.content}</p>
                  <div
                    className={`flex items-center gap-2 mt-1 text-xs ${
                      msg.direction === "outbound" ? "text-primary-200" : "text-gray-400"
                    }`}
                  >
                    <span>
                      {msg.created_at
                        ? new Date(msg.created_at).toLocaleTimeString()
                        : ""}
                    </span>
                    {msg.agent_type && (
                      <span className="capitalize">• {msg.agent_type} agent</span>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {!loading && messages.length === 0 && phone && (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-12 text-center">
          <p className="text-gray-500">No messages found for this phone number.</p>
        </div>
      )}

      {!loading && !phone && (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-12 text-center">
          <p className="text-gray-500">Enter a phone number to view conversation history.</p>
        </div>
      )}
    </div>
  );
}
