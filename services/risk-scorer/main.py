import json
import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel
import aio_pika
from aio_pika import ExchangeType

from scorer import RiskScorer
from events import publish_event, consume_events

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global variables
connection = None
channel = None
exchange = None
risk_scorer = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    global connection, channel, exchange, risk_scorer
    
    try:
        # Initialize risk scorer
        risk_scorer = RiskScorer()
        
        # Connect to RabbitMQ
        connection = await aio_pika.connect_robust("amqp://guest:guest@rabbitmq:5672/")
        channel = await connection.channel()
        exchange = await channel.declare_exchange(
            "aml.events", 
            ExchangeType.FANOUT,
            durable=True
        )
        
        # Start consuming events
        asyncio.create_task(consume_events(channel, exchange, process_features_ready_event))
        
        logger.info("Risk Scoring service started successfully")
        
    except Exception as e:
        logger.error(f"Failed to start Risk Scoring service: {e}")
        raise
    
    yield
    
    # Shutdown
    if connection:
        await connection.close()

app = FastAPI(
    title="AML Risk Scoring API",
    version="1.0.0",
    description="ML-based risk scoring service using ONNX runtime",
    lifespan=lifespan
)

class ScoreRequest(BaseModel):
    txn_id: str
    features: Dict[str, float]

class ScoreResponse(BaseModel):
    txn_id: str
    risk_score: float
    confidence: float
    shap_values: Dict[str, float]
    scored_at: datetime

class ModelMetrics(BaseModel):
    model_version: str
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    last_updated: datetime

class ScoresListResponse(BaseModel):
    scores: list
    total: int

class HealthResponse(BaseModel):
    status: str
    timestamp: datetime

# In-memory storage for demo purposes
scored_transactions = {}



async def process_features_ready_event(event_data: Dict[str, Any]):
    """Process FeaturesReady events and compute risk scores"""
    event_type = event_data.get("type")
    data = event_data.get("data", {})
    
    try:
        if event_type == "FeaturesReady":
            txn_id = data["txn_id"]
            features = data["features"]
            
            # Compute risk score
            score_result = await risk_scorer.score_transaction(txn_id, features)
            
            # Store the score
            scored_transactions[txn_id] = score_result
            
            # Publish scored event
            await publish_event(
                exchange,
                "Scored",
                score_result
            )
            
    except Exception as e:
        logger.error(f"Error processing FeaturesReady event: {e}")

@app.post("/score", response_model=ScoreResponse)
async def score_transaction(request: ScoreRequest):
    """Score transaction risk"""
    try:
        score_result = await risk_scorer.score_transaction(
            request.txn_id, 
            request.features
        )
        
        return ScoreResponse(**score_result)
        
    except Exception as e:
        logger.error(f"Error scoring transaction {request.txn_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Error computing risk score"
        )

@app.get("/model/metrics", response_model=ModelMetrics)
async def get_model_metrics():
    """Get model performance metrics"""
    try:
        metrics = risk_scorer.get_model_metrics()
        return ModelMetrics(**metrics)
        
    except Exception as e:
        logger.error(f"Error getting model metrics: {e}")
        raise HTTPException(
            status_code=500,
            detail="Error retrieving model metrics"
        )

@app.get("/scores", response_model=ScoresListResponse)
async def get_all_scores():
    """Get all computed risk scores"""
    
    scores_list = []
    for txn_id, score_data in scored_transactions.items():
        # Convert datetime to string for JSON serialization
        score_copy = score_data.copy()
        if 'scored_at' in score_copy and isinstance(score_copy['scored_at'], datetime):
            score_copy['scored_at'] = score_copy['scored_at'].isoformat()
        
        scores_list.append({
            "customer_id": f"CUST_{txn_id[-1]}",  # Mock customer ID
            "account_id": f"ACC_{txn_id[-3:]}",   # Mock account ID
            **score_copy
        })
    
    return ScoresListResponse(
        scores=scores_list,
        total=len(scores_list)
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
    uvicorn.run(app, host="0.0.0.0", port=8003) 