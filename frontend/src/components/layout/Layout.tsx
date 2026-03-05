import type { ReactNode } from "react";
import { Sidebar } from "../sidebar/Sidebar";

interface LayoutProps {
  children: ReactNode;
  selectedCampaign: string;
  onCampaignChange: (campaign: string, name: string) => void;
}

export function Layout({ children, selectedCampaign, onCampaignChange }: LayoutProps) {
  return (
    <div className="flex min-h-screen">
      <Sidebar selectedCampaign={selectedCampaign} onCampaignChange={onCampaignChange} />
      <main className="flex-1 ml-72 p-6">
        {children}
      </main>
    </div>
  );
}
