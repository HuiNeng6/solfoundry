'use client';

import React, { useState, useEffect } from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  BarChart,
  Bar,
} from 'recharts';
import { dashboardApi } from '../../services/api';
import type { DashboardResponse, BountyHistoryItem } from '../../types/dashboard';
import { formatDistanceToNow, format } from 'date-fns';
import clsx from 'clsx';

interface ContributorDashboardProps {
  contributorId: string;
  walletAddress?: string;
}

export const ContributorDashboard: React.FC<ContributorDashboardProps> = ({
  contributorId,
  walletAddress = 'Amu1YJjcKWKL6xuMTo2dx511kfzXAxgpetJrZp7N71o7',
}) => {
  const [dashboard, setDashboard] = useState<DashboardResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'overview' | 'earnings' | 'reputation' | 'history'>('overview');

  useEffect(() => {
    const fetchDashboard = async () => {
      try {
        setLoading(true);
        const data = await dashboardApi.getDashboard(contributorId);
        setDashboard(data);
        setError(null);
      } catch (err) {
        setError('Failed to load dashboard data. Please try again later.');
        console.error('Dashboard fetch error:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchDashboard();
  }, [contributorId]);

  const formatNumber = (num: number): string => {
    if (num >= 1000000) {
      return `${(num / 1000000).toFixed(1)}M`;
    }
    if (num >= 1000) {
      return `${(num / 1000).toFixed(1)}K`;
    }
    return num.toFixed(2);
  };

  const truncateAddress = (address: string): string => {
    if (!address) return 'Not connected';
    return `${address.slice(0, 6)}...${address.slice(-4)}`;
  };

  const getStatusColor = (status: string): string => {
    switch (status) {
      case 'completed':
        return 'bg-green-500/20 text-green-400 border-green-500/30';
      case 'claimed':
        return 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30';
      case 'open':
        return 'bg-blue-500/20 text-blue-400 border-blue-500/30';
      default:
        return 'bg-gray-500/20 text-gray-400 border-gray-500/30';
    }
  };

  const getTierBadge = (tier: number): JSX.Element => {
    const colors: Record<number, string> = {
      1: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30',
      2: 'bg-amber-500/20 text-amber-400 border-amber-500/30',
      3: 'bg-rose-500/20 text-rose-400 border-rose-500/30',
    };
    return (
      <span className={`px-2 py-0.5 text-xs rounded-full border ${colors[tier] || colors[1]}`}>
        Tier {tier}
      </span>
    );
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-950 flex items-center justify-center">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-purple-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-400">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-950 flex items-center justify-center p-4">
        <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-6 text-center max-w-md">
          <svg className="w-12 h-12 text-red-400 mx-auto mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
          <p className="text-red-400">{error}</p>
          <button
            onClick={() => window.location.reload()}
            className="mt-4 px-4 py-2 bg-red-500/20 hover:bg-red-500/30 text-red-400 rounded-lg transition-colors"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  if (!dashboard) return null;

  const { summary, earnings_chart, reputation_history, bounty_history } = dashboard;

  return (
    <div className="min-h-screen bg-gray-950 text-white p-4 md:p-6 lg:p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="bg-gray-900 rounded-2xl p-6 mb-6 border border-gray-800">
          <div className="flex flex-col sm:flex-row items-start sm:items-center gap-4">
            <div className="w-20 h-20 rounded-full bg-gradient-to-br from-purple-500 to-purple-600 flex items-center justify-center text-3xl font-bold shrink-0">
              {summary.avatar_url ? (
                <img src={summary.avatar_url} alt={summary.display_name} className="w-full h-full rounded-full object-cover" />
              ) : (
                summary.display_name.charAt(0).toUpperCase()
              )}
            </div>
            <div className="flex-1 min-w-0">
              <h1 className="text-2xl md:text-3xl font-bold truncate">{summary.display_name}</h1>
              <p className="text-gray-400">@{summary.username}</p>
              <p className="text-sm text-gray-500 font-mono mt-1">
                {truncateAddress(walletAddress)}
              </p>
            </div>
            <div className="flex flex-wrap gap-3">
              <div className="bg-gray-800/50 rounded-lg px-4 py-2 border border-gray-700">
                <p className="text-xs text-gray-400">Total Earned</p>
                <p className="text-lg font-bold text-green-400">
                  {formatNumber(summary.earnings.total_earned)} FNDRY
                </p>
              </div>
              <div className="bg-gray-800/50 rounded-lg px-4 py-2 border border-gray-700">
                <p className="text-xs text-gray-400">Reputation</p>
                <p className="text-lg font-bold text-yellow-400">
                  {summary.reputation.current_score}
                </p>
              </div>
              <div className="bg-gray-800/50 rounded-lg px-4 py-2 border border-gray-700">
                <p className="text-xs text-gray-400">Active</p>
                <p className="text-lg font-bold text-purple-400">
                  {summary.active_bounties}
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Tabs */}
        <div className="flex gap-2 mb-6 overflow-x-auto pb-2">
          {(['overview', 'earnings', 'reputation', 'history'] as const).map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={clsx(
                'px-4 py-2 rounded-lg font-medium transition-all whitespace-nowrap',
                activeTab === tab
                  ? 'bg-purple-500 text-white'
                  : 'bg-gray-800 text-gray-400 hover:bg-gray-700 hover:text-gray-200'
              )}
            >
              {tab.charAt(0).toUpperCase() + tab.slice(1)}
            </button>
          ))}
        </div>

        {/* Overview Tab */}
        {activeTab === 'overview' && (
          <>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
              <StatCard label="Total Earned" value={`${formatNumber(summary.earnings.total_earned)} FNDRY`} icon="💰" color="green" />
              <StatCard label="Bounties Completed" value={summary.earnings.total_bounties.toString()} icon="🏆" color="purple" />
              <StatCard label="Reputation Score" value={summary.reputation.current_score.toString()} icon="⭐" color="yellow" />
              <StatCard label="Active Bounties" value={summary.active_bounties.toString()} icon="🔄" color="blue" />
            </div>
            <div className="grid md:grid-cols-2 gap-6">
              <div className="bg-gray-900 rounded-xl p-6 border border-gray-800">
                <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
                  <span className="text-green-400">✓</span>
                  Recent Completions
                </h2>
                <div className="space-y-3">
                  {summary.completed_bounties.length > 0 ? (
                    summary.completed_bounties.map((bounty) => <BountyListItem key={bounty.id} bounty={bounty} />)
                  ) : (
                    <p className="text-gray-500 text-sm">No completed bounties yet</p>
                  )}
                </div>
              </div>
              <div className="bg-gray-900 rounded-xl p-6 border border-gray-800">
                <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
                  <span className="text-yellow-400">⏳</span>
                  Active Bounties
                </h2>
                <div className="space-y-3">
                  {summary.claimed_bounties.length > 0 ? (
                    summary.claimed_bounties.map((bounty) => <BountyListItem key={bounty.id} bounty={bounty} />)
                  ) : (
                    <p className="text-gray-500 text-sm">No active bounties</p>
                  )}
                </div>
              </div>
            </div>
          </>
        )}

        {/* Earnings Tab */}
        {activeTab === 'earnings' && (
          <div className="space-y-6">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <StatCard label="This Month" value={`${formatNumber(summary.earnings.this_month_earned)} FNDRY`} icon="📈" color="green" />
              <StatCard label="Last Month" value={`${formatNumber(summary.earnings.last_month_earned)} FNDRY`} icon="📊" color="blue" />
              <StatCard label="Avg Reward" value={`${formatNumber(summary.earnings.average_reward)} FNDRY`} icon="💵" color="purple" />
              <StatCard label="Total Bounties" value={summary.earnings.total_bounties.toString()} icon="🎯" color="yellow" />
            </div>
            <div className="bg-gray-900 rounded-xl p-6 border border-gray-800">
              <h2 className="text-lg font-semibold mb-4">Earnings Over Time</h2>
              <div className="h-64 md:h-80">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={earnings_chart}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                    <XAxis dataKey="month" stroke="#9CA3AF" />
                    <YAxis stroke="#9CA3AF" />
                    <Tooltip
                      contentStyle={{ backgroundColor: '#1F2937', border: '1px solid #374151', borderRadius: '0.5rem' }}
                      formatter={(value: number) => [`${formatNumber(value)} FNDRY`, 'Earned']}
                    />
                    <Bar dataKey="earned" fill="#a855f7" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
            {Object.keys(summary.earnings.by_token).length > 0 && (
              <div className="bg-gray-900 rounded-xl p-6 border border-gray-800">
                <h2 className="text-lg font-semibold mb-4">Earnings by Token</h2>
                <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                  {Object.entries(summary.earnings.by_token).map(([token, amount]) => (
                    <div key={token} className="bg-gray-800/50 rounded-lg p-4 border border-gray-700">
                      <p className="text-sm text-gray-400">{token}</p>
                      <p className="text-xl font-bold text-green-400">{formatNumber(amount)}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Reputation Tab */}
        {activeTab === 'reputation' && (
          <div className="space-y-6">
            <div className="bg-gray-900 rounded-xl p-6 border border-gray-800 text-center">
              <h2 className="text-lg font-semibold mb-2">Current Reputation</h2>
              <div className="text-6xl font-bold bg-gradient-to-r from-yellow-400 to-orange-500 bg-clip-text text-transparent">
                {summary.reputation.current_score}
              </div>
              <p className="text-gray-400 mt-2">{summary.reputation.total_changes} reputation changes recorded</p>
            </div>
            <div className="bg-gray-900 rounded-xl p-6 border border-gray-800">
              <h2 className="text-lg font-semibold mb-4">Reputation Growth</h2>
              <div className="h-64 md:h-80">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={reputation_history}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                    <XAxis dataKey="month" stroke="#9CA3AF" />
                    <YAxis stroke="#9CA3AF" />
                    <Tooltip
                      contentStyle={{ backgroundColor: '#1F2937', border: '1px solid #374151', borderRadius: '0.5rem' }}
                      formatter={(value: number) => [value, 'Score']}
                    />
                    <Line type="monotone" dataKey="score" stroke="#eab308" strokeWidth={3} dot={{ fill: '#eab308', strokeWidth: 2 }} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>
            <div className="bg-gray-900 rounded-xl p-6 border border-gray-800">
              <h2 className="text-lg font-semibold mb-4">Recent Changes</h2>
              <div className="space-y-3">
                {summary.reputation.recent_changes.length > 0 ? (
                  summary.reputation.recent_changes.map((change, idx) => (
                    <div key={idx} className="flex items-center justify-between bg-gray-800/50 rounded-lg p-4 border border-gray-700">
                      <div className="flex-1 min-w-0">
                        <p className="font-medium truncate">{change.reason}</p>
                        <p className="text-sm text-gray-400">{format(new Date(change.date), 'MMM d, yyyy')}</p>
                      </div>
                      <div className="text-right ml-4">
                        <p className={`font-bold ${change.change > 0 ? 'text-green-400' : 'text-red-400'}`}>
                          {change.change > 0 ? '+' : ''}{change.change}
                        </p>
                        <p className="text-sm text-gray-400">Total: {change.new_total}</p>
                      </div>
                    </div>
                  ))
                ) : (
                  <p className="text-gray-500 text-sm">No recent reputation changes</p>
                )}
              </div>
            </div>
          </div>
        )}

        {/* History Tab */}
        {activeTab === 'history' && (
          <div className="bg-gray-900 rounded-xl p-6 border border-gray-800">
            <h2 className="text-lg font-semibold mb-4">Bounty Participation History</h2>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="text-left text-gray-400 text-sm border-b border-gray-800">
                    <th className="pb-3 font-medium">Bounty</th>
                    <th className="pb-3 font-medium">Status</th>
                    <th className="pb-3 font-medium">Tier</th>
                    <th className="pb-3 font-medium">Reward</th>
                    <th className="pb-3 font-medium">Date</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-800">
                  {bounty_history.length > 0 ? (
                    bounty_history.map((bounty) => (
                      <tr key={bounty.id} className="hover:bg-gray-800/50">
                        <td className="py-4"><div className="font-medium truncate max-w-xs">{bounty.title}</div></td>
                        <td className="py-4"><span className={`px-2 py-1 text-xs rounded-full border ${getStatusColor(bounty.status)}`}>{bounty.status}</span></td>
                        <td className="py-4">{getTierBadge(bounty.tier)}</td>
                        <td className="py-4"><span className="text-green-400 font-medium">{formatNumber(bounty.reward_amount)} {bounty.reward_token}</span></td>
                        <td className="py-4 text-sm text-gray-400">{formatDistanceToNow(new Date(bounty.created_at), { addSuffix: true })}</td>
                      </tr>
                    ))
                  ) : (
                    <tr><td colSpan={5} className="py-8 text-center text-gray-500">No bounty history yet</td></tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

// Helper components
interface StatCardProps {
  label: string;
  value: string;
  icon: string;
  color: 'green' | 'purple' | 'yellow' | 'blue';
}

const StatCard: React.FC<StatCardProps> = ({ label, value, icon, color }) => {
  const colorClasses: Record<string, string> = {
    green: 'from-green-500/20 to-green-500/5 border-green-500/20 text-green-400',
    purple: 'from-purple-500/20 to-purple-500/5 border-purple-500/20 text-purple-400',
    yellow: 'from-yellow-500/20 to-yellow-500/5 border-yellow-500/20 text-yellow-400',
    blue: 'from-blue-500/20 to-blue-500/5 border-blue-500/20 text-blue-400',
  };

  return (
    <div className={`bg-gradient-to-br ${colorClasses[color]} rounded-xl p-4 border`}>
      <div className="flex items-center gap-2 mb-2">
        <span>{icon}</span>
        <span className="text-sm text-gray-400">{label}</span>
      </div>
      <p className={`text-xl font-bold`}>{value}</p>
    </div>
  );
};

interface BountyListItemProps {
  bounty: BountyHistoryItem;
}

const BountyListItem: React.FC<BountyListItemProps> = ({ bounty }) => {
  return (
    <div className="flex items-center justify-between bg-gray-800/50 rounded-lg p-3 border border-gray-700">
      <div className="flex-1 min-w-0 mr-3">
        <p className="font-medium truncate">{bounty.title}</p>
        <div className="flex items-center gap-2 mt-1">
          <span className={`px-2 py-0.5 text-xs rounded-full border ${bounty.status === 'completed' ? 'bg-green-500/20 text-green-400 border-green-500/30' : 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30'}`}>
            {bounty.status}
          </span>
          <span className="text-xs text-gray-400">Tier {bounty.tier}</span>
        </div>
      </div>
      <div className="text-right shrink-0">
        <p className="text-green-400 font-medium">{bounty.reward_amount} {bounty.reward_token}</p>
        {bounty.completed_at && <p className="text-xs text-gray-400">{formatDistanceToNow(new Date(bounty.completed_at), { addSuffix: true })}</p>}
      </div>
    </div>
  );
};

export default ContributorDashboard;