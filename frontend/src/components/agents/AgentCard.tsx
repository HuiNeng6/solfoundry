'use client';

import React from 'react';
import {
  Agent,
  AGENT_ROLE_LABELS,
  AGENT_STATUS_LABELS,
  AGENT_TIER_LABELS,
  AGENT_ROLE_COLORS,
  AGENT_STATUS_COLORS,
} from './types';

interface AgentCardProps {
  agent: Agent;
  onHire?: (agentId: string) => void;
  onViewProfile?: (agentId: string) => void;
}

export const AgentCard: React.FC<AgentCardProps> = ({
  agent,
  onHire,
  onViewProfile,
}) => {
  const truncatedWallet = `${agent.walletAddress.slice(0, 6)}...${agent.walletAddress.slice(-4)}`;
  
  const formatNumber = (num: number): string => {
    if (num >= 1000000) {
      return `${(num / 1000000).toFixed(1)}M`;
    }
    if (num >= 1000) {
      return `${(num / 1000).toFixed(1)}K`;
    }
    return num.toString();
  };

  const timeSinceActive = (dateStr: string): string => {
    const date = new Date(dateStr);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMins / 60);
    const diffDays = Math.floor(diffHours / 24);
    
    if (diffDays > 0) return `${diffDays}d ago`;
    if (diffHours > 0) return `${diffHours}h ago`;
    if (diffMins > 0) return `${diffMins}m ago`;
    return 'Just now';
  };

  return (
    <div className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 
                    overflow-hidden hover:shadow-lg hover:border-brand-400 dark:hover:border-brand-500 
                    transition-all duration-300 group">
      {/* Status indicator bar */}
      <div className={`h-1 ${AGENT_STATUS_COLORS[agent.status]}`} />
      
      <div className="p-5">
        {/* Header: Avatar + Name + Status */}
        <div className="flex items-start gap-4 mb-4">
          <div className="relative">
            <div className="w-14 h-14 rounded-full bg-gradient-to-br from-brand-400 to-purple-500 
                            flex items-center justify-center text-white text-xl font-bold shrink-0">
              {agent.avatarUrl ? (
                <img 
                  src={agent.avatarUrl} 
                  alt={agent.name}
                  className="w-full h-full rounded-full object-cover"
                />
              ) : (
                agent.name.charAt(0).toUpperCase()
              )}
            </div>
            {/* Status dot */}
            <div className={`absolute -bottom-0.5 -right-0.5 w-4 h-4 rounded-full border-2 
                            border-white dark:border-gray-900 ${AGENT_STATUS_COLORS[agent.status]}`}
                 title={AGENT_STATUS_LABELS[agent.status]}
            />
          </div>
          
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white truncate">
                {agent.name}
              </h3>
              <span className={`px-2 py-0.5 text-xs font-medium rounded-full text-white 
                               ${AGENT_ROLE_COLORS[agent.role]}`}>
                {AGENT_ROLE_LABELS[agent.role]}
              </span>
            </div>
            <p className="text-sm text-gray-500 dark:text-gray-400 font-mono truncate">
              {truncatedWallet}
            </p>
          </div>
        </div>

        {/* Description */}
        <p className="text-sm text-gray-600 dark:text-gray-300 mb-4 line-clamp-2">
          {agent.description}
        </p>

        {/* Capabilities */}
        <div className="flex flex-wrap gap-1.5 mb-4">
          {agent.capabilities.slice(0, 3).map((cap, idx) => (
            <span key={idx} 
                  className="px-2 py-0.5 text-xs bg-gray-100 dark:bg-gray-800 
                           text-gray-600 dark:text-gray-300 rounded-full">
              {cap}
            </span>
          ))}
          {agent.capabilities.length > 3 && (
            <span className="px-2 py-0.5 text-xs bg-gray-100 dark:bg-gray-800 
                           text-gray-500 dark:text-gray-400 rounded-full">
              +{agent.capabilities.length - 3}
            </span>
          )}
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-3 gap-3 mb-4">
          <div className="text-center p-2 bg-gray-50 dark:bg-gray-800/50 rounded-lg">
            <p className="text-lg font-bold text-brand-500">{formatNumber(agent.stats.totalEarned)}</p>
            <p className="text-xs text-gray-500 dark:text-gray-400">Earned</p>
          </div>
          <div className="text-center p-2 bg-gray-50 dark:bg-gray-800/50 rounded-lg">
            <p className="text-lg font-bold text-green-500">{agent.stats.bountiesCompleted}</p>
            <p className="text-xs text-gray-500 dark:text-gray-400">Bounties</p>
          </div>
          <div className="text-center p-2 bg-gray-50 dark:bg-gray-800/50 rounded-lg">
            <p className="text-lg font-bold text-yellow-500">{agent.stats.reputationScore}</p>
            <p className="text-xs text-gray-500 dark:text-gray-400">Rep</p>
          </div>
        </div>

        {/* Tier + Rate + Last Active */}
        <div className="flex items-center justify-between text-xs text-gray-500 dark:text-gray-400 mb-4">
          <span className={`px-2 py-1 rounded font-medium
                          ${agent.tier === 'tier-1' ? 'bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400' :
                            agent.tier === 'tier-2' ? 'bg-purple-100 dark:bg-purple-900/30 text-purple-600 dark:text-purple-400' :
                            'bg-amber-100 dark:bg-amber-900/30 text-amber-600 dark:text-amber-400'}`}>
            {AGENT_TIER_LABELS[agent.tier]}
          </span>
          {agent.hourlyRate && (
            <span className="font-medium text-gray-700 dark:text-gray-300">
              {formatNumber(agent.hourlyRate)} $FNDRY/h
            </span>
          )}
          <span>Active {timeSinceActive(agent.lastActive)}</span>
        </div>

        {/* Success Rate Bar */}
        <div className="mb-4">
          <div className="flex justify-between text-xs mb-1">
            <span className="text-gray-500 dark:text-gray-400">Success Rate</span>
            <span className="font-medium text-gray-700 dark:text-gray-300">{agent.stats.successRate}%</span>
          </div>
          <div className="h-2 bg-gray-100 dark:bg-gray-800 rounded-full overflow-hidden">
            <div 
              className="h-full bg-gradient-to-r from-green-400 to-green-500 rounded-full transition-all duration-500"
              style={{ width: `${agent.stats.successRate}%` }}
            />
          </div>
        </div>

        {/* Actions */}
        <div className="flex gap-2">
          <button
            onClick={() => onViewProfile?.(agent.id)}
            className="flex-1 px-4 py-2.5 text-sm font-medium text-gray-700 dark:text-gray-300
                      bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700
                      rounded-lg transition-colors focus:outline-none focus:ring-2 focus:ring-brand-500"
          >
            View Profile
          </button>
          <button
            onClick={() => onHire?.(agent.id)}
            disabled={agent.status !== 'available'}
            className="flex-1 px-4 py-2.5 text-sm font-medium text-white
                      bg-gradient-to-r from-brand-500 to-purple-500 
                      hover:from-brand-600 hover:to-purple-600
                      disabled:opacity-50 disabled:cursor-not-allowed
                      rounded-lg transition-all focus:outline-none focus:ring-2 focus:ring-brand-500
                      shadow-sm hover:shadow-md"
          >
            {agent.status === 'available' ? 'Hire Agent' : 'Unavailable'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default AgentCard;