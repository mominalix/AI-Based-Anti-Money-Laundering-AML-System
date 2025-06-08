# Gateway Microservice

## Overview
The Gateway serves as the central API gateway and orchestration layer for the AML system. It provides a unified interface for external clients, handles authentication, routing, and service coordination while maintaining security and performance standards.

## Technical Architecture

### Core Components
- **API Gateway**: Central routing and request handling
- **Service Discovery**: Dynamic service endpoint management
- **Load Balancer**: Request distribution across service instances
- **Authentication**: JWT-based security and authorization
- **Rate Limiter**: Request throttling and abuse prevention
- **Circuit Breaker**: Fault tolerance and service protection

### Workflow

1. **Request Reception**
   - Receives external API requests
   - Validates authentication tokens
   - Applies rate limiting rules
   - Logs request metadata

2. **Service Routing**
   - Routes requests to appropriate microservices
   - Implements load balancing strategies
   - Handles service discovery
   - Manages circuit breaker states

3. **Response Aggregation**
   - Combines responses from multiple services
   - Formats unified API responses
   - Handles error aggregation
   - Applies response transformations

4. **Monitoring and Logging**
   - Tracks API usage metrics
   - Logs security events
   - Monitors service health
   - Generates performance reports

## API Endpoints

### Data Ingestion
Routes to Ingestion API service.

#### POST /api/v1/upload
Uploads batch data for AML processing.

**Request Body:**
```json
{
  "accounts": [...],
  "customers": [...],
  "transactions": [...]
}
```

**Response:**
```json
{
  "message": "Batch uploaded successfully",
  "batch_id": "uuid",
  "records_processed": 150,
  "processing_time": "2.3s"
}
```

### Feature Analysis
Routes to Feature Engine service.

#### GET /api/v1/features
Retrieves computed features for transactions.

**Query Parameters:**
- `txn_id`: Specific transaction ID
- `limit`: Maximum number of results
- `offset`: Pagination offset

**Response:**
```json
{
  "features": [
    {
      "txn_id": "T123",
      "features": {...},
      "computed_at": "2025-01-01T00:00:00Z"
    }
  ],
  "total": 100,
  "limit": 50,
  "offset": 0
}
```

### Risk Assessment
Routes to Risk Scorer service.

#### GET /api/v1/scores
Retrieves risk scores for transactions.

**Query Parameters:**
- `txn_id`: Specific transaction ID
- `risk_threshold`: Minimum risk score
- `limit`: Maximum number of results

**Response:**
```json
{
  "scores": [
    {
      "txn_id": "T123",
      "risk_score": 0.85,
      "confidence": 0.92,
      "risk_category": "high",
      "model_scores": {...},
      "shap_values": {...}
    }
  ],
  "total": 75,
  "limit": 50,
  "offset": 0
}
```

### Network Analysis
Routes to Graph Analysis service.

#### GET /api/v1/graph/analysis
Retrieves graph analysis results.

**Query Parameters:**
- `entity_id`: Specific entity ID
- `analysis_type`: Type of analysis
- `time_window`: Analysis time window

**Response:**
```json
{
  "analysis": [
    {
      "entity_id": "ACC123",
      "centrality_measures": {...},
      "community_id": "C001",
      "anomaly_score": 0.75,
      "risk_patterns": [...]
    }
  ]
}
```

#### GET /api/v1/graph/communities
Retrieves detected communities.

#### GET /api/v1/graph/patterns
Retrieves suspicious patterns.

### Alert Management
Routes to Alert Manager service.

#### GET /api/v1/alerts
Retrieves AML alerts with filtering.

**Query Parameters:**
- `status`: Alert status filter
- `risk_threshold`: Minimum risk score
- `assigned_to`: Assigned investigator
- `limit`: Maximum number of results
- `offset`: Pagination offset

**Response:**
```json
{
  "alerts": [
    {
      "alert_id": "uuid",
      "txn_id": "T123",
      "customer_id": "CUST_123",
      "risk_score": 0.85,
      "status": "open",
      "alert_type": "high_risk_transaction",
      "sar_narrative": "...",
      "created_at": "2025-01-01T00:00:00Z"
    }
  ],
  "total": 150,
  "limit": 100,
  "offset": 0
}
```

#### GET /api/v1/alerts/{alert_id}
Retrieves specific alert details.

#### PATCH /api/v1/alerts/{alert_id}
Updates alert status and investigation notes.

#### GET /api/v1/alerts/statistics
Retrieves alert statistics and metrics.

### System Health
Aggregated health checks across all services.

#### GET /api/v1/health
System-wide health status.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-01-01T00:00:00Z",
  "services": {
    "ingestion-api": "healthy",
    "feature-engine": "healthy",
    "risk-scorer": "healthy",
    "graph-analysis": "healthy",
    "alert-manager": "healthy"
  },
  "response_time": "150ms"
}
```

#### GET /api/v1/health/detailed
Detailed health information for all services.

### Orchestrated Workflows

#### POST /api/v1/workflows/complete-analysis
Triggers complete AML analysis workflow.

**Request Body:**
```json
{
  "data": {
    "accounts": [...],
    "customers": [...],
    "transactions": [...]
  },
  "options": {
    "generate_alerts": true,
    "include_graph_analysis": true,
    "sar_generation": true
  }
}
```

**Response:**
```json
{
  "workflow_id": "uuid",
  "status": "processing",
  "stages": {
    "ingestion": "completed",
    "feature_engineering": "processing",
    "risk_scoring": "pending",
    "graph_analysis": "pending",
    "alert_generation": "pending"
  },
  "estimated_completion": "2025-01-01T00:05:00Z"
}
```

#### GET /api/v1/workflows/{workflow_id}
Retrieves workflow status and results.

## Authentication and Authorization

### JWT Token Authentication
The gateway implements JWT-based authentication for secure API access.

#### Token Structure
```json
{
  "sub": "user@bank.com",
  "role": "analyst",
  "permissions": [
    "read:alerts",
    "write:alerts",
    "read:scores",
    "admin:system"
  ],
  "exp": 1640995200,
  "iat": 1640908800
}
```

#### Authentication Flow
1. Client obtains JWT token from authentication service
2. Token included in Authorization header: `Bearer <token>`
3. Gateway validates token signature and expiration
4. Extracts user permissions for authorization
5. Routes request to appropriate service

### Role-Based Access Control

#### Analyst Role
- Read access to alerts and scores
- Update alert status and notes
- View system health and metrics
- Limited administrative functions

#### Senior Analyst Role
- All analyst permissions
- Create and assign alerts
- Access to advanced analytics
- Export capabilities

#### Administrator Role
- Full system access
- User management
- System configuration
- Service management

#### Compliance Officer Role
- Read-only access to all data
- Export and reporting capabilities
- Audit trail access
- Regulatory reporting functions

## Rate Limiting and Throttling

### Rate Limiting Rules
- **Public endpoints**: 100 requests/minute per IP
- **Authenticated users**: 1000 requests/minute per user
- **Administrative endpoints**: 50 requests/minute per user
- **Bulk operations**: 10 requests/minute per user

### Throttling Strategies
- **Token bucket**: Smooth rate limiting
- **Sliding window**: Precise time-based limits
- **Adaptive throttling**: Dynamic limits based on system load
- **Priority queuing**: VIP user prioritization

### Error Responses
```json
{
  "error": "rate_limit_exceeded",
  "message": "Too many requests",
  "retry_after": 60,
  "limit": 1000,
  "remaining": 0,
  "reset": 1640995200
}
```

## Circuit Breaker Pattern

### Circuit States
1. **Closed**: Normal operation, requests pass through
2. **Open**: Service failure detected, requests fail fast
3. **Half-Open**: Testing service recovery

### Configuration
```yaml
circuit_breaker:
  failure_threshold: 5
  timeout: 30s
  recovery_timeout: 60s
  success_threshold: 3
```

### Fallback Strategies
- **Cached responses**: Return cached data when available
- **Default responses**: Provide safe default values
- **Graceful degradation**: Reduced functionality mode
- **Error responses**: Clear error messages with retry guidance

## Load Balancing

### Load Balancing Algorithms
- **Round Robin**: Equal distribution across instances
- **Weighted Round Robin**: Distribution based on capacity
- **Least Connections**: Route to least busy instance
- **Health-based**: Avoid unhealthy instances

### Service Discovery
- **Static configuration**: Predefined service endpoints
- **Dynamic discovery**: Service registry integration
- **Health checking**: Continuous service monitoring
- **Automatic failover**: Redirect traffic from failed instances

## Monitoring and Observability

### Metrics Collection
- **Request metrics**: Count, latency, error rates
- **Service metrics**: Health, performance, availability
- **Business metrics**: Alert rates, processing volumes
- **Security metrics**: Authentication failures, rate limit hits

### Logging
- **Access logs**: All API requests and responses
- **Error logs**: Detailed error information
- **Security logs**: Authentication and authorization events
- **Performance logs**: Slow queries and bottlenecks

### Distributed Tracing
- **Request correlation**: Track requests across services
- **Performance analysis**: Identify bottlenecks
- **Error tracking**: Trace error propagation
- **Service dependencies**: Visualize service interactions

## Configuration

### Environment Variables
```env
# Gateway Configuration
GATEWAY_PORT=8000
JWT_SECRET=your_jwt_secret_here
RATE_LIMIT_ENABLED=true
CIRCUIT_BREAKER_ENABLED=true

# Service Endpoints
INGESTION_API_URL=http://ingestion-api:8001
FEATURE_ENGINE_URL=http://feature-engine:8002
RISK_SCORER_URL=http://risk-scorer:8003
GRAPH_ANALYSIS_URL=http://graph-analysis:8004
ALERT_MANAGER_URL=http://alert-manager:8005

# Security
CORS_ORIGINS=["http://localhost:3000"]
API_KEY_REQUIRED=false
SSL_ENABLED=false

# Performance
CONNECTION_POOL_SIZE=100
REQUEST_TIMEOUT=30s
KEEP_ALIVE_TIMEOUT=5s
```

### Service Configuration
```yaml
services:
  ingestion-api:
    url: "http://ingestion-api:8001"
    health_check: "/health"
    timeout: 30s
    retries: 3
    
  feature-engine:
    url: "http://feature-engine:8002"
    health_check: "/health"
    timeout: 60s
    retries: 2
```

## Error Handling

### Error Response Format
```json
{
  "error": {
    "code": "SERVICE_UNAVAILABLE",
    "message": "Risk Scorer service is temporarily unavailable",
    "details": {
      "service": "risk-scorer",
      "timestamp": "2025-01-01T00:00:00Z",
      "correlation_id": "uuid"
    },
    "retry_after": 30
  }
}
```

### Error Categories
- **4xx Client Errors**: Invalid requests, authentication failures
- **5xx Server Errors**: Service failures, timeouts
- **Gateway Errors**: Routing failures, circuit breaker trips
- **Upstream Errors**: Microservice-specific errors

## Development

### Local Setup
```bash
cd services/gateway
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000
```

### Testing
```bash
pytest tests/
python -m pytest tests/test_gateway.py -v
```

### API Documentation
```bash
# Start gateway service
uvicorn main:app --port 8000

# Access Swagger UI
open http://localhost:8000/docs

# Access ReDoc
open http://localhost:8000/redoc
```

## Production Considerations

### Scalability
- **Horizontal scaling**: Multiple gateway instances
- **Load balancing**: Distribute traffic across instances
- **Connection pooling**: Efficient resource utilization
- **Caching**: Reduce backend service load

### Security
- **TLS termination**: HTTPS encryption
- **API key management**: Secure key rotation
- **Input validation**: Prevent injection attacks
- **Security headers**: CORS, CSP, HSTS

### Performance
- **Response caching**: Cache frequently accessed data
- **Compression**: Reduce bandwidth usage
- **Connection keep-alive**: Reduce connection overhead
- **Async processing**: Non-blocking request handling

### Monitoring
- **Health checks**: Continuous service monitoring
- **Performance metrics**: Response time tracking
- **Error tracking**: Comprehensive error logging
- **Alerting**: Proactive issue notification 