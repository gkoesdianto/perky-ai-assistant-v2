"""Domain entity factories - placeholder for Phase 2."""

from .base import BaseFactory

# Placeholder implementations - will be fully implemented in Phase 2
class SessionFactory(BaseFactory):
    """Factory for Session entities."""
    pass

class ConversationFactory(BaseFactory):
    """Factory for Conversation entities."""
    pass

class MessageFactory(BaseFactory):
    """Factory for Message entities."""
    pass

class ProductFactory(BaseFactory):
    """Unified product factory replacing duplicate implementations."""
    pass

class VariantFactory(BaseFactory):
    """Factory for VariantInfo value objects."""
    pass
