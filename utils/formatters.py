"""
Customer Insights Platform – Number and string formatting utilities.
"""

from __future__ import annotations


def fmt_currency(value: float | int, symbol: str = "$") -> str:
    """Format a number as USD currency: $1,234.56"""
    try:
        return f"{symbol}{float(value):,.2f}"
    except (TypeError, ValueError):
        return f"{symbol}0.00"


def fmt_number(value: float | int) -> str:
    """Format a number with thousands separators: 12,345"""
    try:
        return f"{int(value):,}"
    except (TypeError, ValueError):
        return "0"


def fmt_percent(value: float | int, decimals: int = 1) -> str:
    """Format a float as percentage: 12.3%"""
    try:
        return f"{float(value):.{decimals}f}%"
    except (TypeError, ValueError):
        return "0.0%"


def fmt_large(value: float | int) -> str:
    """Compact large number formatting: 1.2M, 45K, etc."""
    try:
        v = float(value)
        if abs(v) >= 1_000_000:
            return f"{v/1_000_000:.1f}M"
        if abs(v) >= 1_000:
            return f"{v/1_000:.1f}K"
        return f"{v:.0f}"
    except (TypeError, ValueError):
        return "0"


def fmt_delta(current: float, previous: float) -> tuple[str, bool]:
    """
    Calculate percentage change between two values.
    Returns (formatted_string, is_positive).
    """
    try:
        if not previous or previous == 0:
            return "0.0%", True
        change = (current - previous) / abs(previous) * 100
        return f"{abs(change):.1f}%", change >= 0
    except (TypeError, ValueError, ZeroDivisionError):
        return "0.0%", True
