"""
Mock implementation of ProductRepository for MVP development.
Provides hardcoded Indonesian steel product catalog without external dependencies.
"""

import asyncio
import os
from decimal import Decimal
from typing import Dict, List, Optional

from src.domain.repositories.product_repository import ProductRepository
from src.domain.value_objects import ProductInfo, VariantInfo
from src.domain.value_objects.product_with_variants_info import ProductWithVariantsInfo
from src.infrastructure.mocks.mock_error_simulator import MockErrorSimulator


class MockProductRepository(ProductRepository):
    """
    In-memory mock implementation of ProductRepository.
    Provides realistic Indonesian steel product catalog for MVP testing.
    Thread-safe for concurrent WebSocket connections.
    """

    def __init__(self):
        """Initialize with hardcoded Indonesian steel product catalog."""
        self._lock = asyncio.Lock()  # Thread safety for concurrent access
        self.products = self._create_mock_products()

        # Initialize error simulator from environment
        error_rate = float(os.getenv("MOCK_ERROR_RATE", "0.0"))
        delay_ms = int(os.getenv("MOCK_RESPONSE_DELAY_MS", "0"))
        self.error_simulator = MockErrorSimulator(error_rate, delay_ms)

        # Indonesian terminology mapping for search
        self.terminology_map = {
            # Common products
            "plat": ["plate", "sheet", "plat baja", "plat hitam", "plat galvanis"],
            "hollow": ["hollow", "kotak", "besi kotak", "besi hollow"],
            "kotak": ["hollow", "besi hollow", "besi kotak"],  # Map kotak to hollow
            "besi": ["iron", "steel", "besi baja", "besi beton"],
            "pipa": ["pipe", "tube", "pipa baja"],
            # Specific products
            "wf": ["wide flange", "h-beam", "profil wf", "beam"],
            "hbeam": ["h-beam", "wf", "wide flange", "beam"],
            "h beam": ["h-beam", "wf", "wide flange", "beam"],
            "unp": ["channel", "kanal u", "profil u"],
            "siku": ["angle", "angle bar", "besi siku"],
            "beton": ["rebar", "besi beton", "concrete steel"],
            # Actions
            "beli": ["buy", "purchase", "order"],
            "pesan": ["order", "request", "book"],
            "cek": ["check", "verify", "confirm"],
            "harga": ["price", "cost", "biaya"],
            "stok": ["stock", "inventory", "tersedia"],
        }

    def _create_mock_products(self) -> Dict[str, ProductWithVariantsInfo]:
        """Initialize realistic Indonesian steel product catalog."""
        products = {}

        # PROD-001: Plat Baja Hitam SS400 (Steel Plates)
        products["PROD-001"] = self._create_plat_baja()

        # PROD-002: Besi Hollow Galvanis (Galvanized Hollow)
        products["PROD-002"] = self._create_hollow_galvanis()

        # PROD-003: H-Beam WF (Structural Steel)
        products["PROD-003"] = self._create_h_beam()

        # PROD-004: Besi Beton (Rebar)
        products["PROD-004"] = self._create_besi_beton()

        # PROD-005: Pipa Baja (Steel Pipes)
        products["PROD-005"] = self._create_pipa_baja()

        return products

    def _create_plat_baja(self) -> ProductWithVariantsInfo:
        """Create Plat Baja Hitam SS400 product with variants."""
        product_info = ProductInfo(
            product_id="PROD-001",
            product_name="Plat Baja Hitam SS400",
            product_description="Plat baja kualitas SS400 untuk konstruksi umum dan fabrikasi",
            category="Plat",
            variant_count=8,
        )

        variants = [
            VariantInfo(
                variant_id="VAR-001-001",
                sku="PLT-2MM-4X8",
                product_id="PROD-001",
                variant_name="Plat Hitam 2mm x 1200mm x 2400mm",
                price=Decimal("450000"),
                stock_quantity=200,
                stock_unit="lembar",
                specifications={
                    "thickness": "2mm",
                    "width": "1200mm",
                    "length": "2400mm",
                    "weight": "45.12kg",
                    "grade": "SS400",
                    "standard": "JIS G3101",
                },
                source="pim",
                is_available=True,
            ),
            VariantInfo(
                variant_id="VAR-001-002",
                sku="PLT-3MM-4X8",
                product_id="PROD-001",
                variant_name="Plat Hitam 3mm x 1200mm x 2400mm",
                price=Decimal("675000"),
                stock_quantity=180,
                stock_unit="lembar",
                specifications={
                    "thickness": "3mm",
                    "width": "1200mm",
                    "length": "2400mm",
                    "weight": "67.68kg",
                    "grade": "SS400",
                    "standard": "JIS G3101",
                },
                source="pim",
                is_available=True,
            ),
            VariantInfo(
                variant_id="VAR-001-003",
                sku="PLT-4MM-4X8",
                product_id="PROD-001",
                variant_name="Plat Hitam 4mm x 1200mm x 2400mm",
                price=Decimal("900000"),
                stock_quantity=150,
                stock_unit="lembar",
                specifications={
                    "thickness": "4mm",
                    "width": "1200mm",
                    "length": "2400mm",
                    "weight": "90.24kg",
                    "grade": "SS400",
                    "standard": "JIS G3101",
                },
                source="pim",
                is_available=True,
            ),
            VariantInfo(
                variant_id="VAR-001-004",
                sku="PLT-5MM-4X8",
                product_id="PROD-001",
                variant_name="Plat Hitam 5mm x 1200mm x 2400mm",
                price=Decimal("1125000"),
                stock_quantity=150,
                stock_unit="lembar",
                specifications={
                    "thickness": "5mm",
                    "width": "1200mm",
                    "length": "2400mm",
                    "weight": "112.8kg",
                    "grade": "SS400",
                    "standard": "JIS G3101",
                },
                source="pim",
                is_available=True,
            ),
            VariantInfo(
                variant_id="VAR-001-005",
                sku="PLT-6MM-4X8",
                product_id="PROD-001",
                variant_name="Plat Hitam 6mm x 1200mm x 2400mm",
                price=Decimal("1350000"),
                stock_quantity=120,
                stock_unit="lembar",
                specifications={
                    "thickness": "6mm",
                    "width": "1200mm",
                    "length": "2400mm",
                    "weight": "135.36kg",
                    "grade": "SS400",
                    "standard": "JIS G3101",
                },
                source="pim",
                is_available=True,
            ),
            VariantInfo(
                variant_id="VAR-001-006",
                sku="PLT-8MM-4X8",
                product_id="PROD-001",
                variant_name="Plat Hitam 8mm x 1200mm x 2400mm",
                price=Decimal("1800000"),
                stock_quantity=100,
                stock_unit="lembar",
                specifications={
                    "thickness": "8mm",
                    "width": "1200mm",
                    "length": "2400mm",
                    "weight": "180.48kg",
                    "grade": "SS400",
                    "standard": "JIS G3101",
                },
                source="pim",
                is_available=True,
            ),
            VariantInfo(
                variant_id="VAR-001-007",
                sku="PLT-10MM-4X8",
                product_id="PROD-001",
                variant_name="Plat Hitam 10mm x 1200mm x 2400mm",
                price=Decimal("2250000"),
                stock_quantity=75,
                stock_unit="lembar",
                specifications={
                    "thickness": "10mm",
                    "width": "1200mm",
                    "length": "2400mm",
                    "weight": "225.6kg",
                    "grade": "SS400",
                    "standard": "JIS G3101",
                },
                source="pim",
                is_available=True,
            ),
            VariantInfo(
                variant_id="VAR-001-008",
                sku="PLT-12MM-4X8",
                product_id="PROD-001",
                variant_name="Plat Hitam 12mm x 1200mm x 2400mm",
                price=Decimal("2700000"),
                stock_quantity=50,
                stock_unit="lembar",
                specifications={
                    "thickness": "12mm",
                    "width": "1200mm",
                    "length": "2400mm",
                    "weight": "270.72kg",
                    "grade": "SS400",
                    "standard": "JIS G3101",
                },
                source="pim",
                is_available=True,
            ),
        ]

        return ProductWithVariantsInfo(product=product_info, variants=variants)

    def _create_hollow_galvanis(self) -> ProductWithVariantsInfo:
        """Create Besi Hollow Galvanis product with variants."""
        product_info = ProductInfo(
            product_id="PROD-002",
            product_name="Besi Hollow Galvanis",
            product_description="Hollow section galvanis untuk rangka dan konstruksi ringan",
            category="Hollow",
            variant_count=8,
        )

        variants = [
            VariantInfo(
                variant_id="VAR-002-001",
                sku="HLW-20X20-GLV",
                product_id="PROD-002",
                variant_name="Hollow Galvanis 20mm x 20mm x 6m",
                price=Decimal("45000"),
                stock_quantity=300,
                stock_unit="batang",
                specifications={
                    "size": "20mm x 20mm",
                    "thickness": "1.2mm",
                    "length": "6m",
                    "material": "Galvanis",
                    "weight": "3.6kg/batang",
                },
                source="pim",
                is_available=True,
            ),
            VariantInfo(
                variant_id="VAR-002-002",
                sku="HLW-30X30-GLV",
                product_id="PROD-002",
                variant_name="Hollow Galvanis 30mm x 30mm x 6m",
                price=Decimal("65000"),
                stock_quantity=250,
                stock_unit="batang",
                specifications={
                    "size": "30mm x 30mm",
                    "thickness": "1.4mm",
                    "length": "6m",
                    "material": "Galvanis",
                    "weight": "5.4kg/batang",
                },
                source="pim",
                is_available=True,
            ),
            VariantInfo(
                variant_id="VAR-002-003",
                sku="HLW-40X40-GLV",
                product_id="PROD-002",
                variant_name="Hollow Galvanis 40mm x 40mm x 6m",
                price=Decimal("85000"),
                stock_quantity=200,
                stock_unit="batang",
                specifications={
                    "size": "40mm x 40mm",
                    "thickness": "1.6mm",
                    "length": "6m",
                    "material": "Galvanis",
                    "weight": "7.2kg/batang",
                },
                source="pim",
                is_available=True,
            ),
            VariantInfo(
                variant_id="VAR-002-004",
                sku="HLW-50X50-GLV",
                product_id="PROD-002",
                variant_name="Hollow Galvanis 50mm x 50mm x 6m",
                price=Decimal("110000"),
                stock_quantity=150,
                stock_unit="batang",
                specifications={
                    "size": "50mm x 50mm",
                    "thickness": "1.8mm",
                    "length": "6m",
                    "material": "Galvanis",
                    "weight": "9.0kg/batang",
                },
                source="pim",
                is_available=True,
            ),
            VariantInfo(
                variant_id="VAR-002-005",
                sku="HLW-60X60-GLV",
                product_id="PROD-002",
                variant_name="Hollow Galvanis 60mm x 60mm x 6m",
                price=Decimal("145000"),
                stock_quantity=120,
                stock_unit="batang",
                specifications={
                    "size": "60mm x 60mm",
                    "thickness": "2.0mm",
                    "length": "6m",
                    "material": "Galvanis",
                    "weight": "11.2kg/batang",
                },
                source="pim",
                is_available=True,
            ),
            VariantInfo(
                variant_id="VAR-002-006",
                sku="HLW-75X75-GLV",
                product_id="PROD-002",
                variant_name="Hollow Galvanis 75mm x 75mm x 6m",
                price=Decimal("185000"),
                stock_quantity=100,
                stock_unit="batang",
                specifications={
                    "size": "75mm x 75mm",
                    "thickness": "2.3mm",
                    "length": "6m",
                    "material": "Galvanis",
                    "weight": "14.5kg/batang",
                },
                source="pim",
                is_available=True,
            ),
            VariantInfo(
                variant_id="VAR-002-007",
                sku="HLW-100X100-GLV",
                product_id="PROD-002",
                variant_name="Hollow Galvanis 100mm x 100mm x 6m",
                price=Decimal("320000"),
                stock_quantity=80,
                stock_unit="batang",
                specifications={
                    "size": "100mm x 100mm",
                    "thickness": "3.0mm",
                    "length": "6m",
                    "material": "Galvanis",
                    "weight": "24.0kg/batang",
                },
                source="pim",
                is_available=True,
            ),
            VariantInfo(
                variant_id="VAR-002-008",
                sku="HLW-40X80-GLV",
                product_id="PROD-002",
                variant_name="Hollow Rectangular Galvanis 40mm x 80mm x 6m",
                price=Decimal("125000"),
                stock_quantity=100,
                stock_unit="batang",
                specifications={
                    "size": "40mm x 80mm",
                    "thickness": "2.0mm",
                    "length": "6m",
                    "material": "Galvanis",
                    "weight": "10.8kg/batang",
                    "type": "Rectangular",
                },
                source="pim",
                is_available=True,
            ),
        ]

        return ProductWithVariantsInfo(product=product_info, variants=variants)

    def _create_h_beam(self) -> ProductWithVariantsInfo:
        """Create H-Beam WF product with variants."""
        product_info = ProductInfo(
            product_id="PROD-003",
            product_name="H-Beam WF",
            product_description="Wide Flange beam untuk struktur bangunan dan konstruksi berat",
            category="Profil",
            variant_count=7,
        )

        variants = [
            VariantInfo(
                variant_id="VAR-003-001",
                sku="HBEAM-100X100",
                product_id="PROD-003",
                variant_name="H-Beam 100x100x6x8mm",
                price=Decimal("350000"),
                stock_quantity=100,
                stock_unit="batang",
                specifications={
                    "size": "100x100x6x8mm",
                    "weight": "17.2kg/m",
                    "length": "12m",
                    "total_weight": "206.4kg",
                    "standard": "JIS G3192",
                },
                source="pim",
                is_available=True,
            ),
            VariantInfo(
                variant_id="VAR-003-002",
                sku="HBEAM-125X125",
                product_id="PROD-003",
                variant_name="H-Beam 125x125x6.5x9mm",
                price=Decimal("480000"),
                stock_quantity=80,
                stock_unit="batang",
                specifications={
                    "size": "125x125x6.5x9mm",
                    "weight": "23.8kg/m",
                    "length": "12m",
                    "total_weight": "285.6kg",
                    "standard": "JIS G3192",
                },
                source="pim",
                is_available=True,
            ),
            VariantInfo(
                variant_id="VAR-003-003",
                sku="HBEAM-150X150",
                product_id="PROD-003",
                variant_name="H-Beam 150x150x7x10mm",
                price=Decimal("620000"),
                stock_quantity=70,
                stock_unit="batang",
                specifications={
                    "size": "150x150x7x10mm",
                    "weight": "31.5kg/m",
                    "length": "12m",
                    "total_weight": "378kg",
                    "standard": "JIS G3192",
                },
                source="pim",
                is_available=True,
            ),
            VariantInfo(
                variant_id="VAR-003-004",
                sku="HBEAM-200X200",
                product_id="PROD-003",
                variant_name="H-Beam 200x200x8x12mm",
                price=Decimal("850000"),
                stock_quantity=50,
                stock_unit="batang",
                specifications={
                    "size": "200x200x8x12mm",
                    "weight": "49.9kg/m",
                    "length": "12m",
                    "total_weight": "598.8kg",
                    "standard": "JIS G3192",
                },
                source="pim",
                is_available=True,
            ),
            VariantInfo(
                variant_id="VAR-003-005",
                sku="HBEAM-250X250",
                product_id="PROD-003",
                variant_name="H-Beam 250x250x9x14mm",
                price=Decimal("1350000"),
                stock_quantity=40,
                stock_unit="batang",
                specifications={
                    "size": "250x250x9x14mm",
                    "weight": "72.4kg/m",
                    "length": "12m",
                    "total_weight": "868.8kg",
                    "standard": "JIS G3192",
                },
                source="pim",
                is_available=True,
            ),
            VariantInfo(
                variant_id="VAR-003-006",
                sku="HBEAM-300X300",
                product_id="PROD-003",
                variant_name="H-Beam 300x300x10x15mm",
                price=Decimal("1850000"),
                stock_quantity=30,
                stock_unit="batang",
                specifications={
                    "size": "300x300x10x15mm",
                    "weight": "94.0kg/m",
                    "length": "12m",
                    "total_weight": "1128kg",
                    "standard": "JIS G3192",
                },
                source="pim",
                is_available=True,
            ),
            VariantInfo(
                variant_id="VAR-003-007",
                sku="HBEAM-350X350",
                product_id="PROD-003",
                variant_name="H-Beam 350x350x12x19mm",
                price=Decimal("2650000"),
                stock_quantity=20,
                stock_unit="batang",
                specifications={
                    "size": "350x350x12x19mm",
                    "weight": "137kg/m",
                    "length": "12m",
                    "total_weight": "1644kg",
                    "standard": "JIS G3192",
                },
                source="pim",
                is_available=True,
            ),
        ]

        return ProductWithVariantsInfo(product=product_info, variants=variants)

    def _create_besi_beton(self) -> ProductWithVariantsInfo:
        """Create Besi Beton (Rebar) product with variants."""
        product_info = ProductInfo(
            product_id="PROD-004",
            product_name="Besi Beton",
            product_description="Besi beton ulir dan polos untuk tulangan konstruksi beton",
            category="Besi Beton",
            variant_count=9,
        )

        variants = [
            VariantInfo(
                variant_id="VAR-004-001",
                sku="BTN-6MM-12M",
                product_id="PROD-004",
                variant_name="Besi Beton Polos 6mm x 12m",
                price=Decimal("28000"),
                stock_quantity=500,
                stock_unit="batang",
                specifications={
                    "diameter": "6mm",
                    "length": "12m",
                    "type": "Polos (Plain)",
                    "weight": "2.66kg/batang",
                    "standard": "SNI 2052",
                },
                source="pim",
                is_available=True,
            ),
            VariantInfo(
                variant_id="VAR-004-002",
                sku="BTN-8MM-12M",
                product_id="PROD-004",
                variant_name="Besi Beton Polos 8mm x 12m",
                price=Decimal("48000"),
                stock_quantity=450,
                stock_unit="batang",
                specifications={
                    "diameter": "8mm",
                    "length": "12m",
                    "type": "Polos (Plain)",
                    "weight": "4.74kg/batang",
                    "standard": "SNI 2052",
                },
                source="pim",
                is_available=True,
            ),
            VariantInfo(
                variant_id="VAR-004-003",
                sku="BTN-10MM-12M",
                product_id="PROD-004",
                variant_name="Besi Beton Ulir 10mm x 12m",
                price=Decimal("75000"),
                stock_quantity=400,
                stock_unit="batang",
                specifications={
                    "diameter": "10mm",
                    "length": "12m",
                    "type": "Ulir (Deformed)",
                    "weight": "7.40kg/batang",
                    "standard": "SNI 2052",
                },
                source="pim",
                is_available=True,
            ),
            VariantInfo(
                variant_id="VAR-004-004",
                sku="BTN-12MM-12M",
                product_id="PROD-004",
                variant_name="Besi Beton Ulir 12mm x 12m",
                price=Decimal("108000"),
                stock_quantity=350,
                stock_unit="batang",
                specifications={
                    "diameter": "12mm",
                    "length": "12m",
                    "type": "Ulir (Deformed)",
                    "weight": "10.66kg/batang",
                    "standard": "SNI 2052",
                },
                source="pim",
                is_available=True,
            ),
            VariantInfo(
                variant_id="VAR-004-005",
                sku="BTN-13MM-12M",
                product_id="PROD-004",
                variant_name="Besi Beton Ulir 13mm x 12m",
                price=Decimal("128000"),
                stock_quantity=300,
                stock_unit="batang",
                specifications={
                    "diameter": "13mm",
                    "length": "12m",
                    "type": "Ulir (Deformed)",
                    "weight": "12.48kg/batang",
                    "standard": "SNI 2052",
                },
                source="pim",
                is_available=True,
            ),
            VariantInfo(
                variant_id="VAR-004-006",
                sku="BTN-16MM-12M",
                product_id="PROD-004",
                variant_name="Besi Beton Ulir 16mm x 12m",
                price=Decimal("192000"),
                stock_quantity=250,
                stock_unit="batang",
                specifications={
                    "diameter": "16mm",
                    "length": "12m",
                    "type": "Ulir (Deformed)",
                    "weight": "18.96kg/batang",
                    "standard": "SNI 2052",
                },
                source="pim",
                is_available=True,
            ),
            VariantInfo(
                variant_id="VAR-004-007",
                sku="BTN-19MM-12M",
                product_id="PROD-004",
                variant_name="Besi Beton Ulir 19mm x 12m",
                price=Decimal("270000"),
                stock_quantity=200,
                stock_unit="batang",
                specifications={
                    "diameter": "19mm",
                    "length": "12m",
                    "type": "Ulir (Deformed)",
                    "weight": "26.76kg/batang",
                    "standard": "SNI 2052",
                },
                source="pim",
                is_available=True,
            ),
            VariantInfo(
                variant_id="VAR-004-008",
                sku="BTN-22MM-12M",
                product_id="PROD-004",
                variant_name="Besi Beton Ulir 22mm x 12m",
                price=Decimal("360000"),
                stock_quantity=150,
                stock_unit="batang",
                specifications={
                    "diameter": "22mm",
                    "length": "12m",
                    "type": "Ulir (Deformed)",
                    "weight": "35.76kg/batang",
                    "standard": "SNI 2052",
                },
                source="pim",
                is_available=True,
            ),
            VariantInfo(
                variant_id="VAR-004-009",
                sku="BTN-25MM-12M",
                product_id="PROD-004",
                variant_name="Besi Beton Ulir 25mm x 12m",
                price=Decimal("465000"),
                stock_quantity=100,
                stock_unit="batang",
                specifications={
                    "diameter": "25mm",
                    "length": "12m",
                    "type": "Ulir (Deformed)",
                    "weight": "46.20kg/batang",
                    "standard": "SNI 2052",
                },
                source="pim",
                is_available=True,
            ),
        ]

        return ProductWithVariantsInfo(product=product_info, variants=variants)

    def _create_pipa_baja(self) -> ProductWithVariantsInfo:
        """Create Pipa Baja (Steel Pipes) product with variants."""
        product_info = ProductInfo(
            product_id="PROD-005",
            product_name="Pipa Baja",
            product_description="Pipa baja hitam dan galvanis untuk berbagai aplikasi industri",
            category="Pipa",
            variant_count=8,
        )

        variants = [
            VariantInfo(
                variant_id="VAR-005-001",
                sku="PIPA-1/2-SCH40",
                product_id="PROD-005",
                variant_name="Pipa Baja Hitam 1/2 inch Sch 40 x 6m",
                price=Decimal("85000"),
                stock_quantity=200,
                stock_unit="batang",
                specifications={
                    "size": "1/2 inch",
                    "od": "21.3mm",
                    "thickness": "2.77mm",
                    "schedule": "40",
                    "length": "6m",
                    "type": "Black Steel",
                    "weight": "7.8kg/batang",
                },
                source="pim",
                is_available=True,
            ),
            VariantInfo(
                variant_id="VAR-005-002",
                sku="PIPA-3/4-SCH40",
                product_id="PROD-005",
                variant_name="Pipa Baja Hitam 3/4 inch Sch 40 x 6m",
                price=Decimal("110000"),
                stock_quantity=180,
                stock_unit="batang",
                specifications={
                    "size": "3/4 inch",
                    "od": "26.7mm",
                    "thickness": "2.87mm",
                    "schedule": "40",
                    "length": "6m",
                    "type": "Black Steel",
                    "weight": "10.2kg/batang",
                },
                source="pim",
                is_available=True,
            ),
            VariantInfo(
                variant_id="VAR-005-003",
                sku="PIPA-1-SCH40",
                product_id="PROD-005",
                variant_name="Pipa Baja Hitam 1 inch Sch 40 x 6m",
                price=Decimal("145000"),
                stock_quantity=160,
                stock_unit="batang",
                specifications={
                    "size": "1 inch",
                    "od": "33.4mm",
                    "thickness": "3.38mm",
                    "schedule": "40",
                    "length": "6m",
                    "type": "Black Steel",
                    "weight": "15.6kg/batang",
                },
                source="pim",
                is_available=True,
            ),
            VariantInfo(
                variant_id="VAR-005-004",
                sku="PIPA-1.5-SCH40",
                product_id="PROD-005",
                variant_name="Pipa Baja Hitam 1.5 inch Sch 40 x 6m",
                price=Decimal("215000"),
                stock_quantity=140,
                stock_unit="batang",
                specifications={
                    "size": "1.5 inch",
                    "od": "48.3mm",
                    "thickness": "3.68mm",
                    "schedule": "40",
                    "length": "6m",
                    "type": "Black Steel",
                    "weight": "24.6kg/batang",
                },
                source="pim",
                is_available=True,
            ),
            VariantInfo(
                variant_id="VAR-005-005",
                sku="PIPA-2-SCH40",
                product_id="PROD-005",
                variant_name="Pipa Baja Hitam 2 inch Sch 40 x 6m",
                price=Decimal("280000"),
                stock_quantity=120,
                stock_unit="batang",
                specifications={
                    "size": "2 inch",
                    "od": "60.3mm",
                    "thickness": "3.91mm",
                    "schedule": "40",
                    "length": "6m",
                    "type": "Black Steel",
                    "weight": "33.0kg/batang",
                },
                source="pim",
                is_available=True,
            ),
            VariantInfo(
                variant_id="VAR-005-006",
                sku="PIPA-3-SCH40",
                product_id="PROD-005",
                variant_name="Pipa Baja Hitam 3 inch Sch 40 x 6m",
                price=Decimal("485000"),
                stock_quantity=100,
                stock_unit="batang",
                specifications={
                    "size": "3 inch",
                    "od": "88.9mm",
                    "thickness": "5.49mm",
                    "schedule": "40",
                    "length": "6m",
                    "type": "Black Steel",
                    "weight": "66.6kg/batang",
                },
                source="pim",
                is_available=True,
            ),
            VariantInfo(
                variant_id="VAR-005-007",
                sku="PIPA-4-SCH40",
                product_id="PROD-005",
                variant_name="Pipa Baja Hitam 4 inch Sch 40 x 6m",
                price=Decimal("720000"),
                stock_quantity=80,
                stock_unit="batang",
                specifications={
                    "size": "4 inch",
                    "od": "114.3mm",
                    "thickness": "6.02mm",
                    "schedule": "40",
                    "length": "6m",
                    "type": "Black Steel",
                    "weight": "94.8kg/batang",
                },
                source="pim",
                is_available=True,
            ),
            VariantInfo(
                variant_id="VAR-005-008",
                sku="PIPA-6-SCH40",
                product_id="PROD-005",
                variant_name="Pipa Baja Hitam 6 inch Sch 40 x 6m",
                price=Decimal("1350000"),
                stock_quantity=50,
                stock_unit="batang",
                specifications={
                    "size": "6 inch",
                    "od": "168.3mm",
                    "thickness": "7.11mm",
                    "schedule": "40",
                    "length": "6m",
                    "type": "Black Steel",
                    "weight": "165.6kg/batang",
                },
                source="pim",
                is_available=True,
            ),
        ]

        return ProductWithVariantsInfo(product=product_info, variants=variants)

    async def get_product_with_variants(
        self, product_id: str
    ) -> Optional[ProductWithVariantsInfo]:
        """
        Fetch product with all its variants.
        Thread-safe implementation with asyncio.Lock.
        """
        async with self._lock:
            return self.products.get(product_id)

    async def get_variant_by_sku(self, sku: str) -> Optional[VariantInfo]:
        """
        Fetch specific variant by SKU.
        Searches across all products for the matching SKU.
        """
        async with self._lock:
            for product in self.products.values():
                for variant in product.variants:
                    if variant.sku == sku:
                        return variant
            return None

    async def search_products(self, query: str) -> List[ProductInfo]:
        """
        Search products by name or description with Indonesian terminology support.
        Returns top 5 relevant products matching the query.
        """
        # Simulate potential errors and delays
        await self.error_simulator.maybe_delay()
        await self.error_simulator.maybe_fail("search_products")

        async with self._lock:
            query_lower = query.lower()
            results = []

            # Normalize query using terminology map
            normalized_queries = self._normalize_query(query_lower)

            for product_with_variants in self.products.values():
                product = product_with_variants.product
                score = 0

                # Check direct match in product name
                if query_lower in product.product_name.lower():
                    score += 10

                # Check normalized queries
                for norm_query in normalized_queries:
                    if norm_query in product.product_name.lower():
                        score += 8
                    if (
                        product.product_description
                        and norm_query in product.product_description.lower()
                    ):
                        score += 5
                    if product.category and norm_query in product.category.lower():
                        score += 3

                # Check variant names for matches
                for variant in product_with_variants.variants:
                    if query_lower in variant.variant_name.lower():
                        score += 2
                        break

                if score > 0:
                    results.append((score, product))

            # Sort by score and return top 5
            results.sort(key=lambda x: x[0], reverse=True)
            return [product for _, product in results[:5]]

    async def get_variants_by_product(self, product_id: str) -> List[VariantInfo]:
        """
        Fetch all variants for a product.
        Returns empty list if product not found.
        """
        async with self._lock:
            product_with_variants = self.products.get(product_id)
            if product_with_variants:
                return product_with_variants.variants
            return []

    def _normalize_query(self, query: str) -> List[str]:
        """
        Normalize Indonesian terminology to include related terms.
        Returns list of terms that should match the query intent.
        """
        normalized = [query]  # Always include original query

        # Check each word in the query against terminology map
        words = query.split()
        for word in words:
            if word in self.terminology_map:
                normalized.extend(self.terminology_map[word])

        # Check full query against terminology map
        if query in self.terminology_map:
            normalized.extend(self.terminology_map[query])

        # Remove duplicates while preserving order
        seen = set()
        result = []
        for item in normalized:
            if item not in seen:
                seen.add(item)
                result.append(item)

        return result
