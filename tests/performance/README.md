# Performance Testing

This directory contains performance tests for the Steel Chat WebSocket application.

## Setup

The performance testing dependencies (locust and websocket-client) are included in the development requirements:

```bash
pip install -r requirements/dev.txt
```

## Running Tests

### Using Locust Web UI

Start the Locust web interface:

```bash
locust -f tests/performance/locustfile.py --host ws://localhost:8000
```

Then navigate to http://localhost:8089 to configure and start the load test.

### Headless Mode

Run without the web UI:

```bash
locust -f tests/performance/locustfile.py \
    --host ws://localhost:8000 \
    --headless \
    --users 10 \
    --spawn-rate 1 \
    --run-time 60s
```

Parameters:
- `--users`: Number of concurrent users
- `--spawn-rate`: Users spawned per second
- `--run-time`: Test duration

## Test Scenarios

The performance tests simulate:
1. WebSocket connections and disconnections
2. Message sending and receiving
3. Session persistence and recovery
4. Concurrent user interactions
5. Rate limiting behavior

## Metrics

Key metrics monitored:
- Connection establishment time
- Message round-trip time
- Message throughput
- Error rates
- Session stability

## Notes

- The performance tests are optional and not included in the main development dependencies
- These tests require the main application to be running (`python -m uvicorn src.main:app`)
- Results are best interpreted in conjunction with application logs and monitoring
