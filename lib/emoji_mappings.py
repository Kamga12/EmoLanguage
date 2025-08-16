"""Emoji mapping utilities for the EmoLanguage system.

This module provides shared utilities for loading, managing, and accessing
word-to-emoji mappings used by both the encoder and decoder modules.
"""

import json
from pathlib import Path
from typing import Dict, Tuple

from .config import MAPPING_FILE_PATH


def load_emoji_mappings() -> Tuple[Dict[str, str], Dict[str, str]]:
    """Load word-to-emoji mappings from file.
    
    Returns:
        Tuple of (word_to_emoji, emoji_to_word) dictionaries
        
    Raises:
        FileNotFoundError: If mapping file doesn't exist
        json.JSONDecodeError: If mapping file is invalid JSON
    """
    mapping_path = Path(MAPPING_FILE_PATH)
    
    try:
        with open(mapping_path, encoding='utf-8') as f:
            word_to_emoji = json.load(f)
    except FileNotFoundError:
        raise FileNotFoundError(
            f"Mapping file not found: {mapping_path}. "
            "Run build_mapping.py to generate mappings first."
        )
    
    # Build reverse mapping for decoding
    emoji_to_word = {v: k for k, v in word_to_emoji.items()}
    
    return word_to_emoji, emoji_to_word


def get_cached_mappings() -> Tuple[Dict[str, str], Dict[str, str]]:
    """Get cached emoji mappings, loading them if necessary.
    
    This function provides a singleton-like interface to emoji mappings,
    loading them once and caching them for subsequent calls.
    
    Returns:
        Tuple of (word_to_emoji, emoji_to_word) dictionaries
    """
    if not hasattr(get_cached_mappings, '_cached_mappings'):
        get_cached_mappings._cached_mappings = load_emoji_mappings()
    
    return get_cached_mappings._cached_mappings


def clear_mapping_cache() -> None:
    """Clear the cached emoji mappings.
    
    This forces the next call to get_cached_mappings() to reload the mappings
    from file. Useful when mappings have been updated on disk.
    """
    if hasattr(get_cached_mappings, '_cached_mappings'):
        delattr(get_cached_mappings, '_cached_mappings')


def get_word_to_emoji() -> Dict[str, str]:
    """Get the word-to-emoji mapping dictionary.
    
    Returns:
        Dictionary mapping words to emoji sequences
    """
    word_to_emoji, _ = get_cached_mappings()
    return word_to_emoji


def get_emoji_to_word() -> Dict[str, str]:
    """Get the emoji-to-word mapping dictionary.
    
    Returns:
        Dictionary mapping emoji sequences to words
    """
    _, emoji_to_word = get_cached_mappings()
    return emoji_to_word
