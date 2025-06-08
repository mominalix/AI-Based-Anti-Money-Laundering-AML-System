import json
import uuid
from datetime import datetime, date
from typing import List, Dict, Any
import asyncio
import logging

from fastapi import FastAPI, UploadFile, File, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ValidationError
import aio_pika
from aio_pika import ExchangeType

from models import Account, Customer, Transaction
from events import publish_event
from data_processor import DataProcessor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="AML Ingestion API",
    version="1.0.0",
    description="Accepts batch uploads of accounts, customers, and transactions data"
)

# Global variables for RabbitMQ connection
connection = None
channel = None
exchange = None

# Initialize data processor
data_processor = DataProcessor()

def serialize_datetime(obj):
    """Convert datetime objects to JSON serializable format"""
    if isinstance(obj, datetime):
        return obj.isoformat() + "Z"
    elif isinstance(obj, date):
        return obj.isoformat()
    elif isinstance(obj, dict):
        return {k: serialize_datetime(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [serialize_datetime(item) for item in obj]
    return obj

class BatchResponse(BaseModel):
    message: str
    batch_id: str
    records_processed: int

class HealthResponse(BaseModel):
    status: str
    timestamp: datetime

@app.on_event("startup")
async def startup_event():
    """Initialize RabbitMQ connection on startup"""
    global connection, channel, exchange
    try:
        connection = await aio_pika.connect_robust("amqp://guest:guest@rabbitmq:5672/")
        channel = await connection.channel()
        exchange = await channel.declare_exchange(
            "aml.events", 
            ExchangeType.FANOUT,
            durable=True
        )
        logger.info("Connected to RabbitMQ successfully")
    except Exception as e:
        logger.error(f"Failed to connect to RabbitMQ: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Close RabbitMQ connection on shutdown"""
    global connection
    if connection:
        await connection.close()

@app.post("/batch", response_model=BatchResponse, status_code=status.HTTP_201_CREATED)
async def upload_batch(
    accounts: UploadFile = File(...),
    customers: UploadFile = File(...),
    transactions: UploadFile = File(...)
):
    """Upload batch data files and publish events"""
    batch_id = str(uuid.uuid4())
    total_records = 0
    
    try:
        # Read file contents
        accounts_content = await accounts.read()
        customers_content = await customers.read()
        transactions_content = await transactions.read()
        
        # Process and enrich data using data processor
        enriched_accounts, enriched_customers, enriched_transactions = await data_processor.process_batch_files(
            accounts_content, customers_content, transactions_content
        )
        
        # Validate enriched data with Pydantic models
        validated_accounts = []
        for account_data in enriched_accounts:
            try:
                account = Account(**account_data)
                validated_accounts.append(account)
            except ValidationError as e:
                logger.warning(f"Account validation warning: {e}")
                # Use enriched data directly if Pydantic validation fails
                validated_accounts.append(account_data)
        
        validated_customers = []
        for customer_data in enriched_customers:
            try:
                customer = Customer(**customer_data)
                validated_customers.append(customer)
            except ValidationError as e:
                logger.warning(f"Customer validation warning: {e}")
                # Use enriched data directly if Pydantic validation fails
                validated_customers.append(customer_data)
        
        validated_transactions = []
        for transaction_data in enriched_transactions:
            try:
                transaction = Transaction(**transaction_data)
                validated_transactions.append(transaction)
            except ValidationError as e:
                logger.warning(f"Transaction validation warning: {e}")
                # Use enriched data directly if Pydantic validation fails
                validated_transactions.append(transaction_data)
        
        # Publish events for each record with enriched data
        for account in validated_accounts:
            account_dict = account.dict() if hasattr(account, 'dict') else account
            account_dict = serialize_datetime(account_dict)
            await publish_event(
                exchange,
                "IngestedAccount",
                account_dict,
                batch_id
            )
            total_records += 1
        
        for customer in validated_customers:
            customer_dict = customer.dict() if hasattr(customer, 'dict') else customer
            customer_dict = serialize_datetime(customer_dict)
            await publish_event(
                exchange,
                "IngestedCustomer", 
                customer_dict,
                batch_id
            )
            total_records += 1
        
        for transaction in validated_transactions:
            transaction_dict = transaction.dict() if hasattr(transaction, 'dict') else transaction
            transaction_dict = serialize_datetime(transaction_dict)
            await publish_event(
                exchange,
                "IngestedTransaction",
                transaction_dict,
                batch_id
            )
            total_records += 1
        
        logger.info(f"Processed batch {batch_id} with {total_records} records")
        
        return BatchResponse(
            message="Batch uploaded successfully",
            batch_id=batch_id,
            records_processed=total_records
        )
        
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=400,
            detail="Invalid JSON format in uploaded files"
        )
    except Exception as e:
        logger.error(f"Error processing batch: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error processing batch"
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
    uvicorn.run(app, host="0.0.0.0", port=8001) 