import json
from datetime import datetime
from typing import Dict, Any, Callable
import aio_pika
import logging

logger = logging.getLogger(__name__)

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
        "alert-manager-queue",
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
                
                # Only process Scored events
                if event_type == "Scored":
                    await event_handler(event_data)
                    logger.info(f"Processed {event_type} event")
                
            except Exception as e:
                logger.error(f"Error processing message: {e}")
                raise
    
    # Start consuming
    await queue.consume(process_message)
    logger.info("Started consuming events from aml.events exchange") 