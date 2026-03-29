'use client';

import { useEffect, useState } from 'react';
import { listAgents } from '../lib/api';

export function AgentList() {
  const [agents, setAgents] = useState<string[]>([]);

  useEffect(() => {
    listAgents().then(setAgents).catch(() => setAgents([]));
  }, []);

  return (
    <section className="panel">
      <h3>Registered Agents</h3>
      <ul>
        {agents.map((agent) => (
          <li key={agent}>{agent}</li>
        ))}
      </ul>
    </section>
  );
}
