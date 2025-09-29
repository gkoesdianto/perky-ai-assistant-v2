"""Test configuration management.

This module provides configuration loading and management for different test
environments.
"""

import os
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, Optional

import yaml


@dataclass
class DatabaseConfig:
    """Database configuration for tests."""

    url: Optional[str] = None
    url_env: Optional[str] = None
    url_suffix: str = ""
    pool_size: int = 5
    pool_timeout: int = 30
    echo_sql: bool = False
    use_transactions: bool = True
    use_memory: bool = False

    def get_url(self, base_url: Optional[str] = None) -> str:
        """Get the database URL."""
        if self.url:
            return self.url
        elif self.url_env:
            return os.getenv(self.url_env, "")
        elif base_url and self.url_suffix:
            # Append suffix to base database name
            if "postgresql" in base_url:
                parts = base_url.rsplit("/", 1)
                db_name = parts[1].split("?")[0] if len(parts) > 1 else "test"
                return f"{parts[0]}/{db_name}{self.url_suffix}"
            return base_url + self.url_suffix
        elif self.use_memory:
            return "sqlite+aiosqlite:///:memory:"
        return base_url or ""


@dataclass
class RedisConfig:
    """Redis configuration for tests."""

    url: Optional[str] = None
    url_env: Optional[str] = None
    db_number: int = 15
    max_connections: int = 10
    socket_timeout: int = 5
    decode_responses: bool = True
    use_mock: bool = False

    def get_url(self, base_url: Optional[str] = None) -> str:
        """Get the Redis URL."""
        if self.url:
            return self.url
        elif self.url_env:
            return os.getenv(self.url_env, "")
        elif base_url:
            # Update database number in URL
            if "/" in base_url:
                parts = base_url.rsplit("/", 1)
                return f"{parts[0]}/{self.db_number}"
            return f"{base_url}/{self.db_number}"
        return f"redis://localhost:6379/{self.db_number}"


@dataclass
class TimeoutConfig:
    """Timeout configuration for tests."""

    default: float = 10.0
    async_timeout: float = 30.0  # renamed from 'async' to avoid keyword
    websocket: float = 5.0
    http_request: float = 10.0


@dataclass
class FeatureConfig:
    """Feature flags for tests."""

    performance_monitoring: bool = False
    coverage_tracking: bool = True
    test_isolation: bool = True
    parallel_execution: bool = False
    verbose_logging: bool = False


@dataclass
class ServiceConfig:
    """External service configuration for tests."""

    mock_external: bool = True
    stub_ai_responses: bool = True
    use_test_database: bool = True
    use_test_redis: bool = True


@dataclass
class TestEnvironmentConfig:
    """Complete test environment configuration."""

    name: str
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    redis: RedisConfig = field(default_factory=RedisConfig)
    timeouts: TimeoutConfig = field(default_factory=TimeoutConfig)
    features: FeatureConfig = field(default_factory=FeatureConfig)
    services: ServiceConfig = field(default_factory=ServiceConfig)

    @classmethod
    def from_dict(cls, name: str, data: Dict[str, Any]) -> "TestEnvironmentConfig":
        """Create configuration from dictionary."""
        return cls(
            name=name,
            database=DatabaseConfig(**data.get("database", {})),
            redis=RedisConfig(**data.get("redis", {})),
            timeouts=TimeoutConfig(
                default=data.get("timeouts", {}).get("default", 10.0),
                async_timeout=data.get("timeouts", {}).get("async", 30.0),
                websocket=data.get("timeouts", {}).get("websocket", 5.0),
                http_request=data.get("timeouts", {}).get("http_request", 10.0),
            ),
            features=FeatureConfig(**data.get("features", {})),
            services=ServiceConfig(**data.get("services", {})),
        )


class TestConfigLoader:
    """Loads and manages test configurations."""

    def __init__(self, config_file: Optional[Path] = None):
        """Initialize the configuration loader.

        Args:
            config_file: Path to the configuration file
        """
        if config_file is None:
            config_file = Path(__file__).parent / "test_env.yaml"
        self.config_file = config_file
        self._config_data: Optional[Dict[str, Any]] = None

    @property
    def config_data(self) -> Dict[str, Any]:
        """Lazily load configuration data."""
        if self._config_data is None:
            self._config_data = self._load_config()
        return self._config_data

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        if not self.config_file.exists():
            return {}

        with open(self.config_file, "r") as f:
            return yaml.safe_load(f) or {}

    def _merge_configs(
        self, base: Dict[str, Any], override: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Merge two configuration dictionaries.

        Args:
            base: Base configuration
            override: Configuration to override with

        Returns:
            Merged configuration
        """
        result = base.copy()

        for key, value in override.items():
            if key == "inherit":
                continue
            elif (
                isinstance(value, dict)
                and key in result
                and isinstance(result[key], dict)
            ):
                result[key] = self._merge_configs(result[key], value)
            else:
                result[key] = value

        return result

    def get_environment(self, env_name: str) -> TestEnvironmentConfig:
        """Get configuration for a specific environment.

        Args:
            env_name: Name of the environment

        Returns:
            Test environment configuration
        """
        if env_name not in self.config_data:
            # Return default configuration if environment not found
            env_name = "default"

        env_data = self.config_data.get(env_name, {})

        # Handle inheritance
        if "inherit" in env_data and env_data["inherit"] in self.config_data:
            base_data = self.config_data[env_data["inherit"]]
            env_data = self._merge_configs(base_data, env_data)

        return TestEnvironmentConfig.from_dict(env_name, env_data)

    def get_active_environment(self) -> TestEnvironmentConfig:
        """Get the currently active test environment configuration.

        The environment is determined by:
        1. TEST_ENV environment variable
        2. Pytest markers or command-line options
        3. Default to 'unit'
        """
        # Check environment variable
        env_name = os.getenv("TEST_ENV", "unit")

        # Check for pytest options (this would be set by pytest plugins)
        import sys

        if "--e2e" in sys.argv:
            env_name = "e2e"
        elif "--integration" in sys.argv:
            env_name = "integration"
        elif "--performance" in sys.argv:
            env_name = "performance"

        # Check if running in CI
        if os.getenv("CI"):
            env_name = "ci"

        return self.get_environment(env_name)


# Global configuration loader instance
_config_loader = TestConfigLoader()


@lru_cache(maxsize=None)
def get_test_config(env_name: Optional[str] = None) -> TestEnvironmentConfig:
    """Get test configuration for the specified environment.

    Args:
        env_name: Environment name (optional, auto-detected if not provided)

    Returns:
        Test environment configuration
    """
    if env_name:
        return _config_loader.get_environment(env_name)
    return _config_loader.get_active_environment()


def get_database_url(env_name: Optional[str] = None) -> str:
    """Get database URL for the specified environment.

    Args:
        env_name: Environment name

    Returns:
        Database URL
    """
    config = get_test_config(env_name)
    base_url = os.getenv("DATABASE_URL", "postgresql://localhost/perky_db")
    return config.database.get_url(base_url)


def get_redis_url(env_name: Optional[str] = None) -> str:
    """Get Redis URL for the specified environment.

    Args:
        env_name: Environment name

    Returns:
        Redis URL
    """
    config = get_test_config(env_name)
    base_url = os.getenv("REDIS_URL", "redis://localhost:6379")
    return config.redis.get_url(base_url)


def should_mock_external_services(env_name: Optional[str] = None) -> bool:
    """Check if external services should be mocked.

    Args:
        env_name: Environment name

    Returns:
        True if external services should be mocked
    """
    config = get_test_config(env_name)
    return config.services.mock_external


def get_timeout(timeout_type: str = "default", env_name: Optional[str] = None) -> float:
    """Get timeout value for the specified type.

    Args:
        timeout_type: Type of timeout (default, async, websocket, http_request)
        env_name: Environment name

    Returns:
        Timeout value in seconds
    """
    config = get_test_config(env_name)
    return getattr(config.timeouts, timeout_type, config.timeouts.default)
