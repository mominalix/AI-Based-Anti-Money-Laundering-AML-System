import json
import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

from fastapi import FastAPI, HTTPException, status, Query
from pydantic import BaseModel
import aio_pika
from aio_pika import ExchangeType

from alerts import AlertManager
from events import consume_events

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="AML Alert Manager API",
    version="1.0.0",
    description="Manages AML alerts, deduplication, and SAR narrative generation"
)

# Global variables
connection = None
channel = None
exchange = None
alert_manager = None

class Alert(BaseModel):
    alert_id: str
    txn_id: str
    customer_id: str
    risk_score: float
    status: str
    alert_type: str
    created_at: datetime
    updated_at: datetime
    sar_narrative: Optional[str] = None
    investigation_notes: Optional[str] = None
    assigned_to: Optional[str] = None

class AlertUpdate(BaseModel):
    status: Optional[str] = None
    investigation_notes: Optional[str] = None
    assigned_to: Optional[str] = None

class AlertsResponse(BaseModel):
    alerts: List[Alert]
    total: int
    limit: int
    offset: int

class HealthResponse(BaseModel):
    status: str
    timestamp: datetime

@app.on_event("startup")
async def startup_event():
    """Initialize RabbitMQ connection and alert manager on startup"""
    global connection, channel, exchange, alert_manager
    
    try:
        # Initialize alert manager
        alert_manager = AlertManager()
        
        # Connect to RabbitMQ
        connection = await aio_pika.connect_robust("amqp://guest:guest@rabbitmq:5672/")
        channel = await connection.channel()
        exchange = await channel.declare_exchange(
            "aml.events", 
            ExchangeType.FANOUT,
            durable=True
        )
        
        # Start consuming events
        asyncio.create_task(consume_events(channel, exchange, process_scored_event))
        
        logger.info("Alert Manager service started successfully")
        
    except Exception as e:
        logger.error(f"Failed to start Alert Manager service: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Close RabbitMQ connection on shutdown"""
    global connection
    if connection:
        await connection.close()

async def process_scored_event(event_data: Dict[str, Any]):
    """Process Scored events and generate alerts"""
    event_type = event_data.get("type")
    data = event_data.get("data", {})
    
    try:
        if event_type == "Scored":
            # Create alert from scored transaction
            alert = await alert_manager.process_scored_transaction(data)
            if alert:
                logger.info(f"Created alert {alert['alert_id']} for transaction {alert['txn_id']}")
            
    except Exception as e:
        logger.error(f"Error processing Scored event: {e}")

@app.get("/alerts", response_model=AlertsResponse)
async def get_alerts(
    status: Optional[str] = Query(None, description="Filter by alert status"),
    risk_threshold: Optional[float] = Query(None, description="Minimum risk score"),
    limit: int = Query(100, description="Maximum number of alerts to return"),
    offset: int = Query(0, description="Number of alerts to skip")
):
    """Get alerts with optional filtering"""
    try:
        alerts = await alert_manager.get_alerts(
            status=status,
            risk_threshold=risk_threshold,
            limit=limit,
            offset=offset
        )
        
        total = await alert_manager.count_alerts(status=status, risk_threshold=risk_threshold)
        
        return AlertsResponse(
            alerts=alerts,
            total=total,
            limit=limit,
            offset=offset
        )
        
    except Exception as e:
        logger.error(f"Error retrieving alerts: {e}")
        raise HTTPException(
            status_code=500,
            detail="Error retrieving alerts"
        )

@app.get("/alerts/{alert_id}", response_model=Alert)
async def get_alert(alert_id: str):
    """Get specific alert by ID"""
    try:
        alert = await alert_manager.get_alert_by_id(alert_id)
        
        if not alert:
            raise HTTPException(
                status_code=404,
                detail="Alert not found"
            )
        
        return Alert(**alert)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving alert {alert_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Error retrieving alert"
        )

@app.patch("/alerts/{alert_id}", response_model=Alert)
async def update_alert(alert_id: str, update: AlertUpdate):
    """Update alert status and notes"""
    try:
        updated_alert = await alert_manager.update_alert(alert_id, update.dict(exclude_unset=True))
        
        if not updated_alert:
            raise HTTPException(
                status_code=404,
                detail="Alert not found"
            )
        
        return Alert(**updated_alert)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating alert {alert_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Error updating alert"
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
    uvicorn.run(app, host="0.0.0.0", port=8005) 