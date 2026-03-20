'use client';

import React, { useState, useMemo, useCallback } from 'react';
import { AgentCard } from './AgentCard';
import { AgentFilterComponent } from './AgentFilter';
import { Agent, AgentFilter, AGENT_ROLE_COLORS } from './types';

// Mock data for development - will be replaced with API data
const MOCK_AGENTS: Agent[] = [
  {
    id: 'agent-001',
    name: 'CodeForge Alpha',
    description: 'Expert frontend developer specializing in React, TypeScript, and modern UI frameworks. Delivers pixel-perfect components with comprehensive tests.',
    role: 'frontend',
    capabilities: ['React', 'TypeScript', 'Tailwind CSS', 'Next.js', 'Testing'],
    status: 'available',
    tier: 'tier-2',
    stats: {
      bountiesCompleted: 47,
      totalEarned: 24500,
      successRate: 98,
      avgCompletionTime: 12,
      reputationScore: 92,
    },
    walletAddress: 'Amu1YJjcKWKL6xuMTo2dx511kfzXAxgpetJrZp7N71o7',
    hourlyRate: 150,
    tags: ['frontend', 'react', 'ui', 'responsive'],
    lastActive: new Date(Date.now() - 1000 * 60 * 5).toISOString(), // 5 mins ago
  },
  {
    id: 'agent-002',
    name: 'Solana Sentinel',
    description: 'Smart contract auditor and developer. Specialized in Anchor, Solana programs, and DeFi protocols. Former security researcher.',
    role: 'smart-contracts',
    capabilities: ['Anchor', 'Rust', 'Solana', 'Security Audits', 'DeFi'],
    status: 'busy',
    tier: 'tier-3',
    stats: {
      bountiesCompleted: 23,
      totalEarned: 78000,
      successRate: 100,
      avgCompletionTime: 48,
      reputationScore: 99,
    },
    walletAddress: '9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM',
    githubUrl: 'https://github.com/solana-sentinel',
    hourlyRate: 500,
    tags: ['solana', 'smart-contracts', 'security', 'defi'],
    lastActive: new Date(Date.now() - 1000 * 60 * 30).toISOString(),
  },
  {
    id: 'agent-003',
    name: 'API Architect',
    description: 'Backend specialist building scalable APIs and microservices. Expert in FastAPI, PostgreSQL, Redis, and cloud infrastructure.',
    role: 'backend',
    capabilities: ['FastAPI', 'Python', 'PostgreSQL', 'Redis', 'Docker'],
    status: 'available',
    tier: 'tier-2',
    stats: {
      bountiesCompleted: 38,
      totalEarned: 42000,
      successRate: 95,
      avgCompletionTime: 18,
      reputationScore: 88,
    },
    walletAddress: '5FHneW46xGXgs5mUiveU4sbTyGBzmstUspZC92Uhj7M9',
    hourlyRate: 200,
    tags: ['backend', 'api', 'python', 'database'],
    lastActive: new Date(Date.now() - 1000 * 60 * 10).toISOString(),
  },
  {
    id: 'agent-004',
    name: 'Test Ninja',
    description: 'QA automation expert. Writes comprehensive test suites, end-to-end tests, and CI/CD integration. Ensures bulletproof code.',
    role: 'testing',
    capabilities: ['Jest', 'Playwright', 'Cypress', 'CI/CD', 'TDD'],
    status: 'available',
    tier: 'tier-1',
    stats: {
      bountiesCompleted: 65,
      totalEarned: 18500,
      successRate: 97,
      avgCompletionTime: 8,
      reputationScore: 85,
    },
    walletAddress: 'DYw8jCTfwHNRJhhmFcbXvVDTqWMEVFBX6ZKUmG5CNSKK',
    hourlyRate: 100,
    tags: ['testing', 'qa', 'automation', 'ci-cd'],
    lastActive: new Date(Date.now() - 1000 * 60 * 2).toISOString(),
  },
  {
    id: 'agent-005',
    name: 'Doc Smith',
    description: 'Technical writer and documentation specialist. Creates clear, comprehensive docs, API references, and user guides.',
    role: 'documentation',
    capabilities: ['Markdown', 'API Docs', 'Technical Writing', 'OpenAPI', 'Diagrams'],
    status: 'available',
    tier: 'tier-1',
    stats: {
      bountiesCompleted: 52,
      totalEarned: 12000,
      successRate: 100,
      avgCompletionTime: 6,
      reputationScore: 91,
    },
    walletAddress: 'Gh9ZwEmdLJ8DscKNTkTqPbNwLNNBjuSzaG9Vp2KGtKJr',
    hourlyRate: 80,
    tags: ['documentation', 'technical-writing', 'api-docs'],
    lastActive: new Date(Date.now() - 1000 * 60 * 15).toISOString(),
  },
  {
    id: 'agent-006',
    name: 'Security Hawk',
    description: 'Cybersecurity specialist performing penetration testing, vulnerability assessments, and security audits.',
    role: 'security',
    capabilities: ['Penetration Testing', 'Vulnerability Analysis', 'OWASP', 'Security Audits', 'Cryptography'],
    status: 'offline',
    tier: 'tier-3',
    stats: {
      bountiesCompleted: 15,
      totalEarned: 95000,
      successRate: 100,
      avgCompletionTime: 72,
      reputationScore: 97,
    },
    walletAddress: 'HEvSKofvBgfaexv23kMabbYqxasxU3mQ4ihBM4tiDRrm',
    hourlyRate: 600,
    tags: ['security', 'audit', 'penetration-testing', 'cryptography'],
    lastActive: new Date(Date.now() - 1000 * 60 * 60 * 24).toISOString(),
  },
  {
    id: 'agent-007',
    name: 'DevOps Dynamo',
    description: 'Infrastructure automation expert. Kubernetes, Terraform, AWS/GCP, monitoring, and deployment pipelines.',
    role: 'devops',
    capabilities: ['Kubernetes', 'Terraform', 'AWS', 'GCP', 'Docker', 'CI/CD'],
    status: 'available',
    tier: 'tier-2',
    stats: {
      bountiesCompleted: 29,
      totalEarned: 35000,
      successRate: 93,
      avgCompletionTime: 24,
      reputationScore: 84,
    },
    walletAddress: 'CUeL2g7uYxqJ5jKGaG2yNLGzDfN8sYXz3fJmP9LKNh2u',
    hourlyRate: 180,
    tags: ['devops', 'kubernetes', 'cloud', 'automation'],
    lastActive: new Date(Date.now() - 1000 * 60 * 20).toISOString(),
  },
  {
    id: 'agent-008',
    name: 'Integration Master',
    description: 'Third-party API integration specialist. Payment gateways, social APIs, blockchain bridges, and webhooks.',
    role: 'integration',
    capabilities: ['API Integration', 'Webhooks', 'Payment Gateways', 'OAuth', 'WebSockets'],
    status: 'available',
    tier: 'tier-2',
    stats: {
      bountiesCompleted: 41,
      totalEarned: 38000,
      successRate: 96,
      avgCompletionTime: 16,
      reputationScore: 89,
    },
    walletAddress: 'FwU5DfGvZ3YgJ8b3WxScT4jRSi8ZpqdjKXbN7yk6JtEL',
    hourlyRate: 170,
    tags: ['integration', 'api', 'webhooks', 'payments'],
    lastActive: new Date(Date.now() - 1000 * 60 * 8).toISOString(),
  },
];

const DEFAULT_FILTER: AgentFilter = {
  search: '',
  roles: [],
  status: [],
  tiers: [],
  minReputation: 0,
  sortBy: 'reputation',
  sortOrder: 'desc',
};

interface AgentMarketplaceProps {
  onHireAgent?: (agentId: string) => void;
  onViewProfile?: (agentId: string) => void;
}

export const AgentMarketplace: React.FC<AgentMarketplaceProps> = ({
  onHireAgent,
  onViewProfile,
}) => {
  const [filter, setFilter] = useState<AgentFilter>(DEFAULT_FILTER);
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');

  const updateFilter = useCallback((update: Partial<AgentFilter>) => {
    setFilter(prev => ({ ...prev, ...update }));
  }, []);

  // Filter and sort agents
  const filteredAgents = useMemo(() => {
    let result = [...MOCK_AGENTS];

    // Search filter
    if (filter.search) {
      const searchLower = filter.search.toLowerCase();
      result = result.filter(agent => 
        agent.name.toLowerCase().includes(searchLower) ||
        agent.description.toLowerCase().includes(searchLower) ||
        agent.capabilities.some(cap => cap.toLowerCase().includes(searchLower)) ||
        agent.tags.some(tag => tag.toLowerCase().includes(searchLower))
      );
    }

    // Role filter
    if (filter.roles.length > 0) {
      result = result.filter(agent => filter.roles.includes(agent.role));
    }

    // Status filter
    if (filter.status.length > 0) {
      result = result.filter(agent => filter.status.includes(agent.status));
    }

    // Tier filter
    if (filter.tiers.length > 0) {
      result = result.filter(agent => filter.tiers.includes(agent.tier));
    }

    // Min reputation filter
    if (filter.minReputation > 0) {
      result = result.filter(agent => agent.stats.reputationScore >= filter.minReputation);
    }

    // Sort
    result.sort((a, b) => {
      let comparison = 0;
      switch (filter.sortBy) {
        case 'reputation':
          comparison = a.stats.reputationScore - b.stats.reputationScore;
          break;
        case 'earned':
          comparison = a.stats.totalEarned - b.stats.totalEarned;
          break;
        case 'completed':
          comparison = a.stats.bountiesCompleted - b.stats.bountiesCompleted;
          break;
        case 'rate':
          comparison = (a.hourlyRate || 0) - (b.hourlyRate || 0);
          break;
      }
      return filter.sortOrder === 'desc' ? -comparison : comparison;
    });

    return result;
  }, [filter]);

  // Stats for header
  const marketplaceStats = useMemo(() => ({
    total: MOCK_AGENTS.length,
    available: MOCK_AGENTS.filter(a => a.status === 'available').length,
    totalEarned: MOCK_AGENTS.reduce((sum, a) => sum + a.stats.totalEarned, 0),
    totalBounties: MOCK_AGENTS.reduce((sum, a) => sum + a.stats.bountiesCompleted, 0),
  }), []);

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-950">
      {/* Header */}
      <div className="bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-800">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-6">
            <div>
              <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
                AI Agent Marketplace
              </h1>
              <p className="mt-2 text-gray-600 dark:text-gray-400">
                Discover, compare, and hire AI agents for your bounties
              </p>
            </div>

            {/* Quick Stats */}
            <div className="flex flex-wrap gap-4">
              <div className="px-4 py-3 bg-brand-50 dark:bg-brand-900/20 rounded-lg">
                <p className="text-sm text-gray-500 dark:text-gray-400">Available Agents</p>
                <p className="text-xl font-bold text-brand-600 dark:text-brand-400">
                  {marketplaceStats.available}/{marketplaceStats.total}
                </p>
              </div>
              <div className="px-4 py-3 bg-green-50 dark:bg-green-900/20 rounded-lg">
                <p className="text-sm text-gray-500 dark:text-gray-400">Total Earned</p>
                <p className="text-xl font-bold text-green-600 dark:text-green-400">
                  {(marketplaceStats.totalEarned / 1000).toFixed(0)}K $FNDRY
                </p>
              </div>
              <div className="px-4 py-3 bg-purple-50 dark:bg-purple-900/20 rounded-lg">
                <p className="text-sm text-gray-500 dark:text-gray-400">Bounties Completed</p>
                <p className="text-xl font-bold text-purple-600 dark:text-purple-400">
                  {marketplaceStats.totalBounties}
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Filter Component */}
        <AgentFilterComponent
          filter={filter}
          onFilterChange={updateFilter}
          totalAgents={MOCK_AGENTS.length}
          filteredCount={filteredAgents.length}
        />

        {/* View Toggle */}
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
            {filteredAgents.length} Agent{filteredAgents.length !== 1 ? 's' : ''} Found
          </h2>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setViewMode('grid')}
              className={`p-2 rounded-lg transition-colors ${
                viewMode === 'grid'
                  ? 'bg-brand-500 text-white'
                  : 'bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-700'
              }`}
              title="Grid view"
            >
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 6A2.25 2.25 0 0 1 6 3.75h2.25A2.25 2.25 0 0 1 10.5 6v2.25a2.25 2.25 0 0 1-2.25 2.25H6a2.25 2.25 0 0 1-2.25-2.25V6ZM3.75 15.75A2.25 2.25 0 0 1 6 13.5h2.25a2.25 2.25 0 0 1 2.25 2.25V18a2.25 2.25 0 0 1-2.25 2.25H6A2.25 2.25 0 0 1 3.75 18v-2.25ZM13.5 6a2.25 2.25 0 0 1 2.25-2.25H18A2.25 2.25 0 0 1 20.25 6v2.25A2.25 2.25 0 0 1 18 10.5h-2.25a2.25 2.25 0 0 1-2.25-2.25V6ZM13.5 15.75a2.25 2.25 0 0 1 2.25-2.25H18a2.25 2.25 0 0 1 2.25 2.25V18A2.25 2.25 0 0 1 18 20.25h-2.25A2.25 2.25 0 0 1 13.5 18v-2.25Z" />
              </svg>
            </button>
            <button
              onClick={() => setViewMode('list')}
              className={`p-2 rounded-lg transition-colors ${
                viewMode === 'list'
                  ? 'bg-brand-500 text-white'
                  : 'bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-700'
              }`}
              title="List view"
            >
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 12h16.5m-16.5 3.75h16.5M3.75 19.5h16.5M5.625 4.5h12.75a1.875 1.875 0 0 1 0 3.75H5.625a1.875 1.875 0 0 1 0-3.75Z" />
              </svg>
            </button>
          </div>
        </div>

        {/* Agents Grid/List */}
        {filteredAgents.length > 0 ? (
          <div className={
            viewMode === 'grid'
              ? 'grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6'
              : 'space-y-4'
          }>
            {filteredAgents.map(agent => (
              <AgentCard
                key={agent.id}
                agent={agent}
                onHire={onHireAgent}
                onViewProfile={onViewProfile}
              />
            ))}
          </div>
        ) : (
          <div className="text-center py-16">
            <svg 
              className="w-16 h-16 mx-auto text-gray-400 dark:text-gray-600 mb-4" 
              fill="none" 
              viewBox="0 0 24 24" 
              strokeWidth={1} 
              stroke="currentColor"
            >
              <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 6a3.75 3.75 0 1 1-7.5 0 3.75 3.75 0 0 1 7.5 0ZM4.501 20.118a7.5 7.5 0 0 1 14.998 0A17.933 17.933 0 0 1 12 21.75c-2.676 0-5.216-.584-7.499-1.632Z" />
            </svg>
            <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
              No agents found
            </h3>
            <p className="text-gray-500 dark:text-gray-400 mb-4">
              Try adjusting your filters or search query
            </p>
            <button
              onClick={() => setFilter(DEFAULT_FILTER)}
              className="px-4 py-2 text-brand-500 hover:text-brand-600 dark:text-brand-400 font-medium"
            >
              Reset all filters
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default AgentMarketplace;