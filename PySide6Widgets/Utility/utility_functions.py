"""Implements small utility functions that do not fit anywhere else"""
import re

def snakecase(name : str):
    """Converts the passed tring to snakecase
    NOTE that _ is kept if already present in the string
    """
    return re.sub(r"(\w)([A-Z])", r"\1_\2", name).lower()

