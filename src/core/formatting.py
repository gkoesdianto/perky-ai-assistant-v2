"""Formatting utilities for the application."""

from decimal import Decimal


def format_rupiah(amount: Decimal) -> str:
    """Format amount as Indonesian Rupiah.

    Args:
        amount: The amount to format

    Returns:
        Formatted string like "Rp 1.500.000"

    Examples:
        >>> format_rupiah(Decimal("1500000"))
        'Rp 1.500.000'
        >>> format_rupiah(Decimal("150"))
        'Rp 150'
    """
    price_str = f"{amount:.0f}"
    formatted = ""
    for i, digit in enumerate(reversed(price_str)):
        if i > 0 and i % 3 == 0:
            formatted = "." + formatted
        formatted = digit + formatted
    return f"Rp {formatted}"
