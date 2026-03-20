'use client';

import React, { useState, useMemo } from 'react';
import type { 
  BountyTimelineData, 
  TimelineStageDetails, 
  TimelineStage,
  TimelineStageStatus 
} from '../types/timeline';
import { TIMELINE_STAGE_CONFIG } from '../types/timeline';
import { getTimelineByBountyId, mockTimelines } from '../data/mockTimeline';

// Utility functions
const formatDate = (date?: string): string => {
  if (!date) return '—';
  const d = new Date(date);
  return d.toLocaleDateString('en-US', { 
    month: 'short', 
    day: 'numeric',
    year: d.getFullYear() !== new Date().getFullYear() ? 'numeric' : undefined
  });
};

const formatTimeAgo = (date?: string): string => {
  if (!date) return '';
  const d = new Date(date).getTime();
  const now = Date.now();
  const diff = now - d;
  const days = Math.floor(diff / 864e5);
  const hours = Math.floor((diff % 864e5) / 36e5);
  
  if (days > 0) return `${days}d ago`;
  if (hours > 0) return `${hours}h ago`;
  return 'Just now';
};

// Stage status styles
const getStageStyles = (status: TimelineStageStatus, isCurrent: boolean): {
  container: string;
  icon: string;
  connector: string;
  badge: string;
} => {
  const baseContainer = 'relative rounded-xl border-2 transition-all duration-300';
  
  switch (status) {
    case 'completed':
      return {
        container: `${baseContainer} border-green-500/50 bg-green-500/10`,
        icon: 'text-green-400',
        connector: 'bg-green-500',
        badge: 'bg-green-500/20 text-green-400',
      };
    case 'current':
      return {
        container: `${baseContainer} border-blue-500 bg-blue-500/10 ring-2 ring-blue-400/50 ring-offset-2 ring-offset-gray-900`,
        icon: 'text-blue-400 animate-pulse',
        connector: 'bg-gray-700',
        badge: 'bg-blue-500/20 text-blue-400 animate-pulse',
      };
    case 'pending':
    default:
      return {
        container: `${baseContainer} border-gray-700 bg-gray-800/50 opacity-60`,
        icon: 'text-gray-500',
        connector: 'bg-gray-700',
        badge: 'bg-gray-700 text-gray-400',
      };
  }
};

// Sub-components
const SubmissionList: React.FC<{ submissions: TimelineStageDetails['submissions'] }> = ({ submissions }) => {
  if (!submissions || submissions.length === 0) return null;
  
  return (
    <div className="mt-3 space-y-2">
      {submissions.map((sub, idx) => (
        <div 
          key={idx} 
          className="flex items-center gap-2 text-xs p-2 bg-gray-800/50 rounded-lg"
        >
          <span className={`w-2 h-2 rounded-full ${
            sub.status === 'approved' ? 'bg-green-400' :
            sub.status === 'rejected' ? 'bg-red-400' :
            sub.status === 'in_review' ? 'bg-blue-400 animate-pulse' :
            'bg-gray-500'
          }`} />
          <span className="font-mono">#{sub.prNumber}</span>
          <span className="text-gray-400">by</span>
          <span className="text-gray-300">{sub.author}</span>
          {sub.url && (
            <a 
              href={sub.url} 
              target="_blank" 
              rel="noopener noreferrer"
              className="ml-auto text-blue-400 hover:text-blue-300"
            >
              →
            </a>
          )}
        </div>
      ))}
    </div>
  );
};

const ReviewResults: React.FC<{ results: TimelineStageDetails['reviewResults'] }> = ({ results }) => {
  if (!results || results.length === 0) return null;
  
  return (
    <div className="mt-3 space-y-2">
      {results.map((review, idx) => (
        <div 
          key={idx} 
          className={`p-3 rounded-lg ${
            review.verdict === 'approved' ? 'bg-green-500/10 border border-green-500/20' :
            review.verdict === 'rejected' ? 'bg-red-500/10 border border-red-500/20' :
            'bg-yellow-500/10 border border-yellow-500/20'
          }`}
        >
          <div className="flex items-center justify-between mb-1">
            <span className="text-sm font-medium">PR #{review.prNumber}</span>
            <span className={`text-xs px-2 py-0.5 rounded ${
              review.verdict === 'approved' ? 'bg-green-500/20 text-green-400' :
              review.verdict === 'rejected' ? 'bg-red-500/20 text-red-400' :
              'bg-yellow-500/20 text-yellow-400'
            }`}>
              Score: {review.score}/10 — {review.verdict === 'approved' ? '✓ Approved' : review.verdict === 'rejected' ? '✗ Rejected' : '⚠ Needs Work'}
            </span>
          </div>
          {review.details && (
            <p className="text-xs text-gray-400">{review.details}</p>
          )}
        </div>
      ))}
    </div>
  );
};

const PayoutDetails: React.FC<{ payout: TimelineStageDetails['payout'] }> = ({ payout }) => {
  if (!payout) return null;
  
  return (
    <div className="mt-3 p-3 bg-green-500/10 border border-green-500/20 rounded-lg">
      <div className="flex items-center gap-2 mb-2">
        <span className="text-green-400 font-bold">{payout.amount} {payout.currency}</span>
        <span className="text-gray-400">→</span>
        <span className="text-gray-300">{payout.recipient}</span>
      </div>
      {payout.transactionHash && (
        <div className="flex items-center gap-2 text-xs">
          <code className="text-gray-500 font-mono truncate flex-1">{payout.transactionHash.slice(0, 20)}...</code>
          {payout.solscanUrl && (
            <a
              href={payout.solscanUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-1 text-blue-400 hover:text-blue-300 transition-colors"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
              </svg>
              <span>View on Solscan</span>
            </a>
          )}
        </div>
      )}
    </div>
  );
};

// Timeline Stage Component
const TimelineStageCard: React.FC<{
  stageDetails: TimelineStageDetails;
  isLast: boolean;
  isExpanded: boolean;
  onToggle: () => void;
}> = ({ stageDetails, isLast, isExpanded, onToggle }) => {
  const config = TIMELINE_STAGE_CONFIG.find(s => s.stage === stageDetails.stage)!;
  const styles = getStageStyles(stageDetails.status, stageDetails.status === 'current');
  const hasDetails = 
    (stageDetails.submissions && stageDetails.submissions.length > 0) ||
    (stageDetails.reviewResults && stageDetails.reviewResults.length > 0) ||
    stageDetails.payout ||
    stageDetails.details;

  return (
    <div className="relative">
      {/* Connector line */}
      {!isLast && (
        <div 
          className={`absolute left-6 top-14 w-0.5 h-full ${styles.connector}`}
          style={{ minHeight: '2rem' }}
        />
      )}
      
      {/* Stage card */}
      <button
        type="button"
        onClick={hasDetails ? onToggle : undefined}
        className={`w-full text-left ${hasDetails ? 'cursor-pointer hover:border-opacity-80' : 'cursor-default'} ${styles.container}`}
        aria-expanded={hasDetails ? isExpanded : undefined}
        aria-label={`${config.defaultTitle}: ${stageDetails.status}`}
      >
        {/* Header */}
        <div className="p-4">
          <div className="flex items-start gap-3">
            {/* Icon */}
            <div className={`text-2xl ${styles.icon} flex-shrink-0`}>
              {config.icon}
            </div>
            
            {/* Content */}
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 flex-wrap">
                <h3 className="font-semibold text-white">
                  {stageDetails.title}
                </h3>
                <span className={`text-xs px-2 py-0.5 rounded-full ${styles.badge}`}>
                  {stageDetails.status.toUpperCase()}
                </span>
              </div>
              
              {stageDetails.description && (
                <p className="text-sm text-gray-400 mt-1">
                  {stageDetails.description}
                </p>
              )}
              
              {stageDetails.date && (
                <p className="text-xs text-gray-500 mt-1">
                  {formatDate(stageDetails.date)} • {formatTimeAgo(stageDetails.date)}
                </p>
              )}
            </div>
            
            {/* Expand indicator */}
            {hasDetails && (
              <div className={`text-gray-500 transition-transform duration-200 ${isExpanded ? 'rotate-180' : ''}`}>
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              </div>
            )}
          </div>
        </div>
        
        {/* Expanded details */}
        {isExpanded && hasDetails && (
          <div className="px-4 pb-4 border-t border-gray-700/50 pt-3">
            {stageDetails.details && (
              <p className="text-sm text-gray-400 mb-3">{stageDetails.details}</p>
            )}
            <SubmissionList submissions={stageDetails.submissions} />
            <ReviewResults results={stageDetails.reviewResults} />
            <PayoutDetails payout={stageDetails.payout} />
          </div>
        )}
      </button>
    </div>
  );
};

// Props interface
export interface BountyTimelineProps {
  bountyId: string;
  data?: BountyTimelineData;
  compact?: boolean;
  showTitle?: boolean;
  onStageClick?: (stage: TimelineStage) => void;
}

// Main Component
export const BountyTimeline: React.FC<BountyTimelineProps> = ({
  bountyId,
  data,
  compact = false,
  showTitle = true,
  onStageClick,
}) => {
  const [expandedStages, setExpandedStages] = useState<Set<TimelineStage>>(new Set());

  // Get timeline data
  const timelineData = useMemo(() => {
    if (data) return data;
    return getTimelineByBountyId(bountyId);
  }, [bountyId, data]);

  // Toggle stage expansion
  const toggleStage = (stage: TimelineStage) => {
    setExpandedStages(prev => {
      const next = new Set(prev);
      if (next.has(stage)) {
        next.delete(stage);
      } else {
        next.add(stage);
      }
      return next;
    });
  };

  // Handle stage click
  const handleStageClick = (stage: TimelineStage) => {
    toggleStage(stage);
    onStageClick?.(stage);
  };

  // Loading state
  if (!timelineData) {
    return (
      <div className="bg-gray-900 rounded-xl p-6 text-center border border-gray-800">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto mb-4" />
        <p className="text-gray-400">Loading timeline...</p>
      </div>
    );
  }

  return (
    <div className={`bg-gray-900 rounded-xl border border-gray-800 ${compact ? 'p-4' : 'p-6'}`}>
      {/* Header */}
      {showTitle && (
        <div className="mb-6 pb-4 border-b border-gray-800">
          <h2 className="text-xl font-bold text-white">Bounty Timeline</h2>
          <p className="text-sm text-gray-400 mt-1">{timelineData.bountyTitle}</p>
          <p className="text-xs text-gray-500 mt-1">Created by {timelineData.creator}</p>
        </div>
      )}
      
      {/* Timeline stages */}
      <div className="space-y-4">
        {timelineData.stages.map((stage, index) => (
          <TimelineStageCard
            key={stage.stage}
            stageDetails={stage}
            isLast={index === timelineData.stages.length - 1}
            isExpanded={expandedStages.has(stage.stage)}
            onToggle={() => handleStageClick(stage.stage)}
          />
        ))}
      </div>
      
      {/* Footer info */}
      {!compact && (
        <div className="mt-6 pt-4 border-t border-gray-800">
          <div className="flex items-center justify-between text-xs text-gray-500">
            <span>Bounty ID: {timelineData.bountyId}</span>
            <span>Current Stage: {timelineData.currentStage}</span>
          </div>
        </div>
      )}
    </div>
  );
};

export default BountyTimeline;