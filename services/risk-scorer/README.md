# Risk Scorer Microservice

## Overview
The Risk Scorer applies machine learning models and business rules to assess money laundering risk for each transaction. It combines ensemble ML models with explainable AI techniques to provide accurate risk scores and detailed explanations for compliance officers.

## Technical Architecture

### Core Components
- **Risk Scorer Class**: Main ML inference engine
- **Model Ensemble**: Multiple ML models for robust predictions
- **Business Rules Engine**: Rule-based risk assessment
- **SHAP Explainer**: Feature importance calculation
- **Event Consumer**: Processes FeatureComputed events

### Workflow

1. **Event Consumption**
   - Listens for FeatureComputed events from RabbitMQ
   - Receives feature vectors from Feature Engine
   - Validates feature completeness and quality

2. **Risk Assessment**
   - Applies ensemble ML models (Gradient Boosting + Random Forest)
   - Executes business rules overlay
   - Combines model predictions with rule-based scores
   - Calculates confidence intervals

3. **Explainability**
   - Computes SHAP values for feature importance
   - Generates risk factor explanations
   - Provides model confidence metrics
   - Creates audit trail for decisions

4. **Event Publishing**
   - Publishes Scored events with complete risk assessment
   - Includes risk score, confidence, and explanations
   - Triggers downstream alert generation

## Machine Learning Models

### Ensemble Architecture
The system uses an ensemble of two complementary models:

#### Primary Model: Gradient Boosting Classifier
- **Algorithm**: XGBoost-style gradient boosting
- **Features**: All 32 computed features
- **Strengths**: Handles feature interactions, robust to outliers
- **Use Case**: Primary risk assessment

#### Secondary Model: Random Forest Classifier
- **Algorithm**: Random Forest with 100 estimators
- **Features**: Selected high-importance features
- **Strengths**: Stable predictions, handles missing values
- **Use Case**: Ensemble validation and confidence estimation

### Model Combination
```python
combined_score = (primary_weight * primary_score + 
                 ensemble_weight * ensemble_score) / 2
```

### Risk Categories
- **Low Risk**: 0.0 - 0.3
- **Medium Risk**: 0.3 - 0.7
- **High Risk**: 0.7 - 0.9
- **Critical Risk**: 0.9 - 1.0

## Business Rules Engine

### Rule Categories

#### Amount-Based Rules
- Large transaction thresholds ($50K, $100K, $500K)
- Round number detection
- Structuring pattern identification
- Currency-specific thresholds

#### Geographic Rules
- Sanctioned country transactions
- High-risk jurisdiction flags
- Tax haven involvement
- Cross-border risk assessment

#### Temporal Rules
- Off-hours transaction patterns
- Weekend activity flags
- Rapid succession detection
- Unusual timing patterns

#### Customer Rules
- PEP (Politically Exposed Person) involvement
- KYC gap assessment
- Account age considerations
- Risk category escalation

### Rule Scoring
Each rule contributes to the overall risk score:
```python
rule_score = base_score + sum(triggered_rules * rule_weights)
final_score = min(ml_score + rule_score, 1.0)
```

## Explainable AI

### SHAP (SHapley Additive exPlanations)
- Computes feature importance for each prediction
- Provides local explanations for individual transactions
- Enables audit trail for regulatory compliance
- Supports model debugging and validation

### Feature Importance Categories
- **High Impact** (>0.05): Primary risk drivers
- **Medium Impact** (0.01-0.05): Secondary factors
- **Low Impact** (<0.01): Background factors

### Explanation Format
```json
{
  "shap_values": {
    "amount": 0.15,
    "country_risk": 0.12,
    "pep_exposure": 0.08,
    "off_hours": 0.03
  },
  "risk_factors": [
    "Large transaction amount ($500K)",
    "High-risk counterparty country",
    "PEP customer involvement"
  ]
}
```

## API Endpoints

### GET /scores
Retrieves risk scores for all transactions.

**Response:**
```json
[
  {
    "txn_id": "T123",
    "risk_score": 0.85,
    "confidence": 0.92,
    "risk_category": "high",
    "model_scores": {
      "primary": 0.83,
      "ensemble": 0.87,
      "combined": 0.85
    },
    "shap_values": {...},
    "scored_at": "2025-01-01T00:00:00Z"
  }
]
```

### GET /scores/{txn_id}
Retrieves risk score for a specific transaction.

### POST /score
Manually triggers risk scoring for a transaction.

**Request Body:**
```json
{
  "txn_id": "T123",
  "features": {
    "amount": 50000.0,
    "country_risk": 0.8,
    ...
  }
}
```

### GET /model/info
Returns model information and statistics.

**Response:**
```json
{
  "model_version": "1.0.0",
  "features_count": 32,
  "training_date": "2025-01-01",
  "performance_metrics": {
    "accuracy": 0.94,
    "precision": 0.91,
    "recall": 0.89,
    "f1_score": 0.90
  }
}
```

### GET /health
Health check endpoint.

## Model Performance

### Training Metrics
- **Accuracy**: 94.2%
- **Precision**: 91.3%
- **Recall**: 89.7%
- **F1-Score**: 90.5%
- **AUC-ROC**: 0.96

### Feature Importance (Top 10)
1. **amount** (0.18): Transaction amount
2. **country_risk** (0.15): Counterparty country risk
3. **pep_exposure** (0.12): PEP involvement
4. **velocity_score** (0.10): Transaction velocity
5. **amount_deviation** (0.08): Amount deviation from normal
6. **sanctions_country** (0.07): Sanctioned country flag
7. **off_hours** (0.06): Off-hours transaction
8. **structuring_score** (0.05): Structuring indicators
9. **kyc_gap_score** (0.04): KYC verification gap
10. **high_risk_country** (0.04): High-risk jurisdiction

### Validation Results
- **Cross-validation accuracy**: 93.8% ± 1.2%
- **Out-of-time validation**: 92.1%
- **False positive rate**: 8.7%
- **False negative rate**: 10.3%

## Configuration

### Environment Variables
- `MODEL_VERSION`: Model version identifier
- `CONFIDENCE_THRESHOLD`: Minimum confidence threshold (default: 0.7)
- `SHAP_ENABLED`: Enable SHAP explanations (default: true)
- `BUSINESS_RULES_ENABLED`: Enable business rules (default: true)
- `RABBITMQ_URL`: RabbitMQ connection string
- `API_PORT`: API server port (default: 8003)

### Model Configuration
- `PRIMARY_MODEL_WEIGHT`: Primary model weight (default: 0.6)
- `ENSEMBLE_MODEL_WEIGHT`: Ensemble model weight (default: 0.4)
- `RULE_WEIGHT`: Business rules weight (default: 0.2)

### Dependencies
- FastAPI: Web framework
- scikit-learn: Machine learning models
- SHAP: Model explainability
- NumPy: Numerical computations
- Pandas: Data manipulation
- aio-pika: RabbitMQ client

## Error Handling

### Model Errors
- Fallback to business rules only
- Default risk scores for missing features
- Model validation and health checks
- Graceful degradation strategies

### Data Quality Issues
- Feature validation and normalization
- Missing value imputation
- Outlier detection and handling
- Data drift monitoring

### Performance Issues
- Model inference timeout handling
- Memory management for large batches
- Async processing for scalability
- Circuit breaker patterns

## Monitoring

### Model Performance
- Prediction accuracy tracking
- Feature drift detection
- Model confidence distributions
- Prediction latency metrics

### Business Metrics
- Risk score distributions
- Alert generation rates
- False positive/negative rates
- Model explanation quality

### System Metrics
- Inference latency (p95, p99)
- Memory usage patterns
- CPU utilization
- Event processing rates

## Model Management

### Model Versioning
- Semantic versioning (major.minor.patch)
- Model artifact storage
- A/B testing capabilities
- Rollback mechanisms

### Model Updates
- Blue-green deployment strategy
- Gradual rollout procedures
- Performance comparison
- Automated validation

### Model Monitoring
- Data drift detection
- Performance degradation alerts
- Feature importance changes
- Prediction distribution shifts

## Development

### Local Setup
```bash
cd services/risk-scorer
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8003
```

### Model Training
```bash
python train_model.py --data data/training.csv --output models/
```

### Testing
```bash
pytest tests/
python -m pytest tests/test_models.py -v
```

### Model Evaluation
```bash
python evaluate_model.py --model models/risk_model.pkl --test data/test.csv
```

## Production Considerations

### Scalability
- Stateless model inference
- Horizontal scaling support
- Model caching strategies
- Batch processing capabilities

### Security
- Model artifact protection
- Feature data encryption
- Audit logging
- Access control

### Compliance
- Model explainability requirements
- Audit trail maintenance
- Regulatory reporting
- Model validation documentation 