/**
 * Mock Timeline Data
 * 
 * 3 sample bounties at different lifecycle stages:
 * 1. Early stage - just created, open for submissions
 * 2. Mid stage - has PRs submitted, under AI review
 * 3. Completed - approved and paid
 */

import type { BountyTimelineData } from '../types/timeline';

// Helper to generate dates
const daysAgo = (days: number): string => 
  new Date(Date.now() - days * 864e5).toISOString();

const hoursAgo = (hours: number): string => 
  new Date(Date.now() - hours * 36e5).toISOString();

/**
 * Bounty 1: Early Stage - Just Created
 * Stage: Open for Submissions
 */
export const timelineEarlyStage: BountyTimelineData = {
  bountyId: 'b-early-001',
  bountyTitle: 'Fix escrow token transfer edge case',
  creator: 'SolFoundry',
  currentStage: 'open',
  stages: [
    {
      stage: 'created',
      status: 'completed',
      date: daysAgo(2),
      title: 'Bounty posted by SolFoundry',
      description: 'Tier 1 Bounty — Open Race',
      details: 'The program panics on closed accounts. Identify the root cause, write a reproducer, and submit a fix.',
    },
    {
      stage: 'open',
      status: 'current',
      date: daysAgo(2),
      title: 'Accepting PRs',
      description: 'Open for submissions',
      details: 'Reward: 350 $FNDRY • Deadline in 5 days',
    },
    {
      stage: 'pr_submitted',
      status: 'pending',
      title: 'PR Submitted',
      description: 'No submissions yet',
    },
    {
      stage: 'ai_review',
      status: 'pending',
      title: 'AI Review',
      description: 'Pending submission',
    },
    {
      stage: 'approved',
      status: 'pending',
      title: 'Approved & Merged',
      description: 'Pending review',
    },
    {
      stage: 'paid',
      status: 'pending',
      title: 'Paid',
      description: 'Pending approval',
    },
  ],
};

/**
 * Bounty 2: Mid Stage - Multiple PRs Under Review
 * Stage: AI Review (with competing PRs)
 */
export const timelineMidStage: BountyTimelineData = {
  bountyId: 'b-mid-002',
  bountyTitle: 'Build staking dashboard',
  creator: 'StakePro',
  currentStage: 'ai_review',
  stages: [
    {
      stage: 'created',
      status: 'completed',
      date: daysAgo(7),
      title: 'Bounty posted by StakePro',
      description: 'Tier 2 Bounty — Assigned',
      details: 'Staking UI showing total staked, APY, staking history, and a stake/unstake interface.',
    },
    {
      stage: 'open',
      status: 'completed',
      date: daysAgo(7),
      title: 'Accepting PRs',
      description: 'Open for submissions',
      details: '5 submissions received',
    },
    {
      stage: 'pr_submitted',
      status: 'completed',
      date: daysAgo(3),
      title: '5 PRs submitted',
      description: 'Multiple competing submissions',
      submissions: [
        { prNumber: 142, author: 'alice_dev', submittedAt: daysAgo(3), status: 'in_review', url: 'https://github.com/example/pr/142' },
        { prNumber: 145, author: 'bob_coder', submittedAt: daysAgo(2), status: 'in_review', url: 'https://github.com/example/pr/145' },
        { prNumber: 148, author: 'charlie_sol', submittedAt: daysAgo(1), status: 'pending', url: 'https://github.com/example/pr/148' },
        { prNumber: 150, author: 'diana_rust', submittedAt: hoursAgo(12), status: 'pending', url: 'https://github.com/example/pr/150' },
        { prNumber: 152, author: 'eve_anchor', submittedAt: hoursAgo(5), status: 'pending', url: 'https://github.com/example/pr/152' },
      ],
    },
    {
      stage: 'ai_review',
      status: 'current',
      date: hoursAgo(4),
      title: 'AI Review in Progress',
      description: 'Evaluating submissions',
      reviewResults: [
        { prNumber: 142, score: 7.5, verdict: 'needs_work', reviewedAt: hoursAgo(2), details: 'Missing error handling for edge cases' },
        { prNumber: 145, score: 8.2, verdict: 'approved', reviewedAt: hoursAgo(1), details: 'Good implementation, minor style issues' },
      ],
    },
    {
      stage: 'approved',
      status: 'pending',
      title: 'Approved & Merged',
      description: 'Pending final selection',
    },
    {
      stage: 'paid',
      status: 'pending',
      title: 'Paid',
      description: 'Pending merge',
    },
  ],
};

/**
 * Bounty 3: Completed - Approved and Paid
 * Stage: Paid (full lifecycle completed)
 */
export const timelineCompleted: BountyTimelineData = {
  bountyId: 'b-done-003',
  bountyTitle: 'API Documentation Generation',
  creator: 'SolFoundry',
  currentStage: 'paid',
  stages: [
    {
      stage: 'created',
      status: 'completed',
      date: daysAgo(14),
      title: 'Bounty posted by SolFoundry',
      description: 'Tier 1 Bounty — Open Race',
      details: 'Generate comprehensive OpenAPI documentation for all backend endpoints.',
    },
    {
      stage: 'open',
      status: 'completed',
      date: daysAgo(14),
      title: 'Accepting PRs',
      description: 'Was open for 7 days',
      details: '4 submissions received',
    },
    {
      stage: 'pr_submitted',
      status: 'completed',
      date: daysAgo(10),
      title: 'PR #138 submitted',
      description: 'by developer_zen',
      author: 'developer_zen',
      prNumber: 138,
      prUrl: 'https://github.com/SolFoundry/solfoundry/pull/138',
      submissions: [
        { prNumber: 135, author: 'fast_coder', submittedAt: daysAgo(12), status: 'rejected', url: 'https://github.com/example/pr/135' },
        { prNumber: 136, author: 'api_wizard', submittedAt: daysAgo(11), status: 'rejected', url: 'https://github.com/example/pr/136' },
        { prNumber: 137, author: 'doc_master', submittedAt: daysAgo(10), status: 'rejected', url: 'https://github.com/example/pr/137' },
        { prNumber: 138, author: 'developer_zen', submittedAt: daysAgo(10), status: 'approved', url: 'https://github.com/SolFoundry/solfoundry/pull/138' },
      ],
    },
    {
      stage: 'ai_review',
      status: 'completed',
      date: daysAgo(8),
      title: 'AI Review Completed',
      description: 'Score: 9.2/10 — Approved',
      reviewResults: [
        { prNumber: 135, score: 5.8, verdict: 'rejected', reviewedAt: daysAgo(11), details: 'Incomplete coverage' },
        { prNumber: 136, score: 6.5, verdict: 'needs_work', reviewedAt: daysAgo(10), details: 'Missing auth endpoints' },
        { prNumber: 137, score: 7.8, verdict: 'needs_work', reviewedAt: daysAgo(9), details: 'Missing rate limit docs' },
        { prNumber: 138, score: 9.2, verdict: 'approved', reviewedAt: daysAgo(8), details: 'Comprehensive and well-structured' },
      ],
    },
    {
      stage: 'approved',
      status: 'completed',
      date: daysAgo(5),
      title: 'PR #138 merged',
      description: 'Approved and merged to main',
      details: 'Merged by maintainer after final review',
    },
    {
      stage: 'paid',
      status: 'completed',
      date: daysAgo(4),
      title: '200 $FNDRY sent to developer_zen',
      description: 'Payment confirmed',
      payout: {
        amount: 200,
        currency: '$FNDRY',
        recipient: 'developer_zen',
        transactionHash: '5Xy8ZqW2vN3mK7jR9pL4tS6uH8fB1cD2eA3gF5iJ0kM',
        solscanUrl: 'https://solscan.io/tx/5Xy8ZqW2vN3mK7jR9pL4tS6uH8fB1cD2eA3gF5iJ0kM',
        paidAt: daysAgo(4),
      },
    },
  ],
};

/**
 * Bounty 4: Rejected - Failed AI Review
 * Edge case: bounty with rejected submissions
 */
export const timelineRejected: BountyTimelineData = {
  bountyId: 'b-rejected-004',
  bountyTitle: 'Security Vulnerability Fix',
  creator: 'SecureSol',
  currentStage: 'ai_review',
  stages: [
    {
      stage: 'created',
      status: 'completed',
      date: daysAgo(5),
      title: 'Bounty posted by SecureSol',
      description: 'Tier 3 Bounty — Elite',
      details: 'Critical security vulnerability in token program. Must be fixed urgently.',
    },
    {
      stage: 'open',
      status: 'completed',
      date: daysAgo(5),
      title: 'Accepting PRs',
      description: 'Open for submissions',
      details: '1 submission received',
    },
    {
      stage: 'pr_submitted',
      status: 'completed',
      date: daysAgo(2),
      title: 'PR #201 submitted',
      description: 'by security_expert',
      author: 'security_expert',
      prNumber: 201,
      submissions: [
        { prNumber: 201, author: 'security_expert', submittedAt: daysAgo(2), status: 'rejected', url: 'https://github.com/example/pr/201' },
      ],
    },
    {
      stage: 'ai_review',
      status: 'current',
      date: daysAgo(1),
      title: 'AI Review Completed',
      description: 'Score: 4.5/10 — Rejected',
      reviewResults: [
        { 
          prNumber: 201, 
          score: 4.5, 
          verdict: 'rejected', 
          reviewedAt: daysAgo(1), 
          details: 'Introduced new vulnerabilities. Failed security audit. Does not address root cause.' 
        },
      ],
    },
    {
      stage: 'approved',
      status: 'pending',
      title: 'Approved & Merged',
      description: 'Awaiting new submission',
    },
    {
      stage: 'paid',
      status: 'pending',
      title: 'Paid',
      description: 'Pending approval',
    },
  ],
};

// Export all mock timelines
export const mockTimelines: BountyTimelineData[] = [
  timelineEarlyStage,
  timelineMidStage,
  timelineCompleted,
  timelineRejected,
];

// Helper to get timeline by bounty ID
export const getTimelineByBountyId = (bountyId: string): BountyTimelineData | undefined => 
  mockTimelines.find(t => t.bountyId === bountyId);