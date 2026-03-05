export enum Sector {
  ROBOTICS = "robotics",
  AUTONOMOUS_VEHICLES = "autonomous_vehicles",
  INDUSTRIAL_AUTOMATION = "industrial_automation",
  SMART_CITIES = "smart_cities",
  HEALTHCARE = "healthcare",
  AGRICULTURE = "agriculture",
  RETAIL = "retail",
  DEFENSE = "defense",
  DRONES = "drones",
  EDGE_AI = "edge_ai",
  COMPUTER_VISION = "computer_vision",
  OTHER = "other",
}

export enum CompanyType {
  END_USER = "end_user",
  RESELLER = "reseller",
  MANUFACTURER = "manufacturer",
  SERVICE_PROVIDER = "service_provider",
  DISTRIBUTOR = "distributor",
  UNKNOWN = "unknown",
}

export interface Lead {
  id: number;
  company_name: string;
  sector: string;
  company_type: string;
  funding_stage: string | null;
  product_name: string;
  location: string | null;
  website_url: string;
  source_url: string;
  source_type: string;
  tech_stack: string[];
  jetson_usage: string | null;
  jetson_models: string[];
  jetson_confirmed: boolean;
  user_rating: number | null;
  feedback: string | null;
  campaign: string;
  summary: string;
  discovered_at: string;
}

export interface Campaign {
  name: string;
  filename: string;
  description: string;
}

export interface BlockedCompany {
  company_name: string;
  blocked_at: string;
  reason: string;
}

export interface Stats {
  total: number;
  rated: number;
  queue: number;
}

export interface ResearchJobStatus {
  job_id: string;
  status: "pending" | "running" | "completed" | "failed";
  progress: number;
  phase: string;
  result: { saved: number; skipped: number } | null;
  error: string | null;
}

export interface ProviderInfo {
  name: string;
  has_key: boolean;
}
