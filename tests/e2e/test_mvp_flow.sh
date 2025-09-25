#!/bin/bash

echo "==================================="
echo "Steel Chat MVP E2E Test Suite"
echo "==================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counter
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# Function to run a test
run_test() {
    local test_name=$1
    local command=$2
    local expected=$3

    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    echo -e "${YELLOW}Running: $test_name${NC}"

    result=$(eval $command 2>&1)

    if echo "$result" | grep -q "$expected"; then
        echo -e "${GREEN}✓ PASSED${NC}"
        PASSED_TESTS=$((PASSED_TESTS + 1))
    else
        echo -e "${RED}✗ FAILED${NC}"
        echo "Expected: $expected"
        echo "Got: $result"
        FAILED_TESTS=$((FAILED_TESTS + 1))
    fi
    echo ""
}

# Check dependencies
echo "Checking dependencies..."

# Check if Python is available
if ! command -v python &> /dev/null; then
    echo -e "${RED}Python is not installed${NC}"
    exit 1
fi

# Check if websocat is available (optional)
if ! command -v websocat &> /dev/null; then
    echo -e "${YELLOW}Warning: websocat not found. Installing alternative...${NC}"
fi

# Start application in background
echo "Starting application..."
python -m uvicorn src.main:app --port 8000 > /tmp/app.log 2>&1 &
APP_PID=$!
sleep 5

# Check if app started successfully
if ! ps -p $APP_PID > /dev/null; then
    echo -e "${RED}Failed to start application${NC}"
    cat /tmp/app.log
    exit 1
fi

echo "Application started with PID: $APP_PID"
echo ""

# Test 1: Health check
run_test "Health Check" \
    "curl -s http://localhost:8000/health" \
    "healthy"

# Test 2: API Documentation
run_test "API Documentation Available" \
    "curl -s -o /dev/null -w '%{http_code}' http://localhost:8000/docs" \
    "200"

# Test 3: Root endpoint
run_test "Root endpoint serves HTML" \
    "curl -s http://localhost:8000/ | head -1" \
    "html"

# Python test script for WebSocket
cat > /tmp/test_ws.py << 'EOF'
import asyncio
import websockets
import json
import sys

async def test_chat():
    uri = "ws://localhost:8000/api/v1/ws/test-e2e-session"
    try:
        async with websockets.connect(uri) as websocket:
            # Receive welcome
            welcome = await websocket.recv()
            welcome_data = json.loads(welcome)
            assert welcome_data["type"] == "system"
            assert welcome_data["event"] == "connected"
            print("✓ Connection established")

            # Test ping-pong
            await websocket.send(json.dumps({"type": "ping"}))
            pong = await websocket.recv()
            pong_data = json.loads(pong)
            assert pong_data["type"] == "pong"
            print("✓ Ping-pong successful")

            # Send product inquiry
            await websocket.send(json.dumps({
                "type": "user_message",
                "message": "Ada plat baja 5mm?"
            }))

            # Receive typing indicator
            typing = await websocket.recv()
            typing_data = json.loads(typing)
            assert typing_data["type"] == "system"
            assert typing_data["event"] == "typing"
            print("✓ Typing indicator received")

            # Receive response
            response = await websocket.recv()
            response_data = json.loads(response)
            assert response_data["type"] == "ai_response"
            assert response_data["message"] is not None
            print("✓ AI response received")

            # Test price inquiry
            await websocket.send(json.dumps({
                "type": "user_message",
                "message": "Berapa harga besi beton D12?"
            }))

            # Skip typing
            await websocket.recv()

            # Get price response
            price_response = await websocket.recv()
            price_data = json.loads(price_response)
            assert price_data["type"] == "ai_response"
            print("✓ Price inquiry handled")

            print("SUCCESS")
            return True
    except Exception as e:
        print(f"FAILED: {e}")
        return False

try:
    result = asyncio.run(test_chat())
    sys.exit(0 if result else 1)
except Exception as e:
    print(f"FAILED: {e}")
    sys.exit(1)
EOF

# Test 4: WebSocket Chat Flow
run_test "WebSocket Chat Flow" \
    "python /tmp/test_ws.py 2>&1" \
    "SUCCESS"

# Test 5: Multiple concurrent connections
echo "Testing concurrent connections..."
cat > /tmp/test_concurrent.py << 'EOF'
import asyncio
import websockets
import json

async def test_client(session_id):
    uri = f"ws://localhost:8000/api/v1/ws/concurrent-{session_id}"
    try:
        async with websockets.connect(uri) as websocket:
            # Receive welcome
            welcome = await websocket.recv()
            welcome_data = json.loads(welcome)

            # Send ping
            await websocket.send(json.dumps({"type": "ping"}))

            # Receive pong
            pong = await websocket.recv()
            pong_data = json.loads(pong)

            if pong_data["type"] == "pong":
                return True
            return False
    except Exception:
        return False

async def test_concurrent():
    tasks = [test_client(i) for i in range(5)]
    results = await asyncio.gather(*tasks)
    successful = sum(results)
    print(f"Successful connections: {successful}/5")
    return successful == 5

try:
    result = asyncio.run(test_concurrent())
    print("SUCCESS" if result else f"PARTIAL: {result}")
except Exception as e:
    print(f"FAILED: {e}")
EOF

run_test "Concurrent Connections" \
    "python /tmp/test_concurrent.py 2>&1" \
    "SUCCESS"

# Test 6: Performance Test - Response Time
echo "Testing response times..."
cat > /tmp/test_performance.py << 'EOF'
import asyncio
import websockets
import json
import time

async def test_response_time():
    uri = "ws://localhost:8000/api/v1/ws/perf-test"
    response_times = []

    async with websockets.connect(uri) as websocket:
        # Skip welcome
        await websocket.recv()

        # Test 10 requests
        for i in range(10):
            start = time.time()

            # Send message
            await websocket.send(json.dumps({
                "type": "user_message",
                "message": f"Test message {i}"
            }))

            # Skip typing
            await websocket.recv()

            # Get response
            await websocket.recv()

            elapsed = time.time() - start
            response_times.append(elapsed)

        avg_time = sum(response_times) / len(response_times)
        p90_time = sorted(response_times)[int(len(response_times) * 0.9)]

        print(f"Average: {avg_time:.2f}s, P90: {p90_time:.2f}s")

        # Check if 90% of responses are under 2 seconds
        if p90_time < 2.0:
            print("PERFORMANCE_OK")
            return True
        else:
            print("PERFORMANCE_SLOW")
            return False

try:
    asyncio.run(test_response_time())
except Exception as e:
    print(f"FAILED: {e}")
EOF

run_test "Response Time Performance" \
    "python /tmp/test_performance.py 2>&1" \
    "PERFORMANCE_OK"

# Test 7: Indonesian Language Test
echo "Testing Indonesian language responses..."
cat > /tmp/test_indonesian.py << 'EOF'
import asyncio
import websockets
import json

async def test_indonesian():
    uri = "ws://localhost:8000/api/v1/ws/indo-test"

    async with websockets.connect(uri) as websocket:
        # Get welcome message
        welcome = await websocket.recv()
        welcome_data = json.loads(welcome)

        # Check welcome is in Indonesian
        if "Selamat datang" not in welcome_data.get("message", ""):
            print("Welcome message not in Indonesian")
            return False

        # Send greeting
        await websocket.send(json.dumps({
            "type": "user_message",
            "message": "Halo"
        }))

        # Skip typing
        await websocket.recv()

        # Get greeting response
        response = await websocket.recv()
        response_data = json.loads(response)
        message = response_data.get("message", "")

        # Check for Indonesian greeting elements
        if any(word in message for word in ["Selamat", "PERKY", "SMS Perkasa"]):
            print("INDONESIAN_OK")
            return True
        else:
            print("INDONESIAN_FAIL")
            return False

try:
    asyncio.run(test_indonesian())
except Exception as e:
    print(f"FAILED: {e}")
EOF

run_test "Indonesian Language Support" \
    "python /tmp/test_indonesian.py 2>&1" \
    "INDONESIAN_OK"

# Test 8: Error Handling
echo "Testing error handling..."
cat > /tmp/test_errors.py << 'EOF'
import asyncio
import websockets
import json

async def test_errors():
    uri = "ws://localhost:8000/api/v1/ws/error-test"

    async with websockets.connect(uri) as websocket:
        # Skip welcome
        await websocket.recv()

        # Test 1: Invalid message type
        await websocket.send(json.dumps({
            "type": "invalid_type",
            "data": "test"
        }))

        # Should get error response
        error1 = await websocket.recv()
        error1_data = json.loads(error1)
        if error1_data["type"] != "error":
            print("No error for invalid type")
            return False

        # Test 2: Empty message
        await websocket.send(json.dumps({
            "type": "user_message",
            "message": ""
        }))

        error2 = await websocket.recv()
        error2_data = json.loads(error2)
        if error2_data["type"] != "error":
            print("No error for empty message")
            return False

        # Test 3: Connection should still work after errors
        await websocket.send(json.dumps({"type": "ping"}))
        pong = await websocket.recv()
        pong_data = json.loads(pong)

        if pong_data["type"] == "pong":
            print("ERROR_HANDLING_OK")
            return True
        else:
            print("Connection broken after errors")
            return False

try:
    asyncio.run(test_errors())
except Exception as e:
    print(f"FAILED: {e}")
EOF

run_test "Error Handling" \
    "python /tmp/test_errors.py 2>&1" \
    "ERROR_HANDLING_OK"

# Cleanup
echo ""
echo "Cleaning up..."
kill $APP_PID 2>/dev/null
rm /tmp/test_ws.py 2>/dev/null
rm /tmp/test_concurrent.py 2>/dev/null
rm /tmp/test_performance.py 2>/dev/null
rm /tmp/test_indonesian.py 2>/dev/null
rm /tmp/test_errors.py 2>/dev/null
rm /tmp/app.log 2>/dev/null

# Summary
echo ""
echo "==================================="
echo "Test Summary"
echo "==================================="
echo -e "Total Tests: $TOTAL_TESTS"
echo -e "${GREEN}Passed: $PASSED_TESTS${NC}"
echo -e "${RED}Failed: $FAILED_TESTS${NC}"

if [ $FAILED_TESTS -eq 0 ]; then
    echo -e "${GREEN}All tests passed! MVP is ready.${NC}"
    exit 0
else
    echo -e "${RED}Some tests failed. Please review.${NC}"
    exit 1
fi
