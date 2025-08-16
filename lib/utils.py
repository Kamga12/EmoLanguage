#!/usr/bin/env python3
"""
EmoLanguage Utility Functions Module

This module provides essential utility functions for the emoji mapping system,
including prompt formatting, text processing, data analysis, and validation.
These functions are designed to be lightweight, reusable, and support the
core functionality across multiple system components.

Functional Areas:
    - Prompt Formatting: Functions for preparing LLM prompts with proper structure
    - Text Processing: String manipulation and truncation utilities  
    - Data Conversion: Transform between different mapping data structures
    - Analysis & Reporting: Generate statistics and reports on mapping results
    - Validation: Ensure data integrity and completeness

Dependencies:
    - Only imports TYPE_CHECKING from lib/file_manager to avoid circular imports
    - Uses late imports within functions where necessary

Author: EmoLanguage Team
Version: 2.0.0
"""

import logging
from typing import Dict, List, Set, TYPE_CHECKING, Optional, Union

if TYPE_CHECKING:
    from .file_manager import NewMapping

logger = logging.getLogger(__name__)

# =============================================================================
# TEXT PROCESSING UTILITIES
# =============================================================================

def truncate_emoji_list_for_logging(emoji_list: str, max_length: int = 100) -> str:
    """Truncate a long emoji sequence for safe logging display.
    
    Prevents log messages from becoming unwieldy when displaying large sets
    of emoji data. Preserves readability while providing length information.
    
    Args:
        emoji_list: The emoji string to potentially truncate
        max_length: Maximum character length before truncation
        
    Returns:
        Original string if within limits, otherwise truncated with suffix info
        
    Example:
        >>> truncate_emoji_list_for_logging("😀😁😂😃" * 50, 20)
        '😀😁😂😃😀😁😂... [TRUNCATED - 180 more characters]'
    """
    if len(emoji_list) > max_length:
        remaining_chars = len(emoji_list) - max_length
        return emoji_list[:max_length] + f"... [TRUNCATED - {remaining_chars} more characters]"
    return emoji_list

# =============================================================================
# PROMPT FORMATTING UTILITIES
# =============================================================================

def format_words_for_prompt(words: List[str]) -> str:
    """Format a list of words into numbered list format for LLM prompts.
    
    Creates a structured, numbered list that LLMs can easily parse and
    maintain order consistency in their responses.
    
    Args:
        words: List of words to format
        
    Returns:
        Formatted string with numbered entries, one per line
        
    Example:
        >>> format_words_for_prompt(["cat", "dog", "tree"])
        '1. cat\\n2. dog\\n3. tree'
    """
    if not words:
        return ""
    return "\n".join([f"{i+1}. {word}" for i, word in enumerate(words)])

def format_existing_emojis_for_prompt(existing_emojis: Set[str]) -> str:
    """Format existing emoji set for basic LLM prompt inclusion.
    
    Provides a simple comma-separated list of existing emojis to help
    the LLM avoid duplicates during generation.
    
    Args:
        existing_emojis: Set of emoji strings already in use
        
    Returns:
        Comma-separated string of emojis, or explanatory text if empty
        
    Example:
        >>> format_existing_emojis_for_prompt({"🐱", "🐶", "🌳"})
        '🐱, 🐶, 🌳'
    """
    if not existing_emojis:
        return "None (these are the first mappings)"
    
    emoji_list = sorted(list(existing_emojis))  # Sort for consistency
    return ", ".join(emoji_list)

def format_existing_emojis_for_collision_prompt(existing_emojis: Set[str], max_emojis: int = 100) -> str:
    """Format existing emojis for collision resolution with smart truncation.
    
    Specifically designed for collision resolution prompts where context length
    is critical. Limits the number of emojis shown while preserving essential
    information for the LLM to avoid creating new collisions.
    
    Args:
        existing_emojis: Set of emoji strings already in use
        max_emojis: Maximum number of emojis to include before truncation
        
    Returns:
        Formatted string with truncation info if needed
        
    Example:
        >>> emojis = {f"emoji_{i}" for i in range(150)}
        >>> result = format_existing_emojis_for_collision_prompt(emojis, 3)
        >>> "TRUNCATED - 147 more emojis" in result
        True
    """
    if not existing_emojis:
        return "None (these are the first mappings)"
    
    emoji_list = sorted(list(existing_emojis))  # Sort for consistency
    
    # Truncate if too many emojis to prevent context length overflow
    if len(emoji_list) > max_emojis:
        truncated_list = emoji_list[:max_emojis]
        remaining_count = len(emoji_list) - max_emojis
        result = ", ".join(truncated_list) + f", ... [TRUNCATED - {remaining_count} more emojis not shown to prevent context overflow]"
        return result
    
    return ", ".join(emoji_list)

def truncate_prompt_for_logging(prompt: str, max_emoji_display: int = 100) -> str:
    """Intelligently truncate emoji content in prompts for readable logging.
    
    Scans through prompt lines and selectively truncates emoji lists while
    preserving the overall prompt structure. Essential for debugging without
    overwhelming log files with massive emoji sequences.
    
    Args:
        prompt: The complete prompt text to process
        max_emoji_display: Maximum characters to show for emoji sequences
        
    Returns:
        Prompt with emoji lists truncated for logging readability
        
    Note:
        Specifically looks for lines containing existing_emojis patterns
        and applies truncation only to those sections.
    """
    if not prompt:
        return prompt
        
    prompt_lines = prompt.split('\n')
    truncated_prompt_lines = []
    
    for line in prompt_lines:
        # Check for existing emoji list patterns in the prompt
        if (line.startswith('{{existing_emojis}}:') or 
            line.startswith('{existing_emojis}:') or
            'existing_emojis' in line and ':' in line):
            
            # Extract and potentially truncate the emoji portion
            if ': ' in line:
                prefix, emoji_part = line.split(': ', 1)
                if len(emoji_part) > max_emoji_display:
                    truncated_part = truncate_emoji_list_for_logging(emoji_part, max_emoji_display)
                    truncated_prompt_lines.append(f"{prefix}: {truncated_part}")
                else:
                    truncated_prompt_lines.append(line)
            else:
                truncated_prompt_lines.append(line)
        else:
            truncated_prompt_lines.append(line)
    
    return '\n'.join(truncated_prompt_lines)

# =============================================================================
# ANALYSIS AND REPORTING UTILITIES
# =============================================================================

def analyze_mappings(mappings: List['NewMapping']) -> Dict[str, Union[int, float, Dict[str, int]]]:
    """Generate comprehensive statistics on mapping generation results.
    
    Provides detailed analysis of mapping success rates, category distribution,
    and overall generation quality metrics for reporting and optimization.
    
    Args:
        mappings: List of NewMapping objects to analyze
        
    Returns:
        Dictionary containing analysis metrics:
        - total_mappings: Total number of mapping attempts
        - successful_mappings: Count of mappings with non-empty emojis
        - category_counts: Breakdown by mapping category
        - success_rate: Percentage of successful mappings (0.0 to 1.0)
        
    Example:
        >>> from lib.file_manager import NewMapping
        >>> mappings = [NewMapping("cat", "🐱", "batch"), NewMapping("dog", "", "error")]
        >>> stats = analyze_mappings(mappings)
        >>> stats['success_rate']
        0.5
    """
    if not mappings:
        return {
            'total_mappings': 0,
            'successful_mappings': 0,
            'category_counts': {},
            'success_rate': 0.0
        }
    
    total_mappings = len(mappings)
    successful_mappings = [m for m in mappings if m.suggested_emojis]
    
    # Count mappings by category for detailed breakdown
    category_counts: Dict[str, int] = {}
    for mapping in mappings:
        category = mapping.category or 'uncategorized'
        category_counts[category] = category_counts.get(category, 0) + 1
    
    return {
        'total_mappings': total_mappings,
        'successful_mappings': len(successful_mappings),
        'category_counts': category_counts,
        'success_rate': len(successful_mappings) / total_mappings if total_mappings > 0 else 0.0
    }

def create_generation_report(mappings: List['NewMapping']) -> str:
    """Generate a comprehensive markdown report of mapping generation results.
    
    Creates a formatted report suitable for documentation, debugging, or
    presentation purposes. Includes overview statistics, category breakdown,
    and sample mappings for quality assessment.
    
    Args:
        mappings: List of NewMapping objects to report on
        
    Returns:
        Markdown-formatted report string
        
    Features:
        - Executive summary with key metrics
        - Detailed category breakdown
        - Sample mappings table for quality review
        - Handles empty mapping lists gracefully
    """
    if not mappings:
        return "# Emoji Mapping Generation Report\n\n**No mappings to report.**\n"
        
    analysis = analyze_mappings(mappings)
    
    report = f"""# Emoji Mapping Generation Report

## Executive Summary
- **Total words processed**: {analysis['total_mappings']:,}
- **Successful mappings**: {analysis['successful_mappings']:,}
- **Success rate**: {analysis['success_rate']:.1%}
- **Failed mappings**: {analysis['total_mappings'] - analysis['successful_mappings']:,}

## Category Distribution
"""
    
    # Sort categories by count for better readability
    sorted_categories = sorted(analysis['category_counts'].items(), 
                             key=lambda x: x[1], reverse=True)
    
    for category, count in sorted_categories:
        percentage = (count / analysis['total_mappings']) * 100
        report += f"- **{category}**: {count:,} ({percentage:.1f}%)\n"
    
    # Add sample mappings section
    sample_size = min(20, len(mappings))
    report += f"\n## Sample Mappings (showing {sample_size} of {len(mappings)})"
    report += "\n\n| Word | Emoji | Category |\n|------|--------|----------|\n"
    
    for mapping in mappings[:sample_size]:
        emoji_display = mapping.suggested_emojis if mapping.suggested_emojis else "*[empty]*"
        category_display = mapping.category or "uncategorized"
        report += f"| {mapping.word} | {emoji_display} | {category_display} |\n"
    
    if len(mappings) > sample_size:
        remaining = len(mappings) - sample_size
        report += f"\n*... and {remaining:,} additional mappings*\n"
    
    return report

# =============================================================================
# VALIDATION UTILITIES
# =============================================================================

def validate_word_mappings(word_mappings: Dict[str, str], expected_words: List[str]) -> List[str]:
    """Validate completeness of word-to-emoji mappings against expected input.
    
    Performs comprehensive validation to ensure all expected words received
    emoji mappings and identifies any gaps that need attention. Critical for
    quality assurance in batch processing workflows.
    
    Args:
        word_mappings: Dictionary containing word -> emoji mappings from LLM
        expected_words: Complete list of words that should have been mapped
        
    Returns:
        List of words that are missing mappings or have empty emoji values
        
    Side Effects:
        Logs error messages for any validation failures found
        
    Example:
        >>> mappings = {"cat": "🐱", "dog": "", "bird": "🐦"}
        >>> expected = ["cat", "dog", "bird", "fish"]
        >>> missing = validate_word_mappings(mappings, expected)
        >>> missing
        ['dog', 'fish']
    """
    if not expected_words:
        return []
        
    missing_words = []
    
    for word in expected_words:
        if word not in word_mappings:
            missing_words.append(word)
            logger.warning(f"Word '{word}' completely missing from LLM response")
        elif not word_mappings[word] or not word_mappings[word].strip():
            missing_words.append(word)
            logger.warning(f"Word '{word}' has empty or whitespace-only emoji mapping")
    
    if missing_words:
        logger.error(f"VALIDATION FAILURE: {len(missing_words)} words missing valid mappings: {missing_words[:10]}{'...' if len(missing_words) > 10 else ''}")
    else:
        logger.info(f"✅ Validation passed: All {len(expected_words)} expected words have valid emoji mappings")
    
    return missing_words

# =============================================================================
# DATA CONVERSION UTILITIES
# =============================================================================

def convert_word_mappings_to_new_mappings(word_mappings: Dict[str, str], 
                                        expected_words: List[str], 
                                        category: str = 'batch') -> List['NewMapping']:
    """Transform word-emoji dictionary into structured NewMapping objects.
    
    Converts the raw dictionary output from LLM processing into the structured
    NewMapping format used throughout the system. Handles missing mappings
    gracefully by creating error entries that can be tracked and reprocessed.
    
    Args:
        word_mappings: Raw dictionary of word -> emoji mappings from LLM
        expected_words: Complete list of words that should be represented
        category: Classification category for these mappings (e.g., 'batch', 'collision')
        
    Returns:
        List of NewMapping objects, one per expected word
        
    Features:
        - Preserves word order from expected_words list
        - Creates error mappings for missing/empty entries
        - Applies consistent categorization
        - Provides detailed logging for troubleshooting
        
    Example:
        >>> word_dict = {"cat": "🐱", "dog": "🐶"}
        >>> expected = ["cat", "dog", "bird"]
        >>> mappings = convert_word_mappings_to_new_mappings(word_dict, expected, "test")
        >>> [(m.word, m.suggested_emojis, m.category) for m in mappings]
        [('cat', '🐱', 'test'), ('dog', '🐶', 'test'), ('bird', '', 'error')]
    """
    # Late import to avoid circular dependency
    from .file_manager import NewMapping
    
    if not expected_words:
        logger.info("No expected words provided, returning empty mapping list")
        return []
    
    mappings = []
    successful_count = 0
    error_count = 0
    
    # Process each expected word in order
    for word in expected_words:
        word_clean = word.strip() if word else ""
        
        if word_clean and word_clean in word_mappings and word_mappings[word_clean]:
            # Successful mapping found
            emoji = word_mappings[word_clean].strip()
            if emoji:  # Double-check emoji is not just whitespace
                mappings.append(NewMapping(
                    word=word_clean,
                    suggested_emojis=emoji,
                    category=category
                ))
                successful_count += 1
            else:
                # Edge case: mapping exists but is empty/whitespace
                logger.warning(f"Word '{word_clean}' has whitespace-only emoji, creating error mapping")
                mappings.append(NewMapping(
                    word=word_clean,
                    suggested_emojis='',
                    category='error'
                ))
                error_count += 1
        else:
            # Missing or empty mapping - create error entry for reprocessing
            reason = "missing from response" if word_clean not in word_mappings else "has empty emoji value"
            logger.error(f"Creating error mapping for '{word_clean}': {reason}")
            mappings.append(NewMapping(
                word=word_clean,
                suggested_emojis='',
                category='error'
            ))
            error_count += 1
    
    logger.info(f"Conversion complete: {successful_count} successful mappings, {error_count} error mappings from {len(expected_words)} expected words")
    return mappings
