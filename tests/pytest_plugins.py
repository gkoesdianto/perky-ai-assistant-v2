"""Pytest plugins for enhanced test functionality.

This module provides custom pytest markers, hooks, and plugins for:
- Priority-based test execution
- Smoke testing
- Performance tracking
- Test categorization
"""

from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, Optional

import pytest
from _pytest.config import Config
from _pytest.nodes import Item

# Priority levels for test execution
PRIORITY_LEVELS = {
    "critical": 1,  # Must pass for deployment
    "high": 2,  # Core functionality
    "medium": 3,  # Important features
    "low": 4,  # Nice-to-have tests
    "trivial": 5,  # Exploratory tests
}


@dataclass
class TestMetrics:
    """Metrics collected during test execution."""

    test_name: str
    duration: float
    priority: str
    category: str
    status: str
    error: Optional[str] = None
    memory_usage: Optional[float] = None


class PriorityPlugin:
    """Plugin for priority-based test execution and filtering."""

    def __init__(self, config: Config):
        self.config = config
        self.priority_filter = config.getoption("--priority", default=None)
        self.min_priority = config.getoption("--min-priority", default=None)
        self.test_metrics: Dict[str, TestMetrics] = {}

    def should_run_test(self, item: Item) -> bool:
        """Determine if test should run based on priority.

        Args:
            item: Test item to check

        Returns:
            True if test should run, False otherwise
        """
        # Get test priority
        priority_marker = item.get_closest_marker("priority")
        test_priority = priority_marker.args[0] if priority_marker else "medium"

        # Check exact priority match
        if self.priority_filter and test_priority != self.priority_filter:
            return False

        # Check minimum priority threshold
        if self.min_priority:
            min_level = PRIORITY_LEVELS.get(self.min_priority, 3)
            test_level = PRIORITY_LEVELS.get(test_priority, 3)
            if test_level > min_level:
                return False

        return True

    @pytest.hookimpl(tryfirst=True)
    def pytest_runtest_setup(self, item: Item):
        """Skip tests that don't meet priority criteria."""
        if not self.should_run_test(item):
            marker = item.get_closest_marker("priority")
            priority = marker.args[0] if marker else "medium"
            pytest.skip(f"Test priority '{priority}' doesn't match filter")

    @pytest.hookimpl(hookwrapper=True)
    def pytest_runtest_makereport(self, item: Item):
        """Collect test metrics during execution."""
        outcome = yield
        report = outcome.get_result()

        # Get test metadata
        priority_marker = item.get_closest_marker("priority")
        priority = priority_marker.args[0] if priority_marker else "medium"

        category_marker = item.get_closest_marker("category")
        category = category_marker.args[0] if category_marker else "general"

        # Store metrics
        if report.when == "call":
            self.test_metrics[item.nodeid] = TestMetrics(
                test_name=item.nodeid,
                duration=report.duration,
                priority=priority,
                category=category,
                status="passed" if report.passed else "failed",
                error=str(report.longrepr) if report.failed else None,
            )


class SmokeTestPlugin:
    """Plugin for smoke test execution."""

    def __init__(self, config: Config):
        self.config = config
        self.smoke_only = config.getoption("--smoke", default=False)

    @pytest.hookimpl(tryfirst=True)
    def pytest_runtest_setup(self, item: Item):
        """Skip non-smoke tests when smoke mode is active."""
        if self.smoke_only:
            smoke_marker = item.get_closest_marker("smoke")
            if not smoke_marker:
                pytest.skip("Not a smoke test")


class CategoryPlugin:
    """Plugin for category-based test filtering."""

    def __init__(self, config: Config):
        self.config = config
        self.category_filter = config.getoption("--category", default=None)
        self.exclude_categories = config.getoption("--exclude-category", default=[])

    @pytest.hookimpl(tryfirst=True)
    def pytest_runtest_setup(self, item: Item):
        """Filter tests based on category."""
        category_marker = item.get_closest_marker("category")
        test_category = category_marker.args[0] if category_marker else "general"

        # Check category inclusion
        if self.category_filter and test_category != self.category_filter:
            pytest.skip(
                f"Category '{test_category}' doesn't match filter "
                f"'{self.category_filter}'"
            )

        # Check category exclusion
        if test_category in self.exclude_categories:
            pytest.skip(f"Category '{test_category}' is excluded")


class PerformancePlugin:
    """Plugin for performance tracking and assertions."""

    def __init__(self, config: Config):
        self.config = config
        self.perf_threshold = config.getoption("--perf-threshold", default=1.0)
        self.slow_tests = []

    @pytest.hookimpl(hookwrapper=True)
    def pytest_runtest_makereport(self, item: Item):
        """Track test execution time and flag slow tests."""
        outcome = yield
        report = outcome.get_result()

        if report.when == "call" and report.passed:
            # Check for performance marker
            perf_marker = item.get_closest_marker("performance")
            if perf_marker:
                max_duration = perf_marker.kwargs.get(
                    "max_duration", self.perf_threshold
                )
                if report.duration > max_duration:
                    self.slow_tests.append(
                        {
                            "test": item.nodeid,
                            "duration": report.duration,
                            "threshold": max_duration,
                        }
                    )
                    # Optionally fail the test
                    if self.config.getoption("--fail-on-slow", default=False):
                        report.outcome = "failed"
                        report.longrepr = (
                            f"Test exceeded performance threshold: "
                            f"{report.duration:.2f}s > {max_duration}s"
                        )

    def pytest_terminal_summary(self, terminalreporter):
        """Report slow tests at the end of test run."""
        if self.slow_tests:
            terminalreporter.section("Slow Tests")
            for test_info in self.slow_tests:
                terminalreporter.write_line(
                    f"  {test_info['test']}: {test_info['duration']:.2f}s "
                    f"(threshold: {test_info['threshold']}s)"
                )


# Register custom markers
def pytest_configure(config):
    """Register custom markers and plugins."""
    # Register markers
    config.addinivalue_line(
        "markers",
        "priority(level): Mark test priority (critical, high, medium, low, trivial)",
    )
    config.addinivalue_line(
        "markers", "smoke: Mark test as smoke test for quick validation"
    )
    config.addinivalue_line(
        "markers",
        "category(name): Categorize tests (unit, integration, e2e, performance)",
    )
    config.addinivalue_line(
        "markers",
        "performance(max_duration=X): Mark performance-sensitive tests with threshold",
    )
    config.addinivalue_line(
        "markers", "flaky(reruns=X): Mark flaky tests that should be retried"
    )
    config.addinivalue_line("markers", "slow: Mark tests that are expected to be slow")
    config.addinivalue_line(
        "markers",
        "requires(feature): Mark tests requiring specific features or services",
    )

    # Register plugins
    config.pluginmanager.register(PriorityPlugin(config), "priority_plugin")
    config.pluginmanager.register(SmokeTestPlugin(config), "smoke_plugin")
    config.pluginmanager.register(CategoryPlugin(config), "category_plugin")
    config.pluginmanager.register(PerformancePlugin(config), "performance_plugin")


def pytest_addoption(parser):
    """Add custom command-line options."""
    # Priority options
    parser.addoption(
        "--priority",
        action="store",
        default=None,
        help="Run tests with specific priority level",
    )
    parser.addoption(
        "--min-priority",
        action="store",
        default=None,
        help="Run tests with minimum priority level",
    )

    # Category options
    parser.addoption(
        "--category",
        action="store",
        default=None,
        help="Run tests from specific category",
    )
    parser.addoption(
        "--exclude-category",
        action="append",
        default=[],
        help="Exclude tests from specific categories",
    )

    # Smoke test option
    parser.addoption(
        "--smoke", action="store_true", default=False, help="Run smoke tests only"
    )

    # Performance options
    parser.addoption(
        "--perf-threshold",
        action="store",
        type=float,
        default=1.0,
        help="Default performance threshold in seconds",
    )
    parser.addoption(
        "--fail-on-slow",
        action="store_true",
        default=False,
        help="Fail tests that exceed performance threshold",
    )

    # Test type options
    parser.addoption(
        "--e2e", action="store_true", default=False, help="Run end-to-end tests"
    )
    parser.addoption(
        "--integration",
        action="store_true",
        default=False,
        help="Run integration tests",
    )
    parser.addoption(
        "--performance",
        action="store_true",
        default=False,
        help="Run performance tests",
    )


# Test result hooks
@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item):
    """Add extra information to test reports."""
    outcome = yield
    report = outcome.get_result()

    # Add test markers to report
    if report.when == "call":
        markers = {}
        for marker in item.iter_markers():
            if marker.name in ["priority", "category", "smoke", "performance"]:
                markers[marker.name] = marker.args[0] if marker.args else True
        report.test_markers = markers


# Collection hooks
def pytest_collection_modifyitems(config, items):
    """Modify test collection based on markers and options."""
    # Sort tests by priority if requested
    if config.getoption("--sort-by-priority", default=False):

        def get_priority_value(item):
            marker = item.get_closest_marker("priority")
            priority = marker.args[0] if marker else "medium"
            return PRIORITY_LEVELS.get(priority, 3)

        items.sort(key=get_priority_value)

    # Add skip markers for conditional tests
    for item in items:
        # Skip tests requiring specific features
        requires_marker = item.get_closest_marker("requires")
        if requires_marker:
            feature = requires_marker.args[0]
            if not config.getoption(f"--has-{feature}", default=False):
                item.add_marker(pytest.mark.skip(reason=f"Requires {feature} feature"))


# Reporting enhancements
def pytest_report_header(config):
    """Add custom information to test report header."""
    lines = []

    # Show active filters
    if config.getoption("--priority"):
        lines.append(f"Priority filter: {config.getoption('--priority')}")
    if config.getoption("--category"):
        lines.append(f"Category filter: {config.getoption('--category')}")
    if config.getoption("--smoke"):
        lines.append("Running smoke tests only")

    return lines


def pytest_terminal_summary(terminalreporter, exitstatus, config):
    """Add custom summary to test report."""
    # Collect test statistics by priority
    priority_stats = defaultdict(lambda: {"passed": 0, "failed": 0, "skipped": 0})

    for report in terminalreporter.stats.get("passed", []):
        if hasattr(report, "test_markers") and "priority" in report.test_markers:
            priority_stats[report.test_markers["priority"]]["passed"] += 1

    for report in terminalreporter.stats.get("failed", []):
        if hasattr(report, "test_markers") and "priority" in report.test_markers:
            priority_stats[report.test_markers["priority"]]["failed"] += 1

    # Display priority summary
    if priority_stats:
        terminalreporter.section("Test Priority Summary")
        for priority in ["critical", "high", "medium", "low", "trivial"]:
            if priority in priority_stats:
                stats = priority_stats[priority]
                total = sum(stats.values())
                terminalreporter.write_line(
                    f"  {priority.capitalize()}: {total} tests "
                    f"(✓ {stats['passed']} / ✗ {stats['failed']} / "
                    f"⊘ {stats['skipped']})"
                )
