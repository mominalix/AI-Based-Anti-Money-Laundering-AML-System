import httpx
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

from fastapi import FastAPI, HTTPException, status, Depends, UploadFile, File, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="AML Gateway API",
    version="1.0.0",
    description="External-facing API gateway for AML system"
)

# Security
security = HTTPBearer(auto_error=False)

# Service URLs (from environment in production)
INGESTION_SERVICE_URL = "http://ingestion:8001"
ALERT_MANAGER_URL = "http://alert-manager:8005"

class BatchResponse(BaseModel):
    message: str
    batch_id: str
    records_processed: int

class Alert(BaseModel):
    alert_id: str
    txn_id: str
    customer_id: str
    risk_score: float
    status: str
    alert_type: str
    created_at: datetime
    updated_at: datetime

class AlertsResponse(BaseModel):
    alerts: List[Alert]
    total: int
    limit: int
    offset: int

class TransactionDetails(BaseModel):
    txn_id: str
    account_id: str
    customer_id: str
    amount: float
    currency: str
    timestamp: datetime
    risk_score: Optional[float] = None
    features: Optional[Dict[str, float]] = None
    alerts: Optional[List[Alert]] = None

class HealthResponse(BaseModel):
    status: str
    timestamp: datetime

async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify JWT token (simplified for demo)"""
    # In production, this would validate JWT tokens
    if not credentials:
        raise HTTPException(
            status_code=401,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # For demo purposes, accept any token
    if credentials.credentials == "demo-token":
        return {"user_id": "demo-user", "role": "analyst"}
    
    # For demo, we'll skip authentication and return a default user
    return {"user_id": "demo-user", "role": "analyst"}

@app.post("/v1/batch", response_model=BatchResponse, status_code=status.HTTP_201_CREATED)
async def upload_batch(
    accounts: UploadFile = File(...),
    customers: UploadFile = File(...),
    transactions: UploadFile = File(...),
    user: dict = Depends(verify_token)
):
    """Upload batch data (proxied to ingestion service)"""
    
    try:
        # Prepare files for forwarding
        files = {
            'accounts': (accounts.filename, await accounts.read(), accounts.content_type),
            'customers': (customers.filename, await customers.read(), customers.content_type),
            'transactions': (transactions.filename, await transactions.read(), transactions.content_type)
        }
        
        # Forward request to ingestion service
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{INGESTION_SERVICE_URL}/batch",
                files=files,
                timeout=60.0
            )
        
        if response.status_code == 201:
            result = response.json()
            logger.info(f"Batch upload successful for user {user['user_id']}: {result['batch_id']}")
            return BatchResponse(**result)
        else:
            logger.error(f"Ingestion service error: {response.status_code} - {response.text}")
            raise HTTPException(
                status_code=response.status_code,
                detail="Error processing batch upload"
            )
            
    except httpx.RequestError as e:
        logger.error(f"Error connecting to ingestion service: {e}")
        raise HTTPException(
            status_code=503,
            detail="Ingestion service unavailable"
        )
    except Exception as e:
        logger.error(f"Unexpected error in batch upload: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )

@app.get("/v1/alerts", response_model=AlertsResponse)
async def get_alerts(
    status: Optional[str] = Query(None, description="Filter by alert status"),
    risk_threshold: Optional[float] = Query(None, description="Minimum risk score"),
    limit: int = Query(100, description="Maximum number of alerts to return"),
    offset: int = Query(0, description="Number of alerts to skip"),
    user: dict = Depends(verify_token)
):
    """Get alerts"""
    
    try:
        # Build query parameters
        params = {
            "limit": limit,
            "offset": offset
        }
        if status:
            params["status"] = status
        if risk_threshold:
            params["risk_threshold"] = risk_threshold
        
        # Forward request to alert manager
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{ALERT_MANAGER_URL}/alerts",
                params=params,
                timeout=30.0
            )
        
        if response.status_code == 200:
            result = response.json()
            logger.info(f"Retrieved {len(result['alerts'])} alerts for user {user['user_id']}")
            return AlertsResponse(**result)
        else:
            logger.error(f"Alert manager error: {response.status_code} - {response.text}")
            raise HTTPException(
                status_code=response.status_code,
                detail="Error retrieving alerts"
            )
            
    except httpx.RequestError as e:
        logger.error(f"Error connecting to alert manager: {e}")
        raise HTTPException(
            status_code=503,
            detail="Alert manager service unavailable"
        )
    except Exception as e:
        logger.error(f"Unexpected error retrieving alerts: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )

@app.get("/v1/transactions/{id}", response_model=TransactionDetails)
async def get_transaction(
    id: str,
    user: dict = Depends(verify_token)
):
    """Get transaction details"""
    
    # For demo purposes, return mock transaction details
    # In production, this would aggregate data from multiple services
    
    try:
        # Mock transaction data
        transaction = TransactionDetails(
            txn_id=id,
            account_id=f"ACC{id[-3:]}",
            customer_id=f"CUST{id[-1]}",
            amount=150000.0 if id == "T125" else 8500.0,
            currency="USD" if id == "T125" else "SAR",
            timestamp=datetime.utcnow(),
            risk_score=0.85 if id == "T125" else 0.45,
            features={
                "country_risk": 0.8 if id == "T125" else 0.2,
                "pep_exposure": 1.0 if id == "T124" else 0.0,
                "velocity_score": 0.3
            },
            alerts=[]
        )
        
        logger.info(f"Retrieved transaction {id} for user {user['user_id']}")
        return transaction
        
    except Exception as e:
        logger.error(f"Error retrieving transaction {id}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Error retrieving transaction details"
        )

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow()
    )

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "service": "AML Gateway API",
        "version": "1.0.0",
        "description": "External-facing API gateway for AML system",
        "endpoints": {
            "batch_upload": "/v1/batch",
            "alerts": "/v1/alerts",
            "transactions": "/v1/transactions/{id}",
            "health": "/health"
        },
        "authentication": "Bearer token required for /v1/* endpoints"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 