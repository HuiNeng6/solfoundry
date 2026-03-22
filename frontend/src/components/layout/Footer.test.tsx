import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { Footer } from './Footer';

// Mock navigator.clipboard
const mockClipboard = {
  writeText: vi.fn().mockResolvedValue(undefined),
};

Object.assign(navigator, {
  clipboard: mockClipboard,
});

describe('Footer', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders SolFoundry logo and tagline', () => {
    render(<Footer />);
    expect(screen.getByText('SolFoundry')).toBeInTheDocument();
    expect(screen.getByText('Autonomous AI Software Factory on Solana')).toBeInTheDocument();
  });

  it('renders social links', () => {
    render(<Footer />);
    expect(screen.getByText('GitHub')).toBeInTheDocument();
    expect(screen.getByText('X/Twitter')).toBeInTheDocument();
    expect(screen.getByText('Website')).toBeInTheDocument();
  });

  it('renders $FNDRY token CA', () => {
    render(<Footer />);
    expect(screen.getByText(/\$FNDRY Token CA:/i)).toBeInTheDocument();
    expect(screen.getByText('C2TvY8E8B75EF2UP8cTpTp3EDUjTgjWmpaGnT74VBAGS')).toBeInTheDocument();
  });

  it('renders "Built with 🔥 by the SolFoundry automaton" text', () => {
    render(<Footer />);
    expect(screen.getByText(/Built with 🔥 by the SolFoundry automaton/i)).toBeInTheDocument();
  });

  it('renders current year in copyright', () => {
    render(<Footer />);
    const currentYear = new Date().getFullYear();
    expect(screen.getByText(new RegExp(`© ${currentYear} SolFoundry`))).toBeInTheDocument();
  });

  it('copies contract address to clipboard when copy button is clicked', async () => {
    render(<Footer />);
    
    const copyButton = screen.getByLabelText('Copy contract address');
    fireEvent.click(copyButton);
    
    await waitFor(() => {
      expect(mockClipboard.writeText).toHaveBeenCalledWith('C2TvY8E8B75EF2UP8cTpTp3EDUjTgjWmpaGnT74VBAGS');
    });
  });

  it('shows checkmark after copying', async () => {
    render(<Footer />);
    
    const copyButton = screen.getByLabelText('Copy contract address');
    fireEvent.click(copyButton);
    
    await waitFor(() => {
      expect(screen.getByTitle('Copied!')).toBeInTheDocument();
    });
  });

  it('has correct social link URLs', () => {
    render(<Footer />);
    
    const githubLink = screen.getByText('GitHub').closest('a');
    const twitterLink = screen.getByText('X/Twitter').closest('a');
    const websiteLink = screen.getByText('Website').closest('a');
    
    expect(githubLink).toHaveAttribute('href', 'https://github.com/SolFoundry/solfoundry');
    expect(twitterLink).toHaveAttribute('href', 'https://twitter.com/foundrysol');
    expect(websiteLink).toHaveAttribute('href', 'https://solfoundry.org');
  });
});