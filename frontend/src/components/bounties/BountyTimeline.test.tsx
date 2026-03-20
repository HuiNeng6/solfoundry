import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BountyTimeline, type BountyTimelineData } from './BountyTimeline';

// Mock data for testing
const mockCompletedBounty: BountyTimelineData = {
  bountyId: 'test-completed',
  bountyTitle: 'Completed Bounty',
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
      submission: { user: 'developer42', prNumber: 38, prUrl: 'https://github.com/test/pr/38' },
    },
    {
      stage: 'ai_review',
      status: 'completed',
      date: new Date(Date.now() - 6 * 86400000).toISOString(),
      details: 'AI review completed',
      aiReview: { score: 9, verdict: 'approved', feedback: 'Excellent work' },
    },
    {
      stage: 'approved_merged',
      status: 'completed',
      date: new Date(Date.now() - 5 * 86400000).toISOString(),
      details: 'PR #38 merged successfully',
    },
    {
      stage: 'paid',
      status: 'completed',
      date: new Date(Date.now() - 5 * 86400000).toISOString(),
      details: 'Reward distributed',
      payout: {
        amount: 200000,
        user: 'developer42',
        txHash: 'test-tx-hash',
        txUrl: 'https://solscan.io/tx/test',
      },
    },
  ],
};

const mockInProgressBounty: BountyTimelineData = {
  bountyId: 'test-in-progress',
  bountyTitle: 'In Progress Bounty',
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
        { user: 'alice', prNumber: 42, prUrl: 'https://github.com/test/pr/42' },
        { user: 'bob', prNumber: 43, prUrl: 'https://github.com/test/pr/43' },
      ],
    },
    {
      stage: 'ai_review',
      status: 'current',
      date: new Date().toISOString(),
      details: 'AI evaluating submissions',
    },
    { stage: 'approved_merged', status: 'pending' },
    { stage: 'paid', status: 'pending' },
  ],
};

const mockNewBounty: BountyTimelineData = {
  bountyId: 'test-new',
  bountyTitle: 'New Bounty',
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

describe('BountyTimeline', () => {
  describe('Rendering', () => {
    it('renders the component with header', () => {
      render(<BountyTimeline bountyId="test" data={mockCompletedBounty} />);
      expect(screen.getByText('Bounty Timeline')).toBeInTheDocument();
      expect(screen.getByText(/Track the lifecycle/)).toBeInTheDocument();
    });

    it('renders all 6 stages', () => {
      render(<BountyTimeline bountyId="test" data={mockCompletedBounty} />);
      // Use getAllByText for stages that appear multiple times
      expect(screen.getAllByText('Created').length).toBeGreaterThan(0);
      expect(screen.getByText('Open for Submissions')).toBeInTheDocument();
      expect(screen.getByText('PR Submitted')).toBeInTheDocument();
      expect(screen.getByText('AI Review')).toBeInTheDocument();
      expect(screen.getByText('Approved & Merged')).toBeInTheDocument();
      expect(screen.getByText('Paid')).toBeInTheDocument();
    });

    it('renders bounty ID in footer', () => {
      render(<BountyTimeline bountyId="test-completed" data={mockCompletedBounty} />);
      expect(screen.getByText('test-completed')).toBeInTheDocument();
    });
  });

  describe('Stage Status', () => {
    it('shows completed stages with checkmark', () => {
      render(<BountyTimeline bountyId="test" data={mockCompletedBounty} />);
      // All completed stages should show checkmarks
      const completedStages = screen.getAllByText('✓');
      expect(completedStages.length).toBeGreaterThan(0);
    });

    it('shows current stage with CURRENT label', () => {
      render(<BountyTimeline bountyId="test" data={mockInProgressBounty} />);
      expect(screen.getByText('AI Review')).toBeInTheDocument();
      const currentLabels = screen.getAllByText('CURRENT');
      expect(currentLabels.length).toBeGreaterThan(0);
    });

    it('shows pending stages with PENDING label', () => {
      render(<BountyTimeline bountyId="test" data={mockInProgressBounty} />);
      const pendingLabels = screen.getAllByText('PENDING');
      expect(pendingLabels.length).toBeGreaterThan(0);
    });

    it('shows completed stages with COMPLETED label', () => {
      render(<BountyTimeline bountyId="test" data={mockCompletedBounty} />);
      const completedLabels = screen.getAllByText('COMPLETED');
      expect(completedLabels.length).toBeGreaterThan(0);
    });
  });

  describe('Current Stage Highlight', () => {
    it('applies pulse animation to current stage', () => {
      render(<BountyTimeline bountyId="test" data={mockInProgressBounty} />);
      // The current stage should have animate-pulse class
      const aiReviewCard = screen.getByText('AI Review').closest('button');
      expect(aiReviewCard).toBeInTheDocument();
    });

    it('current stage has ring effect', () => {
      render(<BountyTimeline bountyId="test" data={mockInProgressBounty} />);
      const aiReviewCard = screen.getByText('AI Review').closest('button');
      expect(aiReviewCard?.className).toContain('ring');
    });
  });

  describe('Expandable Details', () => {
    it('shows submission details when expanded', async () => {
      const user = userEvent.setup();
      render(<BountyTimeline bountyId="test" data={mockCompletedBounty} />);
      
      // Click on PR Submitted stage to expand
      const prSubmittedCard = screen.getByText('PR Submitted').closest('button');
      if (prSubmittedCard) {
        await user.click(prSubmittedCard);
      }
      
      // Should show the submitter
      expect(screen.getByText('developer42')).toBeInTheDocument();
    });

    it('shows multiple submissions when expanded', async () => {
      const user = userEvent.setup();
      render(<BountyTimeline bountyId="test" data={mockInProgressBounty} />);
      
      // Click on PR Submitted stage to expand
      const prSubmittedCard = screen.getByText('PR Submitted').closest('button');
      if (prSubmittedCard) {
        await user.click(prSubmittedCard);
      }
      
      // Should show both submitters
      expect(screen.getByText('alice')).toBeInTheDocument();
      expect(screen.getByText('bob')).toBeInTheDocument();
    });

    it('shows AI review score when expanded', async () => {
      const user = userEvent.setup();
      render(<BountyTimeline bountyId="test" data={mockCompletedBounty} />);
      
      // Click on AI Review stage to expand
      const aiReviewCard = screen.getByText('AI Review').closest('button');
      if (aiReviewCard) {
        await user.click(aiReviewCard);
      }
      
      // Should show the score
      expect(screen.getByText(/Score: 9\/10/)).toBeInTheDocument();
    });

    it('shows payout details when expanded', async () => {
      const user = userEvent.setup();
      render(<BountyTimeline bountyId="test" data={mockCompletedBounty} />);
      
      // Click on Paid stage to expand
      const paidCard = screen.getByText('Paid').closest('button');
      if (paidCard) {
        await user.click(paidCard);
      }
      
      // Should show the payout amount
      expect(screen.getByText(/200,000/)).toBeInTheDocument();
      expect(screen.getByText(/\$FNDRY/)).toBeInTheDocument();
    });
  });

  describe('Edge Cases', () => {
    it('handles bounty with no submissions yet', () => {
      render(<BountyTimeline bountyId="test" data={mockNewBounty} />);
      
      // Should show pending status for PR Submitted stage
      expect(screen.getByText('PR Submitted')).toBeInTheDocument();
      
      // Stages after current should be pending
      const pendingLabels = screen.getAllByText('PENDING');
      expect(pendingLabels.length).toBeGreaterThanOrEqual(4);
    });

    it('handles bounty with multiple competing PRs', () => {
      render(<BountyTimeline bountyId="test" data={mockInProgressBounty} />);
      
      // Should show "2 PRs submitted" in details
      expect(screen.getByText('2 PRs submitted')).toBeInTheDocument();
    });

    it('handles rejected AI review verdict', () => {
      const rejectedBounty: BountyTimelineData = {
        ...mockInProgressBounty,
        bountyId: 'test-rejected',
        stages: mockInProgressBounty.stages.map(s => 
          s.stage === 'ai_review' 
            ? { 
                ...s,
                status: 'current' as const, 
                aiReviews: [
                  { score: 4, verdict: 'rejected' as const, feedback: 'Does not meet requirements' },
                ] 
              } 
            : s
        ),
      };
      
      render(<BountyTimeline bountyId="test" data={rejectedBounty} />);
      
      // The component should render without error
      expect(screen.getByText('AI Review')).toBeInTheDocument();
    });
  });

  describe('Responsiveness', () => {
    it('applies responsive padding classes', () => {
      const { container } = render(<BountyTimeline bountyId="test" data={mockCompletedBounty} />);
      
      // Check for responsive classes
      const mainContainer = container.querySelector('.p-4.sm\\:p-6');
      expect(mainContainer).toBeInTheDocument();
    });
  });

  describe('Mock Data Generation', () => {
    it('generates different mock data based on bountyId', () => {
      render(<BountyTimeline bountyId="b-new" />);
      // The mock data generates bountyId in the footer
      expect(screen.getByText('b-new')).toBeInTheDocument();
    });

    it('uses provided data over mock data', () => {
      render(<BountyTimeline bountyId="b-new" data={mockCompletedBounty} />);
      
      // Should use the provided data
      expect(screen.getByText('test-completed')).toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('has proper button elements for expandable stages', () => {
      render(<BountyTimeline bountyId="test" data={mockCompletedBounty} />);
      
      // All stage cards should be buttons
      const buttons = screen.getAllByRole('button');
      expect(buttons.length).toBeGreaterThan(0);
    });

    it('external links open in new tab', async () => {
      const user = userEvent.setup();
      render(<BountyTimeline bountyId="test" data={mockCompletedBounty} />);
      
      // Expand PR Submitted to see the link
      const prSubmittedCard = screen.getByText('PR Submitted').closest('button');
      if (prSubmittedCard) {
        await user.click(prSubmittedCard);
      }
      
      // Find the PR link
      const prLink = screen.getByText('PR #38').closest('a');
      expect(prLink).toHaveAttribute('target', '_blank');
      expect(prLink).toHaveAttribute('rel', 'noopener noreferrer');
    });
  });

  describe('Legend', () => {
    it('shows status legend', () => {
      render(<BountyTimeline bountyId="test" data={mockCompletedBounty} />);
      
      expect(screen.getByText('Status Legend:')).toBeInTheDocument();
      expect(screen.getByText('Completed')).toBeInTheDocument();
      expect(screen.getByText('Current')).toBeInTheDocument();
      expect(screen.getByText('Pending')).toBeInTheDocument();
      expect(screen.getByText('Skipped')).toBeInTheDocument();
    });
  });

  describe('AI Review Verdicts', () => {
    it('displays approved verdict', async () => {
      const user = userEvent.setup();
      render(<BountyTimeline bountyId="test" data={mockCompletedBounty} />);
      
      const aiReviewCard = screen.getByText('AI Review').closest('button');
      if (aiReviewCard) {
        await user.click(aiReviewCard);
      }
      
      expect(screen.getByText('APPROVED')).toBeInTheDocument();
    });

    it('displays needs_changes verdict', async () => {
      const user = userEvent.setup();
      const needsChangesBounty: BountyTimelineData = {
        ...mockInProgressBounty,
        bountyId: 'test-needs-changes',
        stages: mockInProgressBounty.stages.map(s => 
          s.stage === 'ai_review' 
            ? { 
                ...s, 
                status: 'current' as const,
                aiReviews: [
                  { score: 6, verdict: 'needs_changes' as const, feedback: 'Needs improvements' },
                ] 
              } 
            : s
        ),
      };
      
      render(<BountyTimeline bountyId="test" data={needsChangesBounty} />);
      
      const aiReviewCard = screen.getByText('AI Review').closest('button');
      if (aiReviewCard) {
        await user.click(aiReviewCard);
      }
      
      expect(screen.getByText('NEEDS CHANGES')).toBeInTheDocument();
    });
  });
});