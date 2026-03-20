# GitHub ↔ Platform Bi-directional Sync

> Implements Issue #28: GitHub ↔ Platform Bi-directional Sync

## Overview

This feature enables automatic bi-directional synchronization between GitHub issues and platform bounties. Changes on either side reflect on both, keeping everything in perfect sync.

## Features

### GitHub → Platform Sync

1. **Issue Created with Bounty Label**
   - Automatically creates a bounty record in the database
   - Maps GitHub labels to bounty tier and category
   - Sets reward based on tier (T1: 100,000, T2: 450,000, T3: 1,000,000 $FNDRY)

2. **Issue Labeled/Unlabeled**
   - Updates bounty tier when tier label changes
   - Updates bounty category when category label changes
   - Tracks status changes

3. **Issue Closed**
   - Updates bounty status to `completed`
   - Triggers payout workflow if applicable

### Platform → GitHub Sync

1. **Bounty Created via Wizard**
   - Creates GitHub issue with proper template
   - Adds labels: `bounty`, `tier-N`, and status
   - Links GitHub issue URL to bounty

2. **Bounty Claimed**
   - Bot comments on the GitHub issue
   - Updates issue status

3. **Bounty Status Changed**
   - Updates GitHub issue state (open/closed)

### Conflict Resolution

When both sides change simultaneously:
- **GitHub is source of truth** (per requirements)
- Platform data is overwritten with GitHub data
- Conflict is logged for audit trail

### Retry Queue

Failed sync operations are:
- Added to a retry queue
- Retried automatically (max 3 retries)
- Visible in sync status dashboard

### Sync Status Dashboard

Provides visibility into sync operations:
- Last sync time
- Last successful sync time
- Pending syncs count
- Failed syncs count
- Total syncs count
- Last error message
- List of pending and failed items

## API Endpoints

### `POST /api/github/sync/issue/{issue_number}`

Manually trigger sync of a GitHub issue to platform bounty.

**Parameters:**
- `issue_number`: GitHub issue number
- `repository`: Repository full name (e.g., `SolFoundry/solfoundry`)
- `action`: Issue action (default: `opened`)

### `POST /api/github/sync/bounty/{bounty_id}`

Manually trigger sync of a platform bounty to GitHub issue.

**Parameters:**
- `bounty_id`: Platform bounty ID

### `POST /api/github/sync/comment/{bounty_id}`

Post a comment on the GitHub issue associated with a bounty.

**Parameters:**
- `bounty_id`: Platform bounty ID
- `comment`: Comment text

### `GET /api/github/sync/status`

Get sync status dashboard.

**Returns:**
```json
{
  "last_sync_at": "2026-03-20T16:30:00Z",
  "last_successful_sync_at": "2026-03-20T16:30:00Z",
  "pending_syncs_count": 0,
  "failed_syncs_count": 1,
  "total_syncs_count": 10,
  "last_error": "Connection timeout",
  "last_error_at": "2026-03-20T15:00:00Z",
  "pending_items": [],
  "failed_items": [...]
}
```

### `POST /api/github/sync/retry`

Retry failed sync operations.

**Parameters:**
- `max_retries`: Maximum retry count (default: 3)

### `POST /api/github/sync/resolve-conflict/{bounty_id}`

Manually resolve a sync conflict.

**Parameters:**
- `bounty_id`: Platform bounty ID
- `github_data`: GitHub issue data
- `platform_data`: Platform bounty data

### `GET /api/github/sync/pending`

List pending sync operations.

**Parameters:**
- `limit`: Maximum items to return (default: 100)

## Configuration

### Environment Variables

- `GITHUB_TOKEN`: GitHub Personal Access Token with repo scope
- `GITHUB_DEFAULT_REPO`: Default repository for creating issues (default: `SolFoundry/solfoundry`)

### Label Mapping

**Tier Labels:**
- `tier-1` → BountyTier.T1 (100,000 $FNDRY)
- `tier-2` → BountyTier.T2 (450,000 $FNDRY)
- `tier-3` → BountyTier.T3 (1,000,000 $FNDRY)

**Category Labels:**
- `frontend` → frontend
- `backend`, `api`, `python`, `fastapi` → backend
- `smart_contract`, `smart-contract` → smart_contract
- `documentation` → documentation
- `testing` → testing
- `infrastructure` → infrastructure

## Database Models

### SyncQueueDB

Tracks sync operations for retry:
- `direction`: github_to_platform or platform_to_github
- `event_type`: Type of sync event
- `status`: pending, in_progress, completed, failed
- `retry_count`: Number of retry attempts
- `max_retries`: Maximum retries (default: 3)
- `error_message`: Error details if failed

### SyncStatusDB

Tracks overall sync status:
- `last_sync_at`: Timestamp of last sync attempt
- `last_successful_sync_at`: Timestamp of last successful sync
- `pending_syncs_count`: Number of pending syncs
- `failed_syncs_count`: Number of failed syncs
- `total_syncs_count`: Total syncs performed
- `last_error`: Last error message
- `last_error_at`: Timestamp of last error

## Testing

Run tests with:

```bash
cd backend
pytest tests/test_github_sync.py -v
```

## Future Improvements

1. **Celery Integration**
   - Use Celery for async task processing
   - Implement scheduled sync checks
   - Better retry handling with exponential backoff

2. **Webhook Receiver**
   - Integrate with existing webhook endpoint
   - Automatic sync on GitHub events
   - Event filtering and routing

3. **Conflict Resolution UI**
   - Dashboard for reviewing conflicts
   - Manual resolution interface
   - Resolution history

4. **Sync Metrics**
   - Success rate tracking
   - Performance metrics
   - Alerting on failures

## Files Created/Modified

- `backend/app/models/github_sync.py` - Sync models
- `backend/app/services/github_sync_service.py` - Core sync logic
- `backend/app/api/github_sync.py` - API endpoints
- `backend/tests/test_github_sync.py` - Test suite
- `backend/app/main.py` - Router registration

## License

MIT