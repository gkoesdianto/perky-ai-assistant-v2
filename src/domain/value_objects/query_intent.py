from pydantic import BaseModel, Field, ConfigDict
from typing import Literal, Optional, List, Dict, Any


class ClarificationNeeded(BaseModel):
    """Represents an attribute that needs user clarification"""

    attribute_type: Literal[
        "product_type",
        "material",
        "dimensions",
        "thickness",
        "length",
        "grade",
        "finish",
    ]

    question_template: str = Field(
        ..., description="Template for generating clarification question"
    )
    options: List[str] = Field(..., description="Available options for this attribute")
    priority: int = Field(
        ..., ge=1, description="Order of clarification (1 = ask first)"
    )
    depends_on: Optional[str] = Field(
        None, description="Attribute that must be resolved before this one"
    )


class ConversationContext(BaseModel):
    """Maintains state across conversation turns"""

    resolved_attributes: Dict[str, Any] = Field(
        default_factory=dict, description="Attributes already clarified by user"
    )
    pending_clarifications: List[ClarificationNeeded] = Field(
        default_factory=list, description="Attributes still needing clarification"
    )
    conversation_history: List[Dict[str, str]] = Field(
        default_factory=list, description="Previous turns in conversation"
    )
    attribute_confidence: Dict[str, float] = Field(
        default_factory=dict, description="Confidence scores for resolved attributes"
    )


class QueryIntent(BaseModel):
    """
    Enhanced query intent for conversational product/variant discovery.
    Supports multi-turn clarification flow for Pydantic AI agent with ChatGPT 4o mini.
    """

    model_config = ConfigDict(frozen=True)

    type: Literal[
        "product_inquiry",
        "availability_check",
        "price_check",
        "variant_selection",
        "general",
    ]

    clarification_stage: Literal["initial", "narrowing", "confirming", "complete"] = (
        Field(default="initial")
    )

    query_level: Literal["product", "variant", "ambiguous"] = Field(
        default="ambiguous",
        description="Whether query targets product or specific variant",
    )

    conversation_context: ConversationContext = Field(
        default_factory=ConversationContext,
        description="Stateful conversation tracking",
    )
    conversation_turn: int = Field(
        default=1, description="Current turn number in conversation"
    )

    next_action: Literal[
        "provide_info",
        "request_clarification",
        "suggest_alternatives",
        "confirm_selection",
    ] = Field(default="request_clarification")

    next_clarification: Optional[ClarificationNeeded] = Field(
        None, description="Next attribute to clarify if needed"
    )

    suggested_response: Optional[str] = Field(
        None, description="Suggested response for the agent"
    )
    response_data: Optional[Dict[str, Any]] = Field(
        None, description="Data to include in response (products, variants, etc.)"
    )

    matched_products: List[str] = Field(
        default_factory=list, description="Product IDs that match current query state"
    )
    possible_variants: List[str] = Field(
        default_factory=list, description="Variant IDs that match resolved attributes"
    )

    original_query: str = Field(..., description="Original user query text")
    current_query: str = Field(
        ..., description="Current query with accumulated context"
    )
    detected_attributes: Dict[str, Any] = Field(
        default_factory=dict, description="Attributes detected from user input"
    )

    confidence: float = Field(
        ge=0.0, le=1.0, description="Overall classification confidence"
    )
    requires_human_intervention: bool = Field(
        default=False, description="Flag for edge cases needing human help"
    )

    product_name: Optional[str] = None
    quantity: Optional[int] = None
