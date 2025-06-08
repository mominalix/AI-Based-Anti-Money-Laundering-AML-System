# Ingestion API Microservice

## Overview
The Ingestion API serves as the primary entry point for all AML data processing. It receives transaction, customer, and account data, performs initial validation and enrichment, then publishes events to the message queue for downstream processing.

## Technical Architecture

### Core Components
- **FastAPI Application**: RESTful API server
- **Data Processor**: Enriches raw data with relationships and metadata
- **Event Publisher**: Publishes structured events to RabbitMQ
- **Validation Layer**: Pydantic models for data validation

### Workflow

1. **Data Reception**
   - Receives batch uploads via POST /upload endpoint
   - Validates JSON structure and required fields
   - Assigns unique batch ID for tracking

2. **Data Processing**
   - Enriches transactions with customer and account relationships
   - Calculates risk indicators (country risk, PEP exposure, etc.)
   - Applies business rules validation
   - Generates metadata timestamps

3. **Event Publishing**
   - Creates structured events for each data type
   - Publishes to RabbitMQ exchange "aml.events"
   - Ensures reliable delivery with error handling

4. **Response Generation**
   - Returns batch processing summary
   - Includes record counts and processing status
   - Provides batch ID for tracking

## API Endpoints

### POST /upload
Uploads a batch of AML data for processing.

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
  "records_processed": 150
}
```

### GET /health
Health check endpoint for monitoring.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-01-01T00:00:00Z"
}
```

## Data Models

### Transaction
- txn_id: Unique transaction identifier
- account_id: Associated account
- amount: Transaction amount
- currency: Currency code
- counterparty_country: Destination country
- timestamp: Transaction timestamp
- transaction_type: Type of transaction
- purpose: Transaction purpose

### Customer
- customer_id: Unique customer identifier
- full_name: Customer full name
- dob: Date of birth
- kyc_level: KYC verification level
- pep_flag: Politically Exposed Person flag
- nationality: Customer nationality
- risk_category: Risk classification

### Account
- account_id: Unique account identifier
- customer_id: Associated customer
- account_type: Type of account
- currency: Account currency
- balance: Current balance
- opened_at: Account opening date
- status: Account status

## Event Types Published

### TransactionIngested
Published for each transaction received.
```json
{
  "type": "TransactionIngested",
  "data": {
    "txn_id": "T123",
    "account_id": "ACC123",
    "amount": 10000.0,
    "enriched_data": {...}
  }
}
```

### CustomerIngested
Published for each customer received.

### AccountIngested
Published for each account received.

## Configuration

### Environment Variables
- `RABBITMQ_URL`: RabbitMQ connection string
- `API_PORT`: API server port (default: 8001)
- `LOG_LEVEL`: Logging level (default: INFO)

### Dependencies
- FastAPI: Web framework
- Pydantic: Data validation
- aio-pika: RabbitMQ client
- uvicorn: ASGI server

## Error Handling

### Validation Errors
- Returns 422 for invalid data formats
- Provides detailed field-level error messages
- Continues processing valid records

### Processing Errors
- Logs errors with context
- Returns partial success status
- Maintains data integrity

### Connection Errors
- Automatic retry for RabbitMQ connections
- Circuit breaker pattern for external services
- Graceful degradation

## Monitoring

### Health Checks
- Database connectivity
- RabbitMQ connectivity
- Service responsiveness

### Metrics
- Request count and latency
- Processing success/failure rates
- Queue publish success rates

### Logging
- Structured JSON logging
- Request/response correlation IDs
- Error stack traces with context

## Development

### Local Setup
```bash
cd services/ingestion-api
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8001
```

### Testing
```bash
pytest tests/
```

### Docker
```bash
docker build -t aml-ingestion-api .
docker run -p 8001:8001 aml-ingestion-api
```

## Production Considerations

### Scalability
- Stateless design enables horizontal scaling
- Async processing for high throughput
- Connection pooling for database and message queue

### Security
- Input validation and sanitization
- Rate limiting for API endpoints
- Authentication and authorization ready

### Reliability
- Idempotent operations
- Transaction rollback on failures
- Dead letter queues for failed messages 