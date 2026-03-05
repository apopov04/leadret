import { useState, useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
import { Sun, Moon, X, Plus, Trash2, Pencil } from "lucide-react";
import { useTheme } from "../../context/ThemeContext";
import { fetchCampaigns, createCampaign, updateCampaign, deleteCampaign } from "../../api/campaigns";
import { fetchProviders } from "../../api/research";
import { fetchBlocked } from "../../api/blocked";
import { unblockCompany } from "../../api/blocked";
import { useQueryClient } from "@tanstack/react-query";
import { useResearch } from "../../hooks/useResearch";
import type { Campaign } from "../../types";

interface SidebarProps {
  selectedCampaign: string;
  onCampaignChange: (campaign: string, name: string) => void;
}

export function Sidebar({ selectedCampaign, onCampaignChange }: SidebarProps) {
  const { theme, toggle } = useTheme();
  const qc = useQueryClient();
  const [adhocPrompt, setAdhocPrompt] = useState("");
  const [selectedProvider, setSelectedProvider] = useState("gemini");
  const [showNewCampaign, setShowNewCampaign] = useState(false);
  const [newName, setNewName] = useState("");
  const [newDescription, setNewDescription] = useState("");
  const [createError, setCreateError] = useState("");
  const [confirmDelete, setConfirmDelete] = useState(false);
  const [editMode, setEditMode] = useState(false);
  const [editName, setEditName] = useState("");
  const [editDescription, setEditDescription] = useState("");
  const { job, isRunning, run } = useResearch();

  const { data: campaigns = [] } = useQuery({ queryKey: ["campaigns"], queryFn: fetchCampaigns });
  const { data: providers = [] } = useQuery({ queryKey: ["providers"], queryFn: fetchProviders });
  const { data: blocked = [] } = useQuery({ queryKey: ["blocked"], queryFn: fetchBlocked });

  // Sync provider default to first available if current selection is missing
  useEffect(() => {
    if (providers.length > 0 && !providers.find((p) => p.name === selectedProvider)) {
      setSelectedProvider(providers[0].name);
    }
  }, [providers, selectedProvider]);

  const isCustom = selectedCampaign === "__custom__";
  const selectedProviderInfo = providers.find((p) => p.name === selectedProvider);
  const hasKey = selectedProviderInfo?.has_key ?? false;

  const canExecute = isCustom ? adhocPrompt.trim().length > 0 && hasKey : hasKey;

  const handleExecute = () => {
    if (!canExecute || isRunning) return;

    if (isCustom) {
      run({ prompt: adhocPrompt.trim(), provider: selectedProvider });
    } else {
      run({ campaign: selectedCampaign, provider: selectedProvider });
    }
  };

  const handleCreateCampaign = async () => {
    if (!newName.trim() || !newDescription.trim()) return;
    setCreateError("");
    try {
      const created = await createCampaign(newName.trim(), newDescription.trim());
      qc.invalidateQueries({ queryKey: ["campaigns"] });
      onCampaignChange(created.filename, created.name);
      setNewName("");
      setNewDescription("");
      setShowNewCampaign(false);
    } catch (e: any) {
      setCreateError(e.message || "Failed to create campaign");
    }
  };

  const handleDeleteCampaign = async () => {
    if (isCustom || !selectedCampaign) return;
    if (!confirmDelete) {
      setConfirmDelete(true);
      return;
    }
    setConfirmDelete(false);
    try {
      await deleteCampaign(selectedCampaign);
      qc.invalidateQueries({ queryKey: ["campaigns"] });
      const remaining = campaigns.filter((c) => c.filename !== selectedCampaign);
      if (remaining.length > 0) {
        onCampaignChange(remaining[0].filename, remaining[0].name);
      } else {
        onCampaignChange("__custom__", "adhoc");
      }
    } catch {
      // silently fail
    }
  };

  const handleStartEdit = () => {
    const c = campaigns.find((c) => c.filename === selectedCampaign);
    if (!c) return;
    setEditName(c.name);
    setEditDescription(c.description);
    setEditMode(true);
  };

  const handleSaveEdit = async () => {
    if (!editName.trim() || !editDescription.trim()) return;
    try {
      const updated = await updateCampaign(selectedCampaign, editName.trim(), editDescription.trim());
      qc.invalidateQueries({ queryKey: ["campaigns"] });
      onCampaignChange(updated.filename, updated.name);
      setEditMode(false);
    } catch {
      // silently fail
    }
  };

  const handleUnblock = async (name: string) => {
    await unblockCompany(name);
    qc.invalidateQueries({ queryKey: ["blocked"] });
    qc.invalidateQueries({ queryKey: ["leads"] });
    qc.invalidateQueries({ queryKey: ["stats"] });
  };

  return (
    <aside
      className="w-72 h-screen fixed top-0 left-0 flex flex-col p-4 overflow-y-auto"
      style={{ backgroundColor: "var(--bg-secondary)", borderRight: "1px solid var(--border)" }}
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-1">
        <div className="flex items-center gap-2">
          <img
            src={theme === "pipboy" ? "/leadret-green.png" : "/leadret-blue.png"}
            alt="LeadRet"
            className="w-7 h-7"
          />
          <h2 className="text-lg font-bold uppercase m-0" style={{ color: "var(--text-primary)" }}>
            LeadRet
          </h2>
        </div>
        <button
          onClick={toggle}
          className="p-1.5 rounded cursor-pointer bg-transparent border-none"
          style={{ color: "var(--text-muted)" }}
          title="Toggle theme"
        >
          {theme === "pipboy" ? <Sun size={16} /> : <Moon size={16} />}
        </button>
      </div>
      <div className="text-xs uppercase tracking-wide mb-4" style={{ color: "var(--text-muted)" }}>
        V3.0 // React + FastAPI
      </div>

      {/* Campaign selector */}
      <div className="flex items-center justify-between mb-1">
        <label className="text-xs uppercase tracking-wide font-semibold" style={{ color: confirmDelete ? "var(--badge-danger)" : "var(--text-muted)" }}>
          {confirmDelete ? "Delete?" : "Campaign"}
        </label>
        <div className="flex items-center gap-1">
          {!confirmDelete && (
            <button
              onClick={() => setShowNewCampaign(!showNewCampaign)}
              className="bg-transparent border-none cursor-pointer p-0.5"
              style={{ color: showNewCampaign ? "var(--accent)" : "var(--text-muted)" }}
              title="New campaign"
            >
              <Plus size={14} />
            </button>
          )}
          {!isCustom && selectedCampaign && !confirmDelete && (
            <>
              <button
                onClick={handleStartEdit}
                className="bg-transparent border-none cursor-pointer p-0.5 transition-colors"
                style={{ color: editMode ? "var(--accent)" : "var(--text-muted)" }}
                title="Edit campaign"
              >
                <Pencil size={13} />
              </button>
              <button
                onClick={handleDeleteCampaign}
                className="bg-transparent border-none cursor-pointer p-0.5 hover-danger transition-colors"
                style={{ color: "var(--text-muted)" }}
                title="Delete campaign"
              >
                <Trash2 size={13} />
              </button>
            </>
          )}
          {confirmDelete && (
            <>
              <button
                onClick={handleDeleteCampaign}
                className="border-none cursor-pointer px-1.5 py-0.5 rounded text-xs font-bold uppercase"
                style={{ backgroundColor: "var(--badge-danger)", color: "#fff" }}
              >
                Yes
              </button>
              <button
                onClick={() => setConfirmDelete(false)}
                className="bg-transparent cursor-pointer px-1.5 py-0.5 rounded text-xs uppercase"
                style={{ color: "var(--text-muted)", border: "1px solid var(--border)" }}
              >
                No
              </button>
            </>
          )}
        </div>
      </div>

      {editMode ? (
        <div className="mb-3 space-y-2">
          <input
            value={editName}
            onChange={(e) => setEditName(e.target.value)}
            placeholder="Campaign name..."
            className="w-full px-2 py-1.5 rounded text-sm"
            style={{
              backgroundColor: "var(--bg-card)",
              color: "var(--text-primary)",
              border: "1px solid var(--border)",
              fontFamily: "inherit",
            }}
          />
          <textarea
            value={editDescription}
            onChange={(e) => setEditDescription(e.target.value)}
            placeholder="Describe what companies to find..."
            rows={4}
            className="w-full px-2 py-1.5 rounded text-sm resize-none"
            style={{
              backgroundColor: "var(--bg-card)",
              color: "var(--text-primary)",
              border: "1px solid var(--border)",
              fontFamily: "inherit",
            }}
          />
          <div className="flex gap-2">
            <button
              onClick={handleSaveEdit}
              disabled={!editName.trim() || !editDescription.trim()}
              className="flex-1 py-1.5 rounded text-xs font-bold uppercase cursor-pointer disabled:opacity-40 disabled:cursor-not-allowed"
              style={{
                backgroundColor: "var(--accent)",
                color: "var(--bg-primary)",
                border: "none",
                fontFamily: "inherit",
              }}
            >
              Save
            </button>
            <button
              onClick={() => setEditMode(false)}
              className="py-1.5 px-3 rounded text-xs uppercase cursor-pointer"
              style={{
                backgroundColor: "transparent",
                color: "var(--text-muted)",
                border: "1px solid var(--border)",
                fontFamily: "inherit",
              }}
            >
              Cancel
            </button>
          </div>
        </div>
      ) : showNewCampaign ? (
        <div className="mb-3 space-y-2">
          <input
            value={newName}
            onChange={(e) => setNewName(e.target.value)}
            placeholder="Campaign name..."
            className="w-full px-2 py-1.5 rounded text-sm"
            style={{
              backgroundColor: "var(--bg-card)",
              color: "var(--text-primary)",
              border: "1px solid var(--border)",
              fontFamily: "inherit",
            }}
          />
          <textarea
            value={newDescription}
            onChange={(e) => setNewDescription(e.target.value)}
            placeholder="Describe what companies to find..."
            rows={3}
            className="w-full px-2 py-1.5 rounded text-sm resize-none"
            style={{
              backgroundColor: "var(--bg-card)",
              color: "var(--text-primary)",
              border: "1px solid var(--border)",
              fontFamily: "inherit",
            }}
          />
          {createError && (
            <div className="text-xs px-1" style={{ color: "var(--badge-danger)" }}>
              {createError}
            </div>
          )}
          <div className="flex gap-2">
            <button
              onClick={handleCreateCampaign}
              disabled={!newName.trim() || !newDescription.trim()}
              className="flex-1 py-1.5 rounded text-xs font-bold uppercase cursor-pointer disabled:opacity-40 disabled:cursor-not-allowed"
              style={{
                backgroundColor: "var(--accent)",
                color: "var(--bg-primary)",
                border: "none",
                fontFamily: "inherit",
              }}
            >
              Create
            </button>
            <button
              onClick={() => { setShowNewCampaign(false); setNewName(""); setNewDescription(""); setCreateError(""); }}
              className="py-1.5 px-3 rounded text-xs uppercase cursor-pointer"
              style={{
                backgroundColor: "transparent",
                color: "var(--text-muted)",
                border: "1px solid var(--border)",
                fontFamily: "inherit",
              }}
            >
              Cancel
            </button>
          </div>
        </div>
      ) : (
        <>
          <select
            value={isCustom ? "__custom__" : selectedCampaign}
            onChange={(e) => {
              const val = e.target.value;
              if (val === "__custom__") {
                onCampaignChange("__custom__", "adhoc");
              } else {
                const c = campaigns.find((c: Campaign) => c.filename === val);
                onCampaignChange(val, c?.name || val);
              }
            }}
            className="w-full px-2 py-1.5 rounded text-sm mb-3 cursor-pointer"
            style={{
              backgroundColor: "var(--bg-card)",
              color: "var(--text-primary)",
              border: "1px solid var(--border)",
              fontFamily: "inherit",
            }}
          >
            {campaigns.map((c: Campaign) => (
              <option key={c.filename} value={c.filename}>
                {c.name}
              </option>
            ))}
            <option value="__custom__">AD-HOC QUERY</option>
          </select>

          {isCustom && (
            <textarea
              value={adhocPrompt}
              onChange={(e) => setAdhocPrompt(e.target.value)}
              placeholder="&gt; Find robotics startups using ROS2..."
              rows={3}
              className="w-full px-2 py-1.5 rounded text-sm mb-3 resize-none"
              style={{
                backgroundColor: "var(--bg-card)",
                color: "var(--text-primary)",
                border: "1px solid var(--border)",
                fontFamily: "inherit",
              }}
            />
          )}
        </>
      )}

      {/* Divider */}
      <hr style={{ borderColor: "var(--border)" }} className="my-2" />

      {/* Execute section */}
      <label className="text-xs uppercase tracking-wide font-semibold mb-1" style={{ color: "var(--text-muted)" }}>
        Execute
      </label>

      <select
        value={selectedProvider}
        onChange={(e) => setSelectedProvider(e.target.value)}
        className="w-full px-2 py-1.5 rounded text-sm mb-2 cursor-pointer"
        style={{
          backgroundColor: "var(--bg-card)",
          color: "var(--text-primary)",
          border: "1px solid var(--border)",
          fontFamily: "inherit",
        }}
      >
        {providers.map((p) => (
          <option key={p.name} value={p.name}>
            {p.name.toUpperCase()}
          </option>
        ))}
      </select>

      {!hasKey && (
        <div className="text-xs mb-2 px-1" style={{ color: "var(--badge-danger)" }}>
          NO API KEY SET FOR {selectedProvider.toUpperCase()}
        </div>
      )}

      <button
        onClick={handleExecute}
        disabled={!canExecute || isRunning}
        className="w-full py-2 rounded text-sm font-bold uppercase tracking-wide cursor-pointer transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
        style={{
          backgroundColor: "var(--accent)",
          color: "var(--bg-primary)",
          border: "none",
          fontFamily: "inherit",
        }}
      >
        {isRunning ? "RUNNING..." : "EXECUTE"}
      </button>

      {/* Progress */}
      {job && (
        <div className="mt-2">
          <div className="w-full rounded overflow-hidden h-2" style={{ backgroundColor: "var(--border)" }}>
            <div
              className="h-full transition-all duration-500"
              style={{ width: `${job.progress * 100}%`, backgroundColor: "var(--accent)" }}
            />
          </div>
          <div className="text-xs mt-1 uppercase" style={{ color: "var(--text-muted)" }}>
            [{job.phase}]
          </div>
          {job.status === "completed" && job.result && (
            <div className="text-xs mt-1" style={{ color: "var(--accent)" }}>
              Saved {job.result.saved}, skipped {job.result.skipped}
            </div>
          )}
          {job.status === "failed" && (
            <div className="text-xs mt-1" style={{ color: "var(--badge-danger)" }}>
              Error: {job.error}
            </div>
          )}
        </div>
      )}

      {/* Divider */}
      <hr style={{ borderColor: "var(--border)" }} className="my-3" />

      {/* Blocklist */}
      <label className="text-xs uppercase tracking-wide font-semibold mb-1" style={{ color: "var(--text-muted)" }}>
        Blocklist
      </label>
      {blocked.length === 0 ? (
        <div className="text-xs" style={{ color: "var(--text-muted)" }}>empty</div>
      ) : (
        <div className="space-y-1">
          {blocked.map((bc) => (
            <div key={bc.company_name} className="flex items-center justify-between text-xs">
              <span style={{ color: "var(--text-secondary)" }}>~ {bc.company_name}</span>
              <button
                onClick={() => handleUnblock(bc.company_name)}
                className="bg-transparent border-none cursor-pointer p-0.5"
                style={{ color: "var(--text-muted)" }}
              >
                <X size={12} />
              </button>
            </div>
          ))}
        </div>
      )}
    </aside>
  );
}
