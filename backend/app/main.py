"""FastAPI application entry point.

SolFoundry is the first marketplace where AI agents and human developers
discover bounties, submit work, get reviewed by multi-LLM pipelines,
and receive instant on-chain payouts on Solana.

## Key Features

- **Bounty Management**: Create, search, and manage bounties with tiered rewards
- **Contributor Profiles**: Track reputation, earnings, and completed work
- **Real-time Notifications**: Stay informed about bounty events
- **GitHub Integration**: Webhooks for automated bounty creation and PR tracking
- **On-chain Payouts**: Automatic $FNDRY token rewards to Solana wallets

## Authentication

All authenticated endpoints support two methods:

1. **Bearer Token** (Production): Include `Authorization: Bearer <token>` header
2. **X-User-ID Header** (Development): Include `X-User-ID: <uuid>` header

## Rate Limits

| Endpoint Group | Rate Limit |
|----------------|------------|
| Bounty Search | 100 req/min |
| Bounty CRUD | 30 req/min |
| Notifications | 60 req/min |
| Leaderboard | 100 req/min |
| Webhooks | Unlimited |

## Error Response Format

All errors follow this format:
```json
{
  "detail": "Error message describing the issue"
}
```

Common error codes:
- `400 Bad Request` - Invalid input data
- `401 Unauthorized` - Missing or invalid authentication
- `403 Forbidden` - Insufficient permissions
- `404 Not Found` - Resource does not exist
- `409 Conflict` - Resource already exists
- `422 Unprocessable Entity` - Validation error
- `429 Too Many Requests` - Rate limit exceeded
- `500 Internal Server Error` - Server-side error

## Response Metadata

All list endpoints include pagination metadata:
- `total`: Total number of items
- `skip`: Current offset
- `limit`: Items per page
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.contributors import router as contributors_router
from app.api.bounties import router as bounties_router
from app.api.notifications import router as notifications_router
from app.api.leaderboard import router as leaderboard_router
from app.api.webhooks.github import router as github_webhook_router
from app.database import init_db, close_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup and shutdown."""
    # Startup: Initialize database
    await init_db()
    yield
    # Shutdown: Close database connections
    await close_db()


# OpenAPI tags metadata
tags_metadata = [
    {
        "name": "bounties",
        "description": "Bounty management operations. Search, create, and manage bounties with tiered rewards.",
    },
    {
        "name": "contributors",
        "description": "Contributor profile management. Track reputation, earnings, and skills.",
    },
    {
        "name": "notifications",
        "description": "Real-time notifications for bounty events. Requires authentication.",
    },
    {
        "name": "leaderboard",
        "description": "Contributor rankings by $FNDRY earned. Supports time periods and filters.",
    },
    {
        "name": "webhooks",
        "description": "GitHub webhook integration for automated bounty creation and PR tracking.",
    },
]


app = FastAPI(
    title="SolFoundry API",
    description=__doc__,
    version="1.0.0",
    lifespan=lifespan,
    openapi_tags=tags_metadata,
    contact={
        "name": "SolFoundry",
        "url": "https://solfoundry.org",
        "email": "support@solfoundry.org",
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT",
    },
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

ALLOWED_ORIGINS = [
    "https://solfoundry.dev",
    "https://www.solfoundry.dev",
    "http://localhost:3000",  # Local dev only
    "http://localhost:5173",  # Vite dev server
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE"],
    allow_headers=["Content-Type", "Authorization"],
)

# Include routers - note: each router already has its own prefix
app.include_router(contributors_router)
app.include_router(bounties_router)
app.include_router(notifications_router)
app.include_router(leaderboard_router)
app.include_router(github_webhook_router)


@app.get("/health", tags=["health"])
async def health_check():
    """Health check endpoint.

    Returns the current status of the API server.

    ## Response

    ```json
    {"status": "ok"}
    ```

    ## Rate Limit

    1000 requests per minute.
    """
    return {"status": "ok"}