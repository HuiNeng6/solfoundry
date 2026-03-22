import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { CopyAddress, truncateAddress } from './CopyAddress';

// Mock clipboard API
const mockClipboard = {
  writeText: vi.fn().mockResolvedValue(undefined),
};

Object.assign(navigator, {
  clipboard: mockClipboard,
});

describe('truncateAddress', () => {
  it('returns empty string for empty input', () => {
    expect(truncateAddress('')).toBe('');
  });

  it('returns full address if too short to truncate', () => {
    expect(truncateAddress('abc')).toBe('abc');
    expect(truncateAddress('12345678')).toBe('12345678');
  });

  it('truncates long addresses correctly', () => {
    const address = 'C2TvABCDE123456789BAGS';
    expect(truncateAddress(address)).toBe('C2Tv...BAGS');
  });

  it('respects custom start/end chars', () => {
    const address = 'C2TvABCDE123456789BAGS';
    expect(truncateAddress(address, 6, 4)).toBe('C2TvAB...BAGS');
  });
});

describe('CopyAddress', () => {
  const testAddress = 'C2TvABCDE12345678901234567890BAGS';

  beforeEach(() => {
    vi.clearAllMocks();
    mockClipboard.writeText.mockResolvedValue(undefined);
  });

  afterEach(() => {
    vi.clearAllTimers();
  });

  it('renders truncated address', () => {
    render(<CopyAddress address={testAddress} />);
    expect(screen.getByText('C2Tv...BAGS')).toBeInTheDocument();
  });

  it('renders full address if short enough', () => {
    const shortAddress = 'abc123';
    render(<CopyAddress address={shortAddress} />);
    expect(screen.getByText(shortAddress)).toBeInTheDocument();
  });

  it('does not render if address is empty', () => {
    const { container } = render(<CopyAddress address="" />);
    expect(container.firstChild).toBeNull();
  });

  it('shows tooltip with full address on hover', () => {
    render(<CopyAddress address={testAddress} showTooltip />);
    const addressSpan = screen.getByText('C2Tv...BAGS');
    expect(addressSpan).toHaveAttribute('title', testAddress);
  });

  it('hides tooltip when showTooltip is false', () => {
    render(<CopyAddress address={testAddress} showTooltip={false} />);
    const addressSpan = screen.getByText('C2Tv...BAGS');
    expect(addressSpan).not.toHaveAttribute('title');
  });

  it('copies address to clipboard on button click', async () => {
    const user = userEvent.setup();
    render(<CopyAddress address={testAddress} />);

    const copyButton = screen.getByRole('button', { name: /copy address/i });
    await user.click(copyButton);

    expect(mockClipboard.writeText).toHaveBeenCalledWith(testAddress);
  });

  it('shows checkmark after successful copy', async () => {
    const user = userEvent.setup();
    render(<CopyAddress address={testAddress} />);

    const copyButton = screen.getByRole('button', { name: /copy address/i });
    await user.click(copyButton);

    // Check for checkmark icon (indicated by copied state)
    await waitFor(() => {
      expect(screen.getByRole('button', { name: /copied/i })).toBeInTheDocument();
    });
  });

  it('resets copied state after 2 seconds', async () => {
    vi.useFakeTimers();
    const user = userEvent.setup({ delay: null });

    render(<CopyAddress address={testAddress} />);

    const copyButton = screen.getByRole('button', { name: /copy address/i });
    await user.click(copyButton);

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /copied/i })).toBeInTheDocument();
    });

    // Advance timers by 2 seconds
    vi.advanceTimersByTime(2000);

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /copy address/i })).toBeInTheDocument();
    });

    vi.useRealTimers();
  });

  it('supports keyboard interaction (Enter)', async () => {
    const user = userEvent.setup();
    render(<CopyAddress address={testAddress} />);

    const copyButton = screen.getByRole('button', { name: /copy address/i });
    copyButton.focus();
    await user.keyboard('{Enter}');

    expect(mockClipboard.writeText).toHaveBeenCalledWith(testAddress);
  });

  it('supports keyboard interaction (Space)', async () => {
    const user = userEvent.setup();
    render(<CopyAddress address={testAddress} />);

    const copyButton = screen.getByRole('button', { name: /copy address/i });
    copyButton.focus();
    await user.keyboard(' ');

    expect(mockClipboard.writeText).toHaveBeenCalledWith(testAddress);
  });

  it('hides copy button when showCopyButton is false', () => {
    render(<CopyAddress address={testAddress} showCopyButton={false} />);
    expect(screen.queryByRole('button')).not.toBeInTheDocument();
  });

  it('uses custom label in aria-label', () => {
    render(<CopyAddress address={testAddress} label="Wallet" />);
    expect(screen.getByRole('button', { name: /copy wallet/i })).toBeInTheDocument();
  });

  it('applies custom className', () => {
    const { container } = render(
      <CopyAddress address={testAddress} className="custom-class" />
    );
    expect(container.firstChild).toHaveClass('custom-class');
  });

  it('handles clipboard failure gracefully', async () => {
    vi.spyOn(navigator.clipboard, 'writeText').mockRejectedValueOnce(new Error('Failed'));
    const user = userEvent.setup();

    render(<CopyAddress address={testAddress} />);

    const copyButton = screen.getByRole('button', { name: /copy address/i });
    await user.click(copyButton);

    // Should show error state (X icon)
    await waitFor(() => {
      expect(screen.getByRole('button', { name: /failed/i })).toBeInTheDocument();
    });
  });

  it('has proper accessibility attributes', () => {
    render(<CopyAddress address={testAddress} label="Wallet" />);

    const button = screen.getByRole('button');
    expect(button).toHaveAttribute('aria-label', `Copy wallet: ${testAddress}`);

    // Check for screen reader announcement
    const addressSpan = screen.getByText('C2Tv...BAGS');
    expect(addressSpan).toHaveAttribute('aria-label', `Wallet: ${testAddress}`);
  });

  it('announces copy success to screen readers', async () => {
    const user = userEvent.setup();
    render(<CopyAddress address={testAddress} label="Wallet" />);

    const copyButton = screen.getByRole('button');
    await user.click(copyButton);

    await waitFor(() => {
      expect(screen.getByRole('status', { name: /wallet copied/i })).toBeInTheDocument();
    });
  });
});