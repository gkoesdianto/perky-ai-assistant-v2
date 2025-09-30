"""Indonesian language templates for B2B steel product communication.

This module provides professional Indonesian templates for:
- Greetings and introductions
- Product inquiries and responses
- Stock availability messages
- Price information formatting
- Error handling and clarifications
- Variant selection guidance
- Unit formatting
- Conversation closings
"""

GREETING_TEMPLATES = {
    "morning": (
        "Selamat pagi! Saya PERKY, asisten digital SMS Perkasa. "
        "Ada yang bisa saya bantu hari ini?"
    ),
    "afternoon": (
        "Selamat siang! Terima kasih telah menghubungi SMS Perkasa. "
        "Produk baja apa yang Anda cari?"
    ),
    "evening": ("Selamat sore! Saya PERKY, siap membantu kebutuhan produk baja Anda."),
    "default": ("Selamat datang di SMS Perkasa! Saya PERKY, asisten produk baja Anda."),
}

PRODUCT_INQUIRY_TEMPLATES = {
    "availability": (
        "Baik, saya akan cek ketersediaan varian {variant_name} untuk Anda."
    ),
    "specifications": "Berikut spesifikasi lengkap untuk {variant_name}:",
    "pricing": ("Untuk {variant_name}, harga per {stock_unit}: {display_price}"),
    "pricing_inquiry": (
        "Produk {product_name} memiliki beberapa varian. "
        "Varian mana yang Anda butuhkan?"
    ),
    "variant_options": ("Produk {product_name} tersedia dalam {variant_count} varian:"),
    "variant_list": (
        "- {variant_name}: {display_price} per {stock_unit} " "(Stok: {stock_quantity})"
    ),
    "recommendation": (
        "Berdasarkan kebutuhan Anda, saya merekomendasikan produk berikut:"
    ),
}

STOCK_MESSAGES = {
    "in_stock": "✅ {variant_name} tersedia: {stock_quantity} {stock_unit}",
    "low_stock": (
        "⚠️ Stok {variant_name} terbatas: tersisa {stock_quantity} {stock_unit}"
    ),
    "out_of_stock": "❌ Mohon maaf, stok {variant_name} sedang kosong",
    "product_stock_summary": (
        "Stok {product_name}: {available_variants} dari {total_variants} "
        "varian tersedia"
    ),
    "all_variants_available": "✅ Semua varian {product_name} tersedia",
    "some_variants_available": "⚠️ Beberapa varian {product_name} tersedia",
    "no_variants_available": "❌ Semua varian {product_name} sedang kosong",
}

PRICE_TEMPLATES = {
    "unit_price": "{display_price} per {stock_unit}",
    "total_price": "Total untuk {quantity} {stock_unit}: {total_price}",
    "price_range": (
        "Harga {product_name}: {min_price} - {max_price} (tergantung varian)"
    ),
    "volume_discount": (
        "Diskon {discount_percentage}% untuk pembelian di atas "
        "{min_quantity} {stock_unit}"
    ),
    "final_price_with_discount": (
        "Harga setelah diskon: {final_price} (hemat {discount_amount})"
    ),
}

ERROR_MESSAGES = {
    "product_not_found": (
        "Maaf, produk {product_name} tidak ditemukan dalam katalog kami."
    ),
    "variant_not_found": (
        "Maaf, varian {variant_spec} tidak tersedia untuk produk " "{product_name}."
    ),
    "variant_out_of_stock": (
        "Mohon maaf, stok {variant_name} sedang kosong. " "Estimasi tersedia {date}."
    ),
    "insufficient_stock": (
        "Stok {variant_name} tidak mencukupi. " "Tersedia: {available} {stock_unit}"
    ),
    "system_error": (
        "Mohon maaf, terjadi kesalahan sistem. " "Tim kami akan segera memperbaikinya."
    ),
    "clarification": (
        "Mohon maaf, saya perlu informasi lebih detail. "
        "Bisa tolong jelaskan spesifikasi yang Anda butuhkan?"
    ),
    "variant_selection_needed": (
        "Produk {product_name} memiliki beberapa varian. "
        "Mohon pilih spesifikasi yang Anda inginkan:"
    ),
    "specification_needed": (
        "Untuk memberikan harga yang tepat, saya perlu tahu spesifikasi: "
        "{required_specs}"
    ),
}

VARIANT_SELECTION_TEMPLATES = {
    "thickness_selection": "Pilih ketebalan yang dibutuhkan: {available_thicknesses}",
    "size_selection": "Pilih ukuran yang dibutuhkan: {available_sizes}",
    "material_selection": "Pilih grade material: {available_materials}",
    "confirm_variant": "Apakah Anda memilih {variant_name}? (SKU: {sku})",
    "variant_details": """
{variant_name}
- SKU: {sku}
- Harga: {display_price}/{stock_unit}
- Stok: {stock_quantity} {stock_unit}
- Spesifikasi: {specifications}
""",
}

UNIT_TEMPLATES = {
    "lembar": "lembar (sheet)",
    "batang": "batang (bar/rod)",
    "kg": "kilogram",
    "meter": "meter",
    "roll": "roll",
    "unit": "unit",
    "pcs": "pcs (pieces)",
    "quantity_format": "{quantity} {stock_unit}",
    "minimum_order": "Minimum order: {min_quantity} {stock_unit}",
}

CLOSING_TEMPLATES = {
    "order_ready": (
        "Terima kasih! Pesanan Anda siap diproses. "
        "Tim sales kami akan menghubungi Anda segera."
    ),
    "need_help": "Ada yang bisa saya bantu lagi?",
    "thank_you": (
        "Terima kasih telah menghubungi SMS Perkasa. " "Semoga hari Anda menyenangkan!"
    ),
}
