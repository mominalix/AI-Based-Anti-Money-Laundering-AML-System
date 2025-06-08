# Feature Engine Microservice

## Overview
The Feature Engine is responsible for computing comprehensive risk features from transaction data. It transforms raw transaction information into structured feature vectors that enable machine learning models to assess money laundering risk effectively.

## Technical Architecture

### Core Components
- **Feature Engine Class**: Main feature computation engine
- **Event Consumer**: Processes TransactionIngested events
- **Feature Store**: In-memory storage for computed features
- **Risk Calculators**: Specialized modules for different risk types

### Workflow

1. **Event Consumption**
   - Listens for TransactionIngested events from RabbitMQ
   - Maintains transaction, customer, and account stores
   - Processes events in real-time

2. **Feature Computation**
   - Computes 32+ features per transaction
   - Analyzes transaction patterns and relationships
   - Calculates risk indicators and behavioral metrics

3. **Feature Storage**
   - Stores computed features in memory
   - Maintains feature history for velocity analysis
   - Provides API access to feature data

4. **Event Publishing**
   - Publishes FeatureComputed events
   - Includes complete feature vector
   - Triggers downstream risk scoring

## Feature Categories

### Transaction Features
- **amount**: Raw transaction amount
- **amount_log**: Logarithmic transformation of amount
- **amount_rounded**: Round number indicator (0 or 1)
- **amount_threshold_10k**: Above $10K threshold flag
- **amount_threshold_50k**: Above $50K threshold flag

### Velocity Features
- **amt_30d**: Total amount in last 30 days
- **count_30d**: Transaction count in last 30 days
- **avg_amt_30d**: Average amount in last 30 days
- **amt_7d**: Total amount in last 7 days
- **count_7d**: Transaction count in last 7 days
- **velocity_score**: Daily transaction frequency
- **velocity_acceleration**: Change in velocity patterns
- **amount_deviation**: Deviation from historical average

### Country Risk Features
- **country_risk**: Risk score for counterparty country (0.0-1.0)
- **high_risk_country**: High-risk country flag
- **sanctions_country**: Sanctioned country flag
- **high_risk_jurisdiction**: High-risk jurisdiction flag
- **tax_haven**: Tax haven country flag
- **risk_level_low/medium/high/critical**: Risk level categorization

### Customer Features
- **kyc_gap_score**: KYC verification gap score
- **pep_exposure**: Politically Exposed Person flag
- **account_age_score**: Account age normalized score
- **new_account**: New account flag (< 36 days)

### Temporal Features
- **hour_of_day**: Hour of transaction (0-23)
- **is_weekend**: Weekend transaction flag
- **is_off_hours**: Off-hours transaction flag (before 8 AM or after 6 PM)

### Structuring Detection Features
- **structuring_score**: Structuring pattern indicator
- **near_threshold_count**: Count of near-threshold transactions

## API Endpoints

### GET /features
Retrieves computed features for all transactions.

**Response:**
```json
[
  {
    "txn_id": "T123",
    "features": {
      "amount": 50000.0,
      "amount_log": 10.82,
      "country_risk": 0.3,
      "pep_exposure": 1.0,
      ...
    },
    "computed_at": "2025-01-01T00:00:00Z"
  }
]
```

### GET /features/{txn_id}
Retrieves features for a specific transaction.

### POST /compute
Manually triggers feature computation for a transaction.

**Request Body:**
```json
{
  "txn_id": "T123",
  "transaction_data": {...},
  "customer_data": {...},
  "account_data": {...}
}
```

### GET /health
Health check endpoint.

## Risk Data Sources

### Country Risk Scores
Comprehensive mapping of 70+ countries with risk scores:
- **Low Risk (0.0-0.2)**: US, GB, DE, FR, CA, AU, JP
- **Medium Risk (0.2-0.6)**: SA, AE, BR, IN, CN, RU
- **High Risk (0.6-0.8)**: Tax havens (CH, KY, PA, BZ)
- **Critical Risk (0.8-1.0)**: Sanctioned countries (AF, IR, KP, SY)

### Sanctions Lists
- OFAC (Office of Foreign Assets Control)
- EU Sanctions
- UK Sanctions
- UN Security Council

### High-Risk Jurisdictions
- Offshore financial centers
- Tax havens
- Countries with weak AML controls
- Non-cooperative jurisdictions

## Advanced Analytics

### Velocity Analysis
- Configurable time windows (7, 30 days)
- Transaction frequency patterns
- Amount acceleration detection
- Historical baseline comparison

### Structuring Detection
- Multiple reporting thresholds ($10K, $5K, $3K, $1K)
- Near-threshold transaction patterns
- Rapid succession analysis
- Cumulative amount tracking

### Behavioral Analysis
- Deviation from normal patterns
- Account age considerations
- Transaction timing analysis
- Geographic risk assessment

## Configuration

### Environment Variables
- `VELOCITY_WINDOW_DAYS`: Long-term velocity window (default: 30)
- `VELOCITY_SHORT_WINDOW_DAYS`: Short-term velocity window (default: 7)
- `COUNTRY_RISK_HIGH_THRESHOLD`: High-risk country threshold (default: 0.6)
- `RABBITMQ_URL`: RabbitMQ connection string
- `API_PORT`: API server port (default: 8002)

### Dependencies
- FastAPI: Web framework
- NumPy: Numerical computations
- Pandas: Data manipulation
- aio-pika: RabbitMQ client
- Python-dateutil: Date parsing

## Error Handling

### Data Quality Issues
- Missing transaction data handling
- Invalid timestamp format recovery
- Default feature values for errors
- Graceful degradation

### Processing Errors
- Feature computation fallbacks
- Error logging with context
- Partial feature computation
- Recovery mechanisms

### Performance Optimization
- Efficient data structures
- Vectorized computations
- Memory management
- Caching strategies

## Monitoring

### Performance Metrics
- Feature computation latency
- Memory usage patterns
- Event processing rates
- Error rates by feature type

### Data Quality Metrics
- Feature completeness rates
- Default value usage
- Data validation failures
- Timestamp parsing errors

### Business Metrics
- High-risk feature distributions
- Velocity pattern trends
- Country risk exposure
- Structuring detection rates

## Development

### Local Setup
```bash
cd services/feature-engine
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8002
```

### Testing
```bash
pytest tests/
python -m pytest tests/test_features.py -v
```

### Feature Development
- Add new features to FeatureEngine class
- Update feature documentation
- Add unit tests for new features
- Validate feature distributions

## Production Considerations

### Scalability
- Stateless feature computation
- Horizontal scaling capability
- Efficient memory usage
- Batch processing support

### Data Consistency
- Event ordering guarantees
- Feature versioning
- Backward compatibility
- Schema evolution

### Performance
- Sub-second feature computation
- Optimized algorithms
- Memory-efficient data structures
- Parallel processing capability 