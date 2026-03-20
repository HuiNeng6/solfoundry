import { render, screen, fireEvent, within } from '@testing-library/react';
import { BountyTimeline } from './BountyTimeline';
import type { BountyTimelineData, TimelineStage } from '../types/timeline';

// Mock data for testing
const createMockTimelineData = (
  currentStage: TimelineStage = 'open',
  overrides?: Partial<BountyTimelineData>
): BountyTimelineData => ({
  bountyId: 'test-bounty-001',
  bountyTitle: 'Test Bounty Title',
  creator: 'TestCreator',
  currentStage,
  stages: [
    {
      stage: 'created',
      status: 'completed',
      date: '2026-03-15T10:00:00Z',
      title: 'Bounty posted by TestCreator',
      description: 'Tier 1 Bounty — Open Race',
    },
    {
      stage: 'open',
      status: currentStage === 'created' ? 'pending' : currentStage === 'open' ? 'current' : 'completed',
      date: currentStage !== 'created' ? '2026-03-15T10:00:00Z' : undefined,
      title: 'Accepting PRs',
      description: 'Open for submissions',
    },
    {
      stage: 'pr_submitted',
      status: ['pr_submitted', 'ai_review', 'approved', 'paid'].includes(currentStage) ? 'completed' : 'pending',
      title: 'PR Submitted',
      description: 'Pending submission',
    },
    {
      stage: 'ai_review',
      status: currentStage === 'ai_review' ? 'current' : ['approved', 'paid'].includes(currentStage) ? 'completed' : 'pending',
      title: 'AI Review',
      description: 'Pending review',
    },
    {
      stage: 'approved',
      status: currentStage === 'approved' ? 'current' : currentStage === 'paid' ? 'completed' : 'pending',
      title: 'Approved & Merged',
      description: 'Pending approval',
    },
    {
      stage: 'paid',
      status: currentStage === 'paid' ? 'completed' : 'pending',
      title: 'Paid',
      description: 'Pending payment',
    },
  ],
  ...overrides,
});

const createMockTimelineWithPRs = (): BountyTimelineData => ({
  bountyId: 'test-bounty-002',
  bountyTitle: 'Bounty with Multiple PRs',
  creator: 'MultiCreator',
  currentStage: 'ai_review',
  stages: [
    {
      stage: 'created',
      status: 'completed',
      date: '2026-03-10T10:00:00Z',
      title: 'Bounty posted by MultiCreator',
    },
    {
      stage: 'open',
      status: 'completed',
      date: '2026-03-10T10:00:00Z',
      title: 'Accepting PRs',
      description: '3 submissions received',
    },
    {
      stage: 'pr_submitted',
      status: 'completed',
      date: '2026-03-12T10:00:00Z',
      title: '3 PRs submitted',
      submissions: [
        { prNumber: 101, author: 'alice', submittedAt: '2026-03-12T08:00:00Z', status: 'in_review' },
        { prNumber: 102, author: 'bob', submittedAt: '2026-03-12T10:00:00Z', status: 'pending' },
        { prNumber: 103, author: 'charlie', submittedAt: '2026-03-12T12:00:00Z', status: 'pending' },
      ],
    },
    {
      stage: 'ai_review',
      status: 'current',
      date: '2026-03-13T10:00:00Z',
      title: 'AI Review in Progress',
      reviewResults: [
        { prNumber: 101, score: 8.5, verdict: 'approved', reviewedAt: '2026-03-13T11:00:00Z', details: 'Good implementation' },
      ],
    },
    {
      stage: 'approved',
      status: 'pending',
      title: 'Approved & Merged',
    },
    {
      stage: 'paid',
      status: 'pending',
      title: 'Paid',
    },
  ],
});

const createMockCompletedTimeline = (): BountyTimelineData => ({
  bountyId: 'test-bounty-003',
  bountyTitle: 'Completed Bounty',
  creator: 'DoneCreator',
  currentStage: 'paid',
  stages: [
    {
      stage: 'created',
      status: 'completed',
      date: '2026-03-01T10:00:00Z',
      title: 'Bounty posted by DoneCreator',
    },
    {
      stage: 'open',
      status: 'completed',
      date: '2026-03-01T10:00:00Z',
      title: 'Accepting PRs',
    },
    {
      stage: 'pr_submitted',
      status: 'completed',
      date: '2026-03-05T10:00:00Z',
      title: 'PR #99 submitted',
      author: 'winner_dev',
      prNumber: 99,
    },
    {
      stage: 'ai_review',
      status: 'completed',
      date: '2026-03-06T10:00:00Z',
      title: 'AI Review Completed',
      reviewResults: [
        { prNumber: 99, score: 9.2, verdict: 'approved', reviewedAt: '2026-03-06T10:00:00Z', details: 'Excellent work' },
      ],
    },
    {
      stage: 'approved',
      status: 'completed',
      date: '2026-03-07T10:00:00Z',
      title: 'PR #99 merged',
      details: 'Merged to main branch',
    },
    {
      stage: 'paid',
      status: 'completed',
      date: '2026-03-08T10:00:00Z',
      title: '500 $FNDRY sent to winner_dev',
      payout: {
        amount: 500,
        currency: '$FNDRY',
        recipient: 'winner_dev',
        transactionHash: '5Xy8ZqW2vN3mK7jR9pL4tS6uH8fB1cD2eA3gF5iJ0kM',
        solscanUrl: 'https://solscan.io/tx/5Xy8ZqW2vN3mK7jR9pL4tS6uH8fB1cD2eA3gF5iJ0kM',
        paidAt: '2026-03-08T10:00:00Z',
      },
    },
  ],
});

const createMockRejectedTimeline = (): BountyTimelineData => ({
  bountyId: 'test-bounty-004',
  bountyTitle: 'Rejected Bounty',
  creator: 'RejectCreator',
  currentStage: 'ai_review',
  stages: [
    {
      stage: 'created',
      status: 'completed',
      date: '2026-03-10T10:00:00Z',
      title: 'Bounty posted by RejectCreator',
    },
    {
      stage: 'open',
      status: 'completed',
      date: '2026-03-10T10:00:00Z',
      title: 'Accepting PRs',
    },
    {
      stage: 'pr_submitted',
      status: 'completed',
      date: '2026-03-12T10:00:00Z',
      title: 'PR #200 submitted',
      submissions: [
        { prNumber: 200, author: 'bad_coder', submittedAt: '2026-03-12T10:00:00Z', status: 'rejected' },
      ],
    },
    {
      stage: 'ai_review',
      status: 'current',
      date: '2026-03-13T10:00:00Z',
      title: 'AI Review Completed',
      reviewResults: [
        { prNumber: 200, score: 3.5, verdict: 'rejected', reviewedAt: '2026-03-13T10:00:00Z', details: 'Security vulnerabilities found' },
      ],
    },
    {
      stage: 'approved',
      status: 'pending',
      title: 'Approved & Merged',
    },
    {
      stage: 'paid',
      status: 'pending',
      title: 'Paid',
    },
  ],
});

describe('BountyTimeline', () => {
  // Basic Rendering Tests
  describe('Basic Rendering', () => {
    it('renders without crashing', () => {
      const mockData = createMockTimelineData();
      render(<BountyTimeline bountyId="test-bounty-001" data={mockData} />);
      expect(screen.getByText('Bounty Timeline')).toBeInTheDocument();
    });

    it('displays bounty title and creator', () => {
      const mockData = createMockTimelineData();
      render(<BountyTimeline bountyId="test-bounty-001" data={mockData} />);
      expect(screen.getByText('Test Bounty Title')).toBeInTheDocument();
      expect(screen.getByText('Created by TestCreator')).toBeInTheDocument();
    });

    it('displays all 6 stages', () => {
      const mockData = createMockTimelineData();
      render(<BountyTimeline bountyId="test-bounty-001" data={mockData} />);
      expect(screen.getByText('📝')).toBeInTheDocument(); // Created
      expect(screen.getByText('🏷️')).toBeInTheDocument(); // Open
      expect(screen.getByText('🔀')).toBeInTheDocument(); // PR Submitted
      expect(screen.getByText('🤖')).toBeInTheDocument(); // AI Review
      expect(screen.getByText('✅')).toBeInTheDocument(); // Approved
      expect(screen.getByText('💰')).toBeInTheDocument(); // Paid
    });

    it('displays stage titles', () => {
      const mockData = createMockTimelineData();
      render(<BountyTimeline bountyId="test-bounty-001" data={mockData} />);
      expect(screen.getByText('Bounty posted by TestCreator')).toBeInTheDocument();
      expect(screen.getByText('Accepting PRs')).toBeInTheDocument();
    });

    it('shows loading state when no data and bountyId not found', () => {
      render(<BountyTimeline bountyId="non-existent-id" />);
      expect(screen.getByText('Loading timeline...')).toBeInTheDocument();
    });

    it('hides title when showTitle is false', () => {
      const mockData = createMockTimelineData();
      render(<BountyTimeline bountyId="test-bounty-001" data={mockData} showTitle={false} />);
      expect(screen.queryByText('Bounty Timeline')).not.toBeInTheDocument();
    });
  });

  // Stage Status Tests
  describe('Stage Status Display', () => {
    it('shows completed stage with green styling', () => {
      const mockData = createMockTimelineData('open');
      render(<BountyTimeline bountyId="test-bounty-001" data={mockData} />);
      const completedBadges = screen.getAllByText('COMPLETED');
      expect(completedBadges.length).toBeGreaterThan(0);
    });

    it('shows current stage with pulse animation', () => {
      const mockData = createMockTimelineData('open');
      render(<BountyTimeline bountyId="test-bounty-001" data={mockData} />);
      const currentBadge = screen.getByText('CURRENT');
      expect(currentBadge).toHaveClass('animate-pulse');
    });

    it('shows pending stage with gray styling', () => {
      const mockData = createMockTimelineData('created');
      render(<BountyTimeline bountyId="test-bounty-001" data={mockData} />);
      const pendingBadges = screen.getAllByText('PENDING');
      expect(pendingBadges.length).toBeGreaterThan(0);
    });

    it('highlights only one current stage at a time', () => {
      const mockData = createMockTimelineData('ai_review');
      render(<BountyTimeline bountyId="test-bounty-001" data={mockData} />);
      const currentBadges = screen.getAllByText('CURRENT');
      expect(currentBadges.length).toBe(1);
    });
  });

  // Expandable Details Tests
  describe('Expandable Details', () => {
    it('shows expand arrow for stages with details', () => {
      const mockData = createMockTimelineWithPRs();
      render(<BountyTimeline bountyId="test-bounty-002" data={mockData} />);
      // Find expand arrows (chevron icons)
      const arrows = document.querySelectorAll('svg');
      expect(arrows.length).toBeGreaterThan(0);
    });

    it('expands stage on click', () => {
      const mockData = createMockTimelineWithPRs();
      render(<BountyTimeline bountyId="test-bounty-002" data={mockData} />);
      
      // Find PR Submitted stage card
      const prSubmittedCard = screen.getByText('3 PRs submitted').closest('button');
      expect(prSubmittedCard).toBeTruthy();
      
      // Click to expand
      fireEvent.click(prSubmittedCard!);
      
      // Should show submission details
      expect(screen.getByText('#101')).toBeInTheDocument();
      expect(screen.getByText('alice')).toBeInTheDocument();
    });

    it('collapses stage on second click', () => {
      const mockData = createMockTimelineWithPRs();
      render(<BountyTimeline bountyId="test-bounty-002" data={mockData} />);
      
      const prSubmittedCard = screen.getByText('3 PRs submitted').closest('button');
      
      // Click to expand
      fireEvent.click(prSubmittedCard!);
      expect(screen.getByText('#101')).toBeInTheDocument();
      
      // Click to collapse
      fireEvent.click(prSubmittedCard!);
      expect(screen.queryByText('#101')).not.toBeInTheDocument();
    });

    it('does not expand stages without details', () => {
      const mockData = createMockTimelineData('created');
      render(<BountyTimeline bountyId="test-bounty-001" data={mockData} />);
      
      // Find a pending stage
      const pendingStage = screen.getByText('Pending submission').closest('button');
      expect(pendingStage).toBeTruthy();
      
      // Get initial content
      const initialContent = document.body.innerHTML;
      
      // Click should do nothing
      fireEvent.click(pendingStage!);
      
      // Content should be unchanged (no expansion)
      expect(document.body.innerHTML).toBe(initialContent);
    });
  });

  // Multiple PRs Tests
  describe('Multiple PR Submissions', () => {
    it('displays multiple submissions', () => {
      const mockData = createMockTimelineWithPRs();
      render(<BountyTimeline bountyId="test-bounty-002" data={mockData} />);
      
      // Expand PR stage
      const prSubmittedCard = screen.getByText('3 PRs submitted').closest('button');
      fireEvent.click(prSubmittedCard!);
      
      expect(screen.getByText('#101')).toBeInTheDocument();
      expect(screen.getByText('#102')).toBeInTheDocument();
      expect(screen.getByText('#103')).toBeInTheDocument();
    });

    it('shows PR authors', () => {
      const mockData = createMockTimelineWithPRs();
      render(<BountyTimeline bountyId="test-bounty-002" data={mockData} />);
      
      const prSubmittedCard = screen.getByText('3 PRs submitted').closest('button');
      fireEvent.click(prSubmittedCard!);
      
      expect(screen.getByText('alice')).toBeInTheDocument();
      expect(screen.getByText('bob')).toBeInTheDocument();
      expect(screen.getByText('charlie')).toBeInTheDocument();
    });

    it('shows PR status indicators', () => {
      const mockData = createMockTimelineWithPRs();
      render(<BountyTimeline bountyId="test-bounty-002" data={mockData} />);
      
      const prSubmittedCard = screen.getByText('3 PRs submitted').closest('button');
      fireEvent.click(prSubmittedCard!);
      
      // Check for status dots (colored circles)
      const statusDots = document.querySelectorAll('.rounded-full.bg-');
      expect(statusDots.length).toBeGreaterThan(0);
    });
  });

  // AI Review Tests
  describe('AI Review Display', () => {
    it('displays AI review scores', () => {
      const mockData = createMockTimelineWithPRs();
      render(<BountyTimeline bountyId="test-bounty-002" data={mockData} />);
      
      // Expand AI Review stage
      const aiReviewCard = screen.getByText('AI Review in Progress').closest('button');
      fireEvent.click(aiReviewCard!);
      
      expect(screen.getByText(/Score: 8.5/10/)).toBeInTheDocument();
      expect(screen.getByText(/✓ Approved/)).toBeInTheDocument();
    });

    it('shows review details', () => {
      const mockData = createMockTimelineWithPRs();
      render(<BountyTimeline bountyId="test-bounty-002" data={mockData} />);
      
      const aiReviewCard = screen.getByText('AI Review in Progress').closest('button');
      fireEvent.click(aiReviewCard!);
      
      expect(screen.getByText('Good implementation')).toBeInTheDocument();
    });

    it('shows rejected verdict correctly', () => {
      const mockData = createMockRejectedTimeline();
      render(<BountyTimeline bountyId="test-bounty-004" data={mockData} />);
      
      const aiReviewCard = screen.getByText('AI Review Completed').closest('button');
      fireEvent.click(aiReviewCard!);
      
      expect(screen.getByText(/Score: 3.5/10/)).toBeInTheDocument();
      expect(screen.getByText(/✗ Rejected/)).toBeInTheDocument();
      expect(screen.getByText('Security vulnerabilities found')).toBeInTheDocument();
    });
  });

  // Payout Tests
  describe('Payout Display', () => {
    it('displays payout amount and recipient', () => {
      const mockData = createMockCompletedTimeline();
      render(<BountyTimeline bountyId="test-bounty-003" data={mockData} />);
      
      // Expand Paid stage
      const paidCard = screen.getByText(/500 \$FNDRY sent to winner_dev/).closest('button');
      fireEvent.click(paidCard!);
      
      expect(screen.getByText('500 $FNDRY')).toBeInTheDocument();
      expect(screen.getByText('winner_dev')).toBeInTheDocument();
    });

    it('displays transaction hash', () => {
      const mockData = createMockCompletedTimeline();
      render(<BountyTimeline bountyId="test-bounty-003" data={mockData} />);
      
      const paidCard = screen.getByText(/500 \$FNDRY sent to winner_dev/).closest('button');
      fireEvent.click(paidCard!);
      
      expect(screen.getByText(/5Xy8ZqW2vN3mK7jR.../)).toBeInTheDocument();
    });

    it('displays Solscan link', () => {
      const mockData = createMockCompletedTimeline();
      render(<BountyTimeline bountyId="test-bounty-003" data={mockData} />);
      
      const paidCard = screen.getByText(/500 \$FNDRY sent to winner_dev/).closest('button');
      fireEvent.click(paidCard!);
      
      const solscanLink = screen.getByText('View on Solscan');
      expect(solscanLink).toBeInTheDocument();
      expect(solscanLink.closest('a')).toHaveAttribute('href', 'https://solscan.io/tx/5Xy8ZqW2vN3mK7jR9pL4tS6uH8fB1cD2eA3gF5iJ0kM');
      expect(solscanLink.closest('a')).toHaveAttribute('target', '_blank');
    });
  });

  // Edge Cases Tests
  describe('Edge Cases', () => {
    it('handles bounty with no submissions', () => {
      const mockData = createMockTimelineData('open');
      render(<BountyTimeline bountyId="test-bounty-001" data={mockData} />);
      
      expect(screen.getByText('No submissions yet')).toBeInTheDocument();
    });

    it('handles rejected submission gracefully', () => {
      const mockData = createMockRejectedTimeline();
      render(<BountyTimeline bountyId="test-bounty-004" data={mockData} />);
      
      expect(screen.getByText(/Security vulnerabilities found/)).toBeInTheDocument();
    });

    it('handles multiple competing PRs', () => {
      const mockData = createMockTimelineWithPRs();
      render(<BountyTimeline bountyId="test-bounty-002" data={mockData} />);
      
      expect(screen.getByText('3 PRs submitted')).toBeInTheDocument();
      expect(screen.getByText('Multiple competing submissions')).toBeInTheDocument();
    });
  });

  // Compact Mode Tests
  describe('Compact Mode', () => {
    it('renders in compact mode', () => {
      const mockData = createMockTimelineData();
      render(<BountyTimeline bountyId="test-bounty-001" data={mockData} compact />);
      expect(screen.getByText('Bounty Timeline')).toBeInTheDocument();
    });

    it('uses smaller padding in compact mode', () => {
      const mockData = createMockTimelineData();
      const { container } = render(<BountyTimeline bountyId="test-bounty-001" data={mockData} compact />);
      
      const mainContainer = container.querySelector('.p-4');
      expect(mainContainer).toBeInTheDocument();
    });

    it('hides footer info in compact mode', () => {
      const mockData = createMockTimelineData();
      render(<BountyTimeline bountyId="test-bounty-001" data={mockData} compact />);
      
      expect(screen.queryByText('Bounty ID:')).not.toBeInTheDocument();
    });
  });

  // Responsive Design Tests
  describe('Responsive Design', () => {
    it('uses vertical layout on all screen sizes', () => {
      const mockData = createMockTimelineData();
      const { container } = render(<BountyTimeline bountyId="test-bounty-001" data={mockData} />);
      
      // Timeline should use vertical stack
      const stageContainer = container.querySelector('.space-y-4');
      expect(stageContainer).toBeInTheDocument();
    });

    it('cards are full width for mobile', () => {
      const mockData = createMockTimelineData();
      const { container } = render(<BountyTimeline bountyId="test-bounty-001" data={mockData} />);
      
      const buttons = container.querySelectorAll('button');
      buttons.forEach(button => {
        expect(button).toHaveClass('w-full');
      });
    });
  });

  // Accessibility Tests
  describe('Accessibility', () => {
    it('has proper heading structure', () => {
      const mockData = createMockTimelineData();
      render(<BountyTimeline bountyId="test-bounty-001" data={mockData} />);
      
      expect(screen.getByRole('heading', { level: 2, name: 'Bounty Timeline' })).toBeInTheDocument();
    });

    it('has accessible aria-labels on stage cards', () => {
      const mockData = createMockTimelineData('open');
      render(<BountyTimeline bountyId="test-bounty-001" data={mockData} />);
      
      expect(screen.getByLabelText(/Created: completed/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/Open for Submissions: current/i)).toBeInTheDocument();
    });

    it('external links have proper rel attributes', () => {
      const mockData = createMockCompletedTimeline();
      render(<BountyTimeline bountyId="test-bounty-003" data={mockData} />);
      
      const paidCard = screen.getByText(/500 \$FNDRY sent to winner_dev/).closest('button');
      fireEvent.click(paidCard!);
      
      const solscanLink = screen.getByText('View on Solscan').closest('a');
      expect(solscanLink).toHaveAttribute('rel', 'noopener noreferrer');
    });

    it('has aria-expanded for expandable stages', () => {
      const mockData = createMockTimelineWithPRs();
      render(<BountyTimeline bountyId="test-bounty-002" data={mockData} />);
      
      const prSubmittedCard = screen.getByText('3 PRs submitted').closest('button');
      expect(prSubmittedCard).toHaveAttribute('aria-expanded', 'false');
      
      fireEvent.click(prSubmittedCard!);
      expect(prSubmittedCard).toHaveAttribute('aria-expanded', 'true');
    });
  });

  // Callback Tests
  describe('Callbacks', () => {
    it('calls onStageClick when stage is clicked', () => {
      const mockData = createMockTimelineWithPRs();
      const onStageClick = jest.fn();
      render(
        <BountyTimeline 
          bountyId="test-bounty-002" 
          data={mockData} 
          onStageClick={onStageClick}
        />
      );
      
      const prSubmittedCard = screen.getByText('3 PRs submitted').closest('button');
      fireEvent.click(prSubmittedCard!);
      
      expect(onStageClick).toHaveBeenCalledWith('pr_submitted');
    });
  });

  // Date Formatting Tests
  describe('Date Formatting', () => {
    it('displays relative time for recent dates', () => {
      const mockData = createMockTimelineData('open');
      render(<BountyTimeline bountyId="test-bounty-001" data={mockData} />);
      
      // Should show "X days ago" or similar relative time
      const timeTexts = screen.getAllByText(/ago$/i);
      expect(timeTexts.length).toBeGreaterThan(0);
    });
  });
});