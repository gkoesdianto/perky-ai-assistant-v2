"""Test data factories for DTOs and value objects."""

from datetime import datetime, timezone
from decimal import Decimal
from typing import Dict, Any, List, Optional
import uuid

from tests.factories.base import BaseFactory
from src.application.dto import SessionDTO, MessageDTO, ConversationDTO
from src.application.dto.product_query_dto import ProductQueryDTO, ProductResponseDTO
from src.domain.value_objects import ProductWithVariantsInfo


class DTOFactory(BaseFactory):
    """Factory for application DTOs."""

    @classmethod
    def create_session_dto(cls, **kwargs) -> SessionDTO:
        """Create SessionDTO."""
        now = datetime.now(timezone.utc)
        defaults = {
            'session_id': f"test-session-{uuid.uuid4().hex[:8]}",
            'conversation_id': None,
            'started_at': now,
            'last_activity': now,
            'is_active': True,
            'metadata': {'source': 'test'},
        }
        defaults.update(kwargs)
        return SessionDTO(**defaults)

    @classmethod
    def create_message_dto(cls, **kwargs) -> MessageDTO:
        """Create MessageDTO."""
        defaults = {
            'content': 'Test message',
            'sender_type': 'user',
            'session_id': f"test-session-{uuid.uuid4().hex[:8]}",
            'conversation_id': None,
            'timestamp': datetime.now(timezone.utc),
            'metadata': {},
        }
        defaults.update(kwargs)
        return MessageDTO(**defaults)

    @classmethod
    def create_conversation_dto(cls, **kwargs) -> ConversationDTO:
        """Create ConversationDTO."""
        now = datetime.now(timezone.utc)
        defaults = {
            'conversation_id': f"conv-{uuid.uuid4().hex[:8]}",
            'session_id': f"test-session-{uuid.uuid4().hex[:8]}",
            'started_at': now,
            'last_activity': now,
            'messages': [],
            'metadata': {'test': True},
        }
        defaults.update(kwargs)
        return ConversationDTO(**defaults)

    @classmethod
    def create_conversation_with_messages(cls, num_messages: int = 5, **kwargs) -> ConversationDTO:
        """Create ConversationDTO with messages."""
        conversation = cls.create_conversation_dto(**kwargs)

        for i in range(num_messages):
            message = cls.create_message_dto(
                session_id=conversation.session_id,
                conversation_id=conversation.conversation_id,
                sender_type="user" if i % 2 == 0 else "ai_agent",
                content=f"Test message {i}",
            )
            conversation.messages.append(message)

        return conversation

    @classmethod
    def create_product_query_dto(cls, **kwargs) -> ProductQueryDTO:
        """Create ProductQueryDTO."""
        defaults = {
            'query': 'plat baja',
            'session_id': f"test-session-{uuid.uuid4().hex[:8]}",
            'include_variants': True,
            'max_results': 10,
        }
        defaults.update(kwargs)
        return ProductQueryDTO(**defaults)

    @classmethod
    def create_product_response_dto(cls, products: Optional[List] = None, **kwargs) -> ProductResponseDTO:
        """Create ProductResponseDTO."""
        if products is None:
            # Create a default product list if none provided
            from tests.factories.domain import ProductFactory
            product = ProductFactory.steel_plate()
            products = [{
                'product_id': product.product_id,
                'product_name': product.product_name,
                'variant_count': product.variant_count,
            }]

        # Convert product objects to dicts if needed
        product_dicts = []
        for p in products:
            if hasattr(p, '__dict__'):
                # Convert object to dict
                product_dicts.append({
                    'product_id': p.product_id,
                    'product_name': p.product_name,
                    'variant_count': p.variant_count,
                })
            else:
                product_dicts.append(p)

        defaults = {
            'products': product_dicts,
            'query': 'plat baja',
            'response_time_ms': 100,
            'source': 'mock',
        }
        defaults.update(kwargs)
        return ProductResponseDTO(**defaults)


class ProductWithVariantsFactory(BaseFactory[ProductWithVariantsInfo]):
    """Factory for ProductWithVariantsInfo value objects."""

    _model = ProductWithVariantsInfo

    @classmethod
    def _get_defaults(cls) -> Dict[str, Any]:
        """Get defaults for ProductWithVariantsInfo."""
        from tests.factories.domain import ProductFactory, VariantFactory

        product = ProductFactory.steel_plate()
        variants = [
            VariantFactory.steel_plate_10mm(),
            VariantFactory.steel_plate_5mm(),
        ]

        return {
            'product': product,
            'variants': variants,
        }

    @classmethod
    def create_steel_plate_complete(cls, **kwargs) -> ProductWithVariantsInfo:
        """Create complete steel plate with multiple variants."""
        from tests.factories.domain import ProductFactory, VariantFactory

        product = ProductFactory.steel_plate()
        variants = [
            VariantFactory.steel_plate_10mm(),
            VariantFactory.steel_plate_5mm(),
            VariantFactory.create(
                variant_id='var_003',
                sku='PLT-15MM-001',
                product_id='prod_plat_baja',
                variant_name='Plat Baja 15mm x 1200mm x 2400mm',
                price=Decimal('1050000'),
                stock_quantity=15,
                stock_unit='lembar',
                specifications={
                    'thickness': '15mm',
                    'width': '1200mm',
                    'length': '2400mm',
                    'grade': 'SS400',
                }
            )
        ]

        defaults = {
            'product': product,
            'variants': variants,
        }
        defaults.update(kwargs)
        return cls._model(**defaults)

    @classmethod
    def create_minimal(cls, **kwargs) -> ProductWithVariantsInfo:
        """Create minimal product with single variant."""
        from tests.factories.domain import ProductFactory, VariantFactory

        product = ProductFactory.minimal()
        variants = [VariantFactory.create(product_id=product.product_id)]

        defaults = {
            'product': product,
            'variants': variants,
        }
        defaults.update(kwargs)
        return cls._model(**defaults)


class TestDataPresets:
    """Common test data presets for cross-cutting scenarios."""

    @classmethod
    def create_full_conversation_context(cls):
        """Create a complete conversation context for testing."""
        from tests.factories.domain import SessionFactory, ConversationFactory, MessageFactory

        # Create session
        session = SessionFactory.with_metadata()

        # Create conversation linked to session
        conversation = ConversationFactory.create(session_id=session.session_id)

        # Add messages
        messages = [
            MessageFactory.user_message(conversation_id=conversation.id),
            MessageFactory.ai_message(conversation_id=conversation.id),
            MessageFactory.product_query(conversation_id=conversation.id),
        ]

        for message in messages:
            conversation.add_message(message)

        # Update session with conversation
        session.conversation_id = conversation.id

        return {
            'session': session,
            'conversation': conversation,
            'messages': messages,
        }

    @classmethod
    def create_product_search_scenario(cls):
        """Create a product search scenario with query and results."""
        from tests.factories.domain import ProductFactory, VariantFactory

        # Create products
        products = [
            ProductFactory.steel_plate(),
            ProductFactory.complete(),
            ProductFactory.minimal(),
        ]

        # Create variants for first product
        variants = [
            VariantFactory.steel_plate_10mm(),
            VariantFactory.steel_plate_5mm(),
        ]

        # Create query
        query_dto = DTOFactory.create_product_query_dto(
            query='plat baja 5mm',
            max_results=10
        )

        # Create response
        response_dto = DTOFactory.create_product_response_dto(
            products=products,
            query=query_dto.query
        )

        return {
            'query': query_dto,
            'response': response_dto,
            'products': products,
            'variants': variants,
        }
