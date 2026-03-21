/**
 * Tests for TokenomicsSkeleton component
 */
import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { TokenomicsSkeleton } from './TokenomicsSkeleton';

describe('TokenomicsSkeleton', () => {
  it('renders loading skeleton with default props', () => {
    render(<TokenomicsSkeleton />);
    
    expect(screen.getByRole('status')).toBeInTheDocument();
    expect(screen.getByLabelText('Loading tokenomics data')).toBeInTheDocument();
  });

  it('hides treasury section when showTreasury is false', () => {
    render(<TokenomicsSkeleton showTreasury={false} />);
    
    // Only token stats should be rendered
    expect(screen.getByRole('status')).toBeInTheDocument();
  });

  it('hides token stats when showTokenStats is false', () => {
    render(<TokenomicsSkeleton showTokenStats={false} />);
    
    // Only treasury should be rendered
    expect(screen.getByRole('status')).toBeInTheDocument();
  });

  it('has accessible loading text', () => {
    render(<TokenomicsSkeleton />);
    
    expect(screen.getByText('Loading tokenomics and treasury data...')).toHaveClass('sr-only');
  });
});