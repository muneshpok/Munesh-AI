const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? 'http://localhost:8000/api/v1';

export async function runAgent(goal: string, agentName: string) {
  const response = await fetch(`${API_BASE}/agents/run`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ goal, agent_name: agentName }),
  });
  if (!response.ok) throw new Error('Agent execution failed');
  return response.json();
}

export async function listAgents(): Promise<string[]> {
  const response = await fetch(`${API_BASE}/agents`);
  if (!response.ok) throw new Error('Unable to fetch agents');
  return response.json();
}
