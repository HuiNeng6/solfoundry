/**
 * useTreasuryStats - React Query powered hook for tokenomics/treasury data.
 * Fetches from real API with caching, loading states, and error handling.
 * @module hooks/useTreasuryStats
 */

import { useQuery } from '@tanstack/react-query';
import type { TokenomicsData, TreasuryStats } from '../types/tokenomics';
import { fetchTokenomics, fetchTreasuryStats } from '../api/tokenomics';
import { MOCK_TOKENOMICS, MOCK_TREASURY } from '../data/mockTokenomics';

/**
 * Fetches live tokenomics and treasury data from `/api/payouts/tokenomics` and `/api/payouts/treasury`.
 * Falls back to {@link MOCK_TOKENOMICS} / {@link MOCK_TREASURY} when the API is unreachable.
 */
export function useTreasuryStats() {
  // Tokenomics query
  const {
    data: tokenomicsData,
    isLoading: tokenomicsLoading,
    error: tokenomicsError,
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
  } = useQuery({
    queryKey: ['treasury'],
    queryFn: fetchTreasuryStats,
    staleTime: 60 * 1000,
    retry: 2,
  });

  // Combine loading states
  const loading = tokenomicsLoading || treasuryLoading;
  
  // Combine errors
  const error = tokenomicsError || treasuryError;

  // Use API data or fall back to mock
  const tokenomics: TokenomicsData = tokenomicsData || MOCK_TOKENOMICS;
  const treasury: TreasuryStats = treasuryData || MOCK_TREASURY;

  return {
    tokenomics,
    treasury,
    loading,
    error: error as Error | null,
  };
}