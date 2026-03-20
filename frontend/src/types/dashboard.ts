// Dashboard types

export interface BountyHistoryItem {
  id: string;
  title: string;
  status: 'open' | 'claimed' | 'completed' | 'cancelled';
  tier: 1 | 2 | 3;
  reward_amount: number;
  reward_token: string;
  completed_at?: string;
  created_at: string;
}

export interface EarningsStats {
  total_earned: number;
  total_bounties: number;
  average_reward: number;
  this_month_earned: number;
  last_month_earned: number;
  by_token: Record<string, number>;
}

export interface ReputationChange {
  date: string;
  change: number;
  reason: string;
  new_total: number;
}

export interface ReputationStats {
  current_score: number;
  total_changes: number;
  recent_changes: ReputationChange[];
}

export interface DashboardSummary {
  contributor_id: string;
  username: string;
  display_name: string;
  avatar_url?: string;
  wallet_address?: string;
  earnings: EarningsStats;
  reputation: ReputationStats;
  active_bounties: number;
  completed_bounties: BountyHistoryItem[];
  claimed_bounties: BountyHistoryItem[];
}

export interface DashboardResponse {
  summary: DashboardSummary;
  bounty_history: BountyHistoryItem[];
  earnings_chart: { month: string; earned: number }[];
  reputation_history: { month: string; score: number }[];
}

export interface Contributor {
  id: string;
  username: string;
  display_name: string;
  avatar_url?: string;
  bio?: string;
  skills: string[];
  badges: string[];
  stats: {
    total_contributions: number;
    total_bounties_completed: number;
    total_earnings: number;
    reputation_score: number;
  };
  created_at: string;
  updated_at: string;
}