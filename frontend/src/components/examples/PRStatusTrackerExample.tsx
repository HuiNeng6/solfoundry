/**
 * Example usage of PRStatusTracker in bounty detail page
 * 
 * This file demonstrates how to integrate the PRStatusTracker component
 * into the bounty detail page and contributor dashboard.
 */

'use client';

import React, { useState } from 'react';
import { PRStatusTracker } from '../PRStatusTracker';

/**
 * Example: Bounty Detail Page
 * 
 * Shows the PR status tracker for all submissions to a specific bounty.
 */
export function BountyDetailPage({ bountyId }: { bountyId: string }) {
  const [selectedPr, setSelectedPr] = useState<number | null>(null);

  // Mock PR list - in real app, fetch from API
  const mockPRs = [
    { number: 123, title: 'Fix: Implement PR status tracker', author: 'developer1', status: 'ci_running' },
    { number: 124, title: 'Feature: Add WebSocket support', author: 'developer2', status: 'ai_review' },
    { number: 125, title: 'Refactor: Clean up component', author: 'developer3', status: 'approved' },
  ];

  return (
    <div className="max-w-4xl mx-auto p-6">
      <h1 className="text-2xl font-bold mb-6">Bounty: {bountyId}</h1>
      
      {/* PR List */}
      <div className="mb-6">
        <h2 className="text-lg font-semibold mb-4">Submissions</h2>
        <div className="space-y-2">
          {mockPRs.map((pr) => (
            <button
              key={pr.number}
              onClick={() => setSelectedPr(pr.number)}
              className={`w-full text-left p-4 rounded-lg border transition-colors ${
                selectedPr === pr.number
                  ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                  : 'border-gray-200 dark:border-gray-700 hover:border-gray-300'
              }`}
            >
              <div className="flex items-center justify-between">
                <div>
                  <span className="font-medium">#{pr.number}</span>
                  <span className="ml-2">{pr.title}</span>
                </div>
                <span className="text-sm text-gray-500">by {pr.author}</span>
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* Selected PR Status Tracker */}
      {selectedPr && (
        <div className="border rounded-lg p-6 bg-white dark:bg-gray-800">
          <PRStatusTracker
            prNumber={selectedPr}
            bountyId={bountyId}
            websocketUrl="ws://localhost:8000/api/pr-status/ws"
          />
        </div>
      )}
    </div>
  );
}

/**
 * Example: Contributor Dashboard
 * 
 * Shows the PR status tracker for all submissions by a contributor.
 */
export function ContributorDashboard({ username }: { username: string }) {
  const [selectedPr, setSelectedPr] = useState<number | null>(null);

  // Mock user's PRs - in real app, fetch from API
  const mockPRs = [
    { 
      number: 123, 
      title: 'Fix: Implement PR status tracker', 
      bountyTitle: 'Bounty T1: PR Status Tracker Component',
      status: 'ci_running' 
    },
    { 
      number: 120, 
      title: 'Feature: Add notification system', 
      bountyTitle: 'Bounty T2: Notification System',
      status: 'approved' 
    },
    { 
      number: 115, 
      title: 'Fix: Resolve database connection issue', 
      bountyTitle: 'Bounty T1: Database Fix',
      status: 'payout' 
    },
  ];

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'approved':
      case 'payout':
        return 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400';
      case 'denied':
        return 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400';
      case 'ci_running':
      case 'ai_review':
      case 'human_review':
        return 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400';
      default:
        return 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300';
    }
  };

  return (
    <div className="max-w-6xl mx-auto p-6">
      <h1 className="text-2xl font-bold mb-6">My Submissions</h1>
      
      {/* Stats Overview */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
        <div className="bg-white dark:bg-gray-800 rounded-lg p-4 border">
          <div className="text-sm text-gray-500 dark:text-gray-400">Total Submissions</div>
          <div className="text-2xl font-bold">12</div>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-lg p-4 border">
          <div className="text-sm text-gray-500 dark:text-gray-400">Approved</div>
          <div className="text-2xl font-bold text-green-600 dark:text-green-400">8</div>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-lg p-4 border">
          <div className="text-sm text-gray-500 dark:text-gray-400">In Progress</div>
          <div className="text-2xl font-bold text-blue-600 dark:text-blue-400">3</div>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-lg p-4 border">
          <div className="text-sm text-gray-500 dark:text-gray-400">Total Earned</div>
          <div className="text-2xl font-bold text-purple-600 dark:text-purple-400">450,000 $FNDRY</div>
        </div>
      </div>

      {/* PR List */}
      <div className="mb-6">
        <h2 className="text-lg font-semibold mb-4">Recent Submissions</h2>
        <div className="space-y-2">
          {mockPRs.map((pr) => (
            <button
              key={pr.number}
              onClick={() => setSelectedPr(pr.number)}
              className={`w-full text-left p-4 rounded-lg border transition-colors ${
                selectedPr === pr.number
                  ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                  : 'border-gray-200 dark:border-gray-700 hover:border-gray-300'
              }`}
            >
              <div className="flex items-center justify-between">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="font-medium">#{pr.number}</span>
                    <span className="truncate">{pr.title}</span>
                  </div>
                  <div className="text-sm text-gray-500 dark:text-gray-400 truncate">
                    {pr.bountyTitle}
                  </div>
                </div>
                <span className={`ml-4 px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(pr.status)}`}>
                  {pr.status.replace('_', ' ').toUpperCase()}
                </span>
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* Selected PR Status Tracker */}
      {selectedPr && (
        <div className="border rounded-lg p-6 bg-white dark:bg-gray-800">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold">Submission Status</h3>
            <button
              onClick={() => setSelectedPr(null)}
              className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
            >
              Close
            </button>
          </div>
          <PRStatusTracker
            prNumber={selectedPr}
            websocketUrl="ws://localhost:8000/api/pr-status/ws"
          />
        </div>
      )}
    </div>
  );
}

/**
 * Example: Standalone PR Status Page
 * 
 * A dedicated page to view PR status.
 */
export function PRStatusPage({ prNumber }: { prNumber: number }) {
  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 py-8">
      <div className="max-w-2xl mx-auto px-4">
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6">
          <PRStatusTracker
            prNumber={prNumber}
            websocketUrl="ws://localhost:8000/api/pr-status/ws"
          />
        </div>
      </div>
    </div>
  );
}

export default BountyDetailPage;