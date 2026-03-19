# PR Status Tracker Component

A React component for tracking the status of Pull Requests in the SolFoundry bounty system.

## Features

- ✅ Pipeline visualization: Submitted → CI Running → AI Review → Human Review → Approved/Denied → Payout
- ✅ Each stage shows: status (pending/running/pass/fail), timestamp, duration, details
- ✅ AI review stage shows score breakdown (quality, correctness, security, completeness, tests)
- ✅ Payout stage shows tx hash + Solscan link when complete
- ✅ Real-time updates via WebSocket
- ✅ Used on bounty detail page and contributor dashboard
- ✅ Responsive design
- ✅ Dark mode support

## Installation

The component is located at `frontend/src/components/PRStatusTracker.tsx` and is already integrated with the project.

## Usage

### Basic Usage

```tsx
import { PRStatusTracker } from '@/components';

function MyPage() {
  return (
    <PRStatusTracker prNumber={123} />
  );
}
```

### With Bounty ID

```tsx
import { PRStatusTracker } from '@/components';

function BountyDetailPage({ bountyId }: { bountyId: string }) {
  return (
    <PRStatusTracker 
      prNumber={123} 
      bountyId={bountyId}
    />
  );
}
```

### With Custom WebSocket URL

```tsx
import { PRStatusTracker } from '@/components';

function MyPage() {
  return (
    <PRStatusTracker 
      prNumber={123}
      websocketUrl="wss://api.solfoundry.org/api/pr-status/ws"
    />
  );
}
```

### With Custom Styling

```tsx
import { PRStatusTracker } from '@/components';

function MyPage() {
  return (
    <PRStatusTracker 
      prNumber={123}
      className="my-custom-class"
    />
  );
}
```

## Props

| Prop | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `prNumber` | `number` | Yes | - | GitHub PR number |
| `bountyId` | `string` | No | - | Associated bounty ID |
| `websocketUrl` | `string` | No | `'ws://localhost:8000/api/ws/pr-status'` | WebSocket URL for real-time updates |
| `className` | `string` | No | `''` | Additional CSS classes |

## API Endpoints

The component interacts with the following backend endpoints:

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/pr-status/{pr_number}` | Get PR status |
| `GET` | `/api/pr-status` | List PR statuses (with filters) |
| `POST` | `/api/pr-status` | Create PR status |
| `PATCH` | `/api/pr-status/{pr_number}` | Update PR status |
| `POST` | `/api/pr-status/{pr_number}/stage/{stage}` | Update specific stage |
| `POST` | `/api/pr-status/{pr_number}/ai-review` | Update AI review with scores |
| `POST` | `/api/pr-status/{pr_number}/payout` | Update payout info |
| `DELETE` | `/api/pr-status/{pr_number}` | Delete PR status |
| `WS` | `/api/pr-status/ws/{pr_number}` | WebSocket for real-time updates |

## Types

### PRStage

```typescript
type PRStage = 
  | 'submitted'
  | 'ci_running'
  | 'ai_review'
  | 'human_review'
  | 'approved'
  | 'denied'
  | 'payout';
```

### StageStatus

```typescript
type StageStatus = 'pending' | 'running' | 'passed' | 'failed' | 'skipped';
```

### AIReviewScore

```typescript
interface AIReviewScore {
  quality: number;      // 0-10
  correctness: number;  // 0-10
  security: number;     // 0-10
  completeness: number; // 0-10
  tests: number;        // 0-10
  overall: number;      // 0-10
}
```

### PRStatus

```typescript
interface PRStatus {
  prNumber: number;
  prTitle: string;
  prUrl: string;
  author: string;
  bountyId: string;
  bountyTitle: string;
  currentStage: PRStage;
  stages: Record<PRStage, StageDetails>;
  updatedAt: string;
}
```

## Example Integration

### Bounty Detail Page

See `frontend/src/components/examples/PRStatusTrackerExample.tsx` for a complete example of integrating the component into a bounty detail page.

### Contributor Dashboard

See `frontend/src/components/examples/PRStatusTrackerExample.tsx` for a complete example of integrating the component into a contributor dashboard.

## Testing

### Backend Tests

```bash
cd backend
pytest tests/test_pr_status.py
```

### Frontend Tests

```bash
cd frontend
npm test -- PRStatusTracker.test.tsx
```

## Responsive Design

The component is fully responsive and adapts to different screen sizes:

- **Desktop**: Full pipeline visualization with all details
- **Tablet**: Compact layout with essential information
- **Mobile**: Stacked layout with key status indicators

## Dark Mode

The component supports dark mode through Tailwind CSS classes. It automatically adapts to the system theme or can be controlled via the theme toggle in the header.

## WebSocket Events

When connected via WebSocket, the component receives real-time updates:

```json
{
  "pr_number": 123,
  "current_stage": "ci_running",
  "stages": {
    "ci_running": {
      "status": "running",
      "timestamp": "2026-03-19T10:05:00Z"
    }
  }
}
```

## Troubleshooting

### WebSocket Connection Issues

If the WebSocket connection fails:
1. Check that the backend server is running
2. Verify the `websocketUrl` prop is correct
3. Check for CORS issues in the browser console

### API Errors

If the API returns errors:
1. Check the backend logs
2. Verify the PR exists in the database
3. Ensure the API routes are properly registered

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests
5. Submit a PR

## License

MIT