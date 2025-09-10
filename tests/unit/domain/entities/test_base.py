"""
Unit tests for BaseEntity focusing on business logic and domain rules.

Test Coverage Required: 80%
Priority: MEDIUM
"""

import json
from datetime import datetime, timezone
from typing import Optional

from src.domain.entities.base import BaseEntity
from src.domain.entities.session import Session


class TestBaseEntity:
    """Test suite for BaseEntity core functionality."""

    def test_default_values(self):
        """
        Test that our chosen default values are applied correctly.
        Priority: HIGH
        """
        entity = BaseEntity()

        assert entity.is_active is True
        assert entity.updated_at is None
        assert entity.id is not None
        assert entity.created_at is not None
        assert isinstance(entity.id, str)
        assert isinstance(entity.created_at, datetime)
        assert isinstance(entity.is_active, bool)

    def test_entity_inheritance(self):
        """
        Test that subclasses properly inherit BaseEntity fields.
        Priority: HIGH
        """
        session = Session(session_id="test-123")

        assert hasattr(session, "id")
        assert hasattr(session, "created_at")
        assert hasattr(session, "updated_at")
        assert hasattr(session, "is_active")

        assert session.is_active is True
        assert session.updated_at is None
        assert session.session_id == "test-123"
        assert session.conversation_id is None

        assert isinstance(session, Session)
        assert isinstance(session, BaseEntity)

    def test_entity_serialization(self):
        """
        Test model_dump() and model_dump_json() for our use cases.
        Priority: MEDIUM
        """
        entity = BaseEntity()
        entity.is_active = False
        entity.updated_at = datetime.now(timezone.utc)

        entity_dict = entity.model_dump()

        assert isinstance(entity_dict, dict)
        assert "id" in entity_dict
        assert "created_at" in entity_dict
        assert "updated_at" in entity_dict
        assert "is_active" in entity_dict

        assert entity_dict["is_active"] is False
        assert entity_dict["updated_at"] is not None

        entity_json = entity.model_dump_json()

        assert isinstance(entity_json, str)

        parsed_json = json.loads(entity_json)
        assert parsed_json["id"] == entity.id
        assert parsed_json["is_active"] is False
        assert isinstance(parsed_json["created_at"], str)
        assert "T" in parsed_json["created_at"]

        entity_dict_partial = entity.model_dump(exclude={"updated_at"})
        assert "updated_at" not in entity_dict_partial
        assert "is_active" in entity_dict_partial

    def test_field_override(self):
        """
        Test that subclasses can override default values.
        Priority: MEDIUM
        """

        class CustomEntity(BaseEntity):
            is_active: bool = False
            custom_field: str = "custom_value"
            optional_field: Optional[str] = None

        custom = CustomEntity()

        assert custom.is_active is False
        assert custom.custom_field == "custom_value"
        assert custom.optional_field is None

        custom_with_values = CustomEntity(
            is_active=True, custom_field="different", optional_field="set"
        )

        assert custom_with_values.is_active is True
        assert custom_with_values.custom_field == "different"
        assert custom_with_values.optional_field == "set"

        assert custom.id is not None
        assert custom.created_at is not None
        assert custom.updated_at is None

        custom_dict = custom.model_dump()
        assert "custom_field" in custom_dict
        assert custom_dict["is_active"] is False


class TestBaseEntityAdvanced:
    """Additional tests for edge cases and advanced scenarios."""

    def test_multiple_inheritance_levels(self):
        """Test that multi-level inheritance works correctly."""

        class MiddleEntity(BaseEntity):
            middle_field: str = "middle"

        class LeafEntity(MiddleEntity):
            leaf_field: str = "leaf"

        leaf = LeafEntity()

        assert hasattr(leaf, "id")
        assert hasattr(leaf, "middle_field")
        assert hasattr(leaf, "leaf_field")

        assert leaf.is_active is True
        assert leaf.middle_field == "middle"
        assert leaf.leaf_field == "leaf"

    def test_entity_equality(self):
        """Test entity equality based on id."""

        entity1 = BaseEntity()
        entity2 = BaseEntity()

        assert entity1.id != entity2.id
        assert entity1 == entity1
        assert entity1 != entity2

    def test_entity_copy(self):
        """Test that entities can be copied with modifications."""

        original = BaseEntity()
        original.is_active = False

        modified = original.model_copy(update={"is_active": True})

        assert modified.id == original.id
        assert modified.is_active is True
        assert original.is_active is False

    def test_from_attributes_config(self):
        """Test that from_attributes config works for ORM compatibility."""

        entity = BaseEntity()
        assert entity.model_config["from_attributes"] is True


class TestBaseEntityValidation:
    """Test validation and error handling."""

    def test_field_type_coercion(self):
        """Test that Pydantic validates field types."""

        entity = BaseEntity()

        entity.is_active = False
        assert entity.is_active is False

        entity.is_active = True
        assert entity.is_active is True

        another_entity = BaseEntity(is_active=False)
        assert another_entity.is_active is False

        third_entity = BaseEntity(is_active=True)
        assert third_entity.is_active is True

    def test_immutable_field_behavior(self):
        """Test behavior of auto-generated fields."""

        entity = BaseEntity()
        original_created = entity.created_at

        entity.id = "new-id"
        entity.created_at = datetime.now(timezone.utc)

        assert entity.id == "new-id"
        assert entity.created_at != original_created
