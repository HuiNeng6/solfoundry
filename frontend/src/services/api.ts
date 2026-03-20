import axios from 'axios';
import type { DashboardResponse, EarningsStats, ReputationStats, BountyHistoryItem } from '../types/dashboard';

const API_BASE_URL = '/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const dashboardApi = {
  /**
   * Get full dashboard data for a contributor
   */
  async getDashboard(contributorId: string): Promise<DashboardResponse> {
    const response = await api.get<DashboardResponse>(`/dashboard/${contributorId}`);
    return response.data;
  },

  /**
   * Get earnings statistics for a contributor
   */
  async getEarnings(contributorId: string): Promise<EarningsStats> {
    const response = await api.get<EarningsStats>(`/dashboard/${contributorId}/earnings`);
    return response.data;
  },

  /**
   * Get reputation statistics for a contributor
   */
  async getReputation(contributorId: string): Promise<ReputationStats> {
    const response = await api.get<ReputationStats>(`/dashboard/${contributorId}/reputation`);
    return response.data;
  },

  /**
   * Get bounty history for a contributor
   */
  async getBountyHistory(
    contributorId: string,
    options?: { status?: string; limit?: number; offset?: number }
  ): Promise<BountyHistoryItem[]> {
    const params = new URLSearchParams();
    if (options?.status) params.append('status', options.status);
    if (options?.limit) params.append('limit', options.limit.toString());
    if (options?.offset) params.append('offset', options.offset.toString());
    
    const response = await api.get<BountyHistoryItem[]>(
      `/dashboard/${contributorId}/bounty-history?${params.toString()}`
    );
    return response.data;
  },
};

export default api;