/**
 * OnboardingWizard.test.tsx — Tests for contributor onboarding flow.
 */
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { OnboardingWizard, useOnboardingStatus, GetStartedButton } from './OnboardingWizard';

// ── Mock localStorage ─────────────────────────────────────────────────────────

const localStorageMock = (() => {
  let store: Record<string, string> = {};
  return {
    getItem: vi.fn((key: string) => store[key] || null),
    setItem: vi.fn((key: string, value: string) => { store[key] = value; }),
    removeItem: vi.fn((key: string) => { delete store[key]; }),
    clear: vi.fn(() => { store = {}; })
  };
})();

Object.defineProperty(window, 'localStorage', { value: localStorageMock });

// ── Tests ─────────────────────────────────────────────────────────────────────

describe('OnboardingWizard', () => {
  beforeEach(() => {
    localStorageMock.clear();
    vi.clearAllMocks();
  });

  describe('Initial Rendering', () => {
    it('renders the welcome step initially', () => {
      render(<OnboardingWizard />);
      expect(screen.getByText(/Welcome to/i)).toBeInTheDocument();
      expect(screen.getByText('SolFoundry')).toBeInTheDocument();
    });

    it('does not render if hasOnboarded is true in localStorage', async () => {
      localStorageMock.setItem('sf_onboarded', 'true');
      
      render(<OnboardingWizard />);
      
      await waitFor(() => {
        expect(screen.queryByText(/Welcome to/i)).not.toBeInTheDocument();
      });
    });

    it('does not render if isOpen is false', () => {
      render(<OnboardingWizard isOpen={false} />);
      expect(screen.queryByText(/Welcome to/i)).not.toBeInTheDocument();
    });
  });

  describe('Step Navigation', () => {
    it('shows progress indicator with correct number of steps', () => {
      render(<OnboardingWizard />);
      // 4 steps = 4 dots
      const dots = document.querySelectorAll('.h-2.rounded-full');
      expect(dots).toHaveLength(4);
    });

    it('progresses from Step 1 to Step 2 when clicking Get Started', async () => {
      render(<OnboardingWizard />);
      
      fireEvent.click(screen.getByText('Get Started'));
      
      await waitFor(() => {
        expect(screen.getByText('Connect Your Wallet')).toBeInTheDocument();
      });
    });

    it('allows skipping wallet connection', async () => {
      const onSkip = vi.fn();
      render(<OnboardingWizard onSkip={onSkip} />);
      
      // Go to step 2
      fireEvent.click(screen.getByText('Get Started'));
      
      await waitFor(() => {
        expect(screen.getByText('Connect Your Wallet')).toBeInTheDocument();
      });
      
      // Skip wallet connection
      fireEvent.click(screen.getByText(/Skip for now/i));
      
      // Should call onSkip and mark as onboarded
      expect(onSkip).toHaveBeenCalled();
      expect(localStorageMock.setItem).toHaveBeenCalledWith('sf_onboarded', 'true');
    });
  });

  describe('Wallet Connection (Mock)', () => {
    it('shows connecting state when connecting wallet', async () => {
      render(<OnboardingWizard />);
      
      // Go to step 2
      fireEvent.click(screen.getByText('Get Started'));
      
      await waitFor(() => {
        expect(screen.getByText(/Connect with Phantom/i)).toBeInTheDocument();
      });
      
      // Click connect
      fireEvent.click(screen.getByText(/Connect with Phantom/i));
      
      // Should show connecting state
      expect(screen.getByText('Connecting...')).toBeInTheDocument();
    });

    it('shows wallet address after successful connection', async () => {
      render(<OnboardingWizard />);
      
      // Go to step 2
      fireEvent.click(screen.getByText('Get Started'));
      
      await waitFor(() => {
        expect(screen.getByText(/Connect with Phantom/i)).toBeInTheDocument();
      });
      
      // Click connect
      fireEvent.click(screen.getByText(/Connect with Phantom/i));
      
      // Wait for connection to complete
      await waitFor(() => {
        expect(screen.getByText(/Wallet Connected/i)).toBeInTheDocument();
      }, { timeout: 2000 });
    });

    it('can continue after wallet connection', async () => {
      render(<OnboardingWizard />);
      
      // Go to step 2
      fireEvent.click(screen.getByText('Get Started'));
      await waitFor(() => screen.getByText(/Connect with Phantom/i));
      
      // Connect wallet
      fireEvent.click(screen.getByText(/Connect with Phantom/i));
      await waitFor(() => screen.getByText(/Wallet Connected/i), { timeout: 2000 });
      
      // Continue to step 3
      fireEvent.click(screen.getByText('Continue'));
      
      await waitFor(() => {
        expect(screen.getByText('Pick Your Skills')).toBeInTheDocument();
      });
    });
  });

  describe('Skill Selection', () => {
    it('renders skill categories', async () => {
      render(<OnboardingWizard />);
      
      // Go through steps to reach skill selection
      fireEvent.click(screen.getByText('Get Started'));
      await waitFor(() => screen.getByText('Connect Your Wallet'));
      fireEvent.click(screen.getByText(/Connect with Phantom/i));
      await waitFor(() => screen.getByText(/Wallet Connected/i), { timeout: 2000 });
      fireEvent.click(screen.getByText('Continue'));
      
      await waitFor(() => {
        expect(screen.getByText('Pick Your Skills')).toBeInTheDocument();
      });
      
      // Check skill categories are rendered
      expect(screen.getByText('Frontend')).toBeInTheDocument();
      expect(screen.getByText('Backend')).toBeInTheDocument();
      expect(screen.getByText('Blockchain')).toBeInTheDocument();
    });

    it('allows selecting and deselecting skills', async () => {
      render(<OnboardingWizard />);
      
      // Navigate to skill step via wallet connection
      fireEvent.click(screen.getByText('Get Started'));
      await waitFor(() => screen.getByText('Connect Your Wallet'));
      fireEvent.click(screen.getByText(/Connect with Phantom/i));
      await waitFor(() => screen.getByText(/Wallet Connected/i), { timeout: 2000 });
      fireEvent.click(screen.getByText('Continue'));
      await waitFor(() => screen.getByText('Pick Your Skills'));
      
      // Select a skill
      const reactButton = screen.getByRole('button', { name: /React/ });
      fireEvent.click(reactButton);
      
      // Should show checkmark and update count
      expect(screen.getByText(/Continue \(1\)/)).toBeInTheDocument();
      
      // Deselect
      fireEvent.click(reactButton);
      expect(screen.getByText('Continue')).toBeInTheDocument();
    });

    it('disables continue button when no skills selected', async () => {
      render(<OnboardingWizard />);
      
      // Navigate to skill step
      fireEvent.click(screen.getByText('Get Started'));
      await waitFor(() => screen.getByText('Connect Your Wallet'));
      fireEvent.click(screen.getByText(/Connect with Phantom/i));
      await waitFor(() => screen.getByText(/Wallet Connected/i), { timeout: 2000 });
      fireEvent.click(screen.getByText('Continue'));
      await waitFor(() => screen.getByText('Pick Your Skills'));
      
      // Continue should be disabled
      const continueBtn = screen.getByText('Continue');
      expect(continueBtn).toBeDisabled();
    });
  });

  describe('Bounty Recommendations', () => {
    it('shows recommended bounties based on selected skills', async () => {
      render(<OnboardingWizard />);
      
      // Navigate through steps
      fireEvent.click(screen.getByText('Get Started'));
      await waitFor(() => screen.getByText('Connect Your Wallet'));
      fireEvent.click(screen.getByText(/Connect with Phantom/i));
      await waitFor(() => screen.getByText(/Wallet Connected/i), { timeout: 2000 });
      fireEvent.click(screen.getByText('Continue'));
      await waitFor(() => screen.getByText('Pick Your Skills'));
      
      // Select TypeScript skill
      fireEvent.click(screen.getByRole('button', { name: /TypeScript/ }));
      fireEvent.click(screen.getByText(/Continue/));
      
      await waitFor(() => {
        expect(screen.getByText('Your First Bounty')).toBeInTheDocument();
      });
      
      // Should show bounties
      expect(screen.getByText(/\$FNDRY/)).toBeInTheDocument();
    });

    it('allows completing onboarding', async () => {
      const onComplete = vi.fn();
      render(<OnboardingWizard onComplete={onComplete} />);
      
      // Navigate through all steps
      fireEvent.click(screen.getByText('Get Started'));
      await waitFor(() => screen.getByText('Connect Your Wallet'));
      fireEvent.click(screen.getByText(/Connect with Phantom/i));
      await waitFor(() => screen.getByText(/Wallet Connected/i), { timeout: 2000 });
      fireEvent.click(screen.getByText('Continue'));
      await waitFor(() => screen.getByText('Pick Your Skills'));
      fireEvent.click(screen.getByRole('button', { name: /TypeScript/ }));
      fireEvent.click(screen.getByText(/Continue/));
      await waitFor(() => screen.getByText('Your First Bounty'));
      
      // Complete onboarding
      fireEvent.click(screen.getByText(/Start Contributing/i));
      
      expect(onComplete).toHaveBeenCalled();
      expect(localStorageMock.setItem).toHaveBeenCalledWith('sf_onboarded', 'true');
    });
  });

  describe('Skip Functionality', () => {
    it('allows skipping at any step via header close button', async () => {
      const onSkip = vi.fn();
      render(<OnboardingWizard onSkip={onSkip} />);
      
      // Click close button
      const closeBtn = screen.getByLabelText('Close onboarding');
      fireEvent.click(closeBtn);
      
      expect(onSkip).toHaveBeenCalled();
      expect(localStorageMock.setItem).toHaveBeenCalledWith('sf_onboarded', 'true');
    });

    it('allows skipping at step 2', async () => {
      const onSkip = vi.fn();
      render(<OnboardingWizard onSkip={onSkip} />);
      
      fireEvent.click(screen.getByText('Get Started'));
      await waitFor(() => screen.getByText('Connect Your Wallet'));
      fireEvent.click(screen.getByText(/Skip for now/i));
      
      expect(onSkip).toHaveBeenCalled();
      expect(localStorageMock.setItem).toHaveBeenCalledWith('sf_onboarded', 'true');
    });

    it('allows skipping at step 3 via skip button', async () => {
      const onSkip = vi.fn();
      render(<OnboardingWizard onSkip={onSkip} />);
      
      // Navigate to step 3
      fireEvent.click(screen.getByText('Get Started'));
      await waitFor(() => screen.getByText('Connect Your Wallet'));
      fireEvent.click(screen.getByText(/Connect with Phantom/i));
      await waitFor(() => screen.getByText(/Wallet Connected/i), { timeout: 2000 });
      fireEvent.click(screen.getByText('Continue'));
      await waitFor(() => screen.getByText('Pick Your Skills'));
      
      // Click Skip button (not the Skip for now from step 2)
      const skipButtons = screen.getAllByText('Skip');
      fireEvent.click(skipButtons[0]);
      
      expect(onSkip).toHaveBeenCalled();
    });
  });

  describe('State Persistence', () => {
    it('saves state to localStorage', async () => {
      render(<OnboardingWizard />);
      
      fireEvent.click(screen.getByText('Get Started'));
      
      await waitFor(() => {
        expect(localStorageMock.setItem).toHaveBeenCalledWith(
          'sf_onboarding_state',
          expect.stringContaining('"currentStep":1')
        );
      });
    });

    it('restores state from localStorage on mount', async () => {
      // Pre-set state
      localStorageMock.setItem('sf_onboarding_state', JSON.stringify({
        currentStep: 2,
        walletAddress: null,
        selectedSkills: ['React'],
        skipped: false
      }));
      
      render(<OnboardingWizard />);
      
      await waitFor(() => {
        expect(screen.getByText('Pick Your Skills')).toBeInTheDocument();
      });
    });
  });

  describe('Responsive Design', () => {
    it('renders correctly on mobile viewport', () => {
      render(<OnboardingWizard />);
      
      // Check that the modal container has proper mobile classes
      const container = document.querySelector('.max-w-lg');
      expect(container).toBeInTheDocument();
    });
  });
});

describe('useOnboardingStatus', () => {
  beforeEach(() => {
    localStorageMock.clear();
    vi.clearAllMocks();
  });

  it('returns hasOnboarded as true when localStorage is set', async () => {
    localStorageMock.setItem('sf_onboarded', 'true');
    
    const { result } = renderHook(() => useOnboardingStatus());
    
    await waitFor(() => {
      expect(result.current.hasOnboarded).toBe(true);
    });
  });

  it('returns hasOnboarded as false when localStorage is not set', async () => {
    const { result } = renderHook(() => useOnboardingStatus());
    
    await waitFor(() => {
      expect(result.current.hasOnboarded).toBe(false);
    });
  });

  it('resetOnboarding clears localStorage and sets hasOnboarded to false', async () => {
    localStorageMock.setItem('sf_onboarded', 'true');
    
    const { result } = renderHook(() => useOnboardingStatus());
    
    // Wait for initial state
    await waitFor(() => {
      expect(result.current.hasOnboarded).toBe(true);
    });
    
    // Reset
    act(() => {
      result.current.resetOnboarding();
    });
    
    // Should be false now
    await waitFor(() => {
      expect(result.current.hasOnboarded).toBe(false);
    });
    
    expect(localStorageMock.removeItem).toHaveBeenCalledWith('sf_onboarded');
    expect(localStorageMock.removeItem).toHaveBeenCalledWith('sf_onboarding_state');
  });
});

describe('GetStartedButton', () => {
  it('renders with correct text', () => {
    render(<GetStartedButton />);
    expect(screen.getByText('Get Started')).toBeInTheDocument();
  });

  it('calls onClick when clicked', () => {
    const onClick = vi.fn();
    render(<GetStartedButton onClick={onClick} />);
    
    fireEvent.click(screen.getByText('Get Started'));
    expect(onClick).toHaveBeenCalled();
  });
});

// Helper for renderHook
function renderHook<T>(hook: () => T) {
  let result: { current: T } = { current: null as unknown as T };
  
  function TestComponent() {
    result.current = hook();
    return null;
  }
  
  render(<TestComponent />);
  
  return { result };
}