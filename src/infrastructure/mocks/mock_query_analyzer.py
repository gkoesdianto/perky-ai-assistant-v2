"""Mock Query Analyzer for testing and development"""

import re
from typing import Any, Dict, List, Optional

from src.application.dto.message_dto import MessageDTO
from src.application.ports.query_analyzer_port import QueryAnalyzerPort
from src.domain.value_objects.query_intent import (
    ClarificationNeeded,
    ConversationContext,
    QueryIntent,
)


class MockQueryAnalyzer(QueryAnalyzerPort):
    """
    Mock query analyzer for testing and development.
    Pattern-based intent detection for Indonesian queries.
    """

    def __init__(self):
        # Define pattern dictionaries for query classification
        self.patterns = {
            "product_inquiry": [
                "plat",
                "hollow",
                "besi",
                "pipa",
                "profil",
                "siku",
                "unp",
                "wf",
                "h-beam",
                "cnp",
                "galvanis",
                "baja",
                "steel",
            ],
            "price_check": ["harga", "price", "berapa", "cost", "biaya", "tarif"],
            "availability_check": [
                "stok",
                "stock",
                "tersedia",
                "ada",
                "available",
                "ready",
            ],
            "variant_selection": [
                "ukuran",
                "size",
                "tebal",
                "thickness",
                "dimensi",
                "diameter",
                "panjang",
                "lebar",
            ],
        }

        # Indonesian steel terminology mapping
        self.terminology_map = {
            "plat": ["plate", "sheet", "plat baja", "pelat"],
            "hollow": ["hollow", "kotak", "besi kotak", "hollow galvanis"],
            "besi": ["iron", "steel", "besi baja", "beton"],
            "pipa": ["pipe", "tube", "pipa baja", "tubing"],
            "wf": ["wide flange", "h-beam", "profil wf", "beam"],
            "unp": ["channel", "kanal u", "profil u", "u-channel"],
            "siku": ["angle", "angle bar", "besi siku", "l-bracket"],
            "beli": ["buy", "purchase", "order", "pesan"],
            "pesan": ["order", "request", "book", "beli"],
            "cek": ["check", "verify", "confirm", "lihat"],
        }

        # Common product attributes for extraction
        self.product_attributes = {
            "thickness": ["mm", "milimeter", "tebal"],
            "length": ["m", "meter", "panjang"],
            "width": ["cm", "centimeter", "lebar"],
            "diameter": ["inch", "in", "diameter"],
            "grade": ["ss400", "sni", "jis", "astm"],
            "finish": ["galvanis", "hitam", "polish", "coating"],
        }

    async def analyze(
        self, query: str, conversation_context: Optional[List[MessageDTO]] = None
    ) -> QueryIntent:
        """
        Analyze query to determine intent using pattern matching.

        Args:
            query: The user's query text to analyze
            conversation_context: Optional list of previous messages for context

        Returns:
            QueryIntent: The analyzed intent with clarification needs and context
        """
        query_lower = query.lower()

        # Determine query type based on patterns
        query_type = self._detect_query_type(query_lower)

        # Calculate confidence based on pattern matching
        confidence = self._calculate_confidence(query_lower, query_type)

        # Extract attributes from query
        detected_attributes = self._extract_attributes(query_lower)

        # Determine clarification stage based on context and confidence
        clarification_stage = self._determine_clarification_stage(
            confidence, conversation_context, detected_attributes
        )

        # Create conversation context
        conv_context = self._create_conversation_context(
            detected_attributes, conversation_context
        )

        # Determine next action based on stage and confidence
        next_action = self._determine_next_action(clarification_stage, confidence)

        # Extract quantity if present
        quantity = self._extract_quantity(query_lower)

        # Determine query level (product vs variant)
        query_level = self._determine_query_level(detected_attributes)

        # Build next clarification if needed
        next_clarification = self._build_next_clarification(
            clarification_stage, detected_attributes, query_type
        )

        # Create and return QueryIntent
        return QueryIntent(
            type=query_type,
            clarification_stage=clarification_stage,
            query_level=query_level,
            conversation_context=conv_context,
            conversation_turn=self._get_conversation_turn(conversation_context),
            next_action=next_action,
            next_clarification=next_clarification,
            original_query=query,
            current_query=query,
            detected_attributes=detected_attributes,
            confidence=confidence,
            requires_human_intervention=confidence < 0.3,
            product_name=detected_attributes.get("product_type"),
            quantity=quantity,
        )

    def _detect_query_type(self, query_lower: str) -> str:
        """Detect the type of query based on pattern matching."""
        # Check for specific query types first (more specific patterns)
        # Order matters: check more specific patterns before general ones

        # Check for price queries first
        if any(keyword in query_lower for keyword in self.patterns["price_check"]):
            return "price_check"

        # Check for availability/stock queries
        if any(
            keyword in query_lower for keyword in self.patterns["availability_check"]
        ):
            return "availability_check"

        # Check for variant/size selection
        if any(
            keyword in query_lower for keyword in self.patterns["variant_selection"]
        ):
            return "variant_selection"

        # Check for general product inquiries
        if any(keyword in query_lower for keyword in self.patterns["product_inquiry"]):
            return "product_inquiry"

        return "general"

    def _calculate_confidence(self, query_lower: str, query_type: str) -> float:
        """Calculate confidence score based on pattern matching strength."""
        if query_type == "general" or not query_lower.strip():
            return 0.25  # Low confidence for empty/general queries

        # Get patterns for the detected type
        patterns = self.patterns.get(query_type, [])

        # Count matches for the detected type
        type_matches = sum(1 for pattern in patterns if pattern in query_lower)

        # Also check for product mentions (adds to confidence)
        product_matches = sum(
            1 for pattern in self.patterns["product_inquiry"] if pattern in query_lower
        )

        # Calculate total matches
        total_matches = type_matches + (
            product_matches * 0.5
        )  # Product mentions add half weight

        # Base confidence on number of matches
        if total_matches >= 3:
            return 0.9
        elif total_matches >= 2:
            return 0.75
        elif total_matches >= 1:
            return 0.6
        else:
            return 0.4

    def _extract_attributes(self, query_lower: str) -> Dict[str, Any]:
        """Extract product attributes from the query."""
        attributes = {}

        # Extract product type
        product_type = self._extract_product_type(query_lower)
        if product_type:
            attributes["product_type"] = product_type

        # Extract measurements
        measurements = self._extract_measurements(query_lower)
        attributes.update(measurements)

        # Extract finish and grade
        finish = self._extract_finish(query_lower)
        if finish:
            attributes["finish"] = finish

        grade = self._extract_grade(query_lower)
        if grade:
            attributes["grade"] = grade

        return attributes

    def _extract_product_type(self, query_lower: str) -> Optional[str]:
        """Extract product type from query, checking compound terms first."""
        # Check for compound Indonesian terms first (more specific)
        compound_terms = {
            "besi kotak": "hollow",
            "plat hitam": "plat",
            "besi siku": "siku",
            "pipa baja": "pipa",
            "profil wf": "wf",
        }

        for compound, product_type in compound_terms.items():
            if compound in query_lower:
                return product_type

        # If no compound term found, check individual product types
        for product in self.patterns["product_inquiry"]:
            if product in query_lower:
                return product

        return None

    def _extract_measurements(self, query_lower: str) -> Dict[str, float]:
        """Extract measurement attributes from query."""
        attributes = {}
        measurements = re.findall(r"(\d+(?:\.\d+)?)\s*(mm|m|cm|inch|in)", query_lower)

        unit_mapping = {
            "mm": "thickness",
            "milimeter": "thickness",
            "m": "length",
            "meter": "length",
            "cm": "width",
            "centimeter": "width",
            "inch": "diameter",
            "in": "diameter",
        }

        for value, unit in measurements:
            if unit in unit_mapping:
                attr_name = unit_mapping[unit]
                attributes[attr_name] = float(value)

        return attributes

    def _extract_finish(self, query_lower: str) -> Optional[str]:
        """Extract finish type from query."""
        if "galvanis" in query_lower:
            return "galvanis"
        elif "hitam" in query_lower:
            return "hitam"
        return None

    def _extract_grade(self, query_lower: str) -> Optional[str]:
        """Extract grade from query."""
        grade_patterns = ["ss400", "sni", "jis", "astm"]
        for grade in grade_patterns:
            if grade in query_lower:
                return grade.upper()
        return None

    def _determine_clarification_stage(
        self,
        confidence: float,
        conversation_context: Optional[List[MessageDTO]],
        detected_attributes: Dict[str, Any],
    ) -> str:
        """Determine the clarification stage based on context and confidence."""
        # Count conversation turns
        turn_count = len(conversation_context) if conversation_context else 0

        # Determine stage based on confidence and attributes
        if confidence >= 0.85 and len(detected_attributes) >= 3:
            return "complete"
        elif confidence >= 0.7 and len(detected_attributes) >= 2:
            return "confirming"
        elif turn_count > 0 and detected_attributes:
            return "narrowing"
        else:
            return "initial"

    def _create_conversation_context(
        self,
        detected_attributes: Dict[str, Any],
        conversation_context: Optional[List[MessageDTO]],
    ) -> ConversationContext:
        """Create conversation context from detected attributes and history."""
        # Build conversation history
        history = []
        if conversation_context:
            for msg in conversation_context[-4:]:  # Keep last 4 messages
                history.append({"sender": msg.sender_type, "content": msg.content})

        # Create attribute confidence scores
        attribute_confidence = {
            key: 0.8 if key == "product_type" else 0.6
            for key in detected_attributes.keys()
        }

        # Build pending clarifications based on missing attributes
        pending_clarifications = []
        if "product_type" not in detected_attributes:
            pending_clarifications.append(
                ClarificationNeeded(
                    attribute_type="product_type",
                    question_template="Produk apa yang Anda cari?",
                    options=["plat", "hollow", "besi beton", "pipa", "profil"],
                    priority=1,
                )
            )

        if (
            "product_type" in detected_attributes
            and "dimensions" not in detected_attributes
        ):
            pending_clarifications.append(
                ClarificationNeeded(
                    attribute_type="dimensions",
                    question_template="Ukuran berapa yang Anda butuhkan?",
                    options=[],
                    priority=2,
                    depends_on="product_type",
                )
            )

        return ConversationContext(
            resolved_attributes=detected_attributes,
            pending_clarifications=pending_clarifications,
            conversation_history=history,
            attribute_confidence=attribute_confidence,
        )

    def _determine_next_action(
        self, clarification_stage: str, confidence: float
    ) -> str:
        """Determine the next action based on stage and confidence."""
        if clarification_stage == "complete" and confidence >= 0.8:
            return "provide_info"
        elif clarification_stage == "confirming":
            return "confirm_selection"
        elif confidence <= 0.3:  # Very low confidence - need clarification
            return "request_clarification"
        elif confidence < 0.5:  # Medium-low confidence - suggest options
            return "suggest_alternatives"
        else:
            return "request_clarification"

    def _extract_quantity(self, query_lower: str) -> Optional[int]:
        """Extract quantity from the query if present."""
        # Look for number patterns that might indicate quantity
        quantity_patterns = [
            r"(\d+)\s*(?:buah|pcs|pieces|lembar|batang|unit)",
            r"(?:butuh|perlu|mau|order)\s*(\d+)",
        ]

        for pattern in quantity_patterns:
            match = re.search(pattern, query_lower)
            if match:
                try:
                    return int(match.group(1))
                except (ValueError, IndexError):
                    pass

        # Check for standalone numbers that might be quantity
        numbers = re.findall(r"\b(\d+)\b", query_lower)
        for num_str in numbers:
            num = int(num_str)
            # Assume numbers between 1-1000 could be quantities (not dimensions)
            if 1 <= num <= 1000 and str(num) + "mm" not in query_lower:
                return num

        return None

    def _determine_query_level(self, detected_attributes: Dict[str, Any]) -> str:
        """Determine if query is about product or specific variant."""
        # If we have specific dimensions or detailed attributes, it's variant level
        if any(
            key in detected_attributes
            for key in ["thickness", "length", "width", "diameter", "grade"]
        ):
            return "variant"
        elif "product_type" in detected_attributes:
            return "product"
        else:
            return "ambiguous"

    def _build_next_clarification(
        self,
        clarification_stage: str,
        detected_attributes: Dict[str, Any],
        query_type: str,
    ) -> Optional[ClarificationNeeded]:
        """Build the next clarification needed based on current state."""
        if clarification_stage == "complete":
            return None

        # Priority order of clarifications
        if "product_type" not in detected_attributes:
            return ClarificationNeeded(
                attribute_type="product_type",
                question_template=(
                    "Produk baja apa yang Anda cari? " "(plat, hollow, besi beton, dll)"
                ),
                options=["plat", "hollow", "besi beton", "pipa", "profil"],
                priority=1,
            )

        variant_selection = query_type == "variant_selection"
        no_dimensions = "dimensions" not in detected_attributes
        if variant_selection and no_dimensions:
            product = detected_attributes.get("product_type", "produk")
            return ClarificationNeeded(
                attribute_type="dimensions",
                question_template=f"Ukuran {product} berapa yang Anda butuhkan?",
                options=[],
                priority=2,
                depends_on="product_type",
            )

        if query_type == "availability_check" and "material" not in detected_attributes:
            return ClarificationNeeded(
                attribute_type="material",
                question_template="Material apa yang Anda cari? (galvanis/hitam)",
                options=["galvanis", "hitam"],
                priority=3,
                depends_on="product_type",
            )

        return None

    def _get_conversation_turn(
        self, conversation_context: Optional[List[MessageDTO]]
    ) -> int:
        """Get the current conversation turn number."""
        if not conversation_context:
            return 1

        # Count all messages and divide by 2 (user + ai_agent pairs) then add 1
        # This represents the current turn being processed
        return len(conversation_context) // 2 + 1
