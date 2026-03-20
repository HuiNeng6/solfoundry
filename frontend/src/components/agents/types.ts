// Agent Types for SolFoundry Marketplace

export type AgentRole = 
  | 'frontend'
  | 'backend'
  | 'smart-contracts'
  | 'security'
  | 'devops'
  | 'testing'
  | 'documentation'
  | 'integration';

export type AgentStatus = 'available' | 'busy' | 'offline';

export type AgentTier = 'tier-1' | 'tier-2' | 'tier-3';

export interface AgentStats {
  bountiesCompleted: number;
  totalEarned: number; // in $FNDRY
  successRate: number; // 0-100
  avgCompletionTime: number; // in hours
  reputationScore: number;
}

export interface Agent {
  id: string;
  name: string;
  description: string;
  role: AgentRole;
  capabilities: string[];
  status: AgentStatus;
  tier: AgentTier;
  stats: AgentStats;
  walletAddress: string;
  avatarUrl?: string;
  githubUrl?: string;
  lastActive: string; // ISO date string
  hourlyRate?: number; // in $FNDRY
  tags: string[];
}

export interface AgentFilter {
  search: string;
  roles: AgentRole[];
  status: AgentStatus[];
  tiers: AgentTier[];
  minReputation: number;
  sortBy: 'reputation' | 'earned' | 'completed' | 'rate';
  sortOrder: 'asc' | 'desc';
}

export const AGENT_ROLE_LABELS: Record<AgentRole, string> = {
  'frontend': 'Frontend',
  'backend': 'Backend',
  'smart-contracts': 'Smart Contracts',
  'security': 'Security',
  'devops': 'DevOps',
  'testing': 'Testing',
  'documentation': 'Documentation',
  'integration': 'Integration',
};

export const AGENT_STATUS_LABELS: Record<AgentStatus, string> = {
  'available': 'Available',
  'busy': 'Busy',
  'offline': 'Offline',
};

export const AGENT_TIER_LABELS: Record<AgentTier, string> = {
  'tier-1': 'Tier 1',
  'tier-2': 'Tier 2',
  'tier-3': 'Tier 3',
};

export const AGENT_ROLE_COLORS: Record<AgentRole, string> = {
  'frontend': 'bg-blue-500',
  'backend': 'bg-green-500',
  'smart-contracts': 'bg-purple-500',
  'security': 'bg-red-500',
  'devops': 'bg-orange-500',
  'testing': 'bg-yellow-500',
  'documentation': 'bg-cyan-500',
  'integration': 'bg-pink-500',
};

export const AGENT_STATUS_COLORS: Record<AgentStatus, string> = {
  'available': 'bg-green-500',
  'busy': 'bg-yellow-500',
  'offline': 'bg-gray-500',
};