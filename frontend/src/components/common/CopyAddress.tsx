/**
 * CopyAddress - Reusable component for displaying and copying wallet addresses/transaction hashes.
 *
 * Features:
 * - Click-to-copy with visual feedback (checkmark for 2s)
 * - Truncated display with hover tooltip
 * - Keyboard accessible (Enter/Space to copy)
 * - Screen reader announcements
 *
 * @module components/common/CopyAddress
 */
import React, { useState, useCallback, useRef, useEffect } from 'react';

export interface CopyAddressProps {
  /** The full address to display and copy */
  address: string;
  /** Number of characters to show at start (default: 4) */
  startChars?: number;
  /** Number of characters to show at end (default: 4) */
  endChars?: number;
  /** Additional CSS classes */
  className?: string;
  /** Whether to show the copy button (default: true) */
  showCopyButton?: boolean;
  /** Whether to show tooltip on hover (default: true) */
  showTooltip?: boolean;
  /** Custom aria-label prefix (default: "Address") */
  label?: string;
  /** Font size variant: 'xs' | 'sm' | 'base' (default: 'sm') */
  size?: 'xs' | 'sm' | 'base';
  /** Whether to use monospace font (default: true) */
  mono?: boolean;
}

/**
 * Truncate a string for display, e.g. "C2Tv...BAGS"
 */
export function truncateAddress(
  address: string,
  startChars = 4,
  endChars = 4
): string {
  if (!address) return '';
  if (address.length <= startChars + endChars + 3) return address;
  return `${address.slice(0, startChars)}...${address.slice(-endChars)}`;
}

/**
 * Copy text to clipboard with fallback for older browsers
 */
async function copyToClipboard(text: string): Promise<boolean> {
  try {
    await navigator.clipboard.writeText(text);
    return true;
  } catch {
    // Fallback for older browsers or non-HTTPS
    const textarea = document.createElement('textarea');
    textarea.value = text;
    textarea.style.position = 'fixed';
    textarea.style.opacity = '0';
    textarea.style.pointerEvents = 'none';
    document.body.appendChild(textarea);
    textarea.select();
    try {
      const success = document.execCommand('copy');
      document.body.removeChild(textarea);
      return success;
    } catch {
      document.body.removeChild(textarea);
      return false;
    }
  }
}

const sizeClasses = {
  xs: 'text-xs',
  sm: 'text-sm',
  base: 'text-base',
};

const iconSizeClasses = {
  xs: 'w-3 h-3',
  sm: 'w-4 h-4',
  base: 'w-5 h-5',
};

/**
 * Reusable component for displaying wallet addresses or transaction hashes
 * with click-to-copy functionality.
 *
 * @example
 * ```tsx
 * <CopyAddress address="C2Tv...BAGS" />
 * <CopyAddress address={txHash} label="Transaction" />
 * ```
 */
export const CopyAddress: React.FC<CopyAddressProps> = ({
  address,
  startChars = 4,
  endChars = 4,
  className = '',
  showCopyButton = true,
  showTooltip = true,
  label = 'Address',
  size = 'sm',
  mono = true,
}) => {
  const [copied, setCopied] = useState(false);
  const [copyFailed, setCopyFailed] = useState(false);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const buttonRef = useRef<HTMLButtonElement>(null);

  // Clear timer on unmount
  useEffect(() => {
    return () => {
      if (timerRef.current) clearTimeout(timerRef.current);
    };
  }, []);

  const truncated = truncateAddress(address, startChars, endChars);
  const isTruncated = address !== truncated;

  const handleCopy = useCallback(async () => {
    if (!address || copied) return;

    // Clear any existing timer
    if (timerRef.current) clearTimeout(timerRef.current);
    setCopyFailed(false);

    const success = await copyToClipboard(address);
    if (success) {
      setCopied(true);
      timerRef.current = setTimeout(() => setCopied(false), 2000);
    } else {
      setCopyFailed(true);
      timerRef.current = setTimeout(() => setCopyFailed(false), 3000);
    }
  }, [address, copied]);

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        handleCopy();
      }
    },
    [handleCopy]
  );

  if (!address) return null;

  const ariaLabel = copied
    ? `${label} copied to clipboard`
    : copyFailed
    ? `Failed to copy ${label.toLowerCase()}`
    : `Copy ${label.toLowerCase()}: ${address}`;

  return (
    <div
      className={`inline-flex items-center gap-1.5 rounded-lg border border-white/10 bg-white/5 px-2 py-1 ${className}`}
      role="group"
      aria-label={label}
    >
      {/* Address display */}
      <span
        className={`${sizeClasses[size]} ${mono ? 'font-mono' : ''} ${
          copied ? 'text-[#14F195]' : 'text-gray-300'
        }`}
        title={showTooltip && isTruncated ? address : undefined}
        aria-label={`${label}: ${address}`}
      >
        {truncated}
      </span>

      {/* Copy button */}
      {showCopyButton && (
        <button
          ref={buttonRef}
          type="button"
          onClick={handleCopy}
          onKeyDown={handleKeyDown}
          aria-label={ariaLabel}
          title={copied ? 'Copied!' : copyFailed ? 'Copy failed' : `Copy ${label.toLowerCase()}`}
          className={`inline-flex items-center justify-center rounded transition-colors focus:outline-none focus:ring-2 focus:ring-[#14F195]/50 ${
            copyFailed
              ? 'text-red-400'
              : copied
              ? 'text-[#14F195]'
              : 'text-gray-400 hover:text-[#14F195]'
          }`}
        >
          {copyFailed ? (
            // X icon for failure
            <svg
              className={iconSizeClasses[size]}
              fill="none"
              viewBox="0 0 24 24"
              strokeWidth={2}
              stroke="currentColor"
              aria-hidden="true"
            >
              <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
          ) : copied ? (
            // Checkmark icon
            <svg
              className={iconSizeClasses[size]}
              fill="none"
              viewBox="0 0 24 24"
              strokeWidth={2.5}
              stroke="currentColor"
              aria-hidden="true"
            >
              <path strokeLinecap="round" strokeLinejoin="round" d="M4.5 12.75l6 6 9-13.5" />
            </svg>
          ) : (
            // Copy icon
            <svg
              className={iconSizeClasses[size]}
              fill="none"
              viewBox="0 0 24 24"
              strokeWidth={1.5}
              stroke="currentColor"
              aria-hidden="true"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M15.666 3.888A2.25 2.25 0 0013.5 2.25h-3c-1.03 0-1.9.693-2.166 1.638m7.332 0c.055.194.084.4.084.612v0a.75.75 0 01-.75.75H9a.75.75 0 01-.75-.75v0c0-.212.03-.418.084-.612m7.332 0c.646.049 1.288.11 1.927.184 1.1.128 1.907 1.077 1.907 2.185V19.5a2.25 2.25 0 01-2.25 2.25H6.75A2.25 2.25 0 014.5 19.5V6.257c0-1.108.806-2.057 1.907-2.185a48.208 48.208 0 011.927-.184"
              />
            </svg>
          )}
        </button>
      )}

      {/* Screen reader announcement */}
      {copied && (
        <span className="sr-only" role="status" aria-live="polite">
          {label} copied to clipboard
        </span>
      )}
      {copyFailed && (
        <span className="sr-only" role="status" aria-live="polite">
          Failed to copy {label.toLowerCase()}
        </span>
      )}
    </div>
  );
};

export default CopyAddress;