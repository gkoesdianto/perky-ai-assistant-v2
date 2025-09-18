import pytest

from src.application.dto import ProductQueryDTO, ProductResponseDTO


class TestProductQueryDTO:
    def test_create_product_query_dto_with_defaults(self):
        dto = ProductQueryDTO(query="plat baja 5mm", session_id="session-001")

        assert dto.query == "plat baja 5mm"
        assert dto.session_id == "session-001"
        assert dto.include_variants is True
        assert dto.max_results == 10

    def test_create_product_query_dto_with_all_fields(self):
        dto = ProductQueryDTO(
            query="pipa stainless",
            session_id="session-002",
            include_variants=False,
            max_results=20,
        )

        assert dto.query == "pipa stainless"
        assert dto.session_id == "session-002"
        assert dto.include_variants is False
        assert dto.max_results == 20

    @pytest.mark.parametrize("include_variants", [True, False])
    def test_include_variants_options(self, include_variants):
        dto = ProductQueryDTO(
            query="test query",
            session_id="session-test",
            include_variants=include_variants,
        )

        assert dto.include_variants == include_variants

    @pytest.mark.parametrize("max_results", [1, 5, 10, 50, 100])
    def test_max_results_values(self, max_results):
        dto = ProductQueryDTO(
            query="test query", session_id="session-test", max_results=max_results
        )

        assert dto.max_results == max_results


class TestProductResponseDTO:
    def test_create_product_response_dto(self):
        products = [
            {"id": "prod-001", "name": "Steel Plate", "price": 150000},
            {"id": "prod-002", "name": "Steel Pipe", "price": 200000},
        ]

        dto = ProductResponseDTO(
            products=products,
            query="steel products",
            response_time_ms=250,
            source="pim",
        )

        assert dto.products == products
        assert len(dto.products) == 2
        assert dto.query == "steel products"
        assert dto.response_time_ms == 250
        assert dto.source == "pim"

    def test_create_product_response_dto_empty_products(self):
        dto = ProductResponseDTO(
            products=[],
            query="unavailable product",
            response_time_ms=100,
            source="cache",
        )

        assert dto.products == []
        assert len(dto.products) == 0
        assert dto.source == "cache"

    @pytest.mark.parametrize("source", ["pim", "cache", "mock"])
    def test_valid_source_types(self, source):
        dto = ProductResponseDTO(
            products=[], query="test", response_time_ms=50, source=source
        )

        assert dto.source == source

    def test_product_response_with_complex_product_data(self):
        products = [
            {
                "id": "prod-003",
                "name": "Premium Steel Sheet",
                "price": 500000,
                "variants": [
                    {"size": "5mm", "stock": 100},
                    {"size": "10mm", "stock": 50},
                ],
                "metadata": {"category": "steel", "grade": "SS400"},
            }
        ]

        dto = ProductResponseDTO(
            products=products, query="premium steel", response_time_ms=300, source="pim"
        )

        assert dto.products[0]["id"] == "prod-003"
        assert dto.products[0]["variants"][0]["size"] == "5mm"
        assert dto.products[0]["metadata"]["category"] == "steel"
