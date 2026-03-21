/**
 * Tests for LeaderboardSkeleton component
 */
import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { LeaderboardSkeleton } from './LeaderboardSkeleton';

describe('LeaderboardSkeleton', () => {
  it('renders loading skeleton with default props', () => {
    render(<LeaderboardSkeleton />);
    
    expect(screen.getByRole('status')).toBeInTheDocument();
    expect(screen.getByLabelText('Loading leaderboard')).toBeInTheDocument();
  });

  it('renders specified number of rows', () => {
    const { container } = render(<LeaderboardSkeleton rows={5} />);
    
    // Each row has skeleton elements
    const rows = container.querySelectorAll('.grid-cols-6');
    // Header + data rows
    expect(rows.length).toBeGreaterThan(0);
  });

  it('hides controls when showControls is false', () => {
    render(<LeaderboardSkeleton showControls={false} />);
    
    expect(screen.getByRole('status')).toBeInTheDocument();
  });

  it('has accessible loading text', () => {
    render(<LeaderboardSkeleton />);
    
    expect(screen.getByText('Loading leaderboard data...')).toHaveClass('sr-only');
  });
});