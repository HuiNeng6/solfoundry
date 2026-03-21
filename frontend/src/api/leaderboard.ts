/**
 * Leaderboard API service.
 * Provides functions for fetching contributor leaderboard data.
 * @module api/leaderboard
 */

import { apiFetch, withRetry } from './client';
import type { Contributor, TimeRange } from '../types/leaderboard';

/** API response type for leaderboard entry */
interface ApiContributor {
  rank: number;
  username: string;
  avatar_url?: string;
  avatarUrl?: string;
  reputation_score?: number;
  points?: number;
  bounties_completed?: number;
  bountiesCompleted?: number;
  total_earned?: number;
  earningsFndry?: number;
  earnings_sol?: number;
  earningsSol?: number;
  streak?: number;
  top_skills?: string[];
  topSkills?: string[];
}

/** Map API contributor to frontend Contributor type */
function mapApiContributor(c: ApiContributor): Contributor {
  return {
    rank: c.rank,
    username: c.username,
    avatarUrl: c.avatar_url || c.avatarUrl || `https://api.dicebear.com/7.x/identicon/svg?seed=${c.username}`,
    points: c.reputation_score ? Math.floor(c.reputation_score * 100) : c.points || 0,
    bountiesCompleted: c.bounties_completed || c.bountiesCompleted || 0,
    earningsFndry: c.total_earned || c.earningsFndry || 0,
    earningsSol: c.earnings_sol || c.earningsSol || 0,
    streak: c.streak || Math.max(1, Math.floor((c.bounties_completed || 0) / 2)),
    topSkills: c.top_skills || c.topSkills || [],
  };
}

/** Time range mapping for API */
const TIME_RANGE_MAP: Record<TimeRange, string> = {
  '7d': '7d',
  '30d': '30d',
  '90d': '90d',
  all: 'all',
};

/** Fetch leaderboard contributors */
export async function fetchLeaderboard(
  timeRange: TimeRange = 'all',
  tier?: number,
  category?: string,
  limit: number = 50,
  offset: number = 0
): Promise<Contributor[]> {
  try {
    const params = new URLSearchParams();
    params.set('range', TIME_RANGE_MAP[timeRange]);
    params.set('limit', String(limit));
    params.set('offset', String(offset));
    
    if (tier) {
      params.set('tier', String(tier));
    }
    
    if (category) {
      params.set('category', category);
    }
    
    const response = await withRetry(() =>
      apiFetch<ApiContributor[]>(`/api/leaderboard?${params}`)
    );
    
    return response.map(mapApiContributor);
  } catch {
    return [];
  }
}

/** Fetch contributor by username or ID */
export async function fetchContributor(id: string): Promise<Contributor | null> {
  try {
    const response = await withRetry(() =>
      apiFetch<ApiContributor>(`/api/contributors/${id}`)
    );
    return mapApiContributor(response);
  } catch {
    return null;
  }
}