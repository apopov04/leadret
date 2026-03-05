import { LeadCard } from "./LeadCard";
import type { Lead } from "../../types";

interface LeadListProps {
  leads: Lead[];
  mode: "queue" | "rated";
  onRate: (id: number, rating: number) => void;
  onDelete: (id: number) => void;
  onBlock: (company: string) => void;
  onResetRating: (id: number) => void;
  onUpdateWebsite: (id: number, url: string) => void;
}

export function LeadList({ leads, mode, onRate, onDelete, onBlock, onResetRating, onUpdateWebsite }: LeadListProps) {
  if (leads.length === 0) {
    return (
      <div
        className="text-center py-8 rounded text-sm uppercase"
        style={{ color: "var(--text-muted)", backgroundColor: "var(--bg-card)", border: "1px solid var(--border)" }}
      >
        {mode === "queue" ? "[ Queue empty — run research or all leads rated ]" : "[ No rated leads yet ]"}
      </div>
    );
  }

  return (
    <div>
      {leads.map((lead) => (
        <LeadCard
          key={lead.id}
          lead={lead}
          mode={mode}
          onRate={onRate}
          onDelete={onDelete}
          onBlock={onBlock}
          onResetRating={onResetRating}
          onUpdateWebsite={onUpdateWebsite}
        />
      ))}
    </div>
  );
}
