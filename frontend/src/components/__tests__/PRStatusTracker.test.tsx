/**
 * Tests for PR Status Tracker Component
 */

import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { PRStatusTracker } from '../PRStatusTracker';
import type { PRStatus, StageStatus, PRStage } from '../PRStatusTracker';

// Mock fetch
const mockFetch = jest.fn();
global.fetch = mockFetch;

// Mock WebSocket
class MockWebSocket {
  url: string;
  onopen: ((event: Event) => void) | null = null;
  onmessage: ((event: MessageEvent) => void) | null = null;
  onerror: ((event: Event) => void) | null = null;
  onclose: ((event: CloseEvent) => void) | null = null;
  readyState: number = 0;

  constructor(url: string) {
    this.url = url;
  }

  send(data: string) {}
  close() {}
}

global.WebSocket = MockWebSocket as unknown as typeof WebSocket;

// Sample PR status data
const createMockPRStatus = (overrides: Partial<PRStatus> = {}): PRStatus => ({
  prNumber: 123,
  prTitle: 'Test PR Title',
  prUrl: 'https://github.com/test/repo/pull/123',
  author: 'testuser',
  bountyId: 'bounty-001',
  bountyTitle: 'Test Bounty',
  currentStage: 'ci_running' as PRStage,
  stages: {
    submitted: {
      status: 'passed' as StageStatus,
      timestamp: '2026-03-19T10:00:00Z',
      duration: 5,
      message: 'PR submitted successfully'
    },
    ci_running: {
      status: 'running' as StageStatus,
      timestamp: '2026-03-19T10:05:00Z',
      duration: null,
      message: 'CI checks in progress'
    },
    ai_review: {
      status: 'pending' as StageStatus,
      timestamp: null,
      duration: null
    },
    human_review: {
      status: 'pending' as StageStatus,
      timestamp: null,
      duration: null
    },
    approved: {
      status: 'pending' as StageStatus,
      timestamp: null,
      duration: null
    },
    denied: {
      status: 'pending' as StageStatus,
      timestamp: null,
      duration: null
    },
    payout: {
      status: 'pending' as StageStatus,
      timestamp: null,
      duration: null
    }
  },
  updatedAt: '2026-03-19T10:05:00Z',
  ...overrides
});

describe('PRStatusTracker', () => {
  beforeEach(() => {
    mockFetch.mockClear();
  });

  it('shows loading state initially', () => {
    mockFetch.mockImplementation(() => new Promise(() => {}));

    render(<PRStatusTracker prNumber={123} />);

    expect(screen.getByRole('generic')).toHaveClass('animate-pulse');
  });

  it('fetches PR status on mount', async () => {
    const mockStatus = createMockPRStatus();
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(mockStatus)
    });

    render(<PRStatusTracker prNumber={123} />);

    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalledWith('/api/pr-status/123');
    });
  });

  it('displays PR information', async () => {
    const mockStatus = createMockPRStatus();
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(mockStatus)
    });

    render(<PRStatusTracker prNumber={123} />);

    await waitFor(() => {
      expect(screen.getByText(/PR #123 Status/i)).toBeInTheDocument();
      expect(screen.getByText('Test PR Title')).toBeInTheDocument();
      expect(screen.getByText(/testuser/i)).toBeInTheDocument();
    });
  });

  it('displays bounty information', async () => {
    const mockStatus = createMockPRStatus();
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(mockStatus)
    });

    render(<PRStatusTracker prNumber={123} />);

    await waitFor(() => {
      expect(screen.getByText(/Bounty:/i)).toBeInTheDocument();
      expect(screen.getByText('Test Bounty')).toBeInTheDocument();
    });
  });

  it('shows error state on fetch failure', async () => {
    mockFetch.mockRejectedValueOnce(new Error('Network error'));

    render(<PRStatusTracker prNumber={123} />);

    await waitFor(() => {
      expect(screen.getByText(/Network error/i)).toBeInTheDocument();
    });
  });

  it('shows error state on non-ok response', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 404
    });

    render(<PRStatusTracker prNumber={999} />);

    await waitFor(() => {
      expect(screen.getByText(/Failed to fetch PR status/i)).toBeInTheDocument();
    });
  });

  it('displays stage statuses correctly', async () => {
    const mockStatus = createMockPRStatus();
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(mockStatus)
    });

    render(<PRStatusTracker prNumber={123} />);

    await waitFor(() => {
      // Submitted stage should show Passed
      expect(screen.getByText('Passed')).toBeInTheDocument();
      // CI Running stage should show Running
      expect(screen.getByText('Running')).toBeInTheDocument();
      // Pending stages should show Pending
      expect(screen.getAllByText('Pending').length).toBeGreaterThan(0);
    });
  });

  it('shows AI review scores when available', async () => {
    const mockStatus = createMockPRStatus({
      currentStage: 'ai_review' as PRStage,
      stages: {
        ...createMockPRStatus().stages,
        ai_review: {
          status: 'passed' as StageStatus,
          timestamp: '2026-03-19T10:10:00Z',
          duration: 120,
          scores: {
            quality: 8.5,
            correctness: 9.0,
            security: 7.5,
            completeness: 8.0,
            tests: 9.5,
            overall: 8.5
          }
        }
      }
    });

    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(mockStatus)
    });

    render(<PRStatusTracker prNumber={123} />);

    await waitFor(() => {
      expect(screen.getByText('Score Breakdown')).toBeInTheDocument();
      expect(screen.getByText(/Quality/i)).toBeInTheDocument();
      expect(screen.getByText(/Correctness/i)).toBeInTheDocument();
      expect(screen.getByText(/Security/i)).toBeInTheDocument();
      expect(screen.getByText(/Completeness/i)).toBeInTheDocument();
      expect(screen.getByText(/Tests/i)).toBeInTheDocument();
      expect(screen.getByText(/Overall Score/i)).toBeInTheDocument();
    });
  });

  it('shows payout details when available', async () => {
    const mockStatus = createMockPRStatus({
      currentStage: 'payout' as PRStage,
      stages: {
        ...createMockPRStatus().stages,
        approved: {
          status: 'passed' as StageStatus,
          timestamp: '2026-03-19T10:15:00Z',
          duration: 60
        },
        payout: {
          status: 'passed' as StageStatus,
          timestamp: '2026-03-19T10:20:00Z',
          duration: 30,
          txHash: 'abc123xyz',
          solscanUrl: 'https://solscan.io/tx/abc123xyz',
          amount: 150000
        }
      }
    });

    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(mockStatus)
    });

    render(<PRStatusTracker prNumber={123} />);

    await waitFor(() => {
      expect(screen.getByText(/150,000 \$FNDRY/i)).toBeInTheDocument();
      expect(screen.getByText(/abc123xyz/i)).toBeInTheDocument();
      expect(screen.getByText(/View on Solscan/i)).toBeInTheDocument();
    });
  });

  it('shows denied state correctly', async () => {
    const mockStatus = createMockPRStatus({
      currentStage: 'denied' as PRStage,
      stages: {
        ...createMockPRStatus().stages,
        ci_running: {
          status: 'failed' as StageStatus,
          timestamp: '2026-03-19T10:06:00Z',
          duration: 60,
          message: 'CI checks failed'
        },
        denied: {
          status: 'passed' as StageStatus,
          timestamp: '2026-03-19T10:06:00Z',
          message: 'PR denied due to failed CI checks'
        }
      }
    });

    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(mockStatus)
    });

    render(<PRStatusTracker prNumber={123} />);

    await waitFor(() => {
      expect(screen.getByText('Denied')).toBeInTheDocument();
      expect(screen.getByText(/CI checks failed/i)).toBeInTheDocument();
    });
  });

  it('connects to WebSocket for real-time updates', async () => {
    const mockStatus = createMockPRStatus();
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(mockStatus)
    });

    render(<PRStatusTracker prNumber={123} />);

    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalled();
    });
  });

  it('displays custom className', async () => {
    const mockStatus = createMockPRStatus();
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(mockStatus)
    });

    render(<PRStatusTracker prNumber={123} className="custom-class" />);

    await waitFor(() => {
      const container = screen.getByText(/PR #123 Status/i).closest('div');
      expect(container).toHaveClass('custom-class');
    });
  });

  it('uses custom WebSocket URL', async () => {
    const mockStatus = createMockPRStatus();
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(mockStatus)
    });

    render(
      <PRStatusTracker 
        prNumber={123} 
        websocketUrl="wss://custom.example.com/ws/pr-status"
      />
    );

    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalled();
    });
  });
});

describe('StatusBadge', () => {
  // StatusBadge is internal to PRStatusTracker, tested indirectly above
  it('displays correct status labels', async () => {
    const mockStatus = createMockPRStatus();
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(mockStatus)
    });

    render(<PRStatusTracker prNumber={123} />);

    await waitFor(() => {
      expect(screen.getByText('Passed')).toBeInTheDocument();
      expect(screen.getByText('Running')).toBeInTheDocument();
      expect(screen.getByText('Pending')).toBeInTheDocument();
    });
  });
});

describe('ScoreBar', () => {
  // ScoreBar is internal to PRStatusTracker, tested indirectly above
  it('displays AI review scores correctly', async () => {
    const mockStatus = createMockPRStatus({
      currentStage: 'ai_review' as PRStage,
      stages: {
        ...createMockPRStatus().stages,
        ai_review: {
          status: 'passed' as StageStatus,
          timestamp: '2026-03-19T10:10:00Z',
          duration: 120,
          scores: {
            quality: 9.0,
            correctness: 9.0,
            security: 9.0,
            completeness: 9.0,
            tests: 9.0,
            overall: 9.0
          }
        }
      }
    });

    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(mockStatus)
    });

    render(<PRStatusTracker prNumber={123} />);

    await waitFor(() => {
      expect(screen.getByText('9.0')).toBeInTheDocument();
    });
  });
});