import json
import uuid
from datetime import datetime, date
from typing import Dict, Any
import aio_pika
import logging

logger = logging.getLogger(__name__)

class DateTimeEncoder(json.JSONEncoder):
    """Custom JSON encoder for datetime objects"""
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat() + "Z"
        elif isinstance(obj, date):
            return obj.isoformat()
        return super().default(obj)

async def publish_event(
    exchange: aio_pika.Exchange,
    event_type: str,
    data: Dict[str, Any],
    batch_id: str = None
):
    """
    Publish a CloudEvent-style message to RabbitMQ
    
    Args:
        exchange: RabbitMQ exchange to publish to
        event_type: Type of event (e.g., "IngestedTransaction")
        data: Event payload data
        batch_id: Optional batch identifier
    """
    
    event = {
        "specversion": "1.0",
        "type": event_type,
        "source": "aml.ingestion",
        "id": str(uuid.uuid4()),
        "time": datetime.utcnow().isoformat() + "Z",
        "datacontenttype": "application/json",
        "data": data
    }
    
    if batch_id:
        event["batchid"] = batch_id
    
    try:
        message = aio_pika.Message(
            json.dumps(event, cls=DateTimeEncoder).encode(),
            content_type="application/json",
            headers={
                "event_type": event_type,
                "source": "aml.ingestion"
            }
        )
        
        await exchange.publish(message, routing_key="")
        logger.info(f"Published {event_type} event with ID {event['id']}")
        
    except Exception as e:
        logger.error(f"Failed to publish event {event_type}: {e}")
        raise 