/**
 * LeaderboardSkeleton - Loading skeleton for Leaderboard component.
 * Displays animated placeholder rows while data loads.
 * @module components/leaderboard/LeaderboardSkeleton
 */

import React from 'react';
import { Skeleton, SkeletonAvatar, SkeletonTableRow } from '../common/Skeleton';

interface LeaderboardSkeletonProps {
  /** Number of rows to display */
  rows?: number;
  /** Show search/filter controls */
  showControls?: boolean;
}

export function LeaderboardSkeleton({
  rows = 10,
  showControls = true,
}: LeaderboardSkeletonProps) {
  return (
    <div className="space-y-4" role="status" aria-label="Loading leaderboard">
      {/* Controls skeleton */}
      {showControls && (
        <div className="flex flex-col sm:flex-row gap-4 mb-6">
          {/* Search input */}
          <Skeleton height="2.5rem" width="16rem" className="rounded-lg" />
          
          {/* Time range tabs */}
          <div className="flex gap-2">
            {Array.from({ length: 4 }).map((_, i) => (
              <Skeleton key={i} height="2.5rem" width="5rem" variant="pill" />
            ))}
          </div>
          
          {/* Sort dropdown */}
          <Skeleton height="2.5rem" width="8rem" className="rounded-lg ml-auto" />
        </div>
      )}

      {/* Table skeleton */}
      <div className="bg-[#1a1a1a] rounded-xl border border-white/5 overflow-hidden">
        {/* Table header */}
        <div className="grid grid-cols-6 gap-4 p-4 border-b border-white/10 text-xs text-gray-400">
          <div className="col-span-1"><Skeleton height="0.75rem" width="2rem" /></div>
          <div className="col-span-2"><Skeleton height="0.75rem" width="4rem" /></div>
          <div className="col-span-1"><Skeleton height="0.75rem" width="3rem" /></div>
          <div className="col-span-1"><Skeleton height="0.75rem" width="3rem" /></div>
          <div className="col-span-1"><Skeleton height="0.75rem" width="4rem" /></div>
        </div>

        {/* Table rows */}
        <div className="divide-y divide-white/5">
          {Array.from({ length: rows }).map((_, i) => (
            <div key={i} className="grid grid-cols-6 gap-4 p-4 hover:bg-white/5 transition-colors">
              {/* Rank */}
              <div className="col-span-1">
                <Skeleton height="1rem" width="1.5rem" />
              </div>
              
              {/* Contributor */}
              <div className="col-span-2 flex items-center gap-3">
                <SkeletonAvatar size="sm" />
                <Skeleton height="1rem" width="6rem" />
              </div>
              
              {/* Points */}
              <div className="col-span-1">
                <Skeleton height="1rem" width="4rem" />
              </div>
              
              {/* Bounties */}
              <div className="col-span-1">
                <Skeleton height="1rem" width="2rem" />
              </div>
              
              {/* Earnings */}
              <div className="col-span-1">
                <Skeleton height="1rem" width="5rem" />
              </div>
            </div>
          ))}
        </div>
      </div>

      <span className="sr-only">Loading leaderboard data...</span>
    </div>
  );
}

export default LeaderboardSkeleton;