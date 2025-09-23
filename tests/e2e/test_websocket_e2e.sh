#!/bin/bash

# WebSocket E2E Testing Script
# ============================
# Comprehensive end-to-end testing for WebSocket implementation

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SERVER_HOST="localhost"
SERVER_PORT="8000"
SERVER_URL="http://${SERVER_HOST}:${SERVER_PORT}"
WS_URL="ws://${SERVER_HOST}:${SERVER_PORT}/api/v1/ws"
STARTUP_WAIT=5
TEST_TIMEOUT=300  # 5 minutes timeout for tests

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

# Function to check if server is running
check_server() {
    print_status "Checking if server is running..."

    if curl -s -f "${SERVER_URL}/health" > /dev/null 2>&1; then
        print_success "Server is already running on ${SERVER_URL}"
        return 0
    else
        return 1
    fi
}

# Function to start the server
start_server() {
    print_status "Starting WebSocket server..."

    # Start server in background
    python -m uvicorn src.main:app --reload --port ${SERVER_PORT} > server.log 2>&1 &
    SERVER_PID=$!

    print_status "Server starting with PID ${SERVER_PID}..."
    sleep ${STARTUP_WAIT}

    # Verify server started
    if check_server; then
        print_success "Server started successfully"
        return 0
    else
        print_error "Failed to start server"
        cat server.log
        return 1
    fi
}

# Function to stop the server
stop_server() {
    if [ ! -z "${SERVER_PID}" ]; then
        print_status "Stopping server (PID: ${SERVER_PID})..."
        kill ${SERVER_PID} 2>/dev/null || true
        wait ${SERVER_PID} 2>/dev/null || true
        print_success "Server stopped"
    fi
}

# Function to run integration tests
run_integration_tests() {
    print_status "Running integration tests..."

    if pytest tests/integration/test_websocket_flow.py -v --tb=short; then
        print_success "Integration tests passed"
        return 0
    else
        print_error "Integration tests failed"
        return 1
    fi
}

# Function to run performance tests
run_performance_tests() {
    print_status "Running performance tests..."

    # Run the performance test script
    if python tests/performance/test_websocket_load.py; then
        print_success "Performance tests completed"
        return 0
    else
        print_error "Performance tests failed"
        return 1
    fi
}

# Function to test WebSocket with wscat (if available)
test_with_wscat() {
    print_status "Testing WebSocket connection with wscat..."

    # Check if wscat is installed
    if ! command -v wscat &> /dev/null; then
        print_warning "wscat not installed. Skipping wscat tests."
        print_warning "Install with: npm install -g wscat"
        return 0
    fi

    # Test basic connection
    echo '{"type":"ping"}' | wscat -c "${WS_URL}/e2e-test" -w 1 > wscat_test.log 2>&1

    if grep -q "pong" wscat_test.log; then
        print_success "WebSocket connection test passed"
        return 0
    else
        print_error "WebSocket connection test failed"
        cat wscat_test.log
        return 1
    fi
}

# Function to test HTML client
test_html_client() {
    print_status "Testing HTML client..."

    # Check if test_client.html exists
    if [ ! -f "test_client.html" ]; then
        print_error "test_client.html not found"
        return 1
    fi

    # Start simple HTTP server for HTML client
    print_status "Starting HTTP server for HTML client on port 8080..."
    python -m http.server 8080 > http_server.log 2>&1 &
    HTTP_PID=$!
    sleep 2

    print_success "HTML client available at http://localhost:8080/test_client.html"
    print_status "Open the URL in a browser to test manually"
    print_status "Press Enter when manual testing is complete..."
    read -r

    # Stop HTTP server
    kill ${HTTP_PID} 2>/dev/null || true
    print_success "HTTP server stopped"

    return 0
}

# Function to check code quality
run_quality_checks() {
    print_status "Running code quality checks..."

    # Format check
    print_status "Checking code formatting with Black..."
    if black --check src/presentation/websocket/ tests/; then
        print_success "Code formatting check passed"
    else
        print_warning "Code needs formatting. Run: black src/presentation/websocket/ tests/"
    fi

    # Import sorting check
    print_status "Checking import sorting with isort..."
    if isort --check-only src/presentation/websocket/ tests/; then
        print_success "Import sorting check passed"
    else
        print_warning "Imports need sorting. Run: isort src/presentation/websocket/ tests/"
    fi

    # Linting
    print_status "Running flake8 linter..."
    if flake8 src/presentation/websocket/ --max-line-length=88 --extend-ignore=E203,W503; then
        print_success "Linting check passed"
    else
        print_warning "Linting issues found"
    fi

    # Type checking
    print_status "Running mypy type checker..."
    if mypy src/presentation/websocket/; then
        print_success "Type checking passed"
    else
        print_warning "Type checking issues found"
    fi
}

# Function to generate test report
generate_report() {
    print_status "Generating test report..."

    REPORT_FILE="websocket_test_report_$(date +%Y%m%d_%H%M%S).md"

    cat > ${REPORT_FILE} << EOF
# WebSocket E2E Test Report

**Date**: $(date)
**Server**: ${SERVER_URL}
**WebSocket URL**: ${WS_URL}

## Test Results Summary

### Integration Tests
- Status: ${INTEGRATION_RESULT}
- Test Count: $(pytest tests/integration/test_websocket_flow.py --collect-only -q 2>/dev/null | wc -l)

### Performance Tests
- Status: ${PERFORMANCE_RESULT}
- See performance test output for detailed metrics

### Code Quality
- Formatting: ${FORMATTING_RESULT}
- Import Sorting: ${IMPORT_RESULT}
- Linting: ${LINTING_RESULT}
- Type Checking: ${TYPE_RESULT}

## Test Coverage

\`\`\`
$(pytest tests/integration/test_websocket_flow.py --cov=src/presentation/websocket --cov-report=term-missing 2>/dev/null || echo "Coverage data not available")
\`\`\`

## Recommendations

1. Review any failed tests and fix issues
2. Ensure code quality checks pass before deployment
3. Monitor performance metrics for degradation
4. Add more edge case tests as needed

---
*Generated by WebSocket E2E Test Suite*
EOF

    print_success "Test report saved to ${REPORT_FILE}"
}

# Cleanup function
cleanup() {
    print_status "Cleaning up..."

    # Stop servers if running
    stop_server

    # Remove temporary files
    rm -f server.log http_server.log wscat_test.log

    print_success "Cleanup complete"
}

# Trap to ensure cleanup on exit
trap cleanup EXIT INT TERM

# Main execution
main() {
    echo "=========================================="
    echo "   WebSocket E2E Testing Suite"
    echo "=========================================="
    echo

    # Initialize result variables
    INTEGRATION_RESULT="Not Run"
    PERFORMANCE_RESULT="Not Run"
    FORMATTING_RESULT="Not Checked"
    IMPORT_RESULT="Not Checked"
    LINTING_RESULT="Not Checked"
    TYPE_RESULT="Not Checked"

    # Check or start server
    if ! check_server; then
        if ! start_server; then
            print_error "Failed to start server. Exiting."
            exit 1
        fi
    fi

    # Run quality checks
    print_status "Phase 1: Code Quality Checks"
    echo "----------------------------------------"
    if run_quality_checks; then
        FORMATTING_RESULT="Passed"
        IMPORT_RESULT="Passed"
        LINTING_RESULT="Passed"
        TYPE_RESULT="Passed"
    else
        FORMATTING_RESULT="Issues Found"
        IMPORT_RESULT="Issues Found"
        LINTING_RESULT="Issues Found"
        TYPE_RESULT="Issues Found"
    fi
    echo

    # Run integration tests
    print_status "Phase 2: Integration Tests"
    echo "----------------------------------------"
    if run_integration_tests; then
        INTEGRATION_RESULT="Passed"
    else
        INTEGRATION_RESULT="Failed"
        print_warning "Continuing despite integration test failures..."
    fi
    echo

    # Run performance tests
    print_status "Phase 3: Performance Tests"
    echo "----------------------------------------"
    if run_performance_tests; then
        PERFORMANCE_RESULT="Passed"
    else
        PERFORMANCE_RESULT="Failed"
        print_warning "Performance tests failed"
    fi
    echo

    # Test with wscat (optional)
    print_status "Phase 4: WebSocket Protocol Test"
    echo "----------------------------------------"
    test_with_wscat
    echo

    # Test HTML client (optional manual testing)
    print_status "Phase 5: HTML Client Test (Optional)"
    echo "----------------------------------------"
    echo "Do you want to test the HTML client manually? (y/N)"
    read -r response
    if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
        test_html_client
    else
        print_status "Skipping HTML client test"
    fi
    echo

    # Generate report
    print_status "Phase 6: Report Generation"
    echo "----------------------------------------"
    generate_report
    echo

    # Final summary
    echo "=========================================="
    echo "   E2E Test Suite Complete"
    echo "=========================================="

    if [[ "${INTEGRATION_RESULT}" == "Passed" ]] && [[ "${PERFORMANCE_RESULT}" == "Passed" ]]; then
        print_success "All tests passed successfully! ✅"
        exit 0
    else
        print_warning "Some tests failed. Review the report for details."
        exit 1
    fi
}

# Run main function
main
