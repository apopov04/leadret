export function Badge({ children, danger }: { children: React.ReactNode; danger?: boolean }) {
  return (
    <span
      className="inline-block px-2 py-0.5 rounded text-xs font-medium"
      style={{
        backgroundColor: danger ? "transparent" : "var(--badge-bg)",
        color: danger ? "var(--badge-danger)" : "var(--accent)",
        border: danger ? `1px solid var(--badge-danger)` : "none",
      }}
    >
      {children}
    </span>
  );
}
