/**
 * Contributors API service.
 * Provides functions for fetching contributor profiles.
 * @module api/contributors
 */

import { apiFetch, withRetry } from './client';
import type { Contributor } from '../types/leaderboard';

/** API response type for contributor profile */
interface ApiContributorProfile {
  id: string;
  username: string;
  display_name?: string;
  displayName?: string;
  avatar_url?: string;
  avatarUrl?: string;
  bio?: string;
  wallet_address?: string;
  walletAddress?: string;
  skills?: string[];
  badges?: string[];
  total_bounties_completed?: number;
  totalBountiesCompleted?: number;
  total_earned?: number;
  totalEarned?: number;
  reputation_score?: number;
  reputationScore?: number;
  tier?: number;
  created_at?: string;
  createdAt?: string;
}

/** Map API contributor profile to frontend Contributor type */
function mapApiContributorProfile(c: ApiContributorProfile): Contributor & {
  id: string;
  bio?: string;
  walletAddress?: string;
  badges?: string[];
  tier?: number;
} {
  return {
    id: c.id,
    rank: 0,
    username: c.username,
    avatarUrl: c.avatar_url || c.avatarUrl || `https://api.dicebear.com/7.x/identicon/svg?seed=${c.username}`,
    points: c.reputation_score ? Math.floor(c.reputation_score * 100) : 0,
    bountiesCompleted: c.total_bounties_completed || c.totalBountiesCompleted || 0,
    earningsFndry: c.total_earned || c.totalEarned || 0,
    earningsSol: 0,
    streak: Math.max(1, Math.floor((c.total_bounties_completed || 0) / 2)),
    topSkills: c.skills || [],
    bio: c.bio,
    walletAddress: c.wallet_address || c.walletAddress,
    badges: c.badges || [],
    tier: c.tier,
  };
}

/** API response for paginated list */
interface ContributorListResponse {
  items: ApiContributorProfile[];
  total: number;
  skip: number;
  limit: number;
}

/** Fetch contributor by ID */
export async function fetchContributorById(id: string): Promise<Contributor | null> {
  try {
    const response = await withRetry(() =>
      apiFetch<ApiContributorProfile>(`/api/contributors/${id}`)
    );
    return mapApiContributorProfile(response);
  } catch {
    return null;
  }
}

/** Fetch contributor by username */
export async function fetchContributorByUsername(username: string): Promise<Contributor | null> {
  try {
    const response = await withRetry(() =>
      apiFetch<ContributorListResponse>(`/api/contributors?search=${encodeURIComponent(username)}&limit=1`)
    );
    if (response.items.length > 0) {
      return mapApiContributorProfile(response.items[0]);
    }
    return null;
  } catch {
    return null;
  }
}

/** List contributors with filters */
export async function listContributors(options: {
  search?: string;
  skills?: string[];
  badges?: string[];
  skip?: number;
  limit?: number;
} = {}): Promise<{ items: Contributor[]; total: number }> {
  try {
    const params = new URLSearchParams();
    
    if (options.search) {
      params.set('search', options.search);
    }
    if (options.skills?.length) {
      params.set('skills', options.skills.join(','));
    }
    if (options.badges?.length) {
      params.set('badges', options.badges.join(','));
    }
    params.set('skip', String(options.skip || 0));
    params.set('limit', String(options.limit || 20));
    
    const response = await withRetry(() =>
      apiFetch<ContributorListResponse>(`/api/contributors?${params}`)
    );
    
    return {
      items: response.items.map(mapApiContributorProfile),
      total: response.total,
    };
  } catch {
    return { items: [], total: 0 };
  }
}