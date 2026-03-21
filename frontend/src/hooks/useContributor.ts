/**
 * useContributor - React Query hook for fetching contributor profile data.
 * Connects ContributorProfile component to real API.
 * @module hooks/useContributor
 */

import { useQuery } from '@tanstack/react-query';
import type { Contributor } from '../types/leaderboard';
import { fetchContributorById, fetchContributorByUsername } from '../api/contributors';

interface UseContributorOptions {
  /** Contributor ID (from API) */
  id?: string;
  /** GitHub username */
  username?: string;
  /** Enable/disable the query */
  enabled?: boolean;
}

interface ContributorProfile extends Contributor {
  id: string;
  bio?: string;
  walletAddress?: string;
  badges?: string[];
  tier?: number;
}

/**
 * Hook for fetching contributor profile by ID or username.
 * Priority: id > username
 */
export function useContributor(options: UseContributorOptions) {
  const { id, username, enabled = true } = options;

  // Query by ID if provided
  const {
    data: contributorById,
    isLoading: loadingById,
    error: errorById,
    refetch: refetchById,
  } = useQuery({
    queryKey: ['contributor', 'id', id],
    queryFn: () => fetchContributorById(id!),
    enabled: enabled && !!id,
    staleTime: 5 * 60 * 1000,
    retry: 2,
  });

  // Query by username if no ID
  const {
    data: contributorByUsername,
    isLoading: loadingByUsername,
    error: errorByUsername,
    refetch: refetchByUsername,
  } = useQuery({
    queryKey: ['contributor', 'username', username],
    queryFn: () => fetchContributorByUsername(username!),
    enabled: enabled && !id && !!username,
    staleTime: 5 * 60 * 1000,
    retry: 2,
  });

  // Combine results
  const contributor = contributorById || contributorByUsername;
  const loading = loadingById || loadingByUsername;
  const error = errorById || errorByUsername;

  const refetch = () => {
    if (id) refetchById();
    else if (username) refetchByUsername();
  };

  return {
    contributor: contributor as ContributorProfile | null,
    loading,
    error: error as Error | null,
    notFound: !loading && !contributor,
    refetch,
  };
}

export default useContributor;