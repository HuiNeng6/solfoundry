/**
 * Bounties API service.
 * Provides functions for fetching and managing bounties.
 * @module api/bounties
 */

import { apiFetch, withRetry } from './client';
import type { Bounty, BountyBoardFilters, BountySortBy, BountyTier, BountyStatus, CreatorType } from '../types/bounty';

/** API response types */
export interface BountyListResponse {
  items: ApiBounty[];
  total: number;
  skip: number;
  limit: number;
}

export interface BountySearchResponse {
  items: ApiBounty[];
  total: number;
  page: number;
  per_page: number;
  total_pages: number;
}

export interface ApiBounty {
  id: string;
  title: string;
  description?: string;
  tier: string | number;
  required_skills?: string[];
  skills?: string[];
  reward_amount?: number;
  rewardAmount?: number;
  deadline?: string;
  status: string;
  submission_count?: number;
  submissionCount?: number;
  created_at?: string;
  createdAt?: string;
  created_by?: string;
  projectName?: string;
  creator_type?: string;
  creatorType?: string;
  github_issue_url?: string;
  githubIssueUrl?: string;
  relevance_score?: number;
  skill_match_count?: number;
}

/** Status mapping from API to frontend format */
const STATUS_MAP: Record<string, string> = {
  open: 'open',
  in_progress: 'in-progress',
  under_review: 'under_review',
  completed: 'completed',
  disputed: 'disputed',
  paid: 'paid',
  cancelled: 'cancelled',
};

/** Tier mapping from API to frontend format */
const TIER_MAP: Record<number | string, BountyTier> = {
  1: 'T1',
  2: 'T2',
  3: 'T3',
  T1: 'T1',
  T2: 'T2',
  T3: 'T3',
};

/** Map API bounty to frontend Bounty type */
export function mapApiBounty(b: ApiBounty): Bounty {
  const tier = TIER_MAP[b.tier] || 'T2';
  const status = (STATUS_MAP[b.status] || b.status || 'open') as BountyStatus;
  const creatorType = (b.creator_type || b.creatorType || 'platform') as CreatorType;
  
  return {
    id: b.id,
    title: b.title,
    description: b.description || '',
    tier,
    skills: b.required_skills || b.skills || [],
    rewardAmount: b.reward_amount ?? b.rewardAmount ?? 0,
    currency: '$FNDRY',
    deadline: b.deadline || new Date(Date.now() + 7 * 86400000).toISOString(),
    status,
    submissionCount: b.submission_count ?? b.submissionCount ?? 0,
    createdAt: b.created_at ?? b.createdAt ?? new Date().toISOString(),
    projectName: b.created_by || b.projectName || 'SolFoundry',
    creatorType,
    githubIssueUrl: b.github_issue_url || b.githubIssueUrl || undefined,
    relevanceScore: b.relevance_score ?? 0,
    skillMatchCount: b.skill_match_count ?? 0,
  };
}

/** Build search params from filters */
function buildSearchParams(
  filters: BountyBoardFilters,
  sortBy: BountySortBy,
  page: number,
  perPage: number
): URLSearchParams {
  const params = new URLSearchParams();
  
  if (filters.searchQuery.trim()) {
    params.set('q', filters.searchQuery.trim());
  }
  
  if (filters.tier !== 'all') {
    const tierNum = filters.tier === 'T1' ? '1' : filters.tier === 'T2' ? '2' : '3';
    params.set('tier', tierNum);
  }
  
  if (filters.status !== 'all') {
    const statusMap: Record<string, string> = {
      open: 'open',
      'in-progress': 'in_progress',
      completed: 'completed',
    };
    params.set('status', statusMap[filters.status] || filters.status);
  }
  
  if (filters.skills.length) {
    params.set('skills', filters.skills.join(','));
  }
  
  if (filters.rewardMin) {
    params.set('reward_min', filters.rewardMin);
  }
  
  if (filters.rewardMax) {
    params.set('reward_max', filters.rewardMax);
  }
  
  if (filters.creatorType !== 'all') {
    params.set('creator_type', filters.creatorType);
  }
  
  if (filters.category !== 'all') {
    params.set('category', filters.category);
  }
  
  if (filters.deadlineBefore) {
    params.set('deadline_before', new Date(filters.deadlineBefore + 'T23:59:59Z').toISOString());
  }
  
  params.set('sort', sortBy);
  params.set('page', String(page));
  params.set('per_page', String(perPage));
  
  return params;
}

/** Fetch bounties list */
export async function fetchBounties(
  filters: BountyBoardFilters,
  sortBy: BountySortBy,
  page: number = 1,
  perPage: number = 20
): Promise<{ items: Bounty[]; total: number }> {
  try {
    const params = buildSearchParams(filters, sortBy, page, perPage);
    const response = await withRetry(() =>
      apiFetch<BountySearchResponse>(`/api/bounties/search?${params}`)
    );
    
    return {
      items: response.items.map(mapApiBounty),
      total: response.total,
    };
  } catch (error) {
    // Fallback to list endpoint if search fails
    try {
      const response = await withRetry(() =>
        apiFetch<BountyListResponse>(`/api/bounties?limit=100`)
      );
      return {
        items: response.items.map(mapApiBounty),
        total: response.total,
      };
    } catch {
      throw error;
    }
  }
}

/** Fetch single bounty by ID */
export async function fetchBounty(id: string): Promise<Bounty> {
  const response = await withRetry(() =>
    apiFetch<ApiBounty>(`/api/bounties/${id}`)
  );
  return mapApiBounty(response);
}

/** Fetch hot/trending bounties */
export async function fetchHotBounties(limit: number = 6): Promise<Bounty[]> {
  try {
    const response = await withRetry(() =>
      apiFetch<ApiBounty[]>(`/api/bounties/hot?limit=${limit}`)
    );
    return response.map(mapApiBounty);
  } catch {
    return [];
  }
}

/** Fetch recommended bounties based on skills */
export async function fetchRecommendedBounties(
  skills: string[],
  exclude: string[] = [],
  limit: number = 6
): Promise<Bounty[]> {
  try {
    const params = new URLSearchParams();
    params.set('skills', skills.join(','));
    if (exclude.length) {
      params.set('exclude', exclude.join(','));
    }
    params.set('limit', String(limit));
    
    const response = await withRetry(() =>
      apiFetch<ApiBounty[]>(`/api/bounties/recommended?${params}`)
    );
    return response.map(mapApiBounty);
  } catch {
    return [];
  }
}

/** Fetch autocomplete suggestions */
export async function fetchAutocomplete(query: string, limit: number = 8): Promise<string[]> {
  try {
    const response = await withRetry(() =>
      apiFetch<{ suggestions: string[] }>(`/api/bounties/autocomplete?q=${encodeURIComponent(query)}&limit=${limit}`)
    );
    return response.suggestions || [];
  } catch {
    return [];
  }
}