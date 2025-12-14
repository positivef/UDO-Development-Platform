# Multi-Session Architecture Documentation

## 📋 Overview

The Multi-Session Architecture enables multiple terminal windows to work on the same or different projects simultaneously while preventing conflicts and maintaining data consistency. This system is critical for real-world development scenarios where developers use multiple terminals for parallel workflows.

## 🏗️ Architecture Components

### 1. Redis Integration (`redis_client.py`)
- **Purpose**: Centralized state management and distributed locking
- **Features**:
  - Connection pooling (2-50 connections)
  - Distributed lock management with TTL
  - Session state persistence
  - Event pub/sub for real-time communication
  - Conflict tracking and resolution

### 2. Session Manager V2 (`session_manager_v2.py`)
- **Purpose**: Orchestrates multi-terminal session lifecycle
- **Features**:
  - Unique session identification
  - Primary/secondary session roles
  - Resource lock acquisition and release
  - Conflict detection and resolution
  - Heartbeat mechanism for liveness
  - Event broadcasting

### 3. WebSocket Handler (`websocket_handler.py`)
- **Purpose**: Real-time communication between sessions
- **Features**:
  - Session connection management
  - Lock status broadcasting
  - Conflict notifications
  - File change events
  - Cursor position sharing (for collaborative editing)
  - Project-specific channels

### 4. Frontend Components (`session-monitor.tsx`)
- **Purpose**: Visual representation of active sessions and conflicts
- **Features**:
  - Real-time session status display
  - Conflict visualization and resolution UI
  - Lock status indicators
  - Activity timeline
  - WebSocket connection for live updates

## 🔐 Distributed Locking System

### Lock Types
```python
class LockType(Enum):
    FILE = "file"           # File-level locks
    GIT_BRANCH = "git"      # Git operation locks
    PROJECT = "project"     # Project-wide locks
    DATABASE = "database"   # Database operation locks
    EXCLUSIVE = "exclusive" # Exclusive system locks
```

### Lock Acquisition Flow
```
1. Session requests lock for resource
2. Check if lock exists in Redis (atomic SET NX)
3. If available: Grant lock with TTL
4. If unavailable:
   - Check if same session holds it
   - Wait if requested
   - Detect and record conflict
5. Broadcast lock acquisition event
```

### Lock Release Flow
```
1. Verify session owns the lock (Lua script)
2. Atomic delete from Redis
3. Remove from session's lock list
4. Broadcast lock release event
5. Allow waiting sessions to acquire
```

## 🔄 Conflict Detection & Resolution

### Conflict Types
```python
class ConflictType(Enum):
    FILE_EDIT = "file_edit"           # Multiple sessions editing same file
    GIT_MERGE = "git_merge"           # Git operation conflicts
    CONTEXT_SWITCH = "context_switch" # Project context conflicts
    RESOURCE_LOCK = "resource_lock"   # Lock acquisition conflicts
    STATE_DIVERGENCE = "state_divergence" # State inconsistency
```

### Resolution Strategies

1. **Wait and Retry**
   - Session waits for lock release
   - Automatic retry with backoff
   - Timeout after configured period

2. **3-Way Merge**
   - Detect common ancestor
   - Apply both changes if non-conflicting
   - Request manual resolution if conflicting

3. **Coordinated Push**
   - Queue git operations
   - Sequential execution
   - Automatic rebase/merge

4. **Manual Resolution**
   - Notify user via UI
   - Provide conflict details
   - Accept user decision

## 📡 Real-Time Synchronization

### WebSocket Events

#### Client → Server
```javascript
// Lock request
{
  "type": "lock_request",
  "resource_id": "/path/to/file.py",
  "lock_type": "file"
}

// File change notification
{
  "type": "file_change",
  "file_path": "/path/to/file.py",
  "change_type": "edit"
}

// Conflict resolution
{
  "type": "conflict_resolved",
  "conflict_id": "conflict_abc123",
  "resolution": "manual"
}
```

#### Server → Client
```javascript
// Session events
{
  "type": "session_connected",
  "session_id": "term_abc_123",
  "project_id": "proj_xyz"
}

// Lock events
{
  "type": "lock_acquired",
  "session_id": "term_abc_123",
  "resource_id": "/path/to/file.py"
}

// Conflict events
{
  "type": "conflict_detected",
  "conflict_type": "file_edit",
  "resource": "/path/to/file.py",
  "sessions": ["term_abc", "term_def"]
}
```

## 🎯 Use Cases

### 1. Multiple Terminals, Same Project

**Scenario**: Developer has 3 terminals open:
- Terminal 1: Running tests
- Terminal 2: Editing backend code
- Terminal 3: Editing frontend code

**System Behavior**:
- Each terminal gets unique session ID
- Terminal 1 becomes primary session
- File locks prevent simultaneous edits
- Changes broadcast to all terminals
- Test runner aware of file changes

### 2. Multiple Projects in Parallel

**Scenario**: Working on two projects:
- Project A: Feature development
- Project B: Emergency hotfix

**System Behavior**:
- Separate session groups per project
- Independent lock namespaces
- Context switching preserves state
- No interference between projects
- Resource allocation per project

### 3. Collaborative Development

**Scenario**: Two developers on same project:
- Developer A: Backend API
- Developer B: Frontend UI

**System Behavior**:
- Session identification by user
- File-level lock granularity
- Real-time change notifications
- Conflict detection for shared files
- Cursor position sharing (future)

## 🚀 Performance Characteristics

### Redis Operations
- Lock acquisition: <10ms
- Lock release: <5ms
- Event broadcast: <20ms
- Session heartbeat: 30s interval
- Connection pool: 2-50 connections

### WebSocket
- Connection establishment: <100ms
- Message latency: <50ms
- Heartbeat interval: 30s
- Max connections: 1000 concurrent

### Conflict Resolution
- Detection time: <100ms
- Auto-resolution: <500ms
- Manual resolution: User-dependent
- Retry backoff: 100ms, 500ms, 2s

## 🔧 Configuration

### Environment Variables
```bash
# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=optional_password

# WebSocket Configuration
WS_MAX_CONNECTIONS=1000
WS_HEARTBEAT_INTERVAL=30

# Lock Configuration
LOCK_DEFAULT_TTL=300  # 5 minutes
LOCK_WAIT_TIMEOUT=30  # 30 seconds

# Session Configuration
SESSION_TTL=86400     # 24 hours
SESSION_HEARTBEAT=30  # 30 seconds
```

### Redis Keys Structure
```
udo:lock:file:{filepath}          # File locks
udo:lock:git:{branch}              # Git locks
udo:lock:resource:{type}:{id}     # Generic locks

udo:session:{id}:data              # Session data
udo:session:{id}:heartbeat         # Session liveness
udo:session:{id}:locks             # Session's held locks

udo:project:{id}:sessions          # Project's active sessions
udo:project:{id}:state             # Project state
udo:project:{id}:conflicts         # Project conflicts

udo:channel:session                # Session events channel
udo:channel:project:{id}           # Project events channel
udo:channel:conflicts              # Conflict events channel
```

## 🧪 Testing Scenarios

### Unit Tests
1. Lock acquisition and release
2. Conflict detection logic
3. Session lifecycle management
4. Event broadcasting

### Integration Tests
1. Multi-session lock contention
2. WebSocket connection handling
3. Redis failover behavior
4. Conflict resolution workflows

### Load Tests
1. 100 concurrent sessions
2. 1000 lock operations/second
3. 10MB/s event traffic
4. Network partition resilience

## 📊 Monitoring & Metrics

### Key Metrics
- Active sessions count
- Lock contention rate
- Conflict frequency
- Resolution success rate
- WebSocket connection count
- Redis memory usage
- Event throughput

### Health Checks
- Redis connectivity
- WebSocket server status
- Session manager state
- Lock table integrity
- Conflict queue size

## 🚨 Error Handling

### Failure Modes
1. **Redis Unavailable**: Fallback to in-memory mode
2. **WebSocket Disconnect**: Auto-reconnect with backoff
3. **Lock Timeout**: Auto-release and notification
4. **Session Crash**: Cleanup locks and state
5. **Network Partition**: Split-brain prevention

### Recovery Strategies
1. Automatic reconnection
2. State reconciliation
3. Lock cleanup on timeout
4. Conflict queue persistence
5. Manual intervention UI

## 🔮 Future Enhancements

1. **Operational Transformation (OT)**
   - Real-time collaborative editing
   - Character-level conflict resolution
   - CRDT implementation

2. **Session Recording**
   - Command history
   - Replay capability
   - Audit logging

3. **AI-Assisted Conflict Resolution**
   - Smart merge strategies
   - Pattern-based resolution
   - Predictive lock acquisition

4. **Performance Optimizations**
   - Lock-free data structures
   - Optimistic locking
   - Caching layer

## 🎓 Best Practices

1. **Always use unique session IDs** for each terminal
2. **Acquire locks before file operations** to prevent conflicts
3. **Release locks promptly** after operations complete
4. **Handle WebSocket disconnections** gracefully
5. **Implement retry logic** for transient failures
6. **Monitor lock contention** and optimize access patterns
7. **Use appropriate lock granularity** (file vs directory)
8. **Implement heartbeats** to detect dead sessions
9. **Clean up resources** on session termination
10. **Test conflict scenarios** thoroughly

---

## 📚 References

- [Redis Documentation](https://redis.io/docs/)
- [WebSocket API](https://developer.mozilla.org/en-US/docs/Web/API/WebSocket)
- [Distributed Locking Patterns](https://martin.kleppmann.com/2016/02/08/how-to-do-distributed-locking.html)
- [Conflict-Free Replicated Data Types](https://crdt.tech/)
- [Operational Transformation](https://en.wikipedia.org/wiki/Operational_transformation)

---

**Version**: 1.0.0
**Last Updated**: 2024-11-17
**Authors**: UDO Development Team