interface TabSwitcherProps {
  activeTab: string;
  onTabChange: (tab: string) => void;
  tabs: { key: string; label: string; count: number }[];
}

export function TabSwitcher({ activeTab, onTabChange, tabs }: TabSwitcherProps) {
  return (
    <div className="flex gap-2">
      {tabs.map((tab) => (
        <button
          key={tab.key}
          onClick={() => onTabChange(tab.key)}
          className="flex-1 py-2 px-4 rounded text-sm font-semibold uppercase tracking-wide transition-colors cursor-pointer"
          style={{
            backgroundColor: activeTab === tab.key ? "var(--accent)" : "var(--bg-card)",
            color: activeTab === tab.key ? "var(--bg-primary)" : "var(--text-primary)",
            border: `1px solid ${activeTab === tab.key ? "var(--accent)" : "var(--border)"}`,
          }}
        >
          {tab.label} [{tab.count}]
        </button>
      ))}
    </div>
  );
}
