# Testing Guide - MVP Optimized

This guide covers the testing strategy for the Steel Chat AI Assistant, optimized for
MVP development velocity while maintaining quality standards.

## Quick Start

```bash
# Essential MVP testing workflow
make test-smoke      # Quick validation (30s)
make test-mvp        # MVP essential tests
make dev-workflow    # Format + lint + quick tests
make mvp-validate    # Complete MVP validation
```

## Testing Philosophy

### MVP Focus

- **Critical flows first**: Product inquiry, Indonesian language support
- **Pragmatic coverage**: 70% minimum (relaxed from 80% for velocity)
- **Fast feedback**: Most tests under 30s timeout
- **Essential only**: Post-MVP features marked and skipped

### Test Categories

#### 🚀 MVP Essential Tests

- **Smoke tests**: Basic functionality validation
- **Critical priority**: Core business flows
- **Quick tests**: <1s execution for rapid feedback

#### 🔬 Development Tests

- **Unit tests**: Fast, isolated component testing
- **Integration tests**: Cross-component validation
- **E2E essential**: Critical user journey testing

#### 📈 Post-MVP Tests (Marked for Later)

- **Performance tests**: Load and stress testing
- **Edge cases**: Complex scenarios and boundary conditions
- **Advanced concurrency**: Heavy load testing

## Test Structure

```text
tests/
├── unit/           # Fast, isolated tests
├── integration/    # Cross-component tests
├── e2e/           # End-to-end user flows (MVP optimized)
├── fixtures/      # Shared test data and utilities
├── performance/   # Performance tests (post-MVP)
└── pytest_plugins.py  # Custom pytest extensions
```

## Running Tests

### Quick Validation Commands

```bash
# Immediate feedback (use during development)
make test-smoke         # 30s smoke tests
make test-quick         # <1s per test
make test-critical      # Critical priority only

# MVP validation
make test-mvp          # All MVP essential tests
make test-e2e          # Essential E2E flows
make mvp-validate      # Complete MVP validation
```

### Development Workflow Commands

```bash
# Code quality + quick tests
make dev-workflow      # Format, lint, quick tests

# Full quality checks
make quality           # Format, lint, type-check
make coverage-mvp      # Coverage for MVP tests only

# CI/CD preparation
make test-ci           # CI test suite (no flaky tests)
make test-pre-commit   # Pre-commit validation
```

### Comprehensive Testing

```bash
# All stable tests
make test-unit         # Unit tests only
make test-integration  # Integration tests only
make test-all          # All tests (including slow)

# Coverage reporting
make coverage          # Full coverage report
make coverage-mvp      # MVP coverage only
```

## Test Markers

### Priority Markers

```python
@pytest.mark.priority("critical")  # Must pass for MVP
@pytest.mark.priority("high")      # Important for MVP
@pytest.mark.priority("medium")    # Nice to have
@pytest.mark.priority("low")       # Post-MVP
```

### MVP Markers

```python
@pytest.mark.smoke                 # Quick validation
@pytest.mark.mvp                   # MVP essential
@pytest.mark.post_mvp              # Post-MVP feature
@pytest.mark.mvp_critical          # Critical for MVP
@pytest.mark.quick                 # <1s execution
```

### Test Type Markers

```python
@pytest.mark.unit                  # Unit test
@pytest.mark.integration           # Integration test
@pytest.mark.e2e                   # End-to-end test
@pytest.mark.slow                  # >2s execution
@pytest.mark.flaky                 # Skip in MVP
```

## E2E Testing Strategy

### MVP E2E Tests (Optimized)

**Critical User Flows**:
- ✅ Product inquiry flow (Indonesian)
- ✅ Multi-product comparison
- ✅ Basic error recovery
- ✅ Connection lifecycle

**WebSocket Protocol Essentials**:
- ✅ Connection establishment
- ✅ Ping-pong heartbeat
- ✅ Message ordering
- ✅ Error handling

**Post-MVP E2E Tests** (Marked as `@pytest.mark.skip`):
- Heavy concurrent load testing
- Complex timeout scenarios
- Large message handling
- Advanced reconnection patterns

### Dependencies Simplified

**Before**: External websockets library + asyncio complexity

```python
# Complex async setup with external dependencies
async with websockets.connect(url) as websocket:
    await websocket.send(message)
    response = await websocket.recv()
```

**After**: TestClient only

```python
# Simple TestClient usage
with test_client.websocket_connect("/api/v1/ws/test") as websocket:
    websocket.send_text(message)
    response = websocket.receive_text()
```

## Configuration

### pytest.ini Optimizations

```text
# MVP optimized settings
timeout = 30                    # Quick timeout
maxfail = 3                     # Fail fast
min_coverage = 70               # Relaxed for velocity
-x                             # Stop on first failure
```

### Test Groups

```bash
# Quick development groups
pytest -m "smoke"                           # Smoke tests
pytest -m "quick or (smoke and not slow)"   # Quick tests
pytest -m "mvp or smoke or priority('critical')"  # MVP essential

# Quality gates
pytest -m "not flaky and not post_mvp"     # Stable tests only
pytest -m "priority('critical') and not slow"  # Critical tests
```

## Development Workflow

### 1. Development Loop

```bash
# While coding
make test-quick     # Immediate feedback
make dev-workflow   # Quality + quick tests
```

### 2. Feature Completion

```bash
# Before committing
make test-mvp       # All MVP tests
make mvp-validate   # Complete validation
```

### 3. Pre-deployment

```bash
# Before deployment
make test-ci        # CI test suite
make coverage-mvp   # Coverage check
```

## Performance Targets (MVP)

### Test Execution Times

- **Smoke tests**: <30s total
- **Quick tests**: <1s per test
- **MVP suite**: <5 minutes total
- **CI suite**: <10 minutes total

### Coverage Targets

- **Minimum**: 70% (relaxed for MVP velocity)
- **Target**: 80% for critical components
- **Unit tests**: 90% for domain layer
- **E2E tests**: Cover critical user flows

## Troubleshooting

### Common Issues

**Tests taking too long**:

```bash
# Use quick test groups
make test-quick
make test-smoke

# Skip slow tests
pytest -m "not slow"
```

**Flaky test failures**:

```bash
# Skip flaky tests in MVP
pytest -m "not flaky"

# Run stable tests only
make test-ci
```

**Coverage too low**:

```bash
# Focus on critical components
make coverage-mvp

# Identify gaps
pytest --cov=src --cov-report=html
```

### Environment Issues

**Missing dependencies**:

```bash
make dev-install    # Install dev dependencies
make check-env      # Validate environment
```

**Configuration problems**:

```bash
# Check pytest configuration
pytest --markers    # List available markers
pytest --collect-only  # Dry run test collection
```

## Future Enhancements (Post-MVP)

### Performance Testing

- Load testing with multiple concurrent users
- Response time performance benchmarks
- Memory usage monitoring
- Stress testing under heavy load

### Advanced E2E Testing

- Cross-browser WebSocket testing
- Network failure simulation
- Long-running conversation testing
- Complex user interaction patterns

### Quality Improvements

- Mutation testing for test quality
- Property-based testing for edge cases
- Visual regression testing for UI
- Accessibility testing automation

## Best Practices

### Test Writing

1. **Start with smoke tests** for new features
2. **Mark appropriately** with priority and type markers
3. **Keep tests simple** and focused
4. **Use TestClient** exclusively for WebSocket testing
5. **Skip post-MVP** features until later

### MVP Development

1. **Run smoke tests** frequently during development
2. **Use quick tests** for immediate feedback
3. **Focus on critical flows** first
4. **Mark complex tests** as post-MVP
5. **Prioritize stability** over comprehensive coverage

### Code Quality

1. **Format before testing**: `make format`
2. **Fix linting issues**: `make lint`
3. **Check types**: `make type-check`
4. **Run complete workflow**: `make dev-workflow`
