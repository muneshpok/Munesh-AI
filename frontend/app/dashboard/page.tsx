import { AgentList } from '../../components/AgentList';

export default function DashboardPage() {
  return (
    <>
      <AgentList />
      <section className="panel">
        <h3>Platform Overview</h3>
        <p>Monitor agent lifecycle, tool availability, and memory subsystem health from this dashboard.</p>
      </section>
    </>
  );
}
