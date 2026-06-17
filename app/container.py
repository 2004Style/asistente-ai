"""
Dependency injection container for the AI assistant.

Defines a registry of services and resolves dependencies throughout the application.
"""
from typing import Dict, Any, Callable, TypeVar, Type

T = TypeVar('T')

class Container:
    _services: Dict[str, Any] = {}
    _factories: Dict[str, Callable[[], Any]] = {}

    @classmethod
    def register(cls, name: str, service: Any) -> None:
        """Register a singleton service instance."""
        cls._services[name] = service

    @classmethod
    def register_factory(cls, name: str, factory: Callable[[], Any]) -> None:
        """Register a factory function to create a service when resolved."""
        cls._factories[name] = factory

    @classmethod
    def resolve(cls, name: str) -> Any:
        """Resolve and retrieve a service by name."""
        if name in cls._services:
            return cls._services[name]
        if name in cls._factories:
            service = cls._factories[name]()
            cls._services[name] = service
            return service
        raise ValueError(f"Service '{name}' is not registered.")

    @classmethod
    def has(cls, name: str) -> bool:
        """Check if a service is registered."""
        return name in cls._services or name in cls._factories

    @classmethod
    def clear(cls) -> None:
        """Clear all registered services."""
        cls._services.clear()
        cls._factories.clear()
