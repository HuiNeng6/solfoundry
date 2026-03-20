'use client';

import React, { useState, useMemo } from 'react';

// Types for Bounty Timeline
export type TimelineStage = 
  | 'created'
  | 'open_for_submissions'
  | 'pr_submitted'
  | 'ai_review'
  | 'approved_merged'
  | 'paid';

export type StageStatus = 'completed' | 'current' | 'pending' | 'skipped';

export interface SubmissionInfo {
  user: string;
  prNumber: number;
  prUrl: string;
}

export interface AIReviewInfo {
  score: number;
  verdict: 'approved' | 'rejected' | 'needs_changes';
  feedback?: string;
}

export interface PayoutInfo {
  amount: number;
  user: string;
  txHash: string;
  txUrl: string;
}

export interface TimelineStageDetails {
  stage: TimelineStage;
  status: StageStatus;
  date?: string;
  details?: string;
  submission?: SubmissionInfo;
  aiReview?: AIReviewInfo;
  payout?: PayoutInfo;
  submissions?: SubmissionInfo[];
  aiReviews?: AIReviewInfo[];
}

export interface BountyTimelineData {
  bountyId: string;
  bountyTitle: string;
  stages: TimelineStageDetails[];
  currentStage: TimelineStage;
  createdBy: string;
  createdAt: string;
}

export interface BountyTimelineProps {
  bountyId: string;
  data?: BountyTimelineData;
  className?: string;
}

// Stage configuration
const STAGE_CONFIG: { stage: TimelineStage; label: string; icon: string; description: string }[] = [
  { stage: 'created', label: 'Created', icon: '📝', description: 'Bounty posted' },
  { stage: 'open_for_submissions', label: 'Open for Submissions', icon: '🏷️', description: 'Accepting PRs' },
  { stage: 'pr_submitted', label: 'PR Submitted', icon: '🔀', description: 'Pull request(s) submitted' },
  { stage: 'ai_review', label: 'AI Review', icon: '🤖', description: 'AI evaluation in progress' },
  { stage: 'approved_merged', label: 'Approved & Merged', icon: '✅', description: 'PR merged successfully' },
  { stage: 'paid', label: 'Paid', icon: '💰', description: 'Reward distributed' },
];

// Status color mapping
const statusColors: Record<StageStatus, { bg: string; text: string; border: string }> = {
  completed: { bg: 'bg-green-500/20', text: 'text-green-400', border: 'border-green-500' },
  current: { bg: 'bg-blue-500/20', text: 'text-blue-400', border: 'border-blue-500' },
  pending: { bg: 'bg-gray-700/50', text: 'text-gray-500', border: 'border-gray-600' },
  skipped: { bg: 'bg-gray-800', text: 'text-gray-600', border: 'border-gray-700' },
};

// Utility function to format date
const formatDate = (date?: string): string => {
  if (!date) return '—';
  const d = new Date(date);
  return d.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
};

// AI Review Badge Component
const AIVerdictBadge: React.FC<{ verdict: AIReviewInfo['verdict'] }> = ({ verdict }) => {
  const colors = {
    approved: 'bg-green-500/20 text-green-400 border-green-500/30',
    rejected: 'bg-red-500/20 text-red-400 border-red-500/30',
    needs_changes: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30',
  };

  return (
    <span className={`px-2 py-0.5 rounded text-xs font-medium border ${colors[verdict]}`}>
      {verdict.replace('_', ' ').toUpperCase()}
    </span>
  );
};

// Submission Detail Component
const SubmissionDetail: React.FC<{ submission: SubmissionInfo }> = ({ submission }) => (
  <a
    href={submission.prUrl}
    target="_blank"
    rel="noopener noreferrer"
    className="flex items-center gap-2 p-2 bg-gray-800 rounded hover:bg-gray-700 transition-colors min-h-[44px]"
  >
    <div className="w-6 h-6 rounded-full bg-purple-500/30 flex items-center justify-center text-xs font-bold text-purple-300">
      {submission.user.charAt(0).toUpperCase()}
    </div>
    <span className="text-sm text-gray-300">{submission.user}</span>
    <span className="text-sm text-blue-400 hover:underline ml-auto">
      PR #{submission.prNumber}
    </span>
  </a>
);

// AI Review Detail Component
const AIReviewDetail: React.FC<{ review: AIReviewInfo; index: number }> = ({ review, index }) => (
  <div className="p-3 bg-gray-800 rounded">
    <div className="flex items-center justify-between mb-2">
      <span className="text-sm text-gray-400">Submission {index + 1}</span>
      <AIVerdictBadge verdict={review.verdict} />
    </div>
    <div className="flex items-center gap-2">
      <span className="text-lg font-bold text-white">Score: {review.score}/10</span>
    </div>
    {review.feedback && (
      <p className="mt-2 text-sm text-gray-400">{review.feedback}</p>
    )}
  </div>
);

// Payout Detail Component
const PayoutDetail: React.FC<{ payout: PayoutInfo }> = ({ payout }) => (
  <div className="p-3 bg-gray-800 rounded">
    <div className="flex items-center gap-2 mb-2">
      <span className="text-lg font-bold text-green-400">
        {payout.amount.toLocaleString()} $FNDRY
      </span>
      <span className="text-sm text-gray-400">sent to {payout.user}</span>
    </div>
    <a
      href={payout.txUrl}
      target="_blank"
      rel="noopener noreferrer"
      className="flex items-center gap-2 text-sm text-blue-400 hover:underline min-h-[44px] px-2 py-1 rounded hover:bg-gray-700"
    >
      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
      </svg>
      <span className="font-mono text-xs truncate">{payout.txHash}</span>
    </a>
  </div>
);

// Timeline Stage Item Component
const TimelineStageItem: React.FC<{
  stageDetails: TimelineStageDetails;
  isLast: boolean;
  isExpanded: boolean;
  onToggle: () => void;
}> = ({ stageDetails, isLast, isExpanded, onToggle }) => {
  const config = STAGE_CONFIG.find(s => s.stage === stageDetails.stage)!;
  const colors = statusColors[stageDetails.status];
  const isCompleted = stageDetails.status === 'completed';
  const isCurrent = stageDetails.status === 'current';
  const hasDetails = stageDetails.submission || stageDetails.aiReview || 
                     stageDetails.payout || (stageDetails.submissions && stageDetails.submissions.length > 0) ||
                     (stageDetails.aiReviews && stageDetails.aiReviews.length > 0);

  return (
    <div className="relative">
      {/* Timeline connector line */}
      {!isLast && (
        <div
          className={`absolute left-5 top-12 w-0.5 h-full ${
            isCompleted ? 'bg-green-500' : 'bg-gray-700'
          }`}
        />
      )}

      {/* Stage content */}
      <button
        onClick={hasDetails ? onToggle : undefined}
        className={`w-full text-left p-4 rounded-lg border-2 transition-all duration-300 ${
          colors.bg
        } ${colors.border} ${
          isCurrent ? 'ring-2 ring-blue-400 ring-offset-2 ring-offset-gray-900 shadow-lg shadow-blue-500/20' : ''
        } ${hasDetails ? 'cursor-pointer hover:border-opacity-100' : 'cursor-default'}`}
      >
        {/* Header */}
        <div className="flex items-center gap-3">
          {/* Icon with status indicator */}
          <div
            className={`relative flex items-center justify-center w-10 h-10 rounded-full ${
              isCompleted ? 'bg-green-500' : isCurrent ? 'bg-blue-500' : 'bg-gray-700'
            } ${isCurrent ? 'animate-pulse' : ''}`}
          >
            <span className="text-xl">
              {isCompleted ? '✓' : config.icon}
            </span>
            {/* Pulse ring for current stage */}
            {isCurrent && (
              <span className="absolute inset-0 rounded-full border-2 border-blue-400 animate-ping opacity-50" />
            )}
          </div>

          {/* Label and status */}
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 flex-wrap">
              <h3 className={`font-semibold ${colors.text}`}>
                {config.label}
              </h3>
              <span className={`px-2 py-0.5 rounded text-xs font-medium ${colors.bg} ${colors.text} border ${colors.border}`}>
                {stageDetails.status.toUpperCase()}
              </span>
            </div>
            <p className="text-sm text-gray-400 mt-1">
              {stageDetails.details || config.description}
            </p>
          </div>

          {/* Expand indicator */}
          {hasDetails && (
            <div className={`transform transition-transform duration-200 ${isExpanded ? 'rotate-180' : ''}`}>
              <svg className={`w-5 h-5 ${colors.text}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
              </svg>
            </div>
          )}
        </div>

        {/* Date */}
        {stageDetails.date && (
          <p className="mt-2 text-xs text-gray-500">
            {formatDate(stageDetails.date)}
          </p>
        )}
      </button>

      {/* Expanded Details */}
      {isExpanded && hasDetails && (
        <div className="mt-2 ml-14 p-3 bg-gray-900/50 rounded-lg border border-gray-700 space-y-2">
          {/* Single submission */}
          {stageDetails.submission && (
            <SubmissionDetail submission={stageDetails.submission} />
          )}

          {/* Multiple submissions */}
          {stageDetails.submissions && stageDetails.submissions.length > 0 && (
            <div className="space-y-2">
              <p className="text-sm font-medium text-gray-300">
                Submissions ({stageDetails.submissions.length})
              </p>
              {stageDetails.submissions.map((sub, idx) => (
                <SubmissionDetail key={idx} submission={sub} />
              ))}
            </div>
          )}

          {/* Single AI review */}
          {stageDetails.aiReview && (
            <AIReviewDetail review={stageDetails.aiReview} index={0} />
          )}

          {/* Multiple AI reviews */}
          {stageDetails.aiReviews && stageDetails.aiReviews.length > 0 && (
            <div className="space-y-2">
              <p className="text-sm font-medium text-gray-300">
                AI Reviews ({stageDetails.aiReviews.length})
              </p>
              {stageDetails.aiReviews.map((review, idx) => (
                <AIReviewDetail key={idx} review={review} index={idx} />
              ))}
            </div>
          )}

          {/* Payout details */}
          {stageDetails.payout && (
            <PayoutDetail payout={stageDetails.payout} />
          )}
        </div>
      )}
    </div>
  );
};

// Mock data generator
const generateMockTimelineData = (bountyId: string): BountyTimelineData => {
  // Return different mock data based on bountyId to show different lifecycle stages
  if (bountyId === 'b-new') {
    // New bounty - just created
    return {
      bountyId,
      bountyTitle: 'New Feature Request',
      currentStage: 'open_for_submissions',
      createdBy: 'SolFoundry',
      createdAt: new Date().toISOString(),
      stages: [
        {
          stage: 'created',
          status: 'completed',
          date: new Date(Date.now() - 86400000).toISOString(),
          details: 'Bounty posted by SolFoundry',
        },
        {
          stage: 'open_for_submissions',
          status: 'current',
          date: new Date().toISOString(),
          details: 'Accepting PRs',
        },
        { stage: 'pr_submitted', status: 'pending' },
        { stage: 'ai_review', status: 'pending' },
        { stage: 'approved_merged', status: 'pending' },
        { stage: 'paid', status: 'pending' },
      ],
    };
  }

  if (bountyId === 'b-progress') {
    // Bounty in progress - PR submitted, under review
    return {
      bountyId,
      bountyTitle: 'Fix escrow token transfer',
      currentStage: 'ai_review',
      createdBy: 'SolFoundry',
      createdAt: new Date(Date.now() - 3 * 86400000).toISOString(),
      stages: [
        {
          stage: 'created',
          status: 'completed',
          date: new Date(Date.now() - 3 * 86400000).toISOString(),
          details: 'Bounty posted by SolFoundry',
        },
        {
          stage: 'open_for_submissions',
          status: 'completed',
          date: new Date(Date.now() - 3 * 86400000).toISOString(),
          details: 'Accepting PRs',
        },
        {
          stage: 'pr_submitted',
          status: 'completed',
          date: new Date(Date.now() - 1 * 86400000).toISOString(),
          details: '2 PRs submitted',
          submissions: [
            { user: 'alice', prNumber: 42, prUrl: 'https://github.com/SolFoundry/solfoundry/pull/42' },
            { user: 'bob', prNumber: 43, prUrl: 'https://github.com/SolFoundry/solfoundry/pull/43' },
          ],
        },
        {
          stage: 'ai_review',
          status: 'current',
          date: new Date().toISOString(),
          details: 'AI evaluating submissions',
          aiReviews: [
            { score: 8, verdict: 'approved', feedback: 'Clean implementation with good test coverage.' },
            { score: 6, verdict: 'needs_changes', feedback: 'Missing edge case handling.' },
          ],
        },
        { stage: 'approved_merged', status: 'pending' },
        { stage: 'paid', status: 'pending' },
      ],
    };
  }

  // Completed bounty (default)
  return {
    bountyId,
    bountyTitle: 'API Documentation',
    currentStage: 'paid',
    createdBy: 'SolFoundry',
    createdAt: new Date(Date.now() - 14 * 86400000).toISOString(),
    stages: [
      {
        stage: 'created',
        status: 'completed',
        date: new Date(Date.now() - 14 * 86400000).toISOString(),
        details: 'Bounty posted by SolFoundry',
      },
      {
        stage: 'open_for_submissions',
        status: 'completed',
        date: new Date(Date.now() - 14 * 86400000).toISOString(),
        details: 'Accepting PRs',
      },
      {
        stage: 'pr_submitted',
        status: 'completed',
        date: new Date(Date.now() - 7 * 86400000).toISOString(),
        details: 'PR submitted by developer42',
        submission: { user: 'developer42', prNumber: 38, prUrl: 'https://github.com/SolFoundry/solfoundry/pull/38' },
      },
      {
        stage: 'ai_review',
        status: 'completed',
        date: new Date(Date.now() - 6 * 86400000).toISOString(),
        details: 'AI review completed',
        aiReview: { score: 9, verdict: 'approved', feedback: 'Excellent documentation with comprehensive examples.' },
      },
      {
        stage: 'approved_merged',
        status: 'completed',
        date: new Date(Date.now() - 5 * 86400000).toISOString(),
        details: 'PR #38 merged successfully',
        submission: { user: 'developer42', prNumber: 38, prUrl: 'https://github.com/SolFoundry/solfoundry/pull/38' },
      },
      {
        stage: 'paid',
        status: 'completed',
        date: new Date(Date.now() - 5 * 86400000).toISOString(),
        details: 'Reward distributed',
        payout: {
          amount: 200000,
          user: 'developer42',
          txHash: '5KtR...x9Ym',
          txUrl: 'https://solscan.io/tx/5KtR...x9Ym',
        },
      },
    ],
  };
};

// Main Component
export const BountyTimeline: React.FC<BountyTimelineProps> = ({
  bountyId,
  data: propData,
  className = '',
}) => {
  const [expandedStages, setExpandedStages] = useState<Set<TimelineStage>>(new Set());

  // Use provided data or generate mock data
  const timelineData = useMemo(() => {
    return propData || generateMockTimelineData(bountyId);
  }, [propData, bountyId]);

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

  // Get stage details by stage type
  const getStageDetails = (stage: TimelineStage): TimelineStageDetails => {
    const found = timelineData.stages.find(s => s.stage === stage);
    if (found) return found;
    // Return default pending stage
    return { stage, status: 'pending' };
  };

  return (
    <div className={`bg-gray-950 rounded-lg p-4 sm:p-6 text-white ${className}`}>
      {/* Header */}
      <div className="mb-6">
        <h2 className="text-xl font-bold flex items-center gap-2">
          <span>🕐</span>
          <span>Bounty Timeline</span>
        </h2>
        <p className="text-sm text-gray-400 mt-1">
          Track the lifecycle of this bounty from creation to payout
        </p>
      </div>

      {/* Timeline */}
      <div className="space-y-4">
        {STAGE_CONFIG.map((config, index) => {
          const stageDetails = getStageDetails(config.stage);
          const isLast = index === STAGE_CONFIG.length - 1;
          const isExpanded = expandedStages.has(config.stage);

          return (
            <TimelineStageItem
              key={config.stage}
              stageDetails={stageDetails}
              isLast={isLast}
              isExpanded={isExpanded}
              onToggle={() => toggleStage(config.stage)}
            />
          );
        })}
      </div>

      {/* Legend */}
      <div className="mt-6 pt-4 border-t border-gray-800">
        <p className="text-xs text-gray-500 mb-2">Status Legend:</p>
        <div className="flex flex-wrap gap-3">
          {Object.entries(statusColors).map(([status, colors]) => (
            <div key={status} className="flex items-center gap-2">
              <div className={`w-3 h-3 rounded-full ${colors.bg} border ${colors.border}`} />
              <span className={`text-xs ${colors.text}`}>
                {status.charAt(0).toUpperCase() + status.slice(1)}
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* Bounty Info */}
      <div className="mt-4 p-3 bg-gray-900 rounded-lg">
        <div className="flex items-center justify-between flex-wrap gap-2">
          <div>
            <p className="text-xs text-gray-500">Bounty ID</p>
            <p className="font-mono text-sm">{timelineData.bountyId}</p>
          </div>
          <div className="text-right">
            <p className="text-xs text-gray-500">Created</p>
            <p className="text-sm">{formatDate(timelineData.createdAt)}</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default BountyTimeline;