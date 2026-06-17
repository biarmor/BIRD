# BIRD System Architecture

## System Overview

The BIRD (Business Intelligence Reasoning & Deployment) system is a sophisticated multi-agent architecture designed for intelligent analysis, reasoning, and marketing campaign deployment. The system combines specialized agents, adaptive planning, and advanced retrieval-augmented reasoning to deliver enterprise-grade intelligence capabilities.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     API Layer (FastAPI)                      │
├─────────────────────────────────────────────────────────────┤
│  /intelligence  │  /vault  │  /forge  │  /attack  │ /auth   │
└────────┬────────────────────────────────────────────────────┘
         │
┌────────▼──────────────────────────────────────────────────────┐
│              Orchestration Layer                              │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │  Orchestrator Agent (Query Routing & Coordination)       │ │
│  │  Adaptive Planning Agent (Dynamic Task Scheduling)       │ │
│  └──────────────────────────────────────────────────────────┘ │
└────────┬──────────────────────────────────────────────────────┘
         │
┌────────▼──────────────────────────────────────────────────────┐
│              Multi-Agent Layer                                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │ Vault Agent  │  │ Reasoning    │  │ Debate Agent │       │
│  │ (Memory)     │  │ Agent        │  │ (Validation) │       │
│  └──────────────┘  └──────────────┘  └──────────────┘       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │ RAR Agent    │  │ Forge Agent  │  │ Attack Agent │       │
│  │ (Reasoning)  │  │ (Generation) │  │ (Deployment) │       │
│  └──────────────┘  └──────────────┘  └──────────────┘       │
└────────┬──────────────────────────────────────────────────────┘
         │
┌────────▼──────────────────────────────────────────────────────┐
│              Data & Storage Layer                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │ SQLite/      │  │ ChromaDB     │  │ Cache Layer  │       │
│  │ PostgreSQL   │  │ (Embeddings) │  │ (Redis)      │       │
│  └──────────────┘  └──────────────┘  └──────────────┘       │
└────────┬──────────────────────────────────────────────────────┘
         │
┌────────▼──────────────────────────────────────────────────────┐
│              External Services                                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │ Ollama       │  │ Web APIs     │  │ LLM Services │       │
│  │ (Local LLMs) │  │ (Radar)      │  │ (Frontier)   │       │
│  └──────────────┘  └──────────────┘  └──────────────┘       │
└────────────────────────────────────────────────────────────────┘
```

## Agent Architecture

### 1. Orchestrator Agent

**Purpose:** Routes queries to appropriate agents and coordinates multi-agent execution.

**Capabilities:**
- Query analysis and classification
- Agent selection based on query type
- Sequential and parallel execution modes
- Result aggregation and synthesis
- Performance tracking

**Execution Modes:**
- **Sequential**: Agents execute one after another
- **Parallel**: Agents execute concurrently
- **Adaptive**: Mode selected based on query complexity

**Key Metrics:**
- Execution time: 100-500ms per query
- Success rate: >95%
- Token efficiency: 80-90% local models

### 2. Vault Agent

**Purpose:** Manages intelligent memory with semantic search and multi-hop retrieval.

**Capabilities:**
- Fact storage with embeddings
- Multi-hop semantic retrieval (up to 5 hops)
- Memory quality scoring
- Recency-weighted ranking
- Conflict detection and resolution
- Semantic deduplication

**Data Structure:**
```python
VaultFact:
  - id: unique identifier
  - fact: text content
  - embedding: vector representation
  - category: classification
  - confidence: quality score
  - created_at: timestamp
  - metadata: tags, source, etc.
```

**Retrieval Algorithm:**
1. Embed query using sentence-transformers
2. Semantic search with cosine similarity
3. Multi-hop expansion (retrieve related facts)
4. Quality scoring (recency + confidence)
5. Deduplication and conflict resolution

### 3. Reasoning Agent

**Purpose:** Performs multi-step logical reasoning and causal analysis.

**Capabilities:**
- Causal inference and hypothesis generation
- Multi-step reasoning chains
- Evidence evaluation
- Confidence scoring per step
- Reasoning chain tracking
- Explanation generation

**Reasoning Types:**
- **Deductive**: From general to specific
- **Inductive**: From specific to general
- **Abductive**: Inference to best explanation
- **Causal**: Cause-effect relationships

### 4. Debate Agent

**Purpose:** Validates conclusions through multi-perspective debate.

**Capabilities:**
- Multi-perspective analysis (5 perspectives)
- Argument generation and evaluation
- Consensus building
- Conflict resolution
- Claim validation
- Perspective synthesis

**Debate Perspectives:**
1. **Optimistic**: Best-case scenario
2. **Pessimistic**: Worst-case scenario
3. **Pragmatic**: Realistic assessment
4. **Analytical**: Data-driven perspective
5. **Creative**: Alternative viewpoint

### 5. Adaptive Planning Agent

**Purpose:** Creates and executes adaptive plans with dynamic task scheduling.

**Capabilities:**
- Dynamic task scheduling
- Dependency management
- Parallel and sequential execution
- Failure recovery with replanning
- Performance optimization
- Adaptive confidence scoring

**Task Priorities:**
- **Critical**: Must execute
- **High**: Important for accuracy
- **Medium**: Enhances results
- **Low**: Optional optimization

### 6. RAR Agent (Retrieval-Augmented Reasoning)

**Purpose:** Performs advanced reasoning with external knowledge retrieval.

**Capabilities:**
- Multi-hop reasoning with retrieval
- Retrieval context management
- Evidence-based reasoning
- Automatic next-query generation
- Reasoning verification
- Explanation generation

**RAR Pipeline:**
1. Initial query analysis
2. Retrieve relevant facts from vault
3. Perform reasoning step
4. Generate next query if needed
5. Repeat until convergence
6. Synthesize final conclusion

### 7. Forge Agent

**Purpose:** Generates marketing assets and content.

**Capabilities:**
- Multi-format asset generation
- Tone customization
- Quality scoring
- Campaign variation generation
- Content optimization
- Asset tracking

**Supported Asset Types:**
- Social posts
- Email campaigns
- Blog posts
- Landing pages
- Ad copy
- Video scripts
- Presentations

### 8. Attack Agent

**Purpose:** Manages campaign deployment and execution.

**Capabilities:**
- Campaign creation and management
- Multi-channel deployment
- Scheduling and timing
- Performance monitoring
- Budget management
- Campaign lifecycle management

**Supported Channels:**
- Social media
- Email
- Web
- SMS
- Push notifications
- Direct mail

## Data Flow

### Intelligence Analysis Flow

```
User Query
    ↓
Orchestrator (Route)
    ↓
┌─────────────────────────────────────┐
│ Parallel Agent Execution            │
├─────────────────────────────────────┤
│ Vault Agent → Retrieve Facts        │
│ Reasoning Agent → Analyze           │
│ Debate Agent → Validate             │
└─────────────────────────────────────┘
    ↓
Result Aggregation
    ↓
Confidence Scoring
    ↓
Response to User
```

### Campaign Deployment Flow

```
Marketing Strategy
    ↓
Forge Agent (Generate Assets)
    ↓
Asset Variations (3-5 versions)
    ↓
Attack Agent (Create Campaign)
    ↓
Target Audience Selection
    ↓
Channel Configuration
    ↓
Campaign Deployment
    ↓
Performance Monitoring
    ↓
Optimization & Reporting
```

## Database Schema

### Core Tables

```sql
-- Users and Sessions
users (id, email, password_hash, created_at)
sessions (id, user_id, token, expires_at)

-- Workspaces
workspaces (id, owner_id, name, description)

-- Intelligence
intelligence_queries (id, workspace_id, query, mode, status, result)
reasoning_chains (id, query_id, steps, confidence)

-- Vault
vault_facts (id, workspace_id, fact, embedding, category, confidence)
memory_quality_scores (id, fact_id, score, timestamp)

-- Campaigns
campaigns (id, workspace_id, name, status, budget, start_date, end_date)
campaign_executions (id, campaign_id, channel, target_id, status, metrics)
campaign_targets (id, workspace_id, name, size, demographics)

-- Assets
generated_assets (id, type, content, tone, quality_score, created_at)
```

## API Endpoints

### Intelligence Endpoints
- `POST /api/v2/intelligence/analyze` - Multi-agent analysis
- `GET /api/v2/intelligence/{id}` - Get query results
- `GET /api/v2/intelligence/{id}/reasoning` - Get reasoning chain
- `POST /api/v2/intelligence/reason` - Reasoning analysis
- `POST /api/v2/intelligence/debate` - Debate conclusion

### Vault Endpoints
- `POST /api/v2/vault/facts` - Add fact
- `GET /api/v2/vault/search` - Search vault
- `GET /api/v2/vault/stats` - Get statistics

### Forge Endpoints
- `POST /api/v2/forge/generate` - Generate asset
- `POST /api/v2/forge/campaign` - Generate campaign

### Attack Endpoints
- `POST /api/v2/attack/campaigns` - Create campaign
- `POST /api/v2/attack/campaigns/{id}/deploy` - Deploy campaign
- `GET /api/v2/attack/campaigns/{id}/metrics` - Get metrics

## Performance Characteristics

### Latency

| Operation | Latency | Notes |
|-----------|---------|-------|
| Query orchestration | 100-500ms | Depends on agent count |
| Vault search | 50-200ms | With multi-hop retrieval |
| Reasoning analysis | 200-800ms | Multi-step reasoning |
| Asset generation | 100-300ms | Single asset |
| Campaign deployment | 500-2000ms | Multi-channel |

### Throughput

- **Queries per second**: 10-50 (single instance)
- **Concurrent users**: 100-500 (with load balancing)
- **Vault facts**: 100K+ facts supported
- **Campaign executions**: 1K+ concurrent campaigns

### Resource Usage

- **Memory**: 512MB-2GB per instance
- **CPU**: 1-4 cores recommended
- **Storage**: 10GB+ for models and data
- **Network**: 1-10 Mbps typical

## Security Architecture

### Authentication & Authorization

```
┌──────────────┐
│ User Login   │
└──────┬───────┘
       ↓
┌──────────────────────────┐
│ Verify Credentials       │
│ (Bcrypt hashing)         │
└──────┬───────────────────┘
       ↓
┌──────────────────────────┐
│ Generate JWT Token       │
│ (HS256 signing)          │
└──────┬───────────────────┘
       ↓
┌──────────────────────────┐
│ Return Token to Client   │
└──────────────────────────┘
```

### Data Protection

- **In Transit**: HTTPS/TLS encryption
- **At Rest**: Database encryption
- **Secrets**: Environment variables
- **Audit**: Comprehensive logging

## Scaling Strategy

### Horizontal Scaling

```
┌──────────────────────────────────────┐
│         Load Balancer (Nginx)        │
├──────────────────────────────────────┤
│ Instance 1  │ Instance 2  │ Instance 3
│ (8000)      │ (8001)      │ (8002)
└──────────────────────────────────────┘
       ↓
┌──────────────────────────────────────┐
│   Shared Database (PostgreSQL)       │
└──────────────────────────────────────┘
```

### Vertical Scaling

- Increase CPU cores for parallel processing
- Increase RAM for caching and embeddings
- Upgrade storage for vault facts

### Caching Strategy

- Query results cached for 1 hour
- Embeddings cached in ChromaDB
- API responses cached with Redis
- LLM outputs cached per workspace

## Monitoring & Observability

### Metrics

- Request latency (p50, p95, p99)
- Error rates and types
- Agent success rates
- Cache hit rates
- Database query performance
- Memory and CPU usage

### Logging

- Structured JSON logging
- Log levels: DEBUG, INFO, WARNING, ERROR
- Centralized log aggregation
- Audit trail for sensitive operations

### Alerting

- High error rate (>5%)
- High latency (>2s)
- Database connection failures
- Out of memory conditions
- Disk space warnings

## Disaster Recovery

### Backup Strategy

- Daily database backups
- Vault facts snapshots
- Configuration backups
- 30-day retention policy

### Recovery Procedures

- Database restore from backup
- Vault facts reindexing
- Configuration restoration
- Service health verification

### RTO/RPO

- **RTO** (Recovery Time Objective): 1 hour
- **RPO** (Recovery Point Objective): 1 day

## Future Enhancements

1. **Multi-language Support**: Support for non-English queries
2. **Real-time Streaming**: WebSocket support for live updates
3. **Advanced Analytics**: Detailed performance analytics
4. **Custom Agents**: User-defined agent creation
5. **Federated Learning**: Distributed model training
6. **GraphQL API**: Alternative API interface
7. **Mobile App**: Native mobile applications
8. **Advanced Caching**: Distributed caching with Redis Cluster

## References

- FastAPI Documentation: https://fastapi.tiangolo.com/
- SQLAlchemy ORM: https://www.sqlalchemy.org/
- ChromaDB: https://www.trychroma.com/
- Ollama: https://ollama.ai/
- Sentence Transformers: https://www.sbert.net/
