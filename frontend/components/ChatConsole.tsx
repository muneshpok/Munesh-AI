'use client';

import { useState } from 'react';
import { runAgent } from '../lib/api';

export function ChatConsole() {
  const [goal, setGoal] = useState('');
  const [agentName, setAgentName] = useState('general');
  const [output, setOutput] = useState('');
  const [loading, setLoading] = useState(false);

  const submit = async () => {
    setLoading(true);
    try {
      const data = await runAgent(goal, agentName);
      setOutput(JSON.stringify(data, null, 2));
    } catch (error) {
      setOutput((error as Error).message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="panel">
      <h3>AI Chat Execution</h3>
      <label>Agent</label>
      <select value={agentName} onChange={(e) => setAgentName(e.target.value)}>
        <option value="general">general</option>
        <option value="research">research</option>
        <option value="planner">planner</option>
      </select>
      <label>Goal</label>
      <textarea rows={4} value={goal} onChange={(e) => setGoal(e.target.value)} placeholder="Describe the task for the selected agent" />
      <button onClick={submit} disabled={loading || goal.length < 3}>{loading ? 'Running...' : 'Run Task'}</button>
      <pre>{output}</pre>
    </section>
  );
}
