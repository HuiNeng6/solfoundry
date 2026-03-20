## 🏭 Bounty T2: Real-time WebSocket Server

Closes #17

### ✅ 实现功能

- [x] WebSocket endpoint: `/ws` with JWT authentication
- [x] Channels: `bounties`, `prs`, `payouts`, `leaderboard`
- [x] Subscribe to specific bounty: `{"type": "subscribe", "scope": "repo", "target_id": "repo_123"}`
- [x] Event format: `{"event": "pr_status_changed", "timestamp": "...", "data": {...}}`
- [x] Connection auth (JWT token in query param)
- [x] Heartbeat/ping-pong for connection health
- [x] Redis pub/sub backend for horizontal scaling
- [x] Rate limiting per connection
- [x] Comprehensive tests + connection stress test

### 📁 文件变更

| 文件 | 说明 |
|------|------|
| `backend/app/api/websocket.py` | WebSocket API 端点 (483行) |
| `backend/app/services/websocket_manager.py` | 连接管理器 + Redis pub/sub (576行) |
| `backend/tests/test_websocket.py` | 完整测试套件 (627行) |
| `backend/app/main.py` | 集成 WebSocket 路由 |
| `backend/requirements.txt` | 添加 redis 依赖 |

### 🔧 技术栈

- FastAPI WebSocket
- Redis pub/sub
- JWT 认证
- 异步心跳机制

### 💰 钱包地址

`Amu1YJjcKWKL6xuMTo2dx511kfzXAxgpetJrZp7N71o7`

---

**评分要求:** ≥7/10 | **赏金:** 400,000 $FNDRY