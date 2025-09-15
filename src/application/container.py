from typing import Dict, Any


class DIContainer:
    """Simple dependency injection container"""

    def __init__(self):
        self._services: Dict[str, Any] = {}
        self._singletons: Dict[str, Any] = {}

    def register(self, name: str, factory, singleton: bool = False):
        """Register a service factory"""
        # Clear cached singleton if re-registering
        if name in self._singletons:
            del self._singletons[name]
        self._services[name] = (factory, singleton)

    def resolve(self, name: str):
        """Resolve a service"""
        if name not in self._services:
            raise ValueError(f"Service {name} not registered")

        factory, is_singleton = self._services[name]

        if is_singleton:
            if name not in self._singletons:
                self._singletons[name] = factory()
            return self._singletons[name]

        return factory()


container = DIContainer()
