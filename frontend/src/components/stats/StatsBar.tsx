import type { Stats } from "../../types";

function StatCard({ label, value }: { label: string; value: number }) {
  return (
    <div
      className="flex-1 rounded px-4 py-3 text-center"
      style={{ backgroundColor: "var(--bg-card)", border: "1px solid var(--border)" }}
    >
      <div className="text-xs uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>
        {label}
      </div>
      <div className="text-2xl font-bold mt-1" style={{ color: "var(--text-primary)" }}>
        {value}
      </div>
    </div>
  );
}

export function StatsBar({ stats }: { stats: Stats }) {
  return (
    <div className="flex gap-3">
      <StatCard label="Total" value={stats.total} />
      <StatCard label="Rated" value={stats.rated} />
      <StatCard label="Queue" value={stats.queue} />
    </div>
  );
}
