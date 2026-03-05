import { useState } from "react";
import { Trash2, Ban, RotateCcw, ExternalLink, ChevronDown, ChevronRight } from "lucide-react";
import { StarRating } from "./StarRating";
import { Badge } from "../common/Badge";
import type { Lead } from "../../types";

interface LeadCardProps {
  lead: Lead;
  mode: "queue" | "rated";
  onRate: (id: number, rating: number) => void;
  onDelete: (id: number) => void;
  onBlock: (company: string) => void;
  onResetRating: (id: number) => void;
  onUpdateWebsite: (id: number, url: string) => void;
}

export function LeadCard({ lead, mode, onRate, onDelete, onBlock, onResetRating, onUpdateWebsite }: LeadCardProps) {
  const [sourceOpen, setSourceOpen] = useState(false);
  const [webInput, setWebInput] = useState("");

  const tags: string[] = [];
  if (lead.sector !== "other") tags.push(lead.sector.replace(/_/g, " "));
  if (lead.company_type !== "unknown") tags.push(lead.company_type.replace(/_/g, " "));
  if (lead.location) tags.push(lead.location);

  const truncate = (s: string, n: number) => (s.length > n ? s.slice(0, n) + "..." : s);

  return (
    <div
      className="rounded-md p-4 mb-3"
      style={{ backgroundColor: "var(--bg-card)", border: "1px solid var(--border)" }}
    >
      {/* Header */}
      <div className="flex items-center gap-2 mb-1">
        <h3 className="text-lg font-bold uppercase m-0" style={{ color: "var(--text-primary)" }}>
          {lead.company_name}
        </h3>
        {lead.user_rating && (
          <span className="text-sm" style={{ color: "var(--star-color)" }}>
            {"★".repeat(lead.user_rating)}{"☆".repeat(5 - lead.user_rating)}
          </span>
        )}
      </div>

      {/* Tags */}
      {tags.length > 0 && (
        <div className="text-xs uppercase tracking-wide mb-2" style={{ color: "var(--text-muted)" }}>
          {tags.join(" // ")}
        </div>
      )}

      {/* Details grid */}
      <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-sm mb-2">
        <div>
          {lead.product_name && (
            <div><span className="font-semibold uppercase" style={{ color: "var(--text-secondary)" }}>Product:</span> {lead.product_name}</div>
          )}
          {lead.tech_stack.length > 0 && (
            <div className="flex flex-wrap gap-1 mt-1">
              <span className="font-semibold uppercase" style={{ color: "var(--text-secondary)" }}>Stack:</span>
              {lead.tech_stack.map((t) => <Badge key={t}>{t}</Badge>)}
            </div>
          )}
          {lead.funding_stage && (
            <div className="mt-1"><span className="font-semibold uppercase" style={{ color: "var(--text-secondary)" }}>Funding:</span> {lead.funding_stage}</div>
          )}
        </div>
        <div>
          {lead.jetson_confirmed ? (
            <>
              <div className="flex flex-wrap gap-1">
                <span className="font-semibold uppercase" style={{ color: "var(--text-secondary)" }}>Jetson:</span>
                {lead.jetson_models.length > 0
                  ? lead.jetson_models.map((m) => <Badge key={m}>{m}</Badge>)
                  : <Badge>Confirmed</Badge>}
              </div>
              {lead.jetson_usage && (
                <div className="mt-1"><span className="font-semibold uppercase" style={{ color: "var(--text-secondary)" }}>Usage:</span> {lead.jetson_usage}</div>
              )}
            </>
          ) : (
            <div><span className="font-semibold uppercase" style={{ color: "var(--text-secondary)" }}>Jetson:</span> <Badge danger>Unknown</Badge></div>
          )}
          {lead.website_url ? (
            <div className="mt-1">
              <span className="font-semibold uppercase" style={{ color: "var(--text-secondary)" }}>Web: </span>
              <a
                href={lead.website_url}
                target="_blank"
                rel="noopener noreferrer"
                className="hover:underline inline-flex items-center gap-1"
                style={{ color: "var(--accent)" }}
              >
                {truncate(lead.website_url, 35)} <ExternalLink size={12} />
              </a>
            </div>
          ) : (
            <div className="mt-1">
              <input
                type="text"
                placeholder="Enter website URL..."
                value={webInput}
                onChange={(e) => setWebInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && webInput.startsWith("http")) {
                    onUpdateWebsite(lead.id, webInput);
                    setWebInput("");
                  }
                }}
                className="w-full px-2 py-1 rounded text-xs"
                style={{
                  backgroundColor: "var(--bg-primary)",
                  color: "var(--text-primary)",
                  border: "1px solid var(--border)",
                }}
              />
            </div>
          )}
          {lead.source_url && lead.website_url && (
            <div className="mt-1">
              <button
                onClick={() => setSourceOpen(!sourceOpen)}
                className="flex items-center gap-1 text-xs cursor-pointer bg-transparent border-none p-0"
                style={{ color: "var(--text-muted)" }}
              >
                {sourceOpen ? <ChevronDown size={12} /> : <ChevronRight size={12} />}
                SOURCE
              </button>
              {sourceOpen && (
                <a
                  href={lead.source_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-xs hover:underline block mt-0.5"
                  style={{ color: "var(--accent)" }}
                >
                  {truncate(lead.source_url, 45)}
                </a>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Summary */}
      {lead.summary && (
        <div className="text-sm italic mb-3" style={{ color: "var(--text-secondary)" }}>
          {lead.summary}
        </div>
      )}

      {/* Actions */}
      {mode === "queue" ? (
        <div className="flex items-center gap-3">
          <StarRating onRate={(rating) => onRate(lead.id, rating)} size={20} />
          <div className="flex-1" />
          <button
            onClick={() => onDelete(lead.id)}
            className="flex items-center gap-1 px-2 py-1 rounded text-xs cursor-pointer transition-colors hover-danger-btn"
            style={{ backgroundColor: "var(--bg-primary)", color: "var(--text-muted)", border: "1px solid var(--border)" }}
          >
            <Trash2 size={12} /> DELETE
          </button>
          <button
            onClick={() => onBlock(lead.company_name)}
            className="flex items-center gap-1 px-2 py-1 rounded text-xs cursor-pointer transition-colors"
            style={{ backgroundColor: "var(--bg-primary)", color: "var(--text-muted)", border: "1px solid var(--border)" }}
          >
            <Ban size={12} /> BLOCK
          </button>
        </div>
      ) : (
        <div className="flex items-center gap-3">
          <button
            onClick={() => onResetRating(lead.id)}
            className="flex items-center gap-1 px-2 py-1 rounded text-xs cursor-pointer transition-colors"
            style={{ backgroundColor: "var(--bg-primary)", color: "var(--text-muted)", border: "1px solid var(--border)" }}
          >
            <RotateCcw size={12} /> BACK TO QUEUE
          </button>
          <div className="flex-1" />
          <button
            className="flex items-center gap-1 px-3 py-1 rounded text-xs font-semibold cursor-pointer"
            style={{ backgroundColor: "var(--accent)", color: "var(--bg-primary)", border: "none" }}
          >
            PUSH TO SALESFORCE
          </button>
        </div>
      )}
    </div>
  );
}
