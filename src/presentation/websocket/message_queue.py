"""Async message queue for WebSocket processing."""

import asyncio
import logging
from typing import Any, Callable, Dict, Optional

logger = logging.getLogger(__name__)


class MessageQueue:
    """
    Async message queue to prevent blocking.
    Processes messages asynchronously to maintain responsive WebSocket connections.
    """

    def __init__(self, max_size: int = 100):
        """
        Initialize message queue.

        Args:
            max_size: Maximum queue size (default 100)
        """
        self.queue: asyncio.Queue = asyncio.Queue(maxsize=max_size)
        self.worker_task: Optional[asyncio.Task] = None
        self.is_running = False

    async def start_worker(self, process_func: Callable[[Dict[str, Any]], Any]):
        """
        Start the queue worker.

        Args:
            process_func: Async function to process each message
        """
        if self.is_running:
            logger.warning("Worker is already running")
            return

        self.is_running = True
        self.worker_task = asyncio.create_task(self._process_queue(process_func))
        logger.info("Message queue worker started")

    async def _process_queue(self, process_func: Callable[[Dict[str, Any]], Any]):
        """
        Process messages from queue.

        Args:
            process_func: Async function to process each message
        """
        while self.is_running:
            try:
                # Wait for message with timeout to allow checking is_running
                message_data = await asyncio.wait_for(self.queue.get(), timeout=1.0)

                try:
                    await process_func(message_data)
                except Exception as e:
                    logger.error(f"Error processing message: {e}", exc_info=True)
                finally:
                    # Mark task as done
                    self.queue.task_done()

            except asyncio.TimeoutError:
                # Timeout is normal, just check if we should continue
                continue
            except asyncio.CancelledError:
                logger.info("Queue worker cancelled")
                break
            except Exception as e:
                logger.error(f"Queue processing error: {e}", exc_info=True)

    async def add_message(self, message_data: Dict[str, Any]) -> bool:
        """
        Add message to queue.

        Args:
            message_data: Message data to queue

        Returns:
            True if message was queued, False if queue is full
        """
        try:
            # Try to add without blocking
            self.queue.put_nowait(message_data)
            return True
        except asyncio.QueueFull:
            logger.warning("Message queue is full, dropping message")
            return False
        except Exception as e:
            logger.error(f"Failed to queue message: {e}")
            return False

    async def stop_worker(self):
        """Stop the queue worker gracefully."""
        if not self.is_running:
            return

        self.is_running = False

        if self.worker_task:
            # Wait for current message to finish processing
            try:
                await asyncio.wait_for(self.worker_task, timeout=5.0)
            except asyncio.TimeoutError:
                logger.warning("Worker task didn't finish in time, cancelling")
                self.worker_task.cancel()
                try:
                    await self.worker_task
                except asyncio.CancelledError:
                    pass

        logger.info("Message queue worker stopped")

    def get_queue_size(self) -> int:
        """
        Get current queue size.

        Returns:
            Number of messages in queue
        """
        return self.queue.qsize()

    def is_full(self) -> bool:
        """
        Check if queue is full.

        Returns:
            True if queue is at maximum capacity
        """
        return self.queue.full()

    def is_empty(self) -> bool:
        """
        Check if queue is empty.

        Returns:
            True if queue has no messages
        """
        return self.queue.empty()

    async def wait_until_empty(self):
        """Wait until all messages in queue are processed."""
        await self.queue.join()
