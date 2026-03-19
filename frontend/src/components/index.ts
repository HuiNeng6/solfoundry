/**
 * Components index
 * 
 * Export all components from this file for easy importing.
 */

// PR Status Tracker
export { 
  PRStatusTracker,
  default as PRStatusTrackerDefault
} from './PRStatusTracker';

export type {
  PRStage,
  StageStatus,
  AIReviewScore,
  StageDetails,
  PRStatus,
  PRStatusTrackerProps
} from './PRStatusTracker';

// Layout components
export { Header } from './layout/Header';
export { Sidebar } from './layout/Sidebar';
export { ThemeToggle } from './layout/ThemeToggle';

// UI components
export { ResponsiveTable, BountyTableExample } from './ui/ResponsiveTable';
export { ResponsiveChart, ResponsiveStatsGrid } from './ui/ResponsiveChart';

// Example components (for documentation purposes)
export {
  BountyDetailPage,
  ContributorDashboard,
  PRStatusPage
} from './examples/PRStatusTrackerExample';