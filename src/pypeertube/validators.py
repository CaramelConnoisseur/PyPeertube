"""Validators for Peertube."""

from re import match


def channel_name(value: str) -> bool:
    """Validate a Peertube channel name.

    Args:
        value (str): The proposed channel name.

    Returns:
        bool: Whether the channel name is valid.
    """

    return bool(match(r"^[0-9a-z_.]{1,50}$", value))
