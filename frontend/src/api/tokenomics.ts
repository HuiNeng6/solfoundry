/**
 * Tokenomics and Treasury API service.
 * Provides functions for fetching FNDRY token and treasury data.
 * @module api/tokenomics
 */

import { apiFetch, withRetry } from './client';
import type { TokenomicsData, TreasuryStats } from '../types/tokenomics';

/** API response type for tokenomics */
interface ApiTokenomics {
  token_name?: string;
  tokenName?: string;
  token_ca?: string;
  tokenCA?: string;
  total_supply?: number;
  totalSupply?: number;
  circulating_supply?: number;
  circulatingSupply?: number;
  treasury_holdings?: number;
  treasuryHoldings?: number;
  total_distributed?: number;
  totalDistributed?: number;
  total_buybacks?: number;
  totalBuybacks?: number;
  total_burned?: number;
  totalBurned?: number;
  fee_revenue_sol?: number;
  feeRevenueSol?: number;
  last_updated?: string;
  lastUpdated?: string;
  distribution_breakdown?: Record<string, number>;
  distributionBreakdown?: Record<string, number>;
}

/** API response type for treasury stats */
interface ApiTreasury {
  sol_balance?: number;
  solBalance?: number;
  fndry_balance?: number;
  fndryBalance?: number;
  treasury_wallet?: string;
  treasuryWallet?: string;
  total_paid_out_fndry?: number;
  totalPaidOutFndry?: number;
  total_paid_out_sol?: number;
  totalPaidOutSol?: number;
  total_payouts?: number;
  totalPayouts?: number;
  total_buyback_amount?: number;
  totalBuybackAmount?: number;
  total_buybacks?: number;
  totalBuybacks?: number;
  last_updated?: string;
  lastUpdated?: string;
}

/** Map API tokenomics to frontend TokenomicsData type */
function mapApiTokenomics(t: ApiTokenomics): TokenomicsData {
  return {
    tokenName: t.token_name || t.tokenName || 'FNDRY',
    tokenCA: t.token_ca || t.tokenCA || '',
    totalSupply: t.total_supply || t.totalSupply || 0,
    circulatingSupply: t.circulating_supply || t.circulatingSupply || 0,
    treasuryHoldings: t.treasury_holdings || t.treasuryHoldings || 0,
    totalDistributed: t.total_distributed || t.totalDistributed || 0,
    totalBuybacks: t.total_buybacks || t.totalBuybacks || 0,
    totalBurned: t.total_burned || t.totalBurned || 0,
    feeRevenueSol: t.fee_revenue_sol || t.feeRevenueSol || 0,
    lastUpdated: t.last_updated || t.lastUpdated || new Date().toISOString(),
    distributionBreakdown: t.distribution_breakdown || t.distributionBreakdown || {
      contributor_rewards: 0,
      treasury_reserve: 0,
      buybacks: 0,
      burned: 0,
    },
  };
}

/** Map API treasury to frontend TreasuryStats type */
function mapApiTreasury(t: ApiTreasury): TreasuryStats {
  return {
    solBalance: t.sol_balance || t.solBalance || 0,
    fndryBalance: t.fndry_balance || t.fndryBalance || 0,
    treasuryWallet: t.treasury_wallet || t.treasuryWallet || '',
    totalPaidOutFndry: t.total_paid_out_fndry || t.totalPaidOutFndry || 0,
    totalPaidOutSol: t.total_paid_out_sol || t.totalPaidOutSol || 0,
    totalPayouts: t.total_payouts || t.totalPayouts || 0,
    totalBuybackAmount: t.total_buyback_amount || t.totalBuybackAmount || 0,
    totalBuybacks: t.total_buybacks || t.totalBuybacks || 0,
    lastUpdated: t.last_updated || t.lastUpdated || new Date().toISOString(),
  };
}

/** Fetch tokenomics data */
export async function fetchTokenomics(): Promise<TokenomicsData | null> {
  try {
    const response = await withRetry(() =>
      apiFetch<ApiTokenomics>('/api/payouts/tokenomics')
    );
    return mapApiTokenomics(response);
  } catch {
    return null;
  }
}

/** Fetch treasury stats */
export async function fetchTreasuryStats(): Promise<TreasuryStats | null> {
  try {
    const response = await withRetry(() =>
      apiFetch<ApiTreasury>('/api/payouts/treasury')
    );
    return mapApiTreasury(response);
  } catch {
    return null;
  }
}

/** Fetch both tokenomics and treasury data */
export async function fetchTreasuryData(): Promise<{
  tokenomics: TokenomicsData | null;
  treasury: TreasuryStats | null;
}> {
  try {
    const [tokenomics, treasury] = await Promise.all([
      fetchTokenomics(),
      fetchTreasuryStats(),
    ]);
    return { tokenomics, treasury };
  } catch {
    return { tokenomics: null, treasury: null };
  }
}