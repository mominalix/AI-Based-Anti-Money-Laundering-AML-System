import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel

from graph import GraphAnalyzer

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="AML Graph Analysis API",
    version="1.0.0",
    description="Real-time customer/counterparty graph analysis with centrality and community detection"
)

# Global variables
graph_analyzer = None

class ConnectedParty(BaseModel):
    party_id: str
    relationship_strength: float
    risk_contribution: float

class GraphAlert(BaseModel):
    alert_type: str
    severity: str
    description: str
    confidence: float

class GraphRiskResponse(BaseModel):
    party_id: str
    cluster_id: str
    centrality_score: float
    community_risk: float
    connected_parties: List[ConnectedParty]
    graph_alerts: List[GraphAlert]
    analyzed_at: datetime

class HealthResponse(BaseModel):
    status: str
    timestamp: datetime

@app.on_event("startup")
async def startup_event():
    """Initialize graph analyzer on startup"""
    global graph_analyzer
    
    try:
        graph_analyzer = GraphAnalyzer()
        logger.info("Graph Analysis service started successfully")
        
    except Exception as e:
        logger.error(f"Failed to start Graph Analysis service: {e}")
        raise

@app.get("/graph/risk/{party_id}", response_model=GraphRiskResponse)
async def get_graph_risk(party_id: str):
    """Get graph-based risk analysis for a party"""
    
    try:
        risk_analysis = await graph_analyzer.analyze_party_risk(party_id)
        
        if not risk_analysis:
            raise HTTPException(
                status_code=404,
                detail="Party not found in graph"
            )
        
        return GraphRiskResponse(**risk_analysis)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing party {party_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Error performing graph analysis"
        )

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow()
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8004) 