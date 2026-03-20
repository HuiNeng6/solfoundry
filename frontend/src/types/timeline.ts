/**
 * Timeline Types for Bounty Lifecycle
 * 
 * Represents the full lifecycle of a bounty from creation to payout
 */

export type TimelineStage = 
  | 'created'
  | 'open'
  | 'pr_submitted'
  | 'ai_review'
  | 'approved'
  | 'paid';

export type TimelineStageStatus = 'completed' | 'current' | 'pending';

export interface PRSubmission {
  prNumber: number;
  author: string;
  url?: string;
  submittedAt: string;
  status: 'pending' | 'in_review' | 'approved' | 'rejected';
}

export interface AIReviewResult {
  prNumber: number;
  score: number;  // 0-10
  verdict: 'approved' | 'needs_work' | 'rejected';
  reviewedAt: string;
  details?: string;
}

export interface PayoutInfo {
  amount: number;
  currency: string;
  recipient: string;
  transactionHash?: string;
  solscanUrl?: string;
  paidAt: string;
}

export interface TimelineStageDetails {
  stage: TimelineStage;
  status: TimelineStageStatus;
  date?: string;
  title: string;
  description?: string;
  details?: string;
  // Stage-specific data
  prNumber?: number;
  author?: string;
  prUrl?: string;
  submissions?: PRSubmission[];
  reviewResults?: AIReviewResult[];
  payout?: PayoutInfo;
}

export interface BountyTimelineData {
  bountyId: string;
  bountyTitle: string;
  creator: string;
  stages: TimelineStageDetails[];
  currentStage: TimelineStage;
}

// Stage configuration for rendering
export const TIMELINE_STAGE_CONFIG: { stage: TimelineStage; icon: string; defaultTitle: string }[] = [
  { stage: 'created', icon: '📝', defaultTitle: 'Created' },
  { stage: 'open', icon: '🏷️', defaultTitle: 'Open for Submissions' },
  { stage: 'pr_submitted', icon: '🔀', defaultTitle: 'PR Submitted' },
  { stage: 'ai_review', icon: '🤖', defaultTitle: 'AI Review' },
  { stage: 'approved', icon: '✅', defaultTitle: 'Approved & Merged' },
  { stage: 'paid', icon: '💰', defaultTitle: 'Paid' },
];