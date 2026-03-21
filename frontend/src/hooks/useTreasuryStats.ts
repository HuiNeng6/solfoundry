/**
 * useTreasuryStats - React Query powered hook for tokenomics/treasury data.
 * Fetches from real API with caching, loading states, and error handling.
 * No mock data fallbacks - UI handles empty/error states.
 * @module hooks/useTreasuryStats
 */

import { useQuery } from '@tanstack/react-query';
import type { TokenomicsData, TreasuryStats } from '../types/tokenomics';
import { fetchTokenomics, fetchTreasuryStats } from '../api/tokenomics';

// Default empty data structures for when API is unavailable
const EMPTY_TOKENOMICS: TokenomicsData = {
  totalSupply: 0,
  circulatingSupply: 0,
  burned: 0,
  price: 0,
  marketCap: 0,
  holders: 0,
};

const EMPTY_TREASURY: TreasuryStats = {
  totalBalance: 0,
  solBalance: 0,
  fndryBalance: 0,
  lastUpdated: new Date().toISOString(),
};

/**
 * Fetches live tokenomics and treasury data from `/api/payouts/tokenomics` and `/api/payouts/treasury`.
 * Returns empty data structures when API is unavailable - UI should handle error state.
 */
export function useTreasuryStats() {
  // Tokenomics query
  const {
    data: tokenomicsData,
    isLoading: tokenomicsLoading,
    error: tokenomicsError,
    refetch: refetchTokenomics,
  } = useQuery({
    queryKey: ['tokenomics'],
    queryFn: fetchTokenomics,
    staleTime: 60 * 1000,
    retry: 2,
  });

  // Treasury stats query
  const {
    data: treasuryData,
    isLoading: treasuryLoading,
    error: treasuryError,
    refetch: refetchTreasury,
  } = useQuery({
    queryKey: ['treasury'],
    queryFn: fetchTreasuryStats,
    staleTime: 60 * 1000,
    retry: 2,
  });

  // Combine loading states
  const loading = tokenomicsLoading || treasuryLoading;
  
  // Combine errors - return first error if any
  const error = tokenomicsError || treasuryError;
  
  // Check if we have real data
  const hasTokenomics = tokenomicsData !== null && tokenomicsData !== undefined;
  const hasTreasury = treasuryData !== null && treasuryData !== undefined;
  
  // Use API data or empty structures - UI should check isEmpty and error
  const tokenomics: TokenomicsData = hasTokenomics ? tokenomicsData : EMPTY_TOKENOMICS;
  const treasury: TreasuryStats = hasTreasury ? treasuryData : EMPTY_TREASURY;
  
  // Flag for UI to show empty state
  const isEmpty = !hasTokenomics && !hasTreasury && !loading;

  const refetch = () => {
    refetchTokenomics();
    refetchTreasury();
  };

  return {
    tokenomics,
    treasury,
    loading,
    error: error as Error | null,
    isEmpty,
    hasData: hasTokenomics || hasTreasury,
    refetch,
  };
}