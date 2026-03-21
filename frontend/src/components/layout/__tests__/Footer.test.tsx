import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { Footer } from '../Footer';

// Mock clipboard API
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

  afterEach(() => {
    vi.clearAllMocks();
  });

  describe('Rendering', () => {
    it('renders the SolFoundry logo', () => {
      render(<Footer />);
      expect(screen.getByText('SF')).toBeInTheDocument();
    });

    it('renders the SolFoundry brand name', () => {
      render(<Footer />);
      expect(screen.getByText('SolFoundry')).toBeInTheDocument();
    });

    it('renders the tagline', () => {
      render(<Footer />);
      expect(screen.getByText('Decentralized bounty platform for Solana')).toBeInTheDocument();
    });

    it('renders all social links', () => {
      render(<Footer />);
      expect(screen.getByText('GitHub')).toBeInTheDocument();
      expect(screen.getByText('X/Twitter')).toBeInTheDocument();
      expect(screen.getByText('Website')).toBeInTheDocument();
    });

    it('renders the $FNDRY token CA label', () => {
      render(<Footer />);
      expect(screen.getByText('$FNDRY Token CA')).toBeInTheDocument();
    });

    it('renders the contract address', () => {
      render(<Footer />);
      expect(screen.getByText('C2TvY8E8B75EF2UP8cTpTp3EDUjgjWmpaGnT74VBAGS')).toBeInTheDocument();
    });

    it('renders the "Built with fire" text', () => {
      render(<Footer />);
      expect(screen.getByText(/Built with 🔥 by the SolFoundry automaton/)).toBeInTheDocument();
    });

    it('renders copyright with current year', () => {
      render(<Footer />);
      const currentYear = new Date().getFullYear();
      expect(screen.getByText(new RegExp(`© ${currentYear} SolFoundry`))).toBeInTheDocument();
    });
  });

  describe('Copy to Clipboard', () => {
    it('has a copy button for the contract address', () => {
      render(<Footer />);
      const copyButton = screen.getByRole('button', { name: /copy contract address/i });
      expect(copyButton).toBeInTheDocument();
    });

    it('copies the contract address to clipboard when clicked', async () => {
      render(<Footer />);
      const copyButton = screen.getByRole('button', { name: /copy contract address/i });
      
      fireEvent.click(copyButton);
      
      await waitFor(() => {
        expect(mockClipboard.writeText).toHaveBeenCalledWith('C2TvY8E8B75EF2UP8cTpTp3EDUjgjWmpaGnT74VBAGS');
      });
    });

    it('shows "Copied!" feedback after copying', async () => {
      render(<Footer />);
      const copyButton = screen.getByRole('button', { name: /copy contract address/i });
      
      fireEvent.click(copyButton);
      
      await waitFor(() => {
        expect(screen.getByText('Copied!')).toBeInTheDocument();
      });
    });

    it('changes button aria-label to "Copied!" after copying', async () => {
      render(<Footer />);
      const copyButton = screen.getByRole('button', { name: /copy contract address/i });
      
      fireEvent.click(copyButton);
      
      await waitFor(() => {
        expect(screen.getByRole('button', { name: 'Copied!' })).toBeInTheDocument();
      });
    });
  });

  describe('Links', () => {
    it('has correct GitHub link', () => {
      render(<Footer />);
      const githubLink = screen.getByText('GitHub').closest('a');
      expect(githubLink).toHaveAttribute('href', 'https://github.com/SolFoundry/solfoundry');
      expect(githubLink).toHaveAttribute('target', '_blank');
      expect(githubLink).toHaveAttribute('rel', 'noopener noreferrer');
    });

    it('has correct X/Twitter link', () => {
      render(<Footer />);
      const twitterLink = screen.getByText('X/Twitter').closest('a');
      expect(twitterLink).toHaveAttribute('href', 'https://x.com/foundrysol');
      expect(twitterLink).toHaveAttribute('target', '_blank');
      expect(twitterLink).toHaveAttribute('rel', 'noopener noreferrer');
    });

    it('has correct Website link', () => {
      render(<Footer />);
      const websiteLink = screen.getByText('Website').closest('a');
      expect(websiteLink).toHaveAttribute('href', 'https://solfoundry.org');
      expect(websiteLink).toHaveAttribute('target', '_blank');
      expect(websiteLink).toHaveAttribute('rel', 'noopener noreferrer');
    });
  });

  describe('Accessibility', () => {
    it('has correct ARIA role on footer', () => {
      render(<Footer />);
      expect(screen.getByRole('contentinfo')).toBeInTheDocument();
    });

    it('has accessible navigation label for footer links', () => {
      render(<Footer />);
      expect(screen.getByLabelText('Footer navigation')).toBeInTheDocument();
    });

    it('has accessible copy button', () => {
      render(<Footer />);
      const copyButton = screen.getByRole('button', { name: /copy contract address/i });
      expect(copyButton).toBeInTheDocument();
    });
  });

  describe('Styling', () => {
    it('uses dark theme background color', () => {
      render(<Footer />);
      const footer = screen.getByRole('contentinfo');
      expect(footer.className).toContain('bg-surface');
    });

    it('uses Solana purple for link hover states', () => {
      render(<Footer />);
      const githubLink = screen.getByText('GitHub').closest('a');
      expect(githubLink?.className).toContain('hover:text-solana-purple');
    });

    it('uses Solana green for contract address', () => {
      render(<Footer />);
      const caCode = screen.getByText('C2TvY8E8B75EF2UP8cTpTp3EDUjgjWmpaGnT74VBAGS');
      expect(caCode.className).toContain('text-solana-green');
    });

    it('has responsive layout classes', () => {
      render(<Footer />);
      const footer = screen.getByRole('contentinfo');
      // Check for responsive flex layout
      expect(footer.innerHTML).toContain('flex-col');
      expect(footer.innerHTML).toContain('md:flex-row');
    });
  });
});