/**
 * useBountyBoard - React Query powered hook for bounty board data.
 * Fetches from real API with caching, loading states, and error handling.
 * No mock data fallbacks - UI handles empty/error states.
 * @module hooks/useBountyBoard
 */

import { useState, useMemo, useCallback } from 'react';
import { useQuery } from '@tanstack/react-query';
import type { Bounty, BountyBoardFilters, BountySortBy } from '../types/bounty';
import { DEFAULT_FILTERS } from '../types/bounty';
import { 
  fetchBounties, 
  fetchHotBounties, 
  fetchRecommendedBounties,
  mapApiBounty 
} from '../api/bounties';

/** Sort compatibility mapping */
const SORT_COMPAT: Record<string, BountySortBy> = { reward: 'reward_high' };

export function useBountyBoard() {
  const [filters, setFilters] = useState<BountyBoardFilters>(DEFAULT_FILTERS);
  const [sortBy, setSortByRaw] = useState<BountySortBy>('newest');
  const [page, setPage] = useState(1);
  const perPage = 20;

  const setSortBy = useCallback((s: BountySortBy | string) => {
    setSortByRaw((SORT_COMPAT[s] || s) as BountySortBy);
    setPage(1);
  }, []);

  // Main bounties query with React Query
  const { 
    data: apiResults, 
    isLoading: loading, 
    error,
    isFetching,
    refetch
  } = useQuery({
    queryKey: ['bounties', filters, sortBy, page],
    queryFn: () => fetchBounties(filters, sortBy, page, perPage),
    staleTime: 30 * 1000,
    retry: 2,
  });

  // Hot bounties query
  const { data: hotBounties = [], isLoading: hotLoading } = useQuery({
    queryKey: ['bounties', 'hot'],
    queryFn: () => fetchHotBounties(6),
    staleTime: 60 * 1000,
    retry: 1,
  });

  // Recommended bounties query
  const { data: recommendedBounties = [], isLoading: recommendedLoading } = useQuery({
    queryKey: ['bounties', 'recommended', filters.skills],
    queryFn: () => {
      const skills = filters.skills.length > 0 ? filters.skills : ['react', 'typescript', 'rust'];
      return fetchRecommendedBounties(skills, [], 6);
    },
    staleTime: 60 * 1000,
    retry: 1,
  });

  // Use API data directly - no mock fallback
  const bounties = apiResults?.items ?? [];
  const total = apiResults?.total ?? 0;
  const totalPages = Math.max(1, Math.ceil(total / perPage));

  const setFilter = useCallback(<K extends keyof BountyBoardFilters>(k: K, v: BountyBoardFilters[K]) => {
    setFilters(p => ({ ...p, [k]: v }));
    setPage(1);
  }, []);

  return {
    bounties,
    total,
    filters,
    sortBy,
    loading: loading || isFetching,
    error: error as Error | null,
    page,
    totalPages,
    hotBounties,
    recommendedBounties,
    hotLoading,
    recommendedLoading,
    setFilter,
    resetFilters: useCallback(() => { 
      setFilters(DEFAULT_FILTERS); 
      setPage(1); 
    }, []),
    setSortBy,
    setPage,
    refetch,
  };
}