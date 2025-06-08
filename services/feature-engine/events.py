import json
import uuid
from datetime import datetime, date
from typing import Dict, Any, Callable
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
        event_type: Type of event (e.g., "FeaturesReady")
        data: Event payload data
        batch_id: Optional batch identifier
    """
    
    event = {
        "specversion": "1.0",
        "type": event_type,
        "source": "aml.feature-engine",
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
                "source": "aml.feature-engine"
            }
        )
        
        await exchange.publish(message, routing_key="")
        logger.info(f"Published {event_type} event with ID {event['id']}")
        
    except Exception as e:
        logger.error(f"Failed to publish event {event_type}: {e}")
        raise

async def consume_events(
    channel: aio_pika.Channel,
    exchange: aio_pika.Exchange,
    event_handler: Callable[[Dict[str, Any]], None]
):
    """
    Consume events from RabbitMQ exchange
    
    Args:
        channel: RabbitMQ channel
        exchange: Exchange to consume from
        event_handler: Function to handle received events
    """
    
    # Declare a queue for this service
    queue = await channel.declare_queue(
        "feature-engine-queue",
        durable=True,
        auto_delete=False
    )
    
    # Bind queue to exchange
    await queue.bind(exchange)
    
    async def process_message(message: aio_pika.IncomingMessage):
        async with message.process():
            try:
                event_data = json.loads(message.body.decode())
                event_type = event_data.get("type")
                
                # Only process ingested events
                if event_type in ["IngestedTransaction", "IngestedCustomer", "IngestedAccount"]:
                    await event_handler(event_data)
                    logger.info(f"Processed {event_type} event")
                
            except Exception as e:
                logger.error(f"Error processing message: {e}")
                raise
    
    # Start consuming
    await queue.consume(process_message)
    logger.info("Started consuming events from aml.events exchange") 