import { useState } from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ThemeProvider } from "./context/ThemeContext";
import { Layout } from "./components/layout/Layout";
import { StatsBar } from "./components/stats/StatsBar";
import { TabSwitcher } from "./components/common/TabSwitcher";
import { LeadList } from "./components/leads/LeadList";
import { useStats } from "./hooks/useStats";
import {
  useQueueLeads,
  useRatedLeads,
  useRateLead,
  useDeleteLead,
  useBlockCompany,
  useResetRating,
  useUpdateWebsite,
} from "./hooks/useLeads";

const queryClient = new QueryClient({
  defaultOptions: { queries: { staleTime: 5000, refetchOnWindowFocus: true } },
});

function Dashboard() {
  const [campaignFile, setCampaignFile] = useState("jetson");
  const [campaignName, setCampaignName] = useState("NVIDIA Jetson");
  const [activeTab, setActiveTab] = useState("queue");

  const campaign = campaignFile === "__custom__" ? "adhoc" : campaignName;

  const { data: stats } = useStats(campaign);
  const { data: queueLeads = [] } = useQueueLeads(campaign);
  const { data: ratedLeads = [] } = useRatedLeads(campaign);

  const rateLead = useRateLead(campaign);
  const deleteLeadMut = useDeleteLead(campaign);
  const blockCompany = useBlockCompany(campaign);
  const resetRating = useResetRating(campaign);
  const updateWebsite = useUpdateWebsite(campaign);

  const handleCampaignChange = (file: string, name: string) => {
    setCampaignFile(file);
    setCampaignName(name);
  };

  return (
    <Layout selectedCampaign={campaignFile} onCampaignChange={handleCampaignChange}>
      <h1 className="text-2xl font-bold uppercase m-0 mb-1" style={{ color: "var(--text-primary)" }}>
        &gt; Leadrador Retriever
      </h1>
      <div className="text-xs uppercase tracking-wide mb-4" style={{ color: "var(--text-muted)" }}>
        Campaign: {campaign}
      </div>

      {stats && stats.total > 0 ? (
        <StatsBar stats={stats} />
      ) : (
        <div
          className="text-center py-4 rounded text-sm uppercase"
          style={{ color: "var(--text-muted)", backgroundColor: "var(--bg-card)", border: "1px solid var(--border)" }}
        >
          [ No leads found — run a campaign or ad-hoc query ]
        </div>
      )}

      <div className="my-4">
        <TabSwitcher
          activeTab={activeTab}
          onTabChange={setActiveTab}
          tabs={[
            { key: "queue", label: "Queue", count: stats?.queue ?? 0 },
            { key: "rated", label: "Rated", count: stats?.rated ?? 0 },
          ]}
        />
      </div>

      <LeadList
        leads={activeTab === "queue" ? queueLeads : ratedLeads}
        mode={activeTab as "queue" | "rated"}
        onRate={(id, rating) => rateLead.mutate({ id, rating })}
        onDelete={(id) => deleteLeadMut.mutate(id)}
        onBlock={(company) => blockCompany.mutate(company)}
        onResetRating={(id) => resetRating.mutate(id)}
        onUpdateWebsite={(id, url) => updateWebsite.mutate({ id, url })}
      />
    </Layout>
  );
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider>
        <Dashboard />
      </ThemeProvider>
    </QueryClientProvider>
  );
}
