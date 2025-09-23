"""Performance and load testing for WebSocket implementation."""

import asyncio
import time
import websockets
import json
from typing import List, Dict, Any
from dataclasses import dataclass


@dataclass
class LoadTestResults:
    """Results from load testing."""

    sessions: int
    messages_per_session: int
    total_messages: int
    duration: float
    messages_per_second: float
    avg_latency: float
    max_latency: float
    min_latency: float
    errors: int
    success_rate: float


async def client_session(
    session_id: str, messages: int = 10, track_metrics: bool = True
) -> Dict[str, Any]:
    """Simulate a client session with metric tracking."""

    uri = f"ws://localhost:8000/api/v1/ws/{session_id}"
    latencies = []
    errors = 0
    messages_sent = 0

    try:
        async with websockets.connect(uri) as websocket:
            # Receive welcome message
            await websocket.recv()

            # Send messages and track latency
            for i in range(messages):
                start_time = time.time()

                # Send user message
                await websocket.send(
                    json.dumps(
                        {
                            "type": "user_message",
                            "message": f"Test message {i} from {session_id}",
                        }
                    )
                )
                messages_sent += 1

                # Wait for typing indicator
                await websocket.recv()

                # Wait for AI response
                await websocket.recv()

                end_time = time.time()
                latency = (end_time - start_time) * 1000  # Convert to milliseconds

                if track_metrics:
                    latencies.append(latency)

                # Small delay between messages
                await asyncio.sleep(0.1)

    except Exception as e:
        print(f"Error in session {session_id}: {e}")
        errors += 1

    return {
        "session_id": session_id,
        "messages_sent": messages_sent,
        "latencies": latencies,
        "errors": errors,
        "avg_latency": sum(latencies) / len(latencies) if latencies else 0,
        "max_latency": max(latencies) if latencies else 0,
        "min_latency": min(latencies) if latencies else 0,
    }


async def load_test(
    concurrent_sessions: int = 10,
    messages_per_session: int = 10,
    track_metrics: bool = True,
) -> LoadTestResults:
    """Run load test with concurrent sessions."""

    print("\n🚀 Starting load test:")
    print(f"   - Sessions: {concurrent_sessions}")
    print(f"   - Messages per session: {messages_per_session}")
    print(f"   - Total messages: {concurrent_sessions * messages_per_session}")

    start_time = time.time()

    # Create and run concurrent sessions
    tasks = [
        asyncio.create_task(
            client_session(f"load-test-{i}", messages_per_session, track_metrics)
        )
        for i in range(concurrent_sessions)
    ]

    # Wait for all sessions to complete
    results = await asyncio.gather(*tasks)

    end_time = time.time()
    duration = end_time - start_time

    # Aggregate metrics
    all_latencies = []
    total_errors = 0
    total_messages_sent = 0

    for result in results:
        all_latencies.extend(result["latencies"])
        total_errors += result["errors"]
        total_messages_sent += result["messages_sent"]

    total_messages = concurrent_sessions * messages_per_session
    messages_per_second = total_messages_sent / duration if duration > 0 else 0
    success_rate = (
        (total_messages_sent / total_messages * 100) if total_messages > 0 else 0
    )

    return LoadTestResults(
        sessions=concurrent_sessions,
        messages_per_session=messages_per_session,
        total_messages=total_messages,
        duration=duration,
        messages_per_second=messages_per_second,
        avg_latency=sum(all_latencies) / len(all_latencies) if all_latencies else 0,
        max_latency=max(all_latencies) if all_latencies else 0,
        min_latency=min(all_latencies) if all_latencies else 0,
        errors=total_errors,
        success_rate=success_rate,
    )


async def stress_test(
    max_sessions: int = 50, step_size: int = 5, messages_per_session: int = 5
):
    """Progressive stress test to find breaking point."""

    print("\n📊 Running progressive stress test...")
    print("=" * 50)

    results = []

    for sessions in range(step_size, max_sessions + 1, step_size):
        print(f"\n🔄 Testing with {sessions} concurrent sessions...")

        try:
            result = await load_test(sessions, messages_per_session)
            results.append(result)

            print(f"✅ Success: {result.success_rate:.1f}% success rate")
            print(f"   Avg latency: {result.avg_latency:.0f}ms")
            print(f"   Messages/sec: {result.messages_per_second:.1f}")

            # Stop if success rate drops below 95%
            if result.success_rate < 95:
                print(f"\n⚠️ Performance degradation detected at {sessions} sessions")
                break

        except Exception as e:
            print(f"❌ Failed at {sessions} sessions: {e}")
            break

        # Brief pause between tests
        await asyncio.sleep(2)

    return results


async def sustained_load_test(
    sessions: int = 10, duration_minutes: int = 1, messages_per_minute: int = 10
):
    """Test sustained load over time."""

    print(f"\n⏱️ Running sustained load test for {duration_minutes} minute(s)...")
    print(f"   - Concurrent sessions: {sessions}")
    print(f"   - Messages per minute: {messages_per_minute}")

    start_time = time.time()
    end_time = start_time + (duration_minutes * 60)

    metrics = []
    message_interval = 60 / messages_per_minute  # Seconds between messages

    # Create persistent sessions
    websockets_list = []
    try:
        # Establish all connections
        for i in range(sessions):
            ws = await websockets.connect(
                f"ws://localhost:8000/api/v1/ws/sustained-{i}"
            )
            await ws.recv()  # Welcome message
            websockets_list.append(ws)

        print(f"✅ Established {len(websockets_list)} connections")

        message_count = 0
        while time.time() < end_time:
            round_start = time.time()

            # Send one message from each session
            for i, ws in enumerate(websockets_list):
                try:
                    # Send message
                    await ws.send(
                        json.dumps(
                            {
                                "type": "user_message",
                                "message": (
                                    f"Sustained test message {message_count} "
                                    f"from session {i}"
                                ),
                            }
                        )
                    )

                    # Receive responses
                    await ws.recv()  # typing
                    await ws.recv()  # response

                except Exception as e:
                    print(f"Error in session {i}: {e}")

            message_count += 1

            # Track metrics
            round_duration = time.time() - round_start
            metrics.append(
                {
                    "timestamp": time.time() - start_time,
                    "round_duration": round_duration * 1000,  # ms
                    "active_connections": len(websockets_list),
                }
            )

            # Wait for next interval
            elapsed = time.time() - round_start
            if elapsed < message_interval:
                await asyncio.sleep(message_interval - elapsed)

        # Calculate statistics
        total_duration = time.time() - start_time
        avg_round_time = sum(m["round_duration"] for m in metrics) / len(metrics)

        print("\n✅ Sustained test completed:")
        print(f"   Duration: {total_duration:.1f}s")
        print(f"   Messages sent: {message_count * sessions}")
        print(f"   Avg round time: {avg_round_time:.0f}ms")
        print(f"   Connections maintained: {len(websockets_list)}")

    finally:
        # Clean up connections
        for ws in websockets_list:
            await ws.close()


def print_results(results: LoadTestResults):
    """Print formatted test results."""

    print("\n" + "=" * 50)
    print("📊 Load Test Results")
    print("=" * 50)
    print(f"Sessions: {results.sessions}")
    print(f"Messages per session: {results.messages_per_session}")
    print(f"Total messages: {results.total_messages}")
    print(f"Duration: {results.duration:.2f}s")
    print(f"Messages/second: {results.messages_per_second:.2f}")
    print(f"Success rate: {results.success_rate:.1f}%")
    print("\n📈 Latency Statistics:")
    print(f"  Average: {results.avg_latency:.0f}ms")
    print(f"  Min: {results.min_latency:.0f}ms")
    print(f"  Max: {results.max_latency:.0f}ms")

    # Performance assessment
    print("\n🎯 Performance Assessment:")
    if results.avg_latency < 100:
        print("  ✅ Excellent: Average latency < 100ms")
    elif results.avg_latency < 200:
        print("  ✅ Good: Average latency < 200ms")
    elif results.avg_latency < 500:
        print("  ⚠️ Acceptable: Average latency < 500ms")
    else:
        print("  ❌ Poor: Average latency > 500ms")

    if results.success_rate >= 99:
        print("  ✅ Excellent reliability: >99% success rate")
    elif results.success_rate >= 95:
        print("  ✅ Good reliability: >95% success rate")
    else:
        print("  ❌ Poor reliability: <95% success rate")


async def main():
    """Main test runner."""

    print("\n🧪 WebSocket Performance Test Suite")
    print("=" * 50)

    # Test 1: Basic load test
    print("\n1️⃣ Basic Load Test (10 sessions, 10 messages each)")
    results1 = await load_test(10, 10)
    print_results(results1)

    await asyncio.sleep(2)

    # Test 2: Higher concurrency
    print("\n2️⃣ High Concurrency Test (20 sessions, 5 messages each)")
    results2 = await load_test(20, 5)
    print_results(results2)

    await asyncio.sleep(2)

    # Test 3: Burst load
    print("\n3️⃣ Burst Load Test (5 sessions, 50 messages each)")
    results3 = await load_test(5, 50)
    print_results(results3)

    # Test 4: Progressive stress test (optional - takes longer)
    # Uncomment to run stress test
    # await asyncio.sleep(2)
    # await stress_test(max_sessions=30, step_size=5)

    # Test 5: Sustained load (optional - takes 1 minute)
    # Uncomment to run sustained test
    # await asyncio.sleep(2)
    # await sustained_load_test(sessions=10, duration_minutes=1)

    print("\n✅ All performance tests completed!")


if __name__ == "__main__":
    # Make sure the server is running before executing tests
    print("⚠️ Make sure the WebSocket server is running on localhost:8000")
    print("Run: python -m uvicorn src.main:app --reload")
    input("Press Enter to start tests...")

    asyncio.run(main())
