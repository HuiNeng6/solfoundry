'use client';

import React from 'react';
import {
  AgentFilter as AgentFilterType,
  AgentRole,
  AgentStatus,
  AgentTier,
  AGENT_ROLE_LABELS,
  AGENT_STATUS_LABELS,
  AGENT_TIER_LABELS,
} from './types';

interface AgentFilterProps {
  filter: AgentFilterType;
  onFilterChange: (filter: Partial<AgentFilterType>) => void;
  totalAgents: number;
  filteredCount: number;
}

export const AgentFilterComponent: React.FC<AgentFilterProps> = ({
  filter,
  onFilterChange,
  totalAgents,
  filteredCount,
}) => {
  const roles: AgentRole[] = ['frontend', 'backend', 'smart-contracts', 'security', 'devops', 'testing', 'documentation', 'integration'];
  const statuses: AgentStatus[] = ['available', 'busy', 'offline'];
  const tiers: AgentTier[] = ['tier-1', 'tier-2', 'tier-3'];

  const toggleArrayFilter = <T,>(array: T[], value: T): T[] => {
    return array.includes(value) 
      ? array.filter(v => v !== value)
      : [...array, value];
  };

  return (
    <div className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 p-5 mb-6">
      {/* Search Bar */}
      <div className="relative mb-5">
        <svg 
          className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" 
          fill="none" 
          viewBox="0 0 24 24" 
          strokeWidth={1.5} 
          stroke="currentColor"
        >
          <path strokeLinecap="round" strokeLinejoin="round" d="m21 21-5.197-5.197m0 0A7.5 7.5 0 1 0 5.196 5.196a7.5 7.5 0 0 0 10.607 10.607Z" />
        </svg>
        <input
          type="text"
          placeholder="Search agents by name, capability, or tag..."
          value={filter.search}
          onChange={(e) => onFilterChange({ search: e.target.value })}
          className="w-full pl-10 pr-4 py-3 bg-gray-50 dark:bg-gray-800 border border-gray-200 
                    dark:border-gray-700 rounded-lg text-gray-900 dark:text-gray-100 
                    placeholder-gray-400 dark:placeholder-gray-500
                    focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-transparent"
        />
        {filter.search && (
          <button
            onClick={() => onFilterChange({ search: '' })}
            className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
          >
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" d="M6 18 18 6M6 6l12 12" />
            </svg>
          </button>
        )}
      </div>

      {/* Filter Rows */}
      <div className="space-y-4">
        {/* Role Filter */}
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Role
          </label>
          <div className="flex flex-wrap gap-2">
            {roles.map((role) => (
              <button
                key={role}
                onClick={() => onFilterChange({ roles: toggleArrayFilter(filter.roles, role) })}
                className={`px-3 py-1.5 text-sm rounded-full transition-colors
                  ${filter.roles.includes(role)
                    ? 'bg-brand-500 text-white'
                    : 'bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-700'
                  }`}
              >
                {AGENT_ROLE_LABELS[role]}
              </button>
            ))}
          </div>
        </div>

        {/* Status Filter */}
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Status
          </label>
          <div className="flex flex-wrap gap-2">
            {statuses.map((status) => (
              <button
                key={status}
                onClick={() => onFilterChange({ status: toggleArrayFilter(filter.status, status) })}
                className={`px-3 py-1.5 text-sm rounded-full transition-colors flex items-center gap-1.5
                  ${filter.status.includes(status)
                    ? 'bg-brand-500 text-white'
                    : 'bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-700'
                  }`}
              >
                <span className={`w-2 h-2 rounded-full ${
                  status === 'available' ? 'bg-green-500' :
                  status === 'busy' ? 'bg-yellow-500' : 'bg-gray-400'
                }`} />
                {AGENT_STATUS_LABELS[status]}
              </button>
            ))}
          </div>
        </div>

        {/* Tier Filter */}
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Tier
          </label>
          <div className="flex flex-wrap gap-2">
            {tiers.map((tier) => (
              <button
                key={tier}
                onClick={() => onFilterChange({ tiers: toggleArrayFilter(filter.tiers, tier) })}
                className={`px-3 py-1.5 text-sm rounded-full transition-colors
                  ${filter.tiers.includes(tier)
                    ? 'bg-brand-500 text-white'
                    : 'bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-700'
                  }`}
              >
                {AGENT_TIER_LABELS[tier]}
              </button>
            ))}
          </div>
        </div>

        {/* Min Reputation */}
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Minimum Reputation: {filter.minReputation}
          </label>
          <input
            type="range"
            min="0"
            max="100"
            value={filter.minReputation}
            onChange={(e) => onFilterChange({ minReputation: parseInt(e.target.value) })}
            className="w-full h-2 bg-gray-200 dark:bg-gray-700 rounded-lg appearance-none cursor-pointer
                      accent-brand-500"
          />
        </div>
      </div>

      {/* Sort and Results */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 mt-5 pt-5 border-t border-gray-200 dark:border-gray-800">
        <span className="text-sm text-gray-500 dark:text-gray-400">
          Showing <span className="font-medium text-gray-700 dark:text-gray-300">{filteredCount}</span> of {totalAgents} agents
        </span>
        
        <div className="flex items-center gap-3">
          <select
            value={filter.sortBy}
            onChange={(e) => onFilterChange({ sortBy: e.target.value as AgentFilterType['sortBy'] })}
            className="px-3 py-1.5 text-sm bg-gray-50 dark:bg-gray-800 border border-gray-200 
                      dark:border-gray-700 rounded-lg text-gray-700 dark:text-gray-300
                      focus:outline-none focus:ring-2 focus:ring-brand-500"
          >
            <option value="reputation">Sort by Reputation</option>
            <option value="earned">Sort by Earned</option>
            <option value="completed">Sort by Completed</option>
            <option value="rate">Sort by Rate</option>
          </select>
          
          <button
            onClick={() => onFilterChange({ 
              sortOrder: filter.sortOrder === 'asc' ? 'desc' : 'asc' 
            })}
            className="p-1.5 rounded-lg bg-gray-50 dark:bg-gray-800 border border-gray-200 
                      dark:border-gray-700 text-gray-700 dark:text-gray-300
                      hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
            title={filter.sortOrder === 'asc' ? 'Ascending' : 'Descending'}
          >
            <svg 
              className={`w-5 h-5 transition-transform ${filter.sortOrder === 'asc' ? 'rotate-180' : ''}`} 
              fill="none" 
              viewBox="0 0 24 24" 
              strokeWidth={1.5} 
              stroke="currentColor"
            >
              <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 13.5 12 21m0 0-7.5-7.5M12 21V3" />
            </svg>
          </button>
          
          <button
            onClick={() => onFilterChange({
              search: '',
              roles: [],
              status: [],
              tiers: [],
              minReputation: 0,
              sortBy: 'reputation',
              sortOrder: 'desc',
            })}
            className="px-3 py-1.5 text-sm text-brand-500 hover:text-brand-600 
                      dark:text-brand-400 dark:hover:text-brand-300 font-medium"
          >
            Reset
          </button>
        </div>
      </div>
    </div>
  );
};

export default AgentFilterComponent;