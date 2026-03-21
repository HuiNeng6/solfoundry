/**
 * Tests for useContributor hook
 */
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { describe, it, expect, vi } from 'vitest';
import { useContributor } from './useContributor';
import * as contributorsApi from '../api/contributors';

// Mock the API
vi.mock('../api/contributors', () => ({
  fetchContributorById: vi.fn(),
  fetchContributorByUsername: vi.fn(),
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

describe('useContributor', () => {
  it('returns loading state initially', () => {
    vi.mocked(contributorsApi.fetchContributorById).mockImplementation(
      () => new Promise(() => {}) // Never resolves
    );

    const { result } = renderHook(() => useContributor({ id: 'test-id' }), {
      wrapper: createWrapper(),
    });

    expect(result.current.loading).toBe(true);
    expect(result.current.contributor).toBeNull();
  });

  it('fetches contributor by ID', async () => {
    const mockContributor = {
      id: 'test-id',
      username: 'testuser',
      avatarUrl: 'https://example.com/avatar.png',
      points: 100,
      bountiesCompleted: 5,
      earningsFndry: 1000,
      earningsSol: 0,
      streak: 2,
      topSkills: ['React', 'TypeScript'],
      rank: 0,
    };

    vi.mocked(contributorsApi.fetchContributorById).mockResolvedValue(mockContributor);

    const { result } = renderHook(() => useContributor({ id: 'test-id' }), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.contributor).toEqual(mockContributor);
    expect(result.current.notFound).toBe(false);
  });

  it('fetches contributor by username when no ID provided', async () => {
    const mockContributor = {
      id: 'user-123',
      username: 'testuser',
      avatarUrl: 'https://example.com/avatar.png',
      points: 100,
      bountiesCompleted: 5,
      earningsFndry: 1000,
      earningsSol: 0,
      streak: 2,
      topSkills: ['React'],
      rank: 0,
    };

    vi.mocked(contributorsApi.fetchContributorByUsername).mockResolvedValue(mockContributor);

    const { result } = renderHook(() => useContributor({ username: 'testuser' }), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.contributor).toEqual(mockContributor);
    expect(contributorsApi.fetchContributorByUsername).toHaveBeenCalledWith('testuser');
  });

  it('returns notFound when contributor does not exist', async () => {
    vi.mocked(contributorsApi.fetchContributorById).mockResolvedValue(null);

    const { result } = renderHook(() => useContributor({ id: 'nonexistent' }), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.notFound).toBe(true);
    expect(result.current.contributor).toBeNull();
  });

  it('handles API errors gracefully', async () => {
    vi.mocked(contributorsApi.fetchContributorById).mockRejectedValue(new Error('API Error'));

    const { result } = renderHook(() => useContributor({ id: 'test-id' }), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.error).toBeInstanceOf(Error);
  });

  it('does not fetch when disabled', () => {
    const { result } = renderHook(() => useContributor({ id: 'test-id', enabled: false }), {
      wrapper: createWrapper(),
    });

    expect(contributorsApi.fetchContributorById).not.toHaveBeenCalled();
    expect(result.current.loading).toBe(false);
  });
});