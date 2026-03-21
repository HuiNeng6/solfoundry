/**
 * App — Root component with full routing and layout.
 * All pages wrapped in WalletProvider + SiteLayout.
 * @module App
 */
import { lazy, Suspense, useState, useEffect, useCallback } from 'react';
import { BrowserRouter, Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { useWallet } from '@solana/wallet-adapter-react';
import { WalletProvider } from './components/wallet/WalletProvider';
import { SiteLayout } from './components/layout/SiteLayout';
import { OnboardingWizard, useOnboardingStatus, GetStartedButton } from './components/OnboardingWizard';

// ── Lazy-loaded page components ──────────────────────────────────────────────
const BountiesPage = lazy(() => import('./pages/BountiesPage'));
const BountyDetailPage = lazy(() => import('./pages/BountyDetailPage'));
const BountyCreatePage = lazy(() => import('./pages/BountyCreatePage'));
const LeaderboardPage = lazy(() => import('./pages/LeaderboardPage'));
const AgentMarketplacePage = lazy(() => import('./pages/AgentMarketplacePage'));
const AgentProfilePage = lazy(() => import('./pages/AgentProfilePage'));
const TokenomicsPage = lazy(() => import('./pages/TokenomicsPage'));
const ContributorProfilePage = lazy(() => import('./pages/ContributorProfilePage'));
const DashboardPage = lazy(() => import('./pages/DashboardPage'));
const CreatorDashboardPage = lazy(() => import('./pages/CreatorDashboardPage'));
const DisputeResolutionPage = lazy(() => import('./pages/DisputeResolutionPage'));

// ── Loading spinner ──────────────────────────────────────────────────────────
function LoadingSpinner() {
  return (
    <div className="flex items-center justify-center min-h-[60vh]">
      <div className="flex flex-col items-center gap-4">
        <div className="w-8 h-8 border-2 border-[#9945FF] border-t-transparent rounded-full animate-spin" />
        <p className="text-sm text-gray-400 font-mono">Loading...</p>
      </div>
    </div>
  );
}

// ── Layout wrapper that reads wallet state ───────────────────────────────────
function AppLayout() {
  const location = useLocation();
  const { publicKey, connect, disconnect } = useWallet();
  const walletAddress = publicKey?.toBase58() ?? null;
  const { hasOnboarded } = useOnboardingStatus();
  const [showOnboarding, setShowOnboarding] = useState(false);

  // Show onboarding automatically for first-time visitors
  useEffect(() => {
    if (hasOnboarded === false) {
      // Small delay for better UX
      const timer = setTimeout(() => setShowOnboarding(true), 500);
      return () => clearTimeout(timer);
    }
  }, [hasOnboarded]);

  const handleOnboardingComplete = useCallback(() => {
    setShowOnboarding(false);
  }, []);

  const handleOnboardingSkip = useCallback(() => {
    setShowOnboarding(false);
  }, []);

  return (
    <>
      <SiteLayout
        currentPath={location.pathname}
        walletAddress={walletAddress}
        onConnectWallet={() => connect().catch(console.error)}
        onDisconnectWallet={() => disconnect().catch(console.error)}
      >
        <Suspense fallback={<LoadingSpinner />}>
          <Routes>
            {/* Bounties */}
            <Route path="/" element={<Navigate to="/bounties" replace />} />
            <Route path="/bounties" element={<BountiesPage />} />
            <Route path="/bounties/:id" element={<BountyDetailPage />} />
            <Route path="/bounties/create" element={<BountyCreatePage />} />

            {/* Leaderboard */}
            <Route path="/leaderboard" element={<LeaderboardPage />} />

            {/* Agents */}
            <Route path="/agents" element={<AgentMarketplacePage />} />
            <Route path="/agents/:agentId" element={<AgentProfilePage />} />

            {/* Tokenomics */}
            <Route path="/tokenomics" element={<TokenomicsPage />} />

            {/* Contributor and Creator */}
            <Route path="/profile/:username" element={<ContributorProfilePage />} />
            <Route path="/dashboard" element={<DashboardPage />} />
            <Route path="/creator" element={<CreatorDashboardPage />} />

            {/* Disputes */}
            <Route path="/disputes" element={<DisputeResolutionPage />} />
            <Route path="/disputes/:id" element={<DisputeResolutionPage />} />

            {/* Fallback */}
            <Route path="*" element={<Navigate to="/bounties" replace />} />
          </Routes>
        </Suspense>
      </SiteLayout>

      {/* Onboarding Wizard */}
      <OnboardingWizard
        isOpen={showOnboarding}
        onComplete={handleOnboardingComplete}
        onSkip={handleOnboardingSkip}
      />
    </>
  );
}

// ── Root App ─────────────────────────────────────────────────────────────────
export default function App() {
  return (
    <BrowserRouter>
      <WalletProvider defaultNetwork="mainnet-beta">
        <AppLayout />
      </WalletProvider>
    </BrowserRouter>
  );
}
