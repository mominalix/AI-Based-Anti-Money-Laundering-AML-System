# Graph Analysis Microservice

## Overview
The Graph Analysis service performs network analysis on transaction data to identify suspicious patterns, money laundering networks, and complex financial relationships. It uses graph algorithms to detect anomalies that may not be visible through traditional transaction-level analysis.

## Technical Architecture

### Core Components
- **Graph Builder**: Constructs transaction networks from data
- **Network Analyzer**: Applies graph algorithms for pattern detection
- **Anomaly Detector**: Identifies suspicious network structures
- **Community Detector**: Finds clusters of related entities
- **Event Consumer**: Processes Scored events from Risk Scorer

### Workflow

1. **Graph Construction**
   - Builds dynamic transaction networks
   - Creates nodes for accounts, customers, and entities
   - Establishes edges for transaction relationships
   - Maintains temporal graph evolution

2. **Network Analysis**
   - Calculates centrality measures
   - Identifies key network players
   - Detects community structures
   - Analyzes transaction flows

3. **Anomaly Detection**
   - Identifies unusual network patterns
   - Detects potential money laundering structures
   - Flags suspicious entity relationships
   - Analyzes transaction timing patterns

4. **Event Publishing**
   - Publishes GraphAnalyzed events
   - Includes network metrics and anomaly scores
   - Provides detailed analysis results
   - Triggers alert generation for high-risk patterns

## Graph Analysis Techniques

### Network Centrality Measures

#### Degree Centrality
- Measures direct connections to an entity
- Identifies highly connected accounts
- Useful for finding transaction hubs
- Formula: `degree(v) / (n-1)`

#### Betweenness Centrality
- Measures control over information flow
- Identifies critical intermediary accounts
- Detects potential money laundering conduits
- Formula: `sum(shortest_paths_through_v / total_shortest_paths)`

#### Closeness Centrality
- Measures average distance to all other nodes
- Identifies entities with efficient network access
- Useful for detecting coordination centers
- Formula: `(n-1) / sum(distances_from_v)`

#### PageRank
- Measures importance based on incoming connections
- Weighted by transaction amounts and frequency
- Identifies influential entities in the network
- Adapted Google PageRank algorithm

### Community Detection

#### Louvain Algorithm
- Detects communities of closely connected entities
- Optimizes modularity measure
- Identifies potential money laundering rings
- Hierarchical community structure

#### Label Propagation
- Fast community detection method
- Propagates labels through network connections
- Identifies tightly connected groups
- Useful for real-time analysis

### Anomaly Detection Patterns

#### Circular Transactions
- Detects money flowing in circles
- Identifies potential layering schemes
- Analyzes transaction timing and amounts
- Flags suspicious round-trip patterns

#### Star Patterns
- Identifies central accounts with many connections
- Detects potential smurfing operations
- Analyzes transaction distribution patterns
- Flags unusual concentration of activity

#### Chain Patterns
- Detects long transaction chains
- Identifies potential layering sequences
- Analyzes transaction timing and amounts
- Flags suspicious sequential transfers

#### Bipartite Structures
- Identifies two-group transaction patterns
- Detects potential structuring operations
- Analyzes cross-group transaction flows
- Flags unusual segregation patterns

## API Endpoints

### GET /analysis
Retrieves graph analysis results for all entities.

**Response:**
```json
[
  {
    "entity_id": "ACC123",
    "entity_type": "account",
    "centrality_measures": {
      "degree": 0.15,
      "betweenness": 0.08,
      "closeness": 0.12,
      "pagerank": 0.05
    },
    "community_id": "C001",
    "anomaly_score": 0.75,
    "risk_patterns": ["circular_transactions", "high_velocity"],
    "analyzed_at": "2025-01-01T00:00:00Z"
  }
]
```

### GET /analysis/{entity_id}
Retrieves analysis for a specific entity.

### GET /communities
Retrieves detected communities and their members.

**Response:**
```json
[
  {
    "community_id": "C001",
    "size": 15,
    "modularity": 0.82,
    "risk_score": 0.65,
    "members": ["ACC123", "ACC124", "ACC125"],
    "transaction_volume": 5000000.0,
    "internal_transactions": 45,
    "external_transactions": 12
  }
]
```

### GET /patterns
Retrieves detected suspicious patterns.

**Response:**
```json
[
  {
    "pattern_id": "P001",
    "pattern_type": "circular_transactions",
    "entities": ["ACC123", "ACC124", "ACC125"],
    "confidence": 0.89,
    "risk_score": 0.92,
    "description": "Circular transaction pattern detected",
    "transaction_count": 8,
    "total_amount": 500000.0,
    "time_span": "2 hours"
  }
]
```

### POST /analyze
Manually triggers graph analysis for specific entities.

**Request Body:**
```json
{
  "entity_ids": ["ACC123", "ACC124"],
  "analysis_type": "full",
  "time_window": "30d"
}
```

### GET /network/export
Exports network data for visualization.

**Response:**
```json
{
  "nodes": [
    {
      "id": "ACC123",
      "type": "account",
      "risk_score": 0.75,
      "transaction_count": 25,
      "total_amount": 1000000.0
    }
  ],
  "edges": [
    {
      "source": "ACC123",
      "target": "ACC124",
      "weight": 500000.0,
      "transaction_count": 5,
      "risk_score": 0.65
    }
  ]
}
```

### GET /health
Health check endpoint.

## Advanced Analytics

### Temporal Analysis
- Time-series analysis of network evolution
- Detection of coordinated activity patterns
- Analysis of transaction timing correlations
- Identification of burst activity periods

### Flow Analysis
- Money flow tracking through the network
- Source and destination analysis
- Flow concentration detection
- Unusual flow pattern identification

### Structural Analysis
- Network topology analysis
- Identification of structural anomalies
- Detection of artificial network structures
- Analysis of network resilience

### Risk Propagation
- Risk score propagation through networks
- Contamination analysis
- Risk amplification detection
- Network-based risk assessment

## Suspicious Pattern Detection

### Money Laundering Typologies

#### Placement Patterns
- Large cash deposits followed by transfers
- Multiple small deposits (smurfing)
- Use of multiple accounts for placement
- Rapid movement after placement

#### Layering Patterns
- Complex transaction chains
- Multiple jurisdictional transfers
- Rapid back-and-forth movements
- Shell company involvement

#### Integration Patterns
- Conversion to legitimate assets
- Investment in businesses
- Real estate transactions
- Luxury goods purchases

### Network-Based Indicators

#### Structural Indicators
- Unusual network topology
- Artificial connection patterns
- Isolated subnetworks
- Bridge account usage

#### Behavioral Indicators
- Coordinated transaction timing
- Similar transaction amounts
- Synchronized account activity
- Unusual transaction patterns

#### Temporal Indicators
- Burst activity periods
- Off-hours coordination
- Rapid sequence transactions
- Time-based clustering

## Configuration

### Environment Variables
- `GRAPH_ANALYSIS_ENABLED`: Enable graph analysis (default: true)
- `COMMUNITY_DETECTION_ALGORITHM`: Algorithm choice (default: louvain)
- `ANOMALY_THRESHOLD`: Anomaly detection threshold (default: 0.7)
- `TIME_WINDOW_DAYS`: Analysis time window (default: 30)
- `MIN_COMMUNITY_SIZE`: Minimum community size (default: 3)
- `RABBITMQ_URL`: RabbitMQ connection string
- `API_PORT`: API server port (default: 8004)

### Algorithm Parameters
- `PAGERANK_DAMPING`: PageRank damping factor (default: 0.85)
- `LOUVAIN_RESOLUTION`: Louvain resolution parameter (default: 1.0)
- `CENTRALITY_THRESHOLD`: Centrality significance threshold (default: 0.1)

### Dependencies
- FastAPI: Web framework
- NetworkX: Graph analysis library
- NumPy: Numerical computations
- Pandas: Data manipulation
- scikit-learn: Machine learning algorithms
- aio-pika: RabbitMQ client

## Performance Optimization

### Graph Storage
- Efficient graph data structures
- Memory-optimized representations
- Incremental graph updates
- Compressed storage formats

### Algorithm Optimization
- Parallel algorithm execution
- Approximate algorithms for large graphs
- Incremental computation
- Caching of intermediate results

### Scalability Considerations
- Distributed graph processing
- Graph partitioning strategies
- Streaming graph analysis
- Memory management for large networks

## Monitoring

### Performance Metrics
- Graph construction time
- Analysis algorithm execution time
- Memory usage for graph storage
- Network size and complexity metrics

### Quality Metrics
- Anomaly detection accuracy
- Community detection quality
- Pattern recognition precision
- False positive/negative rates

### Business Metrics
- Suspicious pattern detection rates
- Network risk score distributions
- Community risk assessments
- Investigation success rates

## Visualization Support

### Network Visualization
- Graph layout algorithms (force-directed, circular)
- Node and edge styling based on risk scores
- Interactive exploration capabilities
- Temporal network animation

### Pattern Visualization
- Suspicious pattern highlighting
- Community structure visualization
- Flow diagram generation
- Risk heatmap overlays

### Export Formats
- GraphML for Gephi
- JSON for D3.js
- CSV for spreadsheet analysis
- PNG/SVG for reports

## Development

### Local Setup
```bash
cd services/graph-analysis
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8004
```

### Testing
```bash
pytest tests/
python -m pytest tests/test_graph_analysis.py -v
```

### Algorithm Development
```bash
python test_algorithms.py --algorithm louvain --data sample_network.json
```

## Production Considerations

### Scalability
- Horizontal scaling for large networks
- Distributed graph processing
- Efficient memory management
- Streaming analysis capabilities

### Data Privacy
- Anonymization of sensitive data
- Secure graph storage
- Access control for network data
- Audit logging for analysis

### Regulatory Compliance
- Explainable analysis results
- Audit trail for decisions
- Documentation of methodologies
- Validation of detection accuracy 