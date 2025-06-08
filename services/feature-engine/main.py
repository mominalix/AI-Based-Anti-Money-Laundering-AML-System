import json
import asyncio
import logging
import os
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from collections import defaultdict
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel
import aio_pika
from aio_pika import ExchangeType
from dotenv import load_dotenv

from features import FeatureEngine
from events import publish_event, consume_events

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global variables
connection = None
channel = None
exchange = None
feature_engine = None

# In-memory storage for demo purposes (in production, use Redis or similar)
transaction_store = {}
customer_store = {}
account_store = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    global connection, channel, exchange, feature_engine
    
    try:
        # Initialize feature engine
        feature_engine = FeatureEngine()
        
        # Connect to RabbitMQ
        rabbitmq_url = os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672/")
        connection = await aio_pika.connect_robust(rabbitmq_url)
        channel = await connection.channel()
        exchange = await channel.declare_exchange(
            "aml.events", 
            ExchangeType.FANOUT,
            durable=True
        )
        
        # Start consuming events
        asyncio.create_task(consume_events(channel, exchange, process_ingested_event))
        
        logger.info("Feature Engineering service started successfully")
        
    except Exception as e:
        logger.error(f"Failed to start Feature Engineering service: {e}")
        raise
    
    yield
    
    # Shutdown
    if connection:
        await connection.close()

app = FastAPI(
    title="AML Feature Engineering API",
    version="1.0.0",
    description="Computes features for transactions including velocity, country risk, and KYC gaps",
    lifespan=lifespan
)

class TransactionFeatures(BaseModel):
    txn_id: str
    features: Dict[str, float]
    computed_at: datetime

class ComputeFeaturesRequest(BaseModel):
    txn_id: str
    account_id: str
    timestamp: str
    amount: float
    currency: str
    counterparty_country: str

class FeaturesListResponse(BaseModel):
    features: list
    total: int

class HealthResponse(BaseModel):
    status: str
    timestamp: datetime



async def process_ingested_event(event_data: Dict[str, Any]):
    """Process ingested events and compute features"""
    event_type = event_data.get("type")
    data = event_data.get("data", {})
    
    try:
        if event_type == "IngestedTransaction":
            # Store transaction data
            txn_id = data["txn_id"]
            transaction_store[txn_id] = data
            
            # Compute features
            features = await feature_engine.compute_features(
                data, 
                transaction_store, 
                customer_store, 
                account_store
            )
            
            # Publish features ready event
            await publish_event(
                exchange,
                "FeaturesReady",
                {
                    "txn_id": txn_id,
                    "features": features
                }
            )
            
        elif event_type == "IngestedCustomer":
            customer_store[data["customer_id"]] = data
            
        elif event_type == "IngestedAccount":
            account_store[data["account_id"]] = data
            
    except Exception as e:
        logger.error(f"Error processing event {event_type}: {e}")

@app.get("/features/{txn_id}", response_model=TransactionFeatures)
async def get_features(txn_id: str):
    """Get computed features for a transaction"""
    if txn_id not in transaction_store:
        raise HTTPException(
            status_code=404,
            detail="Transaction not found"
        )
    
    transaction_data = transaction_store[txn_id]
    
    try:
        features = await feature_engine.compute_features(
            transaction_data,
            transaction_store,
            customer_store,
            account_store
        )
        
        return TransactionFeatures(
            txn_id=txn_id,
            features=features,
            computed_at=datetime.utcnow()
        )
        
    except Exception as e:
        logger.error(f"Error computing features for {txn_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Error computing features"
        )

@app.post("/compute", response_model=TransactionFeatures)
async def compute_features(request: ComputeFeaturesRequest):
    """Compute features for a transaction directly"""
    
    # Convert request to transaction data format
    transaction_data = {
        "txn_id": request.txn_id,
        "account_id": request.account_id,
        "timestamp": request.timestamp,
        "amount": request.amount,
        "currency": request.currency,
        "counterparty_country": request.counterparty_country
    }
    
    try:
        features = await feature_engine.compute_features(
            transaction_data,
            transaction_store,
            customer_store,
            account_store
        )
        
        return TransactionFeatures(
            txn_id=request.txn_id,
            features=features,
            computed_at=datetime.utcnow()
        )
        
    except Exception as e:
        logger.error(f"Error computing features: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error computing features: {str(e)}"
        )

@app.get("/features", response_model=FeaturesListResponse)
async def get_all_features():
    """Get all computed features"""
    
    features_list = []
    
    for txn_id, transaction_data in transaction_store.items():
        try:
            features = await feature_engine.compute_features(
                transaction_data,
                transaction_store,
                customer_store,
                account_store
            )
            
            features_list.append({
                "txn_id": txn_id,
                "features": features,
                "computed_at": datetime.utcnow().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Error computing features for {txn_id}: {e}")
    
    return FeaturesListResponse(
        features=features_list,
        total=len(features_list)
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
    uvicorn.run(app, host="0.0.0.0", port=8002) 