/**
 * Tests for BountyBoardSkeleton component
 */
import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { BountyBoardSkeleton } from './BountyBoardSkeleton';

describe('BountyBoardSkeleton', () => {
  it('renders loading skeleton with default props', () => {
    render(<BountyBoardSkeleton />);
    
    // Should have loading status role
    expect(screen.getByRole('status')).toBeInTheDocument();
    expect(screen.getByLabelText('Loading bounty board')).toBeInTheDocument();
  });

  it('renders specified number of bounty cards', () => {
    const { container } = render(<BountyBoardSkeleton count={4} />);
    
    // Check for skeleton cards (each card has multiple skeleton elements)
    const skeletonElements = container.querySelectorAll('[aria-hidden="true"]');
    expect(skeletonElements.length).toBeGreaterThan(0);
  });

  it('hides sections when props are false', () => {
    const { container } = render(
      <BountyBoardSkeleton 
        showFilters={false} 
        showSortBar={false}
        showHotBounties={false}
        showRecommended={false}
      />
    );
    
    // Main grid should still render
    expect(screen.getByRole('status')).toBeInTheDocument();
  });

  it('has accessible loading text', () => {
    render(<BountyBoardSkeleton />);
    
    expect(screen.getByText('Loading bounty board...')).toHaveClass('sr-only');
  });
});