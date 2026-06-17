# BIRD Backend API Documentation

## Overview

The BIRD (Business Intelligence Reasoning & Deployment) backend provides a comprehensive multi-agent system for intelligent analysis, reasoning, and marketing campaign deployment. This documentation covers all API endpoints, authentication, and usage patterns.

## Base URL

```
http://localhost:8000/api/v2
```

## Authentication

All API requests require authentication using JWT tokens. Include the token in the `Authorization` header:

```
Authorization: Bearer <JWT_TOKEN>
```

### Obtaining a Token

**Endpoint:** `POST /api/v1/auth/login`

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "secure_password"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

## Core Endpoints

### 1. Intelligence Analysis

#### Analyze Query with Multi-Agent Orchestration

**Endpoint:** `POST /api/v2/intelligence/analyze`

**Description:** Analyzes an intelligence query using multi-agent orchestration, routing to appropriate agents based on query content.

**Request Body:**
```json
{
  "query": "Analyze market trends and competitive landscape",
  "workspace_id": "workspace-123",
  "mode": "orchestrator_worker"
}
```

**Query Modes:**
- `orchestrator_worker`: Multi-agent orchestration with parallel execution
- `adaptive_planning`: Adaptive planning with dynamic task scheduling
- `debate`: Multi-perspective validation through debate

**Response:**
```json
{
  "id": "query-456",
  "workspace_id": "workspace-123",
  "query": "Analyze market trends and competitive landscape",
  "mode": "orchestrator_worker",
  "status": "completed",
  "result": {
    "query": "Analyze market trends and competitive landscape",
    "findings": [
      {
        "agent": "vault",
        "query": "Analyze market trends and competitive landscape",
        "findings": "Findings from vault agent"
      }
    ],
    "total_agents": 2,
    "successful_agents": 2,
    "failed_agents": 0,
    "confidence": 0.85,
    "total_tokens": 500,
    "total_cost": 0.05,
    "total_execution_time_ms": 2500
  },
  "execution_time_ms": 2500,
  "token_count": 500,
  "cost_estimate": 0.05,
  "completed_at": "2026-06-17T14:30:00Z"
}
```

**Status Codes:**
- `201 Created`: Query successfully created and executed
- `400 Bad Request`: Invalid query or parameters
- `401 Unauthorized`: Missing or invalid authentication
- `500 Internal Server Error`: Server error during execution

---

#### Get Query Result

**Endpoint:** `GET /api/v2/intelligence/{query_id}`

**Description:** Retrieves the result of a previously executed intelligence query.

**Response:**
```json
{
  "id": "query-456",
  "workspace_id": "workspace-123",
  "query": "Analyze market trends",
  "mode": "orchestrator_worker",
  "status": "completed",
  "result": { /* ... */ },
  "execution_time_ms": 2500,
  "token_count": 500,
  "cost_estimate": 0.05,
  "completed_at": "2026-06-17T14:30:00Z"
}
```

---

#### Get Reasoning Chain

**Endpoint:** `GET /api/v2/intelligence/{query_id}/reasoning`

**Description:** Retrieves the detailed reasoning chain for a query, showing all reasoning steps with evidence.

**Response:**
```json
{
  "query_id": "query-456",
  "steps": [
    {
      "step_number": 1,
      "agent_type": "vault",
      "reasoning_text": "Retrieved facts about market trends",
      "evidence": ["Fact 1", "Fact 2"],
      "confidence": 0.9,
      "created_at": "2026-06-17T14:30:00Z"
    }
  ]
}
```

---

#### Perform Reasoning Analysis

**Endpoint:** `POST /api/v2/intelligence/reason`

**Description:** Performs multi-step reasoning analysis on a topic.

**Request Parameters:**
- `query` (string, required): Topic to reason about
- `workspace_id` (string, required): Workspace ID

**Response:**
```json
{
  "query": "Why did market share decline?",
  "concepts": ["market", "share", "decline"],
  "relationships": [
    {
      "concept1": "market",
      "concept2": "share",
      "relationship": "related"
    }
  ],
  "conclusions": ["Conclusion 1", "Conclusion 2"],
  "reasoning_chain": [
    {
      "step": 1,
      "type": "deductive",
      "premise": "Premise text",
      "conclusion": "Conclusion text",
      "confidence": 0.85
    }
  ],
  "overall_confidence": 0.82
}
```

---

#### Debate a Conclusion

**Endpoint:** `POST /api/v2/intelligence/debate`

**Description:** Debates a conclusion through multiple perspectives to validate and build consensus.

**Request Parameters:**
- `conclusion` (string, required): Conclusion to debate
- `workspace_id` (string, required): Workspace ID
- `num_rounds` (integer, optional, default=3): Number of debate rounds (1-5)

**Response:**
```json
{
  "conclusion": "We should expand to new markets",
  "debate_rounds": [
    {
      "round": 1,
      "perspectives": [
        {
          "type": "optimistic",
          "position": "Expansion is positive",
          "confidence": 0.7,
          "supporting_arguments": ["Argument 1"],
          "counter_arguments": ["Counter 1"]
        }
      ],
      "consensus": "Consensus statement",
      "agreement_score": 0.75
    }
  ],
  "final_consensus": 0.78,
  "recommendation": "Moderate consensus: Recommendation is reasonably reliable",
  "confidence": 0.78
}
```

---

#### Get Intelligence Statistics

**Endpoint:** `GET /api/v2/intelligence/stats`

**Description:** Retrieves statistics about intelligence analysis for a workspace.

**Request Parameters:**
- `workspace_id` (string, required): Workspace ID

**Response:**
```json
{
  "workspace_id": "workspace-123",
  "total_queries": 50,
  "completed_queries": 48,
  "failed_queries": 2,
  "success_rate": 0.96,
  "average_execution_time_ms": 2150,
  "total_cost": 2.45,
  "timestamp": "2026-06-17T14:30:00Z"
}
```

---

### 2. Vault Management

#### Add Fact to Vault

**Endpoint:** `POST /api/v2/vault/facts`

**Description:** Adds a new fact to the intelligent vault with metadata.

**Request Body:**
```json
{
  "fact": "Market size is growing at 15% annually",
  "category": "market",
  "tags": ["market", "growth"],
  "source": "Market research report",
  "confidence": 0.9,
  "workspace_id": "workspace-123"
}
```

**Response:**
```json
{
  "id": "fact-789",
  "fact": "Market size is growing at 15% annually",
  "category": "market",
  "tags": ["market", "growth"],
  "source": "Market research report",
  "confidence": 0.9,
  "embedding": [0.1, 0.2, ...],
  "created_at": "2026-06-17T14:30:00Z"
}
```

---

#### Search Vault

**Endpoint:** `GET /api/v2/vault/search`

**Description:** Searches the vault for relevant facts using semantic search and multi-hop retrieval.

**Request Parameters:**
- `query` (string, required): Search query
- `workspace_id` (string, required): Workspace ID
- `max_hops` (integer, optional, default=2): Maximum retrieval hops
- `top_k` (integer, optional, default=5): Number of results

**Response:**
```json
{
  "query": "market growth trends",
  "findings": [
    {
      "fact": "Market size is growing at 15% annually",
      "relevance_score": 0.95,
      "category": "market",
      "source": "Market research report"
    }
  ],
  "total_results": 1,
  "retrieval_hops": 1,
  "execution_time_ms": 150
}
```

---

#### Get Vault Statistics

**Endpoint:** `GET /api/v2/vault/stats`

**Description:** Retrieves statistics about the vault.

**Request Parameters:**
- `workspace_id` (string, required): Workspace ID

**Response:**
```json
{
  "workspace_id": "workspace-123",
  "total_facts": 250,
  "total_categories": 8,
  "average_confidence": 0.82,
  "memory_quality_score": 0.88,
  "last_updated": "2026-06-17T14:30:00Z"
}
```

---

### 3. Asset Generation (Forge)

#### Generate Marketing Asset

**Endpoint:** `POST /api/v2/forge/generate`

**Description:** Generates a marketing asset of specified type with customizable tone.

**Request Body:**
```json
{
  "asset_type": "social_post",
  "context": {
    "topic": "New product launch",
    "hashtags": ["#launch", "#innovation"]
  },
  "tone": "inspirational",
  "workspace_id": "workspace-123"
}
```

**Asset Types:**
- `social_post`: Social media post
- `email_campaign`: Email marketing campaign
- `blog_post`: Blog article
- `landing_page`: Landing page copy
- `ad_copy`: Advertising copy
- `infographic`: Infographic description
- `video_script`: Video script
- `presentation`: Presentation outline

**Tones:**
- `professional`: Professional and formal
- `casual`: Casual and friendly
- `humorous`: Humorous and entertaining
- `urgent`: Urgent and time-sensitive
- `inspirational`: Inspirational and motivational
- `educational`: Educational and informative

**Response:**
```json
{
  "id": "asset-101",
  "asset_type": "social_post",
  "title": "Generated Social Post",
  "content": "Check out this: New product launch\n\n#launch #innovation",
  "tone": "inspirational",
  "quality_score": 0.87,
  "created_at": "2026-06-17T14:30:00Z"
}
```

---

#### Generate Campaign with Variations

**Endpoint:** `POST /api/v2/forge/campaign`

**Description:** Generates a complete marketing campaign with multiple variations.

**Request Body:**
```json
{
  "campaign_name": "Product Launch 2024",
  "campaign_type": "social",
  "context": {
    "topic": "New product",
    "headline": "Revolutionary Solution"
  },
  "num_variations": 3,
  "workspace_id": "workspace-123"
}
```

**Response:**
```json
{
  "name": "Product Launch 2024",
  "type": "social",
  "created_at": "2026-06-17T14:30:00Z",
  "variations": [
    {
      "id": "asset-102",
      "tone": "professional",
      "content": "Content variation 1",
      "quality_score": 0.85
    },
    {
      "id": "asset-103",
      "tone": "casual",
      "content": "Content variation 2",
      "quality_score": 0.82
    }
  ]
}
```

---

### 4. Campaign Deployment (Attack)

#### Create Campaign

**Endpoint:** `POST /api/v2/attack/campaigns`

**Description:** Creates a new marketing campaign.

**Request Body:**
```json
{
  "name": "Q3 Marketing Campaign",
  "description": "Multi-channel campaign for Q3",
  "assets": [
    {
      "id": "asset-102",
      "type": "social_post"
    }
  ],
  "targets": [
    {
      "id": "target-1",
      "name": "Tech Enthusiasts",
      "size": 50000,
      "interests": ["technology", "innovation"]
    }
  ],
  "channels": ["social_media", "email"],
  "budget": 5000,
  "start_date": "2026-07-01T00:00:00Z",
  "end_date": "2026-07-31T23:59:59Z",
  "workspace_id": "workspace-123"
}
```

**Response:**
```json
{
  "id": "campaign-201",
  "name": "Q3 Marketing Campaign",
  "status": "draft",
  "channels": 2,
  "targets": 1,
  "budget": 5000,
  "created_at": "2026-06-17T14:30:00Z"
}
```

---

#### Deploy Campaign

**Endpoint:** `POST /api/v2/attack/campaigns/{campaign_id}/deploy`

**Description:** Deploys a campaign across all configured channels.

**Response:**
```json
{
  "campaign_id": "campaign-201",
  "status": "deployed",
  "executions": 2,
  "total_reach": 50000,
  "deployment_time_ms": 1500
}
```

---

#### Monitor Campaign

**Endpoint:** `GET /api/v2/attack/campaigns/{campaign_id}/metrics`

**Description:** Retrieves real-time performance metrics for a campaign.

**Response:**
```json
{
  "campaign_id": "campaign-201",
  "campaign_name": "Q3 Marketing Campaign",
  "status": "running",
  "total_impressions": 45000,
  "total_clicks": 2250,
  "total_conversions": 225,
  "total_cost": 2250,
  "ctr": 0.05,
  "conversion_rate": 0.1,
  "cpc": 1.0,
  "roi": 0.1,
  "executions": 2,
  "channels": ["social_media", "email"]
}
```

---

#### Pause/Resume Campaign

**Endpoint:** `POST /api/v2/attack/campaigns/{campaign_id}/pause`
**Endpoint:** `POST /api/v2/attack/campaigns/{campaign_id}/resume`

**Description:** Pauses or resumes a running campaign.

**Response:**
```json
{
  "campaign_id": "campaign-201",
  "status": "paused"
}
```

---

#### Stop Campaign

**Endpoint:** `POST /api/v2/attack/campaigns/{campaign_id}/stop`

**Description:** Stops a campaign and completes all executions.

**Response:**
```json
{
  "campaign_id": "campaign-201",
  "status": "completed"
}
```

---

## Error Handling

All endpoints return standard HTTP status codes and error messages:

```json
{
  "detail": "Error message describing what went wrong",
  "status_code": 400,
  "timestamp": "2026-06-17T14:30:00Z"
}
```

**Common Status Codes:**
- `200 OK`: Successful GET request
- `201 Created`: Successful resource creation
- `400 Bad Request`: Invalid request parameters
- `401 Unauthorized`: Missing or invalid authentication
- `404 Not Found`: Resource not found
- `500 Internal Server Error`: Server error

---

## Rate Limiting

API requests are rate-limited to prevent abuse:

- **Standard Tier**: 100 requests per minute
- **Premium Tier**: 1000 requests per minute

Rate limit information is included in response headers:

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1718634600
```

---

## Pagination

List endpoints support pagination using query parameters:

```
GET /api/v2/intelligence/queries?page=1&limit=20
```

**Response:**
```json
{
  "items": [ /* ... */ ],
  "total": 150,
  "page": 1,
  "limit": 20,
  "pages": 8
}
```

---

## Webhooks

Configure webhooks to receive real-time notifications about campaign events:

**Webhook Events:**
- `campaign.deployed`: Campaign deployment started
- `campaign.completed`: Campaign execution completed
- `campaign.failed`: Campaign execution failed
- `query.completed`: Intelligence query completed

**Webhook Payload:**
```json
{
  "event": "campaign.completed",
  "timestamp": "2026-06-17T14:30:00Z",
  "data": {
    "campaign_id": "campaign-201",
    "status": "completed",
    "metrics": { /* ... */ }
  }
}
```

---

## Code Examples

### Python

```python
import requests

# Authentication
auth_response = requests.post(
    "http://localhost:8000/api/v1/auth/login",
    json={
        "email": "user@example.com",
        "password": "password"
    }
)
token = auth_response.json()["access_token"]

# Analyze query
headers = {"Authorization": f"Bearer {token}"}
response = requests.post(
    "http://localhost:8000/api/v2/intelligence/analyze",
    headers=headers,
    json={
        "query": "Analyze market trends",
        "workspace_id": "workspace-123",
        "mode": "orchestrator_worker"
    }
)

result = response.json()
print(f"Confidence: {result['result']['confidence']}")
```

### JavaScript

```javascript
// Authentication
const authResponse = await fetch("http://localhost:8000/api/v1/auth/login", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    email: "user@example.com",
    password: "password"
  })
});

const { access_token } = await authResponse.json();

// Analyze query
const response = await fetch("http://localhost:8000/api/v2/intelligence/analyze", {
  method: "POST",
  headers: {
    "Authorization": `Bearer ${access_token}`,
    "Content-Type": "application/json"
  },
  body: JSON.stringify({
    query: "Analyze market trends",
    workspace_id: "workspace-123",
    mode: "orchestrator_worker"
  })
});

const result = await response.json();
console.log(`Confidence: ${result.result.confidence}`);
```

---

## Support

For API support and questions, please contact:
- **Email**: api-support@bird.local
- **Documentation**: https://docs.bird.local
- **Issues**: https://github.com/bird-system/issues
