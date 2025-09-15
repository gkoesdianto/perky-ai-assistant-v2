"""
Unit tests for ProductServicePort protocol.
Tests the protocol contract using mock implementations from conftest.
"""

import pytest


@pytest.mark.asyncio
class TestMockProductServiceAdapter:
    """Test suite for Product Service port mock implementation."""

    async def test_search_products_empty_query(self, mock_product_service):
        """Test searching with empty query returns empty list."""
        mock_product_service.search_products_mock.return_value = []

        results = await mock_product_service.search_products("")

        assert results == []
        assert mock_product_service.call_count["search"] == 1
        assert mock_product_service.last_search_query == ""

    async def test_search_products_with_results(
        self, mock_product_service, sample_product_info
    ):
        """Test searching products returns matching results."""
        expected_products = [sample_product_info]
        mock_product_service.search_products_mock.return_value = expected_products

        results = await mock_product_service.search_products("plat baja")

        assert results == expected_products
        assert len(results) == 1
        assert results[0].product_name == "Plat Baja"
        assert mock_product_service.call_count["search"] == 1
        assert mock_product_service.last_search_query == "plat baja"

    async def test_search_products_indonesian_query(self, mock_product_service):
        """Test searching with Indonesian query."""
        query = "baja ringan untuk atap"
        mock_product_service.search_products_mock.return_value = []

        await mock_product_service.search_products(query)

        assert mock_product_service.last_search_query == query
        mock_product_service.search_products_mock.assert_called_once_with(query)

    async def test_get_product_with_variants_found(
        self, mock_product_service, sample_product_with_variants
    ):
        """Test getting product with variants when product exists."""
        mock_product_service.get_product_with_variants_mock.return_value = (
            sample_product_with_variants
        )

        result = await mock_product_service.get_product_with_variants("prod_plat_baja")

        assert result == sample_product_with_variants
        assert result.product.product_id == "prod_plat_baja"
        assert len(result.variants) == 2
        assert mock_product_service.call_count["get_variants"] == 1
        assert mock_product_service.last_product_id == "prod_plat_baja"

    async def test_get_product_with_variants_not_found(self, mock_product_service):
        """Test getting product with variants when product doesn't exist."""
        mock_product_service.get_product_with_variants_mock.return_value = None

        result = await mock_product_service.get_product_with_variants(
            "non_existent_product"
        )

        assert result is None
        assert mock_product_service.call_count["get_variants"] == 1
        assert mock_product_service.last_product_id == "non_existent_product"

    async def test_reset_functionality(self, mock_product_service):
        """Test reset clears all state."""
        mock_product_service.search_products_mock.return_value = []
        await mock_product_service.search_products("test query")
        await mock_product_service.get_product_with_variants("test_id")

        assert mock_product_service.call_count["search"] == 1
        assert mock_product_service.call_count["get_variants"] == 1
        assert mock_product_service.last_search_query == "test query"
        assert mock_product_service.last_product_id == "test_id"

        mock_product_service.reset()

        assert mock_product_service.call_count["search"] == 0
        assert mock_product_service.call_count["get_variants"] == 0
        assert mock_product_service.last_search_query is None
        assert mock_product_service.last_product_id is None
        mock_product_service.search_products_mock.assert_not_called()
        mock_product_service.get_product_with_variants_mock.assert_not_called()

    async def test_multiple_searches_tracking(self, mock_product_service):
        """Test tracking multiple search operations."""
        queries = ["baja", "plat", "besi"]
        mock_product_service.search_products_mock.return_value = []

        for i, query in enumerate(queries, 1):
            await mock_product_service.search_products(query)
            assert mock_product_service.call_count["search"] == i

        assert mock_product_service.last_search_query == "besi"

    async def test_protocol_compliance(self, mock_product_service):
        """Test that mock implementation satisfies the protocol."""
        assert hasattr(mock_product_service, "search_products")
        assert hasattr(mock_product_service, "get_product_with_variants")
        assert callable(mock_product_service.search_products)
        assert callable(mock_product_service.get_product_with_variants)

        # Verify method signatures match protocol
        import inspect

        search_sig = inspect.signature(mock_product_service.search_products)
        search_params = list(search_sig.parameters.keys())
        assert "query" in search_params

        get_sig = inspect.signature(mock_product_service.get_product_with_variants)
        get_params = list(get_sig.parameters.keys())
        assert "product_id" in get_params
