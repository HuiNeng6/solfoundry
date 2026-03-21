/**
 * useBountyBoard - React Query powered hook for bounty board data.
 * Fetches from real API with caching, loading states, and error handling.
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
import { mockBounties } from '../data/mockBounties';

/** Sort compatibility mapping */
const SORT_COMPAT: Record<string, BountySortBy> = { reward: 'reward_high' };

/** Local sort function for fallback */
function localSort(arr: Bounty[], sortBy: BountySortBy): Bounty[] {
  const s = [...arr];
  switch (sortBy) {
    case 'reward_high': return s.sort((a, b) => b.rewardAmount - a.rewardAmount);
    case 'reward_low': return s.sort((a, b) => a.rewardAmount - b.rewardAmount);
    case 'deadline': return s.sort((a, b) => new Date(a.deadline).getTime() - new Date(b.deadline).getTime());
    case 'submissions': return s.sort((a, b) => b.submissionCount - a.submissionCount);
    case 'best_match':
    case 'newest':
    default: return s.sort((a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime());
  }
}

/** Local filter function for fallback */
function applyLocalFilters(all: Bounty[], f: BountyBoardFilters, sortBy: BountySortBy): Bounty[] {
  let r = [...all];
  if (f.tier !== 'all') r = r.filter(b => b.tier === f.tier);
  if (f.status !== 'all') r = r.filter(b => b.status === f.status);
  if (f.skills.length) r = r.filter(b => f.skills.some(s => b.skills.map(sk => sk.toLowerCase()).includes(s.toLowerCase())));
  if (f.searchQuery.trim()) {
    const q = f.searchQuery.toLowerCase();
    r = r.filter(b => b.title.toLowerCase().includes(q) || b.description.toLowerCase().includes(q) || b.projectName.toLowerCase().includes(q));
  }
  if (f.rewardMin) { const min = Number(f.rewardMin); if (!isNaN(min)) r = r.filter(b => b.rewardAmount >= min); }
  if (f.rewardMax) { const max = Number(f.rewardMax); if (!isNaN(max)) r = r.filter(b => b.rewardAmount <= max); }
  if (f.deadlineBefore) {
    const cutoff = new Date(f.deadlineBefore + 'T23:59:59Z').getTime();
    r = r.filter(b => new Date(b.deadline).getTime() <= cutoff);
  }
  return localSort(r, sortBy);
}

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
    isFetching 
  } = useQuery({
    queryKey: ['bounties', filters, sortBy, page],
    queryFn: () => fetchBounties(filters, sortBy, page, perPage),
    staleTime: 30 * 1000,
    retry: 2,
  });

  // Hot bounties query
  const { data: hotBounties = [] } = useQuery({
    queryKey: ['bounties', 'hot'],
    queryFn: () => fetchHotBounties(6),
    staleTime: 60 * 1000,
    retry: 1,
  });

  // Recommended bounties query
  const { data: recommendedBounties = [] } = useQuery({
    queryKey: ['bounties', 'recommended', filters.skills],
    queryFn: () => {
      const skills = filters.skills.length > 0 ? filters.skills : ['react', 'typescript', 'rust'];
      return fetchRecommendedBounties(skills, [], 6);
    },
    staleTime: 60 * 1000,
    retry: 1,
  });

  // Fallback to local filtering if API fails or returns empty
  const localFiltered = useMemo(
    () => applyLocalFilters(mockBounties, filters, sortBy),
    [filters, sortBy],
  );

  // Decide which results to use
  const bounties = apiResults?.items?.length ? apiResults.items : localFiltered;
  const total = apiResults?.total ?? localFiltered.length;
  const totalPages = Math.max(1, Math.ceil(total / perPage));

  const setFilter = useCallback(<K extends keyof BountyBoardFilters>(k: K, v: BountyBoardFilters[K]) => {
    setFilters(p => ({ ...p, [k]: v }));
    setPage(1);
  }, []);

  return {
    bounties,
    allBounties: mockBounties,
    total,
    filters,
    sortBy,
    loading: loading || isFetching,
    error: error as Error | null,
    page,
    totalPages,
    hotBounties,
    recommendedBounties,
    setFilter,
    resetFilters: useCallback(() => { 
      setFilters(DEFAULT_FILTERS); 
      setPage(1); 
    }, []),
    setSortBy,
    setPage,
  };
}