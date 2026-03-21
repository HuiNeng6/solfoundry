/**
 * BountyBoardSkeleton - Loading skeleton for BountyBoard component.
 * Displays animated placeholder cards while data loads.
 * @module components/bounties/BountyBoardSkeleton
 */

import React from 'react';
import { Skeleton, SkeletonCard, SkeletonGrid } from '../common/Skeleton';

interface BountyBoardSkeletonProps {
  /** Number of bounty cards to show */
  count?: number;
  /** Show filters skeleton */
  showFilters?: boolean;
  /** Show sort bar skeleton */
  showSortBar?: boolean;
  /** Show hot bounties section */
  showHotBounties?: boolean;
  /** Show recommended section */
  showRecommended?: boolean;
}

export function BountyBoardSkeleton({
  count = 6,
  showFilters = true,
  showSortBar = true,
  showHotBounties = true,
  showRecommended = true,
}: BountyBoardSkeletonProps) {
  return (
    <div className="space-y-6" role="status" aria-label="Loading bounty board">
      {/* Filters skeleton */}
      {showFilters && (
        <div className="bg-[#1a1a1a] rounded-xl p-4 border border-white/5">
          <div className="flex flex-wrap gap-3">
            {Array.from({ length: 4 }).map((_, i) => (
              <Skeleton key={i} height="2.5rem" width="8rem" variant="pill" />
            ))}
          </div>
        </div>
      )}

      {/* Sort bar skeleton */}
      {showSortBar && (
        <div className="flex items-center justify-between">
          <Skeleton height="1.5rem" width="6rem" />
          <div className="flex items-center gap-2">
            <Skeleton height="2rem" width="5rem" />
            <Skeleton height="2rem" width="5rem" />
          </div>
        </div>
      )}

      {/* Hot bounties skeleton */}
      {showHotBounties && (
        <div>
          <Skeleton height="1.5rem" width="10rem" className="mb-3" />
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {Array.from({ length: 3 }).map((_, i) => (
              <SkeletonCard key={i} showAvatar bodyLines={2} showFooter />
            ))}
          </div>
        </div>
      )}

      {/* Main bounty grid skeleton */}
      <div>
        <Skeleton height="1.5rem" width="8rem" className="mb-3" />
        <SkeletonGrid count={count} columns={3} showAvatar />
      </div>

      {/* Recommended bounties skeleton */}
      {showRecommended && (
        <div>
          <Skeleton height="1.5rem" width="12rem" className="mb-3" />
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {Array.from({ length: 3 }).map((_, i) => (
              <SkeletonCard key={i} showAvatar bodyLines={2} showFooter />
            ))}
          </div>
        </div>
      )}

      {/* Pagination skeleton */}
      <div className="flex items-center justify-center gap-2 mt-6">
        {Array.from({ length: 5 }).map((_, i) => (
          <Skeleton key={i} height="2.5rem" width="2.5rem" variant="pill" />
        ))}
      </div>

      <span className="sr-only">Loading bounty board...</span>
    </div>
  );
}

export default BountyBoardSkeleton;