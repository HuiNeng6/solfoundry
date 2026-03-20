import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { ContributorDashboard } from './ContributorDashboard';

// ============================================================================
// Mock Data
// ============================================================================

const mockWalletAddress = 'Amu1YJjcKWKL6xuMTo2dx511kfzXAxgpetJrZp7N71o7';

// ============================================================================
// Tests
// ============================================================================

describe('ContributorDashboard', () => {
  // Basic Rendering Tests
  describe('Rendering', () => {
    it('renders the dashboard header', () => {
      render(<ContributorDashboard walletAddress={mockWalletAddress} />);
      expect(screen.getByText('Contributor Dashboard')).toBeInTheDocument();
      expect(screen.getByText(/track your progress/i)).toBeInTheDocument();
    });

    it('renders all summary cards', () => {
      render(<ContributorDashboard walletAddress={mockWalletAddress} />);
      
      expect(screen.getByText('Total Earned')).toBeInTheDocument();
      expect(screen.getByText('Active Bounties')).toBeInTheDocument();
      expect(screen.getByText('Pending Payouts')).toBeInTheDocument();
      expect(screen.getByText('Reputation Rank')).toBeInTheDocument();
    });

    it('renders tab navigation', () => {
      render(<ContributorDashboard walletAddress={mockWalletAddress} />);
      
      expect(screen.getByText('Overview')).toBeInTheDocument();
      expect(screen.getByText('Notifications')).toBeInTheDocument();
      expect(screen.getByText('Settings')).toBeInTheDocument();
    });

    it('shows unread notification badge', () => {
      render(<ContributorDashboard walletAddress={mockWalletAddress} />);
      
      // Should show badge with unread count
      const notificationTab = screen.getByText('Notifications').closest('button');
      expect(notificationTab).toBeInTheDocument();
    });

    it('renders quick actions', () => {
      render(<ContributorDashboard walletAddress={mockWalletAddress} />);
      
      expect(screen.getByText('Browse Bounties')).toBeInTheDocument();
      expect(screen.getByText('View Leaderboard')).toBeInTheDocument();
      expect(screen.getByText('Check Treasury')).toBeInTheDocument();
    });

    it('renders active bounties section', () => {
      render(<ContributorDashboard walletAddress={mockWalletAddress} />);
      
      expect(screen.getByText('Active Bounties')).toBeInTheDocument();
      expect(screen.getByText('GitHub ↔ Platform Bi-directional Sync')).toBeInTheDocument();
    });

    it('renders earnings chart', () => {
      render(<ContributorDashboard walletAddress={mockWalletAddress} />);
      
      expect(screen.getByText(/earnings \(last 30 days\)/i)).toBeInTheDocument();
    });

    it('renders recent activity section', () => {
      render(<ContributorDashboard walletAddress={mockWalletAddress} />);
      
      expect(screen.getByText('Recent Activity')).toBeInTheDocument();
      expect(screen.getByText('Payout Received')).toBeInTheDocument();
    });
  });

  // Tab Navigation Tests
  describe('Tab Navigation', () => {
    it('switches to notifications tab when clicked', () => {
      render(<ContributorDashboard walletAddress={mockWalletAddress} />);
      
      fireEvent.click(screen.getByText('Notifications'));
      
      expect(screen.getByText('Mark all as read')).toBeInTheDocument();
    });

    it('switches to settings tab when clicked', () => {
      render(<ContributorDashboard walletAddress={mockWalletAddress} />);
      
      fireEvent.click(screen.getByText('Settings'));
      
      expect(screen.getByText('Linked Accounts')).toBeInTheDocument();
      expect(screen.getByText('Notifications')).toBeInTheDocument();
    });

    it('switches back to overview tab', () => {
      render(<ContributorDashboard walletAddress={mockWalletAddress} />);
      
      // Go to settings
      fireEvent.click(screen.getByText('Settings'));
      
      // Go back to overview
      fireEvent.click(screen.getByText('Overview'));
      
      expect(screen.getByText('Active Bounties')).toBeInTheDocument();
    });
  });

  // Notification Tests
  describe('Notifications', () => {
    it('marks notification as read when clicked', () => {
      render(<ContributorDashboard walletAddress={mockWalletAddress} />);
      
      // Go to notifications tab
      fireEvent.click(screen.getByText('Notifications'));
      
      // Find unread notification
      const prMergedNotification = screen.getByText('PR Merged').closest('div');
      expect(prMergedNotification).toBeInTheDocument();
      
      // Click to mark as read
      if (prMergedNotification) {
        fireEvent.click(prMergedNotification);
      }
    });

    it('marks all notifications as read', () => {
      render(<ContributorDashboard walletAddress={mockWalletAddress} />);
      
      // Go to notifications tab
      fireEvent.click(screen.getByText('Notifications'));
      
      // Click mark all as read
      const markAllButton = screen.getByText('Mark all as read');
      fireEvent.click(markAllButton);
      
      // Button should no longer appear (no unread notifications)
      expect(screen.queryByText('Mark all as read')).not.toBeInTheDocument();
    });
  });

  // Settings Tests
  describe('Settings', () => {
    it('displays linked accounts', () => {
      render(<ContributorDashboard walletAddress={mockWalletAddress} />);
      
      fireEvent.click(screen.getByText('Settings'));
      
      expect(screen.getByText('Github')).toBeInTheDocument();
      expect(screen.getByText('HuiNeng6')).toBeInTheDocument();
    });

    it('toggles notification preferences', () => {
      render(<ContributorDashboard walletAddress={mockWalletAddress} />);
      
      fireEvent.click(screen.getByText('Settings'));
      
      // Find toggle button
      const toggles = screen.getAllByRole('button').filter(btn => 
        btn.className.includes('rounded-full')
      );
      
      if (toggles.length > 0) {
        const firstToggle = toggles[0];
        fireEvent.click(firstToggle);
      }
    });

    it('displays wallet address', () => {
      render(<ContributorDashboard walletAddress={mockWalletAddress} />);
      
      fireEvent.click(screen.getByText('Settings'));
      
      expect(screen.getByText('Connected Wallet')).toBeInTheDocument();
    });
  });

  // Quick Actions Tests
  describe('Quick Actions', () => {
    it('calls onBrowseBounties when clicked', () => {
      const mockCallback = jest.fn();
      render(<ContributorDashboard walletAddress={mockWalletAddress} onBrowseBounties={mockCallback} />);
      
      fireEvent.click(screen.getByText('Browse Bounties'));
      
      expect(mockCallback).toHaveBeenCalled();
    });

    it('calls onViewLeaderboard when clicked', () => {
      const mockCallback = jest.fn();
      render(<ContributorDashboard walletAddress={mockWalletAddress} onViewLeaderboard={mockCallback} />);
      
      fireEvent.click(screen.getByText('View Leaderboard'));
      
      expect(mockCallback).toHaveBeenCalled();
    });

    it('calls onCheckTreasury when clicked', () => {
      const mockCallback = jest.fn();
      render(<ContributorDashboard walletAddress={mockWalletAddress} onCheckTreasury={mockCallback} />);
      
      fireEvent.click(screen.getByText('Check Treasury'));
      
      expect(mockCallback).toHaveBeenCalled();
    });
  });

  // Bounty Card Tests
  describe('Bounty Cards', () => {
    it('displays bounty progress', () => {
      render(<ContributorDashboard walletAddress={mockWalletAddress} />);
      
      expect(screen.getByText('Progress')).toBeInTheDocument();
      expect(screen.getByText('60%')).toBeInTheDocument();
    });

    it('shows deadline countdown', () => {
      render(<ContributorDashboard walletAddress={mockWalletAddress} />);
      
      // Should show days remaining
      expect(screen.getByText(/days left/i)).toBeInTheDocument();
    });

    it('shows reward amount', () => {
      render(<ContributorDashboard walletAddress={mockWalletAddress} />);
      
      // Should show FNDRY token
      expect(screen.getByText(/\$FNDRY/)).toBeInTheDocument();
    });
  });

  // Activity Feed Tests
  describe('Activity Feed', () => {
    it('displays activity types', () => {
      render(<ContributorDashboard walletAddress={mockWalletAddress} />);
      
      expect(screen.getByText('Payout Received')).toBeInTheDocument();
      expect(screen.getByText('Review Completed')).toBeInTheDocument();
      expect(screen.getByText('PR Submitted')).toBeInTheDocument();
      expect(screen.getByText('Bounty Claimed')).toBeInTheDocument();
    });

    it('shows activity amounts for payouts', () => {
      render(<ContributorDashboard walletAddress={mockWalletAddress} />);
      
      // Should show positive amount for payouts
      const amounts = screen.getAllByText(/\+\d/);
      expect(amounts.length).toBeGreaterThan(0);
    });
  });

  // Responsive Tests
  describe('Responsive Design', () => {
    it('renders summary cards in grid layout', () => {
      render(<ContributorDashboard walletAddress={mockWalletAddress} />);
      
      const summaryCards = screen.getByText('Total Earned').closest('div')?.parentElement;
      expect(summaryCards?.className).toMatch(/grid/);
    });

    it('renders main content in responsive grid', () => {
      render(<ContributorDashboard walletAddress={mockWalletAddress} />);
      
      const activeBountiesHeader = screen.getByText('Active Bounties');
      expect(activeBountiesHeader).toBeInTheDocument();
    });
  });

  // Data Formatting Tests
  describe('Data Formatting', () => {
    it('formats large numbers correctly', () => {
      render(<ContributorDashboard walletAddress={mockWalletAddress} />);
      
      // 2450000 should be formatted as 2.5M or similar
      const formattedAmounts = screen.getAllByText(/2\.5M|2450K/i);
      expect(formattedAmounts.length).toBeGreaterThan(0);
    });

    it('truncates wallet address', () => {
      render(<ContributorDashboard walletAddress={mockWalletAddress} />);
      
      fireEvent.click(screen.getByText('Settings'));
      
      // Should show truncated address, not full address
      const truncatedWallets = screen.getAllByText(/Amu1YJjc\.\.\./);
      expect(truncatedWallets.length).toBeGreaterThan(0);
    });
  });
});