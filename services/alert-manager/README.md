# Alert Manager Microservice

## Overview
The Alert Manager is responsible for generating, managing, and processing AML alerts based on risk scores from the Risk Scorer. It includes AI-powered Suspicious Activity Report (SAR) generation using OpenAI GPT-4, comprehensive alert lifecycle management, and regulatory compliance features.

## Technical Architecture

### Core Components
- **Alert Manager Class**: Core alert processing engine
- **SAR Generator**: AI-powered narrative generation
- **Alert Store**: In-memory alert storage and management
- **Event Consumer**: Processes Scored events from Risk Scorer
- **OpenAI Integration**: GPT-4 powered SAR narrative generation

### Workflow

1. **Alert Generation**
   - Consumes Scored events from Risk Scorer
   - Applies alert threshold filtering (default: 0.7)
   - Performs alert deduplication
   - Determines alert type based on risk factors

2. **SAR Generation**
   - Triggers for high-risk alerts (score >= 0.8)
   - Uses OpenAI GPT-4 for professional narrative generation
   - Falls back to template-based generation
   - Ensures regulatory compliance format

3. **Alert Management**
   - Tracks alert lifecycle (open, investigating, closed)
   - Supports alert assignment to investigators
   - Maintains investigation notes and updates
   - Provides alert statistics and reporting

4. **API Services**
   - RESTful API for alert retrieval and management
   - Filtering and pagination support
   - Alert update and status management
   - Health monitoring and statistics

## Alert Types

### High Risk Transaction
- Triggered by large amounts or high-risk countries
- Focus on transaction-specific risk factors
- Includes amount, geography, and timing analysis
- Suitable for immediate investigation

### Suspicious Pattern
- Triggered by behavioral anomalies
- Focus on customer activity patterns
- Includes velocity, structuring, and PEP analysis
- Requires pattern investigation

### Velocity Spike
- Triggered by unusual transaction frequency
- Focus on temporal activity patterns
- Includes acceleration and volume analysis
- Indicates potential account compromise

### Graph Anomaly
- Triggered by network analysis results
- Focus on relationship and flow patterns
- Includes centrality and community analysis
- Indicates complex money laundering schemes

### Structuring
- Triggered by threshold avoidance patterns
- Focus on amount and timing patterns
- Includes multiple transaction analysis
- Strong indicator of intentional evasion

## AI-Powered SAR Generation

### OpenAI Integration
The system integrates with OpenAI GPT-4 to generate professional, regulatory-compliant SAR narratives.

#### Configuration
```env
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4
OPENAI_MAX_TOKENS=500
OPENAI_TEMPERATURE=0.3
SAR_GENERATION_ENABLED=true
```

#### Generation Process
1. **Risk Factor Analysis**: Extracts significant SHAP values
2. **Prompt Construction**: Creates regulatory-compliant prompt
3. **AI Generation**: Calls OpenAI API with expert system role
4. **Quality Validation**: Ensures narrative meets requirements
5. **Fallback Handling**: Uses templates if AI unavailable

#### Sample AI-Generated SAR
```
SUSPICIOUS ACTIVITY REPORT

Customer ID: CUST_0
Transaction ID: T160
Risk Score: 0.85

On [Date], Customer ID CUST_0 initiated a wire transfer transaction 
involving a total amount of USD 500,000,000. The transaction was flagged 
due to its atypical characteristics relative to the customer's normal 
activity profile. The transaction amount represents a significant deviation 
from the customer's typical transaction behavior, indicating a substantial 
increase in transaction size that warrants further investigation.

Key risk factors include the unusually large transaction amount, high-risk 
counterparty country (Venezuela), PEP customer involvement, and off-hours 
transaction timing. These factors collectively suggest potential money 
laundering or other illicit financial activities.

RECOMMENDATION: Immediate investigation and potential regulatory filing required.
```

### Template-Based Fallback
When OpenAI is unavailable, the system uses professional templates:

#### High Risk Transaction Template
```
SUSPICIOUS ACTIVITY REPORT - HIGH RISK TRANSACTION

Customer ID: {customer_id}
Transaction ID: {txn_id}
Amount: ${amount:,.2f} {currency}
Risk Score: {risk_score:.2f}

SUSPICIOUS ACTIVITY DESCRIPTION:
A high-risk transaction has been identified involving customer {customer_id}. 
The transaction amount of ${amount:,.2f} {currency} to {country} has triggered 
multiple risk indicators with an overall risk score of {risk_score:.2f}.

RISK FACTORS IDENTIFIED:
{risk_factors}

RECOMMENDATION:
This transaction requires immediate investigation and potential filing of a 
Suspicious Activity Report (SAR) with relevant authorities.
```

## API Endpoints

### GET /alerts
Retrieves alerts with optional filtering and pagination.

**Query Parameters:**
- `status`: Filter by alert status (open, investigating, closed)
- `risk_threshold`: Minimum risk score filter
- `limit`: Maximum number of alerts (default: 100)
- `offset`: Number of alerts to skip (default: 0)

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
      "created_at": "2025-01-01T00:00:00Z",
      "updated_at": "2025-01-01T00:00:00Z",
      "sar_narrative": "Professional SAR narrative...",
      "investigation_notes": null,
      "assigned_to": null
    }
  ],
  "total": 150,
  "limit": 100,
  "offset": 0
}
```

### GET /alerts/{alert_id}
Retrieves a specific alert by ID.

**Response:**
```json
{
  "alert_id": "uuid",
  "txn_id": "T123",
  "customer_id": "CUST_123",
  "risk_score": 0.85,
  "status": "open",
  "alert_type": "high_risk_transaction",
  "created_at": "2025-01-01T00:00:00Z",
  "updated_at": "2025-01-01T00:00:00Z",
  "sar_narrative": "Professional SAR narrative...",
  "investigation_notes": null,
  "assigned_to": null
}
```

### PATCH /alerts/{alert_id}
Updates an alert's status, notes, or assignment.

**Request Body:**
```json
{
  "status": "investigating",
  "investigation_notes": "Initial review completed, escalating to senior analyst",
  "assigned_to": "analyst@bank.com"
}
```

### GET /alerts/statistics
Retrieves alert statistics for monitoring and reporting.

**Response:**
```json
{
  "total_alerts": 150,
  "by_status": {
    "open": 45,
    "investigating": 30,
    "closed": 75
  },
  "by_type": {
    "high_risk_transaction": 60,
    "suspicious_pattern": 40,
    "velocity_spike": 25,
    "graph_anomaly": 15,
    "structuring": 10
  },
  "avg_risk_score": 0.78,
  "high_risk_count": 85
}
```

### GET /health
Health check endpoint for monitoring.

## Alert Lifecycle Management

### Alert States
1. **Open**: Newly created alert awaiting review
2. **Investigating**: Alert assigned and under investigation
3. **Closed**: Investigation completed, resolution documented

### State Transitions
- Open → Investigating: When assigned to analyst
- Investigating → Closed: When investigation completed
- Closed → Investigating: If reopened for additional review

### Assignment Management
- Alerts can be assigned to specific investigators
- Assignment tracking for workload management
- Automatic assignment rules (future enhancement)
- Escalation procedures for high-risk alerts

### Investigation Notes
- Free-text notes for investigation progress
- Timestamped updates for audit trail
- Structured investigation outcomes
- Integration with case management systems

## Risk Thresholds and Configuration

### Alert Generation Thresholds
- **Alert Threshold**: 0.7 (configurable via RISK_THRESHOLD_ALERT)
- **SAR Generation Threshold**: 0.8 (automatic SAR generation)
- **Critical Alert Threshold**: 0.9 (immediate escalation)

### Configuration Parameters
```env
# Alert Management
RISK_THRESHOLD_ALERT=0.7
AUTO_ASSIGN_ALERTS=false
SAR_GENERATION_ENABLED=true

# OpenAI Configuration
OPENAI_API_KEY=your_key_here
OPENAI_MODEL=gpt-4
OPENAI_MAX_TOKENS=500
OPENAI_TEMPERATURE=0.3

# Service Configuration
RABBITMQ_URL=amqp://guest:guest@rabbitmq:5672/
API_PORT=8005
```

## Deduplication and Quality Control

### Alert Deduplication
- Prevents duplicate alerts for same transaction
- Checks existing alerts before creation
- Updates existing alerts with new information
- Maintains alert history and versions

### Quality Assurance
- Validates SAR narrative quality and length
- Ensures regulatory compliance format
- Checks for required information completeness
- Maintains audit trail for all changes

### Error Handling
- Graceful handling of OpenAI API failures
- Fallback to template-based generation
- Comprehensive error logging
- Recovery mechanisms for service failures

## Monitoring and Metrics

### Performance Metrics
- Alert generation latency
- SAR generation success rate
- API response times
- OpenAI API call success rate

### Business Metrics
- Alert volume by type and risk score
- Investigation completion rates
- SAR filing rates
- False positive analysis

### Quality Metrics
- SAR narrative quality scores
- Regulatory compliance rates
- Investigation outcome tracking
- Customer feedback integration

## Regulatory Compliance

### SAR Requirements
- Professional narrative format
- Complete risk factor documentation
- Specific recommendations for investigators
- Regulatory submission ready format
- Audit trail maintenance

### Documentation Standards
- Detailed investigation notes
- Risk factor explanations
- Decision rationale documentation
- Compliance officer review process

### Audit Trail
- Complete alert lifecycle tracking
- All status changes logged
- Investigation progress documented
- Regulatory submission records

## Development

### Local Setup
```bash
cd services/alert-manager
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8005
```

### Environment Setup
```bash
# Copy example environment file
cp example.env.txt .env

# Edit with your OpenAI API key
nano .env
```

### Testing
```bash
pytest tests/
python -m pytest tests/test_alerts.py -v
```

### SAR Template Development
```bash
python test_sar_generation.py --template high_risk_transaction
```

## Production Considerations

### Scalability
- Stateless alert processing
- Horizontal scaling capability
- Efficient memory management
- Batch processing support

### Security
- Secure OpenAI API key management
- Encrypted alert data storage
- Access control for sensitive data
- Audit logging for compliance

### Reliability
- OpenAI API retry mechanisms
- Fallback to template generation
- Data persistence and recovery
- Health monitoring and alerting

### Integration
- RESTful API for external systems
- Event-driven architecture
- Database integration ready
- Case management system integration 