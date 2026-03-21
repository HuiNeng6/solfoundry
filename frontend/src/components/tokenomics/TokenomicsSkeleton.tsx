/**
 * TokenomicsSkeleton - Loading skeleton for Tokenomics/Treasury components.
 * Displays animated placeholder cards while data loads.
 * @module components/tokenomics/TokenomicsSkeleton
 */

import React from 'react';
import { Skeleton, SkeletonCard } from '../common/Skeleton';

interface TokenomicsSkeletonProps {
  /** Show treasury section */
  showTreasury?: boolean;
  /** Show token stats */
  showTokenStats?: boolean;
}

export function TokenomicsSkeleton({
  showTreasury = true,
  showTokenStats = true,
}: TokenomicsSkeletonProps) {
  return (
    <div className="space-y-6" role="status" aria-label="Loading tokenomics data">
      {/* Token Stats Section */}
      {showTokenStats && (
        <div className="bg-[#1a1a1a] rounded-xl p-6 border border-white/5">
          <div className="flex items-center justify-between mb-6">
            <Skeleton height="1.5rem" width="10rem" />
            <Skeleton height="2rem" width="4rem" variant="pill" />
          </div>

          {/* Price and Market Cap */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
            <div className="bg-[#0a0a0a] rounded-lg p-4">
              <p className="text-gray-400 text-sm mb-2">Current Price</p>
              <Skeleton height="2rem" width="6rem" className="mb-1" />
              <Skeleton height="0.875rem" width="4rem" />
            </div>
            <div className="bg-[#0a0a0a] rounded-lg p-4">
              <p className="text-gray-400 text-sm mb-2">Market Cap</p>
              <Skeleton height="2rem" width="5rem" className="mb-1" />
              <Skeleton height="0.875rem" width="3rem" />
            </div>
          </div>

          {/* Supply Stats Grid */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {Array.from({ length: 4 }).map((_, i) => (
              <div key={i} className="bg-[#0a0a0a] rounded-lg p-3">
                <Skeleton height="0.75rem" width="5rem" className="mb-2" />
                <Skeleton height="1.25rem" width="4rem" />
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Treasury Section */}
      {showTreasury && (
        <div className="bg-[#1a1a1a] rounded-xl p-6 border border-white/5">
          <Skeleton height="1.5rem" width="8rem" className="mb-6" />

          {/* Treasury Balance Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-[#0a0a0a] rounded-lg p-4">
              <p className="text-gray-400 text-sm mb-2">Total Balance</p>
              <Skeleton height="2rem" width="7rem" />
            </div>
            <div className="bg-[#0a0a0a] rounded-lg p-4">
              <p className="text-gray-400 text-sm mb-2">SOL Balance</p>
              <Skeleton height="2rem" width="6rem" />
            </div>
            <div className="bg-[#0a0a0a] rounded-lg p-4">
              <p className="text-gray-400 text-sm mb-2">FNDRY Balance</p>
              <Skeleton height="2rem" width="6rem" />
            </div>
          </div>

          {/* Last Updated */}
          <div className="mt-4 flex items-center justify-end gap-2">
            <Skeleton height="0.75rem" width="6rem" />
            <Skeleton height="0.75rem" width="4rem" />
          </div>
        </div>
      )}

      <span className="sr-only">Loading tokenomics and treasury data...</span>
    </div>
  );
}

export default TokenomicsSkeleton;