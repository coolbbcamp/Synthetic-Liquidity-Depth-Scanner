const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export type Score = {
  exit_capacity_99: number | null;
  exit_capacity_95: number | null;
  exit_capacity_90: number | null;
  no_route_ceiling: number | null;
  mcap_usd: number | null;
  mcap_exit_ratio: number | null;
  binding_leg: string | null;
  cliff_detected: boolean;
  cliff_notional: number | null;
  rfq_dependence: number | null;
  grade: string | null;
  computed_at: string;
};

export type Asset = {
  mint: string;
  symbol: string;
  name: string;
  kind: string;
  quote_symbol: string | null;
  tier: string;
  latest_score: Score | null;
  probed_at: string | null;
  is_probed: boolean;
};

export type AssetDetail = Asset & {
  quote_mint: string | null;
  pool: string | null;
  latest_rungs: Array<{
    notional_usd: number;
    out_usd: number | null;
    efficiency: number | null;
    route_labels: string | null;
    rfq_share: number | null;
    no_route: boolean;
    binding_leg: string | null;
  }>;
  probed_at: string | null;
  session_state: string | null;
};

export type LeaderboardEntry = {
  mint: string;
  exit_capacity_95: number | null;
  mcap_exit_ratio: number | null;
  grade: string | null;
  cliff_detected: boolean;
  no_route_ceiling: number | null;
  computed_at: string;
};

export async function fetchAssets(): Promise<Asset[]> {
  const res = await fetch(`${API_URL}/assets`);
  if (!res.ok) throw new Error("failed to fetch assets");
  return res.json();
}

export async function fetchAsset(mint: string): Promise<AssetDetail> {
  const res = await fetch(`${API_URL}/assets/${mint}`);
  if (!res.ok) throw new Error("failed to fetch asset");
  return res.json();
}

export async function fetchLeaderboard(): Promise<LeaderboardEntry[]> {
  const res = await fetch(`${API_URL}/leaderboard?sort=mcap_exit_ratio`);
  if (!res.ok) throw new Error("failed to fetch leaderboard");
  return res.json();
}

export async function fetchExitQuote(mint: string, notional: number) {
  const res = await fetch(`${API_URL}/exit-quote?mint=${mint}&notional=${notional}`);
  if (!res.ok) {
    if (res.status === 404) throw new Error("404");
    throw new Error(`failed to fetch exit quote (${res.status})`);
  }
  return res.json();
}
