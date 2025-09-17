"""Base factory implementation with preset support."""

from typing import TypeVar, Generic, Dict, Any, List, Callable
import uuid
from datetime import datetime, timezone

T = TypeVar('T')

class BaseFactory(Generic[T]):
    """Base factory for creating test instances with presets.

    Features:
    - Preset configurations for common test scenarios
    - Batch creation support
    - Automatic ID generation
    - Timestamp management
    """

    _model: type = None
    _presets: Dict[str, Dict[str, Any]] = {}

    @classmethod
    def create(cls, **kwargs) -> T:
        """Create single instance with optional overrides."""
        defaults = cls._get_defaults()
        defaults.update(kwargs)
        return cls._model(**defaults)

    @classmethod
    def create_batch(cls, size: int, **kwargs) -> List[T]:
        """Create multiple instances."""
        return [cls.create(**kwargs) for _ in range(size)]

    @classmethod
    def preset(cls, name: str, **defaults) -> Callable:
        """Register a named preset configuration."""
        cls._presets[name] = defaults
        return lambda **overrides: cls.create(**{**defaults, **overrides})

    @classmethod
    def _get_defaults(cls) -> Dict[str, Any]:
        """Get default values for instance creation."""
        return {
            'id': f"{cls.__name__.lower()}-{uuid.uuid4().hex[:8]}",
            'created_at': datetime.now(timezone.utc),
            'updated_at': datetime.now(timezone.utc),
        }
