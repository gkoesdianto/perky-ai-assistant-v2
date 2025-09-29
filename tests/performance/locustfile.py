"""Performance testing with Locust for Steel Chat WebSocket application.

This module provides load testing for WebSocket connections and message handling.
Run with: locust -f tests/performance/locustfile.py --host ws://localhost:8000
"""

import json
import random
import time
from typing import Any, Dict, List, Optional

try:
    import websocket
    from locust import User, between, events, task
    from locust.exception import LocustError
except ImportError:
    # Performance testing dependencies are optional
    # Install with: pip install -r requirements/dev.txt
    pass
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class WebSocketClient:
    """WebSocket client wrapper for Locust."""

    def __init__(self, host: str, user_id: str):
        """Initialize WebSocket client.

        Args:
            host: WebSocket host URL
            user_id: Unique user identifier
        """
        self.host = host
        self.user_id = user_id
        self.ws: Any = None  # websocket.WebSocket
        self.session_id: Optional[str] = None
        self.connected = False

    def connect(self):
        """Establish WebSocket connection."""
        try:
            ws_url = f"{self.host}/api/v1/ws/perf-user-{self.user_id}"
            self.ws = websocket.create_connection(ws_url)

            # Receive welcome message
            welcome = self.ws.recv()
            welcome_data = json.loads(welcome)

            if (
                welcome_data.get("type") == "system"
                and welcome_data.get("event") == "connected"
            ):
                self.session_id = welcome_data.get("session_id")
                self.connected = True
                return True

        except Exception as e:
            logger.error(f"Connection failed for user {self.user_id}: {e}")
            self.connected = False
            return False

    def send_message(self, message: str) -> Dict:
        """Send a user message and receive response.

        Args:
            message: Message content to send

        Returns:
            AI response data or error dict
        """
        if not self.connected:
            return {"error": "Not connected"}

        try:
            # Send message
            self.ws.send(json.dumps({"type": "user_message", "message": message}))

            # Receive typing indicator
            typing = self.ws.recv()
            typing_data = json.loads(typing)

            if typing_data.get("event") != "typing":
                logger.warning(f"Expected typing, got: {typing_data}")

            # Receive AI response
            response = self.ws.recv()
            response_data: Dict[Any, Any] = json.loads(response)

            return response_data

        except Exception as e:
            logger.error(f"Send message failed: {e}")
            return {"error": str(e)}

    def ping(self) -> bool:
        """Send ping and receive pong.

        Returns:
            True if pong received successfully
        """
        if not self.connected:
            return False

        try:
            self.ws.send(json.dumps({"type": "ping"}))
            pong = self.ws.recv()
            pong_data = json.loads(pong)
            return bool(pong_data.get("type") == "pong")

        except Exception as e:
            logger.error(f"Ping failed: {e}")
            return False

    def disconnect(self):
        """Close WebSocket connection."""
        if self.ws:
            try:
                self.ws.close()
            except Exception as e:
                logger.error(f"Disconnect error: {e}")
            finally:
                self.connected = False
                self.ws = None


class WebSocketUser(User):
    """Locust user class for WebSocket testing."""

    # Wait time between tasks (simulates user thinking time)
    wait_time = between(1, 3)

    # Product inquiry messages for realistic testing
    product_messages = [
        "Ada plat baja 5mm?",
        "Berapa harga besi beton D12?",
        "Show me steel plates",
        "I need construction materials",
        "Ada hollow 40x40?",
        "Stock besi siku berapa?",
        "Harga plat galvanis?",
        "Need pricing for steel beams",
        "What products are available?",
        "Ada promo untuk besi beton?",
    ]

    def on_start(self):
        """Called when user starts. Establish WebSocket connection."""
        self.client = WebSocketClient(
            self.host.replace("http://", "ws://").replace("https://", "wss://"),
            str(self.user_instance_id),
        )

        start_time = time.time()
        success = self.client.connect()
        response_time = int((time.time() - start_time) * 1000)

        if success:
            events.request.fire(
                request_type="WebSocket",
                name="Connect",
                response_time=response_time,
                response_length=0,
                exception=None,
                context={},
            )
            logger.info(f"User {self.user_instance_id} connected successfully")
        else:
            events.request.fire(
                request_type="WebSocket",
                name="Connect",
                response_time=response_time,
                response_length=0,
                exception=LocustError("Connection failed"),
                context={},
            )
            raise LocustError("Failed to connect WebSocket")

    def on_stop(self):
        """Called when user stops. Close WebSocket connection."""
        if hasattr(self, "client"):
            self.client.disconnect()
            logger.info(f"User {self.user_instance_id} disconnected")

    @task(10)
    def send_product_inquiry(self):
        """Send a product inquiry message (most common operation)."""
        if not self.client.connected:
            logger.warning(f"User {self.user_instance_id} not connected, skipping task")
            return

        message = random.choice(self.product_messages)
        start_time = time.time()
        response = self.client.send_message(message)
        response_time = int((time.time() - start_time) * 1000)

        if "error" not in response:
            events.request.fire(
                request_type="WebSocket",
                name="Product Inquiry",
                response_time=response_time,
                response_length=len(json.dumps(response)),
                exception=None,
                context={},
            )
        else:
            events.request.fire(
                request_type="WebSocket",
                name="Product Inquiry",
                response_time=response_time,
                response_length=0,
                exception=LocustError(response["error"]),
                context={},
            )

    @task(3)
    def send_price_check(self):
        """Send a price check message."""
        if not self.client.connected:
            return

        price_messages = [
            "Berapa harga per kg?",
            "What's the price?",
            "Ada diskon untuk quantity besar?",
            "Price list please",
        ]

        message = random.choice(price_messages)
        start_time = time.time()
        response = self.client.send_message(message)
        response_time = int((time.time() - start_time) * 1000)

        if "error" not in response:
            events.request.fire(
                request_type="WebSocket",
                name="Price Check",
                response_time=response_time,
                response_length=len(json.dumps(response)),
                exception=None,
                context={},
            )
        else:
            events.request.fire(
                request_type="WebSocket",
                name="Price Check",
                response_time=response_time,
                response_length=0,
                exception=LocustError(response["error"]),
                context={},
            )

    @task(2)
    def send_availability_check(self):
        """Send an availability check message."""
        if not self.client.connected:
            return

        availability_messages = [
            "Ready stock?",
            "Kapan bisa kirim?",
            "Is it available now?",
            "Stock tersedia berapa?",
        ]

        message = random.choice(availability_messages)
        start_time = time.time()
        response = self.client.send_message(message)
        response_time = int((time.time() - start_time) * 1000)

        if "error" not in response:
            events.request.fire(
                request_type="WebSocket",
                name="Availability Check",
                response_time=response_time,
                response_length=len(json.dumps(response)),
                exception=None,
                context={},
            )
        else:
            events.request.fire(
                request_type="WebSocket",
                name="Availability Check",
                response_time=response_time,
                response_length=0,
                exception=LocustError(response["error"]),
                context={},
            )

    @task(1)
    def send_ping(self):
        """Send a ping message (keepalive)."""
        if not self.client.connected:
            return

        start_time = time.time()
        success = self.client.ping()
        response_time = int((time.time() - start_time) * 1000)

        if success:
            events.request.fire(
                request_type="WebSocket",
                name="Ping",
                response_time=response_time,
                response_length=0,
                exception=None,
                context={},
            )
        else:
            events.request.fire(
                request_type="WebSocket",
                name="Ping",
                response_time=response_time,
                response_length=0,
                exception=LocustError("Ping failed"),
                context={},
            )


class ExtendedConversationUser(WebSocketUser):
    """User simulating extended conversations."""

    wait_time = between(2, 5)

    @task
    def extended_conversation(self):
        """Simulate a longer conversation with multiple exchanges."""
        if not self.client.connected:
            return

        conversation_flow = [
            "I need materials for a construction project",
            "What types of steel do you have?",
            "Tell me about the steel plates",
            "What thickness options are available?",
            "I need 10mm thickness",
            "How much for 100 pieces?",
            "Can you deliver to Jakarta?",
            "When can you deliver?",
            "I'll think about it, thank you",
        ]

        for i, message in enumerate(conversation_flow):
            start_time = time.time()
            response = self.client.send_message(message)
            response_time = int((time.time() - start_time) * 1000)

            if "error" not in response:
                events.request.fire(
                    request_type="WebSocket",
                    name=f"Extended Conv Step {i+1}",
                    response_time=response_time,
                    response_length=len(json.dumps(response)),
                    exception=None,
                    context={},
                )
                # Wait between messages in conversation
                time.sleep(random.uniform(1, 3))
            else:
                events.request.fire(
                    request_type="WebSocket",
                    name=f"Extended Conv Step {i+1}",
                    response_time=response_time,
                    response_length=0,
                    exception=LocustError(response["error"]),
                    context={},
                )
                break  # Stop conversation on error


# Custom event handlers for better reporting
@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Called when test starts."""
    logger.info("Performance test starting...")
    logger.info(f"Target host: {environment.host}")
    logger.info(
        f"Total users: {environment.parsed_options.num_users if environment.parsed_options else 'Not set'}"
    )


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Called when test stops."""
    logger.info("Performance test completed")
    logger.info(f"Total requests: {environment.stats.total.num_requests}")
    logger.info(f"Failure rate: {environment.stats.total.fail_ratio * 100:.2f}%")
    logger.info(
        f"Average response time: {environment.stats.total.avg_response_time:.2f}ms"
    )
    logger.info(
        f"Median response time: {environment.stats.total.median_response_time:.2f}ms"
    )
