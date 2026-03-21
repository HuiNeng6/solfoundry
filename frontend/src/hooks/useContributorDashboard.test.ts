/**
 * Tests for useContributorDashboard hook
 */
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { describe, it, expect, vi } from 'vitest';
import { useContributorDashboard } from './useContributorDashboard';
import * as clientApi from '../api/client';

// Mock the API
vi.mock('../api/client', () => ({
  apiFetch: vi.fn(),
}));

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
};

describe('useContributorDashboard', () => {
  it('returns loading state initially', () => {
    vi.mocked(clientApi.apiFetch).mockImplementation(
      () => new Promise(() => {})
    );

    const { result } = renderHook(() => useContributorDashboard({ userId: 'user-123' }), {
      wrapper: createWrapper(),
    });

    expect(result.current.loading).toBe(true);
    expect(result.current.stats).toBeNull();
  });

  it('fetches dashboard data for user', async () => {
    const mockDashboard = {
      stats: {
        totalEarned: 1000000,
        activeBounties: 3,
        pendingPayouts: 500000,
        reputationRank: 42,
        totalContributors: 256,
      },
      bounties: [
        { id: '1', title: 'Test Bounty', reward: 100000, deadline: '2026-04-01', status: 'in_progress', progress: 50 },
      ],
      activities: [],
      notifications: [],
      earnings: [],
      linkedAccounts: [],
    };

    vi.mocked(clientApi.apiFetch).mockResolvedValue(mockDashboard);

    const { result } = renderHook(() => useContributorDashboard({ userId: 'user-123' }), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.stats).toEqual(mockDashboard.stats);
    expect(result.current.bounties).toHaveLength(1);
    expect(result.current.hasData).toBe(true);
  });

  it('returns empty state when no data', async () => {
    vi.mocked(clientApi.apiFetch).mockResolvedValue(null);

    const { result } = renderHook(() => useContributorDashboard({ userId: 'user-123' }), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.isEmpty).toBe(true);
    expect(result.current.hasData).toBe(false);
  });

  it('counts unread notifications', async () => {
    const mockDashboard = {
      stats: { totalEarned: 0, activeBounties: 0, pendingPayouts: 0, reputationRank: 0, totalContributors: 0 },
      bounties: [],
      activities: [],
      notifications: [
        { id: '1', type: 'info', title: 'Test', message: 'Test', timestamp: '2026-03-22T00:00:00Z', read: false },
        { id: '2', type: 'info', title: 'Test', message: 'Test', timestamp: '2026-03-22T00:00:00Z', read: true },
      ],
      earnings: [],
      linkedAccounts: [],
    };

    vi.mocked(clientApi.apiFetch).mockResolvedValue(mockDashboard);

    const { result } = renderHook(() => useContributorDashboard({ userId: 'user-123' }), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.unreadCount).toBe(1);
  });

  it('does not fetch when userId is undefined', () => {
    const { result } = renderHook(() => useContributorDashboard({ userId: undefined }), {
      wrapper: createWrapper(),
    });

    expect(clientApi.apiFetch).not.toHaveBeenCalled();
    expect(result.current.loading).toBe(false);
  });

  it('handles API errors', async () => {
    vi.mocked(clientApi.apiFetch).mockRejectedValue(new Error('API Error'));

    const { result } = renderHook(() => useContributorDashboard({ userId: 'user-123' }), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.error).toBeInstanceOf(Error);
  });
});