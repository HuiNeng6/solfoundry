'use client';

import React, { useState, useEffect, useCallback } from 'react';

// Types for PR Status
export type PRStage = 
  | 'submitted'
  | 'ci_running'
  | 'ai_review'
  | 'human_review'
  | 'approved'
  | 'denied'
  | 'payout';

export type StageStatus = 'pending' | 'running' | 'passed' | 'failed' | 'skipped';

export interface AIReviewScore {
  quality: number;
  correctness: number;
  security: number;
  completeness: number;
  tests: number;
  overall: number;
}

export interface StageDetails {
  status: StageStatus;
  timestamp: string | null;
  duration: number | null; // in seconds
  message?: string;
  // AI Review specific
  scores?: AIReviewScore;
  // Payout specific
  txHash?: string;
  solscanUrl?: string;
  amount?: number;
}

export interface PRStatus {
  prNumber: number;
  prTitle: string;
  prUrl: string;
  author: string;
  bountyId: string;
  bountyTitle: string;
  currentStage: PRStage;
  stages: Record<PRStage, StageDetails>;
  updatedAt: string;
}

// Stage configuration
const STAGE_ORDER: PRStage[] = [
  'submitted',
  'ci_running',
  'ai_review',
  'human_review',
  'approved',
  'payout'
];

const STAGE_LABELS: Record<PRStage, string> = {
  submitted: 'Submitted',
  ci_running: 'CI Running',
  ai_review: 'AI Review',
  human_review: 'Human Review',
  approved: 'Approved',
  denied: 'Denied',
  payout: 'Payout'
};

const STAGE_ICONS: Record<PRStage, React.ReactNode> = {
  submitted: (
    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
    </svg>
  ),
  ci_running: (
    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
    </svg>
  ),
  ai_review: (
    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
    </svg>
  ),
  human_review: (
    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
    </svg>
  ),
  approved: (
    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
  ),
  denied: (
    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
  ),
  payout: (
    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
  )
};

// Status badge component
function StatusBadge({ status }: { status: StageStatus }) {
  const statusStyles: Record<StageStatus, string> = {
    pending: 'bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-300',
    running: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',
    passed: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400',
    failed: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400',
    skipped: 'bg-gray-100 text-gray-400 dark:bg-gray-800 dark:text-gray-500'
  };

  const statusLabels: Record<StageStatus, string> = {
    pending: 'Pending',
    running: 'Running',
    passed: 'Passed',
    failed: 'Failed',
    skipped: 'Skipped'
  };

  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${statusStyles[status]}`}>
      {status === 'running' && (
        <svg className="animate-spin -ml-0.5 mr-1.5 h-3 w-3" fill="none" viewBox="0 0 24 24">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
        </svg>
      )}
      {statusLabels[status]}
    </span>
  );
}

// Score bar component
function ScoreBar({ label, score, maxScore = 10 }: { label: string; score: number; maxScore?: number }) {
  const percentage = (score / maxScore) * 100;
  const getColor = (score: number) => {
    if (score >= 8) return 'bg-green-500';
    if (score >= 6) return 'bg-yellow-500';
    return 'bg-red-500';
  };

  return (
    <div className="flex items-center gap-2">
      <span className="text-xs text-gray-600 dark:text-gray-400 w-24">{label}</span>
      <div className="flex-1 h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
        <div 
          className={`h-full rounded-full transition-all duration-500 ${getColor(score)}`}
          style={{ width: `${percentage}%` }}
        />
      </div>
      <span className="text-xs font-medium text-gray-700 dark:text-gray-300 w-6">{score.toFixed(1)}</span>
    </div>
  );
}

// AI Review scores component
function AIReviewScores({ scores }: { scores: AIReviewScore }) {
  return (
    <div className="mt-4 p-4 bg-gray-50 dark:bg-gray-800/50 rounded-lg space-y-3">
      <h4 className="text-sm font-medium text-gray-900 dark:text-gray-100 mb-3">Score Breakdown</h4>
      <ScoreBar label="Quality" score={scores.quality} />
      <ScoreBar label="Correctness" score={scores.correctness} />
      <ScoreBar label="Security" score={scores.security} />
      <ScoreBar label="Completeness" score={scores.completeness} />
      <ScoreBar label="Tests" score={scores.tests} />
      <div className="pt-3 border-t border-gray-200 dark:border-gray-700">
        <div className="flex items-center justify-between">
          <span className="text-sm font-medium text-gray-900 dark:text-gray-100">Overall Score</span>
          <span className={`text-lg font-bold ${
            scores.overall >= 8 ? 'text-green-600 dark:text-green-400' :
            scores.overall >= 6 ? 'text-yellow-600 dark:text-yellow-400' :
            'text-red-600 dark:text-red-400'
          }`}>
            {scores.overall.toFixed(1)}/10
          </span>
        </div>
      </div>
    </div>
  );
}

// Payout details component
function PayoutDetails({ txHash, solscanUrl, amount }: { txHash?: string; solscanUrl?: string; amount?: number }) {
  if (!txHash) return null;

  return (
    <div className="mt-4 p-4 bg-green-50 dark:bg-green-900/20 rounded-lg">
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm font-medium text-gray-900 dark:text-gray-100">Amount</span>
        <span className="text-lg font-bold text-green-600 dark:text-green-400">
          {amount?.toLocaleString() ?? 0} $FNDRY
        </span>
      </div>
      <div className="space-y-1">
        <div className="flex items-center gap-2">
          <span className="text-xs text-gray-600 dark:text-gray-400">Tx Hash:</span>
          <code className="text-xs text-gray-900 dark:text-gray-100 font-mono truncate flex-1">
            {txHash}
          </code>
        </div>
        {solscanUrl && (
          <a 
            href={solscanUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1 text-sm text-blue-600 dark:text-blue-400 hover:underline"
          >
            View on Solscan
            <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
            </svg>
          </a>
        )}
      </div>
    </div>
  );
}

// Stage card component
function StageCard({ 
  stage, 
  details, 
  isActive, 
  isPast,
  isDenied 
}: { 
  stage: PRStage; 
  details: StageDetails; 
  isActive: boolean;
  isPast: boolean;
  isDenied: boolean;
}) {
  // Skip denied stage in normal flow
  if (stage === 'denied' && !isDenied) return null;
  
  // Skip approved/payout if denied
  if (isDenied && (stage === 'approved' || stage === 'payout')) return null;

  const getBorderColor = () => {
    if (isActive) return 'border-blue-500 dark:border-blue-400 ring-2 ring-blue-500/20';
    if (details.status === 'passed') return 'border-green-500 dark:border-green-400';
    if (details.status === 'failed') return 'border-red-500 dark:border-red-400';
    return 'border-gray-200 dark:border-gray-700';
  };

  return (
    <div className={`relative bg-white dark:bg-gray-800 rounded-lg border-2 p-4 transition-all duration-300 ${getBorderColor()}`}>
      {/* Connector line */}
      {!isPast && STAGE_ORDER.indexOf(stage) < STAGE_ORDER.length - 1 && (
        <div className="absolute left-1/2 -bottom-6 w-0.5 h-4 bg-gray-200 dark:bg-gray-700 transform -translate-x-1/2" />
      )}

      {/* Header */}
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          <span className={`${
            isActive ? 'text-blue-600 dark:text-blue-400' :
            details.status === 'passed' ? 'text-green-600 dark:text-green-400' :
            details.status === 'failed' ? 'text-red-600 dark:text-red-400' :
            'text-gray-400 dark:text-gray-500'
          }`}>
            {STAGE_ICONS[stage]}
          </span>
          <span className={`font-medium ${
            isActive ? 'text-gray-900 dark:text-gray-100' :
            'text-gray-600 dark:text-gray-400'
          }`}>
            {STAGE_LABELS[stage]}
          </span>
        </div>
        <StatusBadge status={details.status} />
      </div>

      {/* Timestamp and duration */}
      {details.timestamp && (
        <div className="flex items-center gap-4 text-xs text-gray-500 dark:text-gray-400 mb-2">
          <span>{new Date(details.timestamp).toLocaleString()}</span>
          {details.duration && (
            <span>({Math.floor(details.duration / 60)}m {details.duration % 60}s)</span>
          )}
        </div>
      )}

      {/* Message */}
      {details.message && (
        <p className="text-sm text-gray-600 dark:text-gray-400">{details.message}</p>
      )}

      {/* AI Review scores */}
      {stage === 'ai_review' && details.scores && details.status === 'passed' && (
        <AIReviewScores scores={details.scores} />
      )}

      {/* Payout details */}
      {stage === 'payout' && details.txHash && (
        <PayoutDetails 
          txHash={details.txHash}
          solscanUrl={details.solscanUrl}
          amount={details.amount}
        />
      )}
    </div>
  );
}

// Main PR Status Tracker Component
interface PRStatusTrackerProps {
  prNumber: number;
  bountyId?: string;
  websocketUrl?: string;
  className?: string;
}

export function PRStatusTracker({ 
  prNumber, 
  bountyId,
  websocketUrl = 'ws://localhost:8000/api/ws/pr-status',
  className = '' 
}: PRStatusTrackerProps) {
  const [status, setStatus] = useState<PRStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [wsConnected, setWsConnected] = useState(false);

  // Fetch initial status
  const fetchStatus = useCallback(async () => {
    try {
      const response = await fetch(`/api/pr-status/${prNumber}`);
      if (!response.ok) throw new Error('Failed to fetch PR status');
      const data = await response.json();
      setStatus(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  }, [prNumber]);

  // WebSocket connection for real-time updates
  useEffect(() => {
    fetchStatus();

    const ws = new WebSocket(`${websocketUrl}/${prNumber}`);

    ws.onopen = () => {
      setWsConnected(true);
      console.log('WebSocket connected for PR', prNumber);
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.pr_number === prNumber) {
        setStatus(data);
      }
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      setWsConnected(false);
    };

    ws.onclose = () => {
      setWsConnected(false);
      console.log('WebSocket disconnected');
    };

    return () => {
      ws.close();
    };
  }, [prNumber, websocketUrl, fetchStatus]);

  if (loading) {
    return (
      <div className={`animate-pulse ${className}`}>
        <div className="h-32 bg-gray-200 dark:bg-gray-700 rounded-lg"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={`p-4 bg-red-50 dark:bg-red-900/20 rounded-lg ${className}`}>
        <p className="text-sm text-red-600 dark:text-red-400">{error}</p>
      </div>
    );
  }

  if (!status) {
    return (
      <div className={`p-4 bg-gray-50 dark:bg-gray-800 rounded-lg ${className}`}>
        <p className="text-sm text-gray-600 dark:text-gray-400">No status found</p>
      </div>
    );
  }

  const currentStageIndex = STAGE_ORDER.indexOf(status.currentStage);
  const isDenied = status.currentStage === 'denied';

  return (
    <div className={`${className}`}>
      {/* Header */}
      <div className="flex items-start justify-between mb-6">
        <div>
          <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
            PR #{status.prNumber} Status
          </h3>
          <a 
            href={status.prUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="text-sm text-blue-600 dark:text-blue-400 hover:underline"
          >
            {status.prTitle}
          </a>
          <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
            by <span className="font-medium">{status.author}</span>
          </p>
        </div>
        <div className="flex items-center gap-2">
          {wsConnected && (
            <span className="flex items-center gap-1 text-xs text-green-600 dark:text-green-400">
              <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></span>
              Live
            </span>
          )}
          <span className="text-xs text-gray-500 dark:text-gray-400">
            Updated: {new Date(status.updatedAt).toLocaleTimeString()}
          </span>
        </div>
      </div>

      {/* Bounty info */}
      {status.bountyTitle && (
        <div className="mb-4 p-3 bg-gray-50 dark:bg-gray-800/50 rounded-lg">
          <span className="text-xs text-gray-500 dark:text-gray-400">Bounty:</span>
          <span className="ml-2 text-sm font-medium text-gray-900 dark:text-gray-100">
            {status.bountyTitle}
          </span>
        </div>
      )}

      {/* Pipeline visualization */}
      <div className="space-y-6">
        {STAGE_ORDER.map((stage, index) => {
          const details = status.stages[stage];
          const isActive = stage === status.currentStage;
          const isPast = index < currentStageIndex;

          return (
            <StageCard
              key={stage}
              stage={stage}
              details={details}
              isActive={isActive}
              isPast={isPast}
              isDenied={isDenied}
            />
          );
        })}

        {/* Denied stage (shown when PR is denied) */}
        {isDenied && (
          <StageCard
            stage="denied"
            details={status.stages.denied}
            isActive={true}
            isPast={false}
            isDenied={true}
          />
        )}
      </div>
    </div>
  );
}

export default PRStatusTracker;