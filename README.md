# BIRD Backend - Multi-Agent Intelligence System

**BIRD** is an advanced, multi-agent autonomous reasoning system that transforms competitive intelligence into explainable, actionable insights with privacy-first architecture.

## Project Overview

This is the backend implementation of BIRD, built with FastAPI and featuring:

- **Multi-Agent Orchestration:** Specialized agents for web intelligence (Radar), memory management (Vault), reasoning (Reasoning), validation (Debate), asset generation (Forge), and deployment (Attack)
- **Agentic RAG:** Retrieval-Augmented Reasoning with multi-hop reasoning capabilities
- **Secure Authentication:** Bcrypt password hashing, JWT tokens, and session management
- **Explainable AI:** Full reasoning chains with evidence trails and confidence scoring
- **Cost-Optimized:** Local-first models (Qwen3) with optional frontier model routing (Fable 5, Claude)

## Project Structure

```
bird-backend/
├── app/                          # Application code
│   ├── main.py                  # FastAPI application setup
│   ├── models.py                # SQLAlchemy ORM models
│   ├── schemas.py               # Pydantic request/response models
│   ├── security.py              # Authentication & security utilities
│   ├── database.py              # Database connection & session management
│   └── routers/                 # API route handlers
│       ├── auth.py              # Authentication endpoints
│       ├── workspaces.py        # Workspace management
│       ├── intelligence.py      # Intelligence analysis
│       ├── vault.py             # Smart memory system
│       ├── agents.py            # Agent invocation
│       └── campaigns.py         # Campaign management
├── config/                       # Configuration
│   └── settings.py              # Application settings
├── tests/                        # Test suite
│   ├── test_auth.py             # Authentication tests
│   └── test_*.py                # Other test modules
├── migrations/                   # Database migrations
├── data/                         # Data storage
│   ├── bird.db                  # SQLite database
│   └── chromadb/                # Vector embeddings
├── requirements.txt             # Python dependencies
├── .env.example                 # Environment variables template
├── pytest.ini                   # Pytest configuration
└── README.md                    # This file
```

## Installation

### Prerequisites

- Python 3.9+
- Ollama (for local LLM inference)
- pip or conda

### Setup

1. **Clone or navigate to the project:**

```bash
cd /home/ubuntu/bird-backend
```

2. **Create virtual environment (optional but recommended):**

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies:**

```bash
pip install -r requirements.txt
```

4. **Configure environment:**

```bash
cp .env.example .env
# Edit .env with your settings
```

5. **Initialize database:**

```bash
python -c "from app.database import DatabaseManager; DatabaseManager.initialize()"
```

## Running the Application

### Development Server

```bash
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Production Server

```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Access API Documentation

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
- **OpenAPI Schema:** http://localhost:8000/openapi.json

## API Endpoints

### Authentication (v1)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/register` | Register new user |
| POST | `/api/v1/auth/login` | Login and get access token |
| POST | `/api/v1/auth/logout` | Logout and invalidate session |
| GET | `/api/v1/auth/me` | Get current user info |

### Workspaces (v1)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/workspaces/` | List workspaces |
| POST | `/api/v1/workspaces/` | Create workspace |
| GET | `/api/v1/workspaces/{id}` | Get workspace details |
| PUT | `/api/v1/workspaces/{id}` | Update workspace |
| DELETE | `/api/v1/workspaces/{id}` | Delete workspace |

### Intelligence (v2)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v2/intelligence/analyze` | Analyze intelligence query |
| GET | `/api/v2/intelligence/{id}` | Get query results |
| GET | `/api/v2/intelligence/{id}/reasoning` | Get reasoning chain |

### Vault (v2)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v2/vault/search` | Search vault facts |
| POST | `/api/v2/vault/facts` | Add fact to vault |
| GET | `/api/v2/vault/facts/{id}` | Get fact details |
| PUT | `/api/v2/vault/facts/{id}` | Update fact |

### Agents (v2)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v2/agents/invoke` | Invoke specific agent |
| GET | `/api/v2/agents/status` | Get agent status |
| GET | `/api/v2/agents/executions` | List agent executions |

### Campaigns (v2)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v2/campaigns/` | Create campaign |
| GET | `/api/v2/campaigns/` | List campaigns |
| GET | `/api/v2/campaigns/{id}` | Get campaign details |
| POST | `/api/v2/campaigns/{id}/deploy` | Deploy campaign |
| GET | `/api/v2/campaigns/{id}/metrics` | Get campaign metrics |

## Testing

### Run All Tests

```bash
pytest
```

### Run Specific Test File

```bash
pytest tests/test_auth.py
```

### Run with Coverage

```bash
pytest --cov=app --cov-report=html
```

### Run Specific Test Class

```bash
pytest tests/test_auth.py::TestUserRegistration
```

### Run Specific Test

```bash
pytest tests/test_auth.py::TestUserRegistration::test_register_success
```

## Database Schema

### Users Table
- `id` (UUID): Primary key
- `username` (String): Unique username
- `email` (String): Unique email
- `hashed_password` (String): Bcrypt hashed password
- `full_name` (String): User's full name
- `is_active` (Boolean): Account active status
- `is_admin` (Boolean): Admin flag
- `created_at` (DateTime): Account creation timestamp
- `updated_at` (DateTime): Last update timestamp

### Sessions Table
- `id` (UUID): Primary key
- `user_id` (UUID): Foreign key to users
- `token` (String): Session token
- `ip_address` (String): Client IP address
- `user_agent` (String): Client user agent
- `expires_at` (DateTime): Session expiration
- `created_at` (DateTime): Session creation timestamp

### Workspaces Table
- `id` (UUID): Primary key
- `owner_id` (UUID): Foreign key to users
- `name` (String): Workspace name
- `description` (Text): Workspace description
- `is_active` (Boolean): Active status
- `created_at` (DateTime): Creation timestamp
- `updated_at` (DateTime): Last update timestamp

### Intelligence Queries Table
- `id` (UUID): Primary key
- `workspace_id` (UUID): Foreign key to workspaces
- `query` (Text): Intelligence query
- `mode` (String): Execution mode (orchestrator-worker, adaptive-planning, debate)
- `status` (String): Query status (pending, executing, completed, failed)
- `result` (JSON): Query result
- `error_message` (Text): Error message if failed
- `execution_time_ms` (Integer): Execution time in milliseconds
- `token_count` (Integer): Tokens used
- `cost_estimate` (Float): Estimated cost
- `created_at` (DateTime): Creation timestamp
- `completed_at` (DateTime): Completion timestamp

### Reasoning Chains Table
- `id` (UUID): Primary key
- `query_id` (UUID): Foreign key to intelligence_queries
- `step_number` (Integer): Step number in chain
- `agent_type` (String): Agent type (orchestrator, radar, vault, reasoning, debate, forge, attack)
- `reasoning_text` (Text): Reasoning explanation
- `evidence` (JSON): Supporting evidence
- `confidence` (Float): Confidence score (0-1)
- `created_at` (DateTime): Creation timestamp

### Vault Facts Table
- `id` (UUID): Primary key
- `workspace_id` (UUID): Foreign key to workspaces
- `fact` (Text): Fact content
- `source` (String): Source name
- `source_url` (String): Source URL
- `category` (String): Fact category
- `tags` (JSON): Tags for categorization
- `embedding` (JSON): Vector embedding
- `created_at` (DateTime): Creation timestamp
- `updated_at` (DateTime): Last update timestamp

## Configuration

### Environment Variables

See `.env.example` for all available configuration options:

```env
# Application
APP_NAME=BIRD
DEBUG=False
ENVIRONMENT=development

# Security
SECRET_KEY=your-super-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Database
DATABASE_URL=sqlite:///./data/bird.db

# Ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL_SMALL=qwen2.5:7b
OLLAMA_MODEL_MEDIUM=qwen3:8b
OLLAMA_MODEL_LARGE=qwen3:14b

# ChromaDB
CHROMADB_PATH=./data/chromadb
CHROMADB_COLLECTION_NAME=bird_intelligence

# API
CORS_ORIGINS=["http://localhost:3000"]
```

## Development Workflow

### Phase 0: Foundation Hardening (Current)
- ✅ Session management with secure cookies
- ✅ Password hashing with bcrypt
- ✅ JWT authentication
- ✅ Database models and schema
- ✅ Authentication endpoints
- ⏳ Ollama integration testing
- ⏳ Comprehensive test suite

### Phase 1: Smart Vault (Next)
- Agentic RAG implementation
- Multi-hop retrieval
- Memory quality scoring
- ChromaDB integration

### Phase 2: Multi-Agent Orchestration
- Orchestrator agent
- Radar agents (web intelligence)
- Reasoning agents
- Debate agent
- Parallel execution

### Phase 3: Adaptive Planning & Reasoning
- Adaptive planning agent
- Retrieval-Augmented Reasoning (RAR)
- Reasoning visualization
- Full explainability

### Phase 4: Forge & Attack Integration
- Forge agent (asset generation)
- Attack agent (deployment)
- Campaign management
- Performance tracking

## Security Considerations

1. **Password Security:** All passwords are hashed using bcrypt with salt
2. **Session Management:** Secure, httpOnly cookies with expiration
3. **JWT Tokens:** Signed tokens with configurable expiration
4. **CORS:** Configurable cross-origin resource sharing
5. **Input Validation:** Pydantic schemas validate all inputs
6. **SQL Injection:** SQLAlchemy ORM prevents SQL injection
7. **Environment Secrets:** Sensitive data loaded from `.env` file

## Performance Optimization

- Database indices on frequently queried columns
- Connection pooling for database
- Async/await for I/O operations
- Caching for configuration
- Batch processing for embeddings

## Monitoring & Logging

- Structured logging with JSON format
- Request/response logging
- Error tracking and reporting
- Performance metrics collection
- Agent execution monitoring

## Troubleshooting

### Database Connection Error
```
Error: unable to open database file
```
**Solution:** Ensure `./data` directory exists and is writable

### Ollama Connection Error
```
Error: Failed to connect to Ollama
```
**Solution:** Ensure Ollama is running on the configured URL

### Port Already in Use
```
Error: Address already in use
```
**Solution:** Change port in configuration or kill existing process

### Import Errors
```
Error: ModuleNotFoundError
```
**Solution:** Ensure all dependencies are installed: `pip install -r requirements.txt`

## Contributing

1. Create a feature branch
2. Make your changes
3. Write tests for new functionality
4. Run test suite: `pytest`
5. Submit pull request

## License

Proprietary - BIRD Advanced Architecture

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review API documentation at `/docs`
3. Check logs in `./logs` directory
4. Open an issue with detailed error information

## Next Steps

1. **Phase 0 Completion:** Run full test suite and validate security
2. **Phase 1 Start:** Implement Vault agent with Agentic RAG
3. **Phase 2 Start:** Build multi-agent orchestration framework
4. **Phase 3 Start:** Implement adaptive planning and reasoning
5. **Phase 4 Start:** Build Forge and Attack agents

---

**Version:** 1.0.0  
**Last Updated:** June 17, 2026  
**Status:** Phase 0 - Foundation Hardening
