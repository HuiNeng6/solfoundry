/**
 * OnboardingWizard — Guided first-time contributor onboarding flow.
 * Walks new users through connecting wallet, picking skills, and finding their first bounty.
 * @module OnboardingWizard
 */
'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { mockBounties } from '../data/mockBounties';
import type { Bounty } from '../types/bounty';

// ── Types ────────────────────────────────────────────────────────────────────

interface OnboardingState {
  hasOnboarded: boolean;
  currentStep: number;
  walletAddress: string | null;
  selectedSkills: string[];
  skipped: boolean;
}

interface OnboardingWizardProps {
  onComplete?: () => void;
  onSkip?: () => void;
  isOpen?: boolean;
}

// ── Constants ─────────────────────────────────────────────────────────────────

const ONBOARDING_KEY = 'sf_onboarded';
const ONBOARDING_STATE_KEY = 'sf_onboarding_state';

const ALL_SKILLS = [
  'React', 'TypeScript', 'JavaScript', 'Python', 'Rust', 'Solidity',
  'Node.js', 'FastAPI', 'Anchor', 'Solana', 'Security', 'Content',
  'Community', 'Twitter', 'Go', 'Next.js', 'GraphQL', 'Docker'
];

// ── Step Components ───────────────────────────────────────────────────────────

/** Step 1: Welcome — Introduction to SolFoundry */
function WelcomeStep({ onNext }: { onNext: () => void }) {
  return (
    <div className="flex flex-col items-center text-center space-y-6 p-4">
      <div className="w-20 h-20 rounded-full bg-gradient-to-br from-[#9945FF] to-[#14F195] flex items-center justify-center">
        <span className="text-4xl">🏭</span>
      </div>
      <div className="space-y-3">
        <h1 className="text-2xl md:text-3xl font-bold text-white">
          Welcome to <span className="text-[#14F195]">SolFoundry</span>
        </h1>
        <p className="text-gray-400 max-w-md">
          The Autonomous Software Factory on Solana. Earn bounties by contributing code, 
          and get paid in $FNDRY tokens.
        </p>
      </div>
      
      <div className="w-full max-w-md space-y-4 text-left">
        <div className="p-4 rounded-xl bg-surface-100 border border-gray-700">
          <h3 className="font-semibold text-white mb-2">🎯 What are Bounties?</h3>
          <p className="text-sm text-gray-400">
            Bounties are paid tasks posted by projects. Complete the task, submit your PR, 
            and earn $FNDRY rewards.
          </p>
        </div>
        
        <div className="p-4 rounded-xl bg-surface-100 border border-gray-700">
          <h3 className="font-semibold text-white mb-2">🤖 AI-Powered Review</h3>
          <p className="text-sm text-gray-400">
            Our multi-LLM pipeline reviews your submissions automatically. 
            Quality code wins faster payouts.
          </p>
        </div>
        
        <div className="p-4 rounded-xl bg-surface-100 border border-gray-700">
          <h3 className="font-semibold text-white mb-2">🏆 Tier System</h3>
          <p className="text-sm text-gray-400">
            T1 (Quick Wins) → T2 (Feature Work) → T3 (Major Projects). 
            Start small, build reputation, level up.
          </p>
        </div>
      </div>
      
      <button
        onClick={onNext}
        className="w-full max-w-md py-3 px-6 rounded-lg bg-gradient-to-r from-[#9945FF] to-[#14F195] text-white font-semibold hover:opacity-90 transition-opacity"
      >
        Get Started
      </button>
    </div>
  );
}

/** Step 2: Connect Wallet — Solana wallet connection */
function ConnectWalletStep({ 
  walletAddress, 
  onConnect, 
  onNext, 
  onSkip 
}: { 
  walletAddress: string | null;
  onConnect: () => void;
  onNext: () => void;
  onSkip: () => void;
}) {
  const [isConnecting, setIsConnecting] = useState(false);

  const handleConnect = () => {
    setIsConnecting(true);
    // Mock wallet connection
    setTimeout(() => {
      onConnect();
      setIsConnecting(false);
    }, 1000);
  };

  return (
    <div className="flex flex-col items-center text-center space-y-6 p-4">
      <div className="w-16 h-16 rounded-full bg-[#9945FF]/20 flex items-center justify-center">
        <span className="text-3xl">💼</span>
      </div>
      
      <div className="space-y-2">
        <h2 className="text-2xl font-bold text-white">Connect Your Wallet</h2>
        <p className="text-gray-400 max-w-md">
          Connect your Solana wallet to claim bounties and receive $FNDRY payouts.
        </p>
      </div>
      
      {walletAddress ? (
        <div className="w-full max-w-md space-y-4">
          <div className="p-4 rounded-xl bg-[#14F195]/10 border border-[#14F195]/30">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-full bg-[#14F195] flex items-center justify-center">
                <span className="text-xl">✓</span>
              </div>
              <div className="text-left">
                <p className="text-sm text-gray-400">Wallet Connected</p>
                <p className="font-mono text-sm text-[#14F195]">
                  {walletAddress.slice(0, 8)}...{walletAddress.slice(-8)}
                </p>
              </div>
            </div>
          </div>
          <button
            onClick={onNext}
            className="w-full py-3 px-6 rounded-lg bg-[#14F195] text-black font-semibold hover:bg-[#14F195]/90 transition-colors"
          >
            Continue
          </button>
        </div>
      ) : (
        <div className="w-full max-w-md space-y-4">
          <button
            onClick={handleConnect}
            disabled={isConnecting}
            className="w-full py-3 px-6 rounded-lg bg-gradient-to-r from-[#9945FF] to-[#14F195] text-white font-semibold hover:opacity-90 transition-opacity disabled:opacity-50 flex items-center justify-center gap-2"
          >
            {isConnecting ? (
              <>
                <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                Connecting...
              </>
            ) : (
              <>
                <img 
                  src="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 128 128'%3E%3Cdefs%3E%3ClinearGradient id='a' x1='50%25' y1='0%25' x2='50%25' y2='100%25'%3E%3Cstop offset='0%25' stop-color='%23AB9DFF'/%3E%3Cstop offset='100%25' stop-color='%239945FF'/%3E%3C/linearGradient%3E%3C/defs%3E%3Crect fill='url(%23a)' width='128' height='128' rx='16'/%3E%3Cpath d='M64 16c-26.5 0-48 21.5-48 48s21.5 48 48 48 48-21.5 48-48-21.5-48-48-48zm0 86c-21 0-38-17-38-38s17-38 38-38 38 17 38 38-17 38-38 38z' fill='%2314F195'/%3E%3Ccircle cx='64' cy='64' r='20' fill='%2314F195'/%3E%3C/svg%3E"
                  alt="Phantom"
                  className="w-5 h-5"
                />
                Connect with Phantom
              </>
            )}
          </button>
          
          <div className="flex items-center gap-4">
            <div className="flex-1 h-px bg-gray-700" />
            <span className="text-sm text-gray-500">or</span>
            <div className="flex-1 h-px bg-gray-700" />
          </div>
          
          <button
            onClick={onSkip}
            className="w-full py-3 px-6 rounded-lg border border-gray-600 text-gray-300 font-medium hover:bg-gray-800 transition-colors"
          >
            Skip for now — Browse bounties first
          </button>
          
          <p className="text-xs text-gray-500">
            You can connect your wallet later from the header.
          </p>
        </div>
      )}
    </div>
  );
}

/** Step 3: Pick Your Skills — Skill tag selection */
function PickSkillsStep({ 
  selectedSkills, 
  onToggleSkill, 
  onNext, 
  onSkip 
}: { 
  selectedSkills: string[];
  onToggleSkill: (skill: string) => void;
  onNext: () => void;
  onSkip: () => void;
}) {
  const skillCategories = {
    'Frontend': ['React', 'TypeScript', 'JavaScript', 'Next.js', 'GraphQL'],
    'Backend': ['Python', 'Node.js', 'FastAPI', 'Go', 'Rust'],
    'Blockchain': ['Solana', 'Solidity', 'Anchor', 'Security'],
    'Other': ['Docker', 'Content', 'Community', 'Twitter']
  };

  return (
    <div className="flex flex-col items-center text-center space-y-6 p-4">
      <div className="w-16 h-16 rounded-full bg-[#14F195]/20 flex items-center justify-center">
        <span className="text-3xl">⚡</span>
      </div>
      
      <div className="space-y-2">
        <h2 className="text-2xl font-bold text-white">Pick Your Skills</h2>
        <p className="text-gray-400 max-w-md">
          Select the skills you're proficient in. We'll recommend bounties that match your expertise.
        </p>
      </div>
      
      <div className="w-full max-w-md space-y-4">
        {Object.entries(skillCategories).map(([category, skills]) => (
          <div key={category} className="text-left">
            <h3 className="text-sm font-medium text-gray-400 mb-2">{category}</h3>
            <div className="flex flex-wrap gap-2">
              {skills.map(skill => {
                const isSelected = selectedSkills.includes(skill);
                return (
                  <button
                    key={skill}
                    onClick={() => onToggleSkill(skill)}
                    className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-all ${
                      isSelected
                        ? 'bg-[#9945FF] text-white border border-[#9945FF]'
                        : 'bg-surface-100 text-gray-300 border border-gray-700 hover:border-gray-600'
                    }`}
                  >
                    {skill}
                    {isSelected && <span className="ml-1">✓</span>}
                  </button>
                );
              })}
            </div>
          </div>
        ))}
      </div>
      
      <div className="w-full max-w-md flex gap-3">
        <button
          onClick={onSkip}
          className="flex-1 py-3 px-6 rounded-lg border border-gray-600 text-gray-300 font-medium hover:bg-gray-800 transition-colors"
        >
          Skip
        </button>
        <button
          onClick={onNext}
          disabled={selectedSkills.length === 0}
          className="flex-1 py-3 px-6 rounded-lg bg-gradient-to-r from-[#9945FF] to-[#14F195] text-white font-semibold hover:opacity-90 transition-opacity disabled:opacity-50"
        >
          Continue {selectedSkills.length > 0 && `(${selectedSkills.length})`}
        </button>
      </div>
    </div>
  );
}

/** Step 4: Your First Bounty — Recommended bounties based on skills */
function FirstBountyStep({ 
  selectedSkills, 
  onComplete, 
  onSkip 
}: { 
  selectedSkills: string[];
  onComplete: () => void;
  onSkip: () => void;
}) {
  // Get T1 bounties that match selected skills
  const recommendedBounties = mockBounties
    .filter(b => b.tier === 'T1' && b.status === 'open')
    .filter(b => b.skills.some(s => selectedSkills.includes(s)))
    .slice(0, 3);

  // If no skill match, show any T1 bounties
  const displayBounties = recommendedBounties.length > 0 
    ? recommendedBounties 
    : mockBounties.filter(b => b.tier === 'T1' && b.status === 'open').slice(0, 3);

  return (
    <div className="flex flex-col items-center text-center space-y-6 p-4">
      <div className="w-16 h-16 rounded-full bg-gradient-to-br from-[#9945FF] to-[#14F195] flex items-center justify-center">
        <span className="text-3xl">🎯</span>
      </div>
      
      <div className="space-y-2">
        <h2 className="text-2xl font-bold text-white">Your First Bounty</h2>
        <p className="text-gray-400 max-w-md">
          Based on your skills, here are some bounties we think you'd be great at!
        </p>
      </div>
      
      <div className="w-full max-w-md space-y-3">
        {displayBounties.map((bounty: Bounty) => (
          <div 
            key={bounty.id}
            className="p-4 rounded-xl bg-surface-100 border border-gray-700 hover:border-[#9945FF]/50 transition-colors text-left"
          >
            <div className="flex items-start justify-between gap-3">
              <div className="flex-1">
                <h4 className="font-semibold text-white mb-1">{bounty.title}</h4>
                <div className="flex flex-wrap gap-1 mb-2">
                  {bounty.skills.slice(0, 3).map(skill => (
                    <span 
                      key={skill}
                      className={`text-xs px-2 py-0.5 rounded ${
                        selectedSkills.includes(skill) 
                          ? 'bg-[#9945FF]/20 text-[#9945FF]' 
                          : 'bg-surface-200 text-gray-400'
                      }`}
                    >
                      {skill}
                    </span>
                  ))}
                </div>
                <p className="text-sm text-gray-500 line-clamp-2">{bounty.description}</p>
              </div>
              <div className="text-right shrink-0">
                <p className="text-lg font-bold text-[#14F195]">
                  {bounty.rewardAmount.toLocaleString()}
                </p>
                <p className="text-xs text-gray-500">$FNDRY</p>
              </div>
            </div>
          </div>
        ))}
      </div>
      
      <div className="w-full max-w-md flex gap-3">
        <button
          onClick={onSkip}
          className="flex-1 py-3 px-6 rounded-lg border border-gray-600 text-gray-300 font-medium hover:bg-gray-800 transition-colors"
        >
          Browse All
        </button>
        <button
          onClick={onComplete}
          className="flex-1 py-3 px-6 rounded-lg bg-[#14F195] text-black font-semibold hover:bg-[#14F195]/90 transition-colors"
        >
          Start Contributing 🚀
        </button>
      </div>
    </div>
  );
}

// ── Progress Indicator ────────────────────────────────────────────────────────

function ProgressIndicator({ currentStep, totalSteps }: { currentStep: number; totalSteps: number }) {
  return (
    <div className="flex items-center justify-center gap-2 mb-6">
      {Array.from({ length: totalSteps }, (_, i) => (
        <div
          key={i}
          className={`h-2 rounded-full transition-all duration-300 ${
            i === currentStep 
              ? 'w-8 bg-gradient-to-r from-[#9945FF] to-[#14F195]' 
              : i < currentStep 
                ? 'w-2 bg-[#14F195]' 
                : 'w-2 bg-gray-700'
          }`}
        />
      ))}
    </div>
  );
}

// ── Main Component ────────────────────────────────────────────────────────────

export function OnboardingWizard({ 
  onComplete, 
  onSkip, 
  isOpen = true 
}: OnboardingWizardProps) {
  const [state, setState] = useState<OnboardingState>({
    hasOnboarded: false,
    currentStep: 0,
    walletAddress: null,
    selectedSkills: [],
    skipped: false
  });
  
  const [isAnimating, setIsAnimating] = useState(false);

  // Load state from localStorage on mount
  useEffect(() => {
    try {
      const stored = localStorage.getItem(ONBOARDING_STATE_KEY);
      const hasOnboarded = localStorage.getItem(ONBOARDING_KEY);
      
      if (hasOnboarded === 'true') {
        setState(prev => ({ ...prev, hasOnboarded: true }));
        return;
      }
      
      if (stored) {
        const parsed = JSON.parse(stored);
        setState(prev => ({ ...prev, ...parsed }));
      }
    } catch (e) {
      console.error('Failed to load onboarding state:', e);
    }
  }, []);

  // Save state to localStorage whenever it changes
  useEffect(() => {
    try {
      localStorage.setItem(ONBOARDING_STATE_KEY, JSON.stringify(state));
    } catch (e) {
      console.error('Failed to save onboarding state:', e);
    }
  }, [state]);

  const goToNextStep = useCallback(() => {
    setIsAnimating(true);
    setTimeout(() => {
      setState(prev => ({ ...prev, currentStep: prev.currentStep + 1 }));
      setIsAnimating(false);
    }, 150);
  }, []);

  const handleSkip = useCallback(() => {
    localStorage.setItem(ONBOARDING_KEY, 'true');
    setState(prev => ({ ...prev, hasOnboarded: true, skipped: true }));
    onSkip?.();
  }, [onSkip]);

  const handleComplete = useCallback(() => {
    localStorage.setItem(ONBOARDING_KEY, 'true');
    setState(prev => ({ ...prev, hasOnboarded: true }));
    onComplete?.();
  }, [onComplete]);

  const handleConnectWallet = useCallback(() => {
    // Mock wallet address
    const mockAddress = 'Amu1YJjcKWKL6xuMTo2dx511kfzXAxgpetJrZp7N71o7';
    setState(prev => ({ ...prev, walletAddress: mockAddress }));
  }, []);

  const handleToggleSkill = useCallback((skill: string) => {
    setState(prev => ({
      ...prev,
      selectedSkills: prev.selectedSkills.includes(skill)
        ? prev.selectedSkills.filter(s => s !== skill)
        : [...prev.selectedSkills, skill]
    }));
  }, []);

  // Don't render if already onboarded or not open
  if (state.hasOnboarded || !isOpen) {
    return null;
  }

  const steps = [
    <WelcomeStep key="welcome" onNext={goToNextStep} />,
    <ConnectWalletStep 
      key="wallet" 
      walletAddress={state.walletAddress}
      onConnect={handleConnectWallet}
      onNext={goToNextStep}
      onSkip={handleSkip}
    />,
    <PickSkillsStep 
      key="skills"
      selectedSkills={state.selectedSkills}
      onToggleSkill={handleToggleSkill}
      onNext={goToNextStep}
      onSkip={handleSkip}
    />,
    <FirstBountyStep 
      key="bounty"
      selectedSkills={state.selectedSkills}
      onComplete={handleComplete}
      onSkip={handleSkip}
    />
  ];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4">
      <div className="w-full max-w-lg rounded-2xl bg-surface border border-gray-700 shadow-2xl overflow-hidden">
        {/* Header with close button */}
        <div className="flex items-center justify-between p-4 border-b border-gray-800">
          <ProgressIndicator currentStep={state.currentStep} totalSteps={steps.length} />
          <button
            onClick={handleSkip}
            className="text-gray-500 hover:text-white transition-colors"
            aria-label="Close onboarding"
          >
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        
        {/* Step content with animation */}
        <div className={`p-6 transition-opacity duration-150 ${isAnimating ? 'opacity-0' : 'opacity-100'}`}>
          {steps[state.currentStep]}
        </div>
      </div>
    </div>
  );
}

// ── Hook for checking onboarding status ───────────────────────────────────────

export function useOnboardingStatus() {
  const [hasOnboarded, setHasOnboarded] = useState<boolean | null>(null);

  useEffect(() => {
    const stored = localStorage.getItem(ONBOARDING_KEY);
    setHasOnboarded(stored === 'true');
  }, []);

  const resetOnboarding = useCallback(() => {
    localStorage.removeItem(ONBOARDING_KEY);
    localStorage.removeItem(ONBOARDING_STATE_KEY);
    setHasOnboarded(false);
  }, []);

  return { hasOnboarded, resetOnboarding };
}

// ── Get Started Button Component ──────────────────────────────────────────────

export function GetStartedButton({ 
  onClick 
}: { 
  onClick?: () => void;
}) {
  return (
    <button
      onClick={onClick}
      className="inline-flex items-center gap-2 px-6 py-3 rounded-lg bg-gradient-to-r from-[#9945FF] to-[#14F195] text-white font-semibold hover:opacity-90 transition-opacity"
    >
      <span>Get Started</span>
      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
      </svg>
    </button>
  );
}

export default OnboardingWizard;