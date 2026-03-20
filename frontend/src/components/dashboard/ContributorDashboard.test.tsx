import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { ContributorDashboard } from './ContributorDashboard';
import * as api from '../../services/api';

// Mock the API module
vi.mock('../../services/api', () => ({
  dashboardApi: {
    getDashboard: vi.fn(),
    getEarnings: vi.fn(),
    getReputation: vi.fn(),
    getBountyHistory: vi.fn(),
  },
}));

// Mock Recharts
vi.mock('recharts', () => ({
  LineChart: () => <div data-testid="line-chart">LineChart</div>,
  Line: () => <div>Line</div>,
  XAxis: () => <div>XAxis</div>,
  YAxis: () => <div>YAxis</div>,
  CartesianGrid: () => <div>CartesianGrid</div>,
  Tooltip: () => <div>Tooltip</div>,
  ResponsiveContainer: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="responsive-container">{children}</div>
  ),
  BarChart: () => <div data-testid="bar-chart">BarChart</div>,
  Bar: () => <div>Bar</div>,
}));

const mockDashboardData = {
  summary: {
    contributor_id: 'test-contributor-id',
    username: 'testuser',
    display_name: 'Test User',
    avatar_url: null,
    wallet_address: 'Amu1YJjcKWKL6xuMTo2dx511kfzXAxgpetJrZp7N71o7',
    earnings: {
      total_earned: 1500.5,
      total_bounties: 12,
      average_reward: 125.04,
      this_month_earned: 300.0,
      last_month_earned: 450.0,
      by_token: { FNDRY: 1500.5 },
    },
    reputation: {
      current_score: 85,
      total_changes: 12,
      recent_changes: [
        {
          date: '2026-03-15T10:00:00Z',
          change: 15,
          reason: 'Completed bounty: Implement new feature...',
          new_total: 85,
        },
      ],
    },
    active_bounties: 2,
    completed_bounties: [
      {
        id: 'bounty-1',
        title: 'Test Bounty 1',
        status: 'completed' as const,
        tier: 2 as const,
        reward_amount: 100,
        reward_token: 'FNDRY',
        completed_at: '2026-03-15T10:00:00Z',
        created_at: '2026-03-10T10:00:00Z',
      },
    ],
    claimed_bounties: [
      {
        id: 'bounty-2',
        title: 'Test Bounty 2',
        status: 'claimed' as const,
        tier: 1 as const,
        reward_amount: 50,
        reward_token: 'FNDRY',
        created_at: '2026-03-18T10:00:00Z',
      },
    ],
  },
  bounty_history: [
    {
      id: 'bounty-1',
      title: 'Test Bounty 1',
      status: 'completed' as const,
      tier: 2 as const,
      reward_amount: 100,
      reward_token: 'FNDRY',
      completed_at: '2026-03-15T10:00:00Z',
      created_at: '2026-03-10T10:00:00Z',
    },
  ],
  earnings_chart: [
    { month: '2024-10', earned: 100 },
    { month: '2024-11', earned: 200 },
    { month: '2024-12', earned: 150 },
    { month: '2025-01', earned: 300 },
    { month: '2025-02', earned: 450 },
    { month: '2025-03', earned: 300 },
  ],
  reputation_history: [
    { month: '2024-10', score: 35 },
    { month: '2024-11', score: 45 },
    { month: '2024-12', score: 55 },
    { month: '2025-01', score: 65 },
    { month: '2025-02', score: 75 },
    { month: '2025-03', score: 85 },
  ],
};

describe('ContributorDashboard', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    (api.dashboardApi.getDashboard as ReturnType<typeof vi.fn>).mockResolvedValue(mockDashboardData);
  });

  it('renders loading state initially', () => {
    render(<ContributorDashboard contributorId="test-contributor-id" />);
    expect(screen.getByText('Loading dashboard...')).toBeInTheDocument();
  });

  it('fetches and displays dashboard data', async () => {
    render(<ContributorDashboard contributorId="test-contributor-id" />);

    await waitFor(() => {
      expect(screen.getByText('Test User')).toBeInTheDocument();
    });

    expect(screen.getByText('@testuser')).toBeInTheDocument();
    expect(api.dashboardApi.getDashboard).toHaveBeenCalledWith('test-contributor-id');
  });

  it('displays user avatar with initial when no avatar_url', async () => {
    render(<ContributorDashboard contributorId="test-contributor-id" />);

    await waitFor(() => {
      expect(screen.getByText('T')).toBeInTheDocument(); // First letter of Test User
    });
  });

  it('displays wallet address in truncated format', async () => {
    render(<ContributorDashboard contributorId="test-contributor-id" />);

    await waitFor(() => {
      expect(screen.getByText(/Amu1YJ...71o7/)).toBeInTheDocument();
    });
  });

  it('switches between tabs', async () => {
    render(<ContributorDashboard contributorId="test-contributor-id" />);

    await waitFor(() => {
      expect(screen.getByText('Test User')).toBeInTheDocument();
    });

    // Click Earnings tab
    fireEvent.click(screen.getByRole('button', { name: 'Earnings' }));
    expect(screen.getByText('Earnings Over Time')).toBeInTheDocument();

    // Click Reputation tab
    fireEvent.click(screen.getByRole('button', { name: 'Reputation' }));
    expect(screen.getByText('Current Reputation')).toBeInTheDocument();

    // Click History tab
    fireEvent.click(screen.getByRole('button', { name: 'History' }));
    expect(screen.getByText('Bounty Participation History')).toBeInTheDocument();
  });

  it('handles API error gracefully', async () => {
    (api.dashboardApi.getDashboard as ReturnType<typeof vi.fn>).mockRejectedValue(new Error('API Error'));

    render(<ContributorDashboard contributorId="test-contributor-id" />);

    await waitFor(() => {
      expect(screen.getByText('Failed to load dashboard data. Please try again later.')).toBeInTheDocument();
    });

    expect(screen.getByText('Retry')).toBeInTheDocument();
  });

  it('is responsive - displays correctly on different screen sizes', async () => {
    const { container } = render(<ContributorDashboard contributorId="test-contributor-id" />);

    await waitFor(() => {
      expect(screen.getByText('Test User')).toBeInTheDocument();
    });

    // Check for responsive grid classes
    const gridElements = container.querySelectorAll('.grid');
    expect(gridElements.length).toBeGreaterThan(0);

    // Check for responsive padding
    const mainContainer = container.querySelector('.min-h-screen');
    expect(mainContainer).toHaveClass('p-4', 'md:p-6', 'lg:p-8');
  });

  it('formats large numbers correctly', async () => {
    const largeEarningsData = {
      ...mockDashboardData,
      summary: {
        ...mockDashboardData.summary,
        earnings: {
          ...mockDashboardData.summary.earnings,
          total_earned: 1500000,
        },
      },
    };

    (api.dashboardApi.getDashboard as ReturnType<typeof vi.fn>).mockResolvedValue(largeEarningsData);

    render(<ContributorDashboard contributorId="test-contributor-id" />);

    await waitFor(() => {
      expect(screen.getByText('1.5M FNDRY')).toBeInTheDocument();
    });
  });
});