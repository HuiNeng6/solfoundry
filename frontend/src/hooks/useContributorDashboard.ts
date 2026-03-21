/**
 * useContributorDashboard - React Query hook for contributor dashboard data.
 * Fetches user-specific stats, active bounties, and activities from API.
 * @module hooks/useContributorDashboard
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiFetch } from '../api/client';

// ============================================================================
// Types
// ============================================================================

interface ActiveBounty {
  id: string;
  title: string;
  reward: number;
  deadline: string;
  status: 'claimed' | 'in_progress' | 'submitted' | 'reviewing';
  progress: number;
}

interface Activity {
  id: string;
  type: 'bounty_claimed' | 'pr_submitted' | 'review_received' | 'payout' | 'bounty_completed';
  title: string;
  description: string;
  timestamp: string;
  amount?: number;
}

interface Notification {
  id: string;
  type: 'info' | 'success' | 'warning' | 'error';
  title: string;
  message: string;
  timestamp: string;
  read: boolean;
}

interface DashboardStats {
  totalEarned: number;
  activeBounties: number;
  pendingPayouts: number;
  reputationRank: number;
  totalContributors: number;
}

interface EarningsData {
  date: string;
  amount: number;
}

interface LinkedAccount {
  type: string;
  username: string;
  connected: boolean;
}

interface DashboardData {
  stats: DashboardStats;
  bounties: ActiveBounty[];
  activities: Activity[];
  notifications: Notification[];
  earnings: EarningsData[];
  linkedAccounts: LinkedAccount[];
}

// ============================================================================
// API Functions
// ============================================================================

async function fetchDashboardData(userId: string): Promise<DashboardData> {
  const response = await apiFetch<DashboardData>(`/api/contributors/${userId}/dashboard`);
  return response;
}

async function markNotificationRead(notificationId: string): Promise<void> {
  await apiFetch(`/api/notifications/${notificationId}/read`, { method: 'POST' });
}

async function markAllNotificationsRead(): Promise<void> {
  await apiFetch('/api/notifications/read-all', { method: 'POST' });
}

// ============================================================================
// Hook
// ============================================================================

interface UseContributorDashboardOptions {
  userId?: string;
  walletAddress?: string;
  enabled?: boolean;
}

export function useContributorDashboard(options: UseContributorDashboardOptions) {
  const { userId, walletAddress, enabled = true } = options;
  const queryClient = useQueryClient();

  // Main dashboard data query
  const {
    data,
    isLoading,
    error,
    refetch,
  } = useQuery({
    queryKey: ['contributor-dashboard', userId, walletAddress],
    queryFn: () => fetchDashboardData(userId!),
    enabled: enabled && !!userId,
    staleTime: 30 * 1000,
    retry: 2,
  });

  // Mark notification as read mutation
  const markReadMutation = useMutation({
    mutationFn: markNotificationRead,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['contributor-dashboard'] });
    },
  });

  // Mark all notifications read mutation
  const markAllReadMutation = useMutation({
    mutationFn: markAllNotificationsRead,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['contributor-dashboard'] });
    },
  });

  // Extract data with defaults
  const stats = data?.stats ?? null;
  const bounties = data?.bounties ?? [];
  const activities = data?.activities ?? [];
  const notifications = data?.notifications ?? [];
  const earnings = data?.earnings ?? [];
  const linkedAccounts = data?.linkedAccounts ?? [];

  const unreadCount = notifications.filter(n => !n.read).length;

  return {
    // Data
    stats,
    bounties,
    activities,
    notifications,
    earnings,
    linkedAccounts,
    
    // Derived
    unreadCount,
    hasData: !!data,
    isEmpty: !isLoading && !data,
    
    // States
    loading: isLoading,
    error: error as Error | null,
    
    // Actions
    refetch,
    markNotificationRead: markReadMutation.mutate,
    markAllNotificationsRead: markAllReadMutation.mutate,
    isMarkingRead: markReadMutation.isPending,
    isMarkingAllRead: markAllReadMutation.isPending,
  };
}

export default useContributorDashboard;