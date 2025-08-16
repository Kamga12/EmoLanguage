#!/usr/bin/env python3
"""
Enhanced Semantic Categorization for Improved Mapping Quality

This module provides word categorization and context-aware prompting
to improve emoji mapping quality based on semantic characteristics.
"""

import re
from typing import Dict, List, Set, Tuple, Optional
from enum import Enum
from dataclasses import dataclass

class WordCategory(Enum):
    """Semantic categories for different mapping strategies"""
    CONCRETE_OBJECT = "concrete_object"      # Physical objects: car, book, apple
    ABSTRACT_CONCEPT = "abstract_concept"    # Ideas: freedom, justice, love
    ACTION_VERB = "action_verb"              # Actions: run, jump, think
    DESCRIPTIVE_ADJ = "descriptive_adj"      # Adjectives: red, big, beautiful
    PROPER_NOUN = "proper_noun"              # Names: John, Paris, Apple Inc.
    TECHNICAL_TERM = "technical_term"        # Specialized: algorithm, enzyme
    COMPOUND_WORD = "compound_word"          # Multi-part: sunflower, keyboard
    SINGLE_LETTER = "single_letter"          # Letters: a, b, x
    NUMERIC = "numeric"                      # Numbers: one, twelve, hundred
    ONOMATOPOEIA = "onomatopoeia"           # Sounds: bang, whisper, meow

@dataclass
class WordAnalysis:
    """Analysis result for a word"""
    word: str
    category: WordCategory
    confidence: float
    reasoning: str
    suggested_strategy: str

class SemanticCategorizer:
    """Categorizes words for optimal emoji mapping strategies"""
    
    def __init__(self):
        # Concrete object patterns
        self.concrete_patterns = {
            'tools': ['hammer', 'screwdriver', 'wrench', 'drill', 'saw'],
            'vehicles': ['car', 'truck', 'bike', 'plane', 'train'],
            'animals': ['cat', 'dog', 'bird', 'fish', 'lion'],
            'food': ['apple', 'bread', 'cheese', 'pizza', 'cake'],
            'furniture': ['chair', 'table', 'bed', 'sofa', 'desk'],
            'clothing': ['shirt', 'pants', 'dress', 'hat', 'shoe']
        }
        
        # Abstract concept patterns
        self.abstract_patterns = {
            'emotions': ['love', 'hate', 'fear', 'joy', 'anger'],
            'concepts': ['freedom', 'justice', 'beauty', 'truth', 'wisdom'],
            'qualities': ['strength', 'courage', 'patience', 'kindness']
        }
        
        # Action verb patterns
        self.action_patterns = [
            'run', 'walk', 'jump', 'swim', 'fly', 'eat', 'sleep', 'work',
            'think', 'speak', 'write', 'read', 'play', 'fight', 'build'
        ]
        
        # Technical term patterns
        self.technical_suffixes = [
            'ism', 'ology', 'tion', 'sion', 'ance', 'ence', 'ment',
            'ity', 'ness', 'able', 'ible', 'ous', 'eous', 'ious'
        ]
        
        # Compound word patterns
        self.compound_indicators = [
            'sun', 'fire', 'water', 'air', 'earth', 'sea', 'sky',
            'house', 'work', 'play', 'time', 'day', 'night'
        ]
        
    def categorize_word(self, word: str) -> WordAnalysis:
        """Categorize a word for optimal mapping strategy"""
        word_lower = word.lower().strip()
        
        # Single letter check
        if len(word_lower) == 1 and word_lower.isalpha():
            return WordAnalysis(
                word=word,
                category=WordCategory.SINGLE_LETTER,
                confidence=1.0,
                reasoning="Single alphabetic character",
                suggested_strategy="Use letter block emoji or phonetic representation"
            )
        
        # Numeric check
        if self._is_numeric_word(word_lower):
            return WordAnalysis(
                word=word,
                category=WordCategory.NUMERIC,
                confidence=1.0,
                reasoning="Numeric word",
                suggested_strategy="Use number emoji or counting symbols"
            )
        
        # Proper noun check
        if word[0].isupper() and not word.isupper():
            return WordAnalysis(
                word=word,
                category=WordCategory.PROPER_NOUN,
                confidence=0.8,
                reasoning="Capitalized word suggests proper noun",
                suggested_strategy="Use location/person symbols or representative objects"
            )
        
        # Concrete object check
        concrete_match = self._check_concrete_object(word_lower)
        if concrete_match:
            return WordAnalysis(
                word=word,
                category=WordCategory.CONCRETE_OBJECT,
                confidence=concrete_match[1],
                reasoning=f"Matches {concrete_match[0]} pattern",
                suggested_strategy="Use direct emoji representation"
            )
        
        # Abstract concept check
        abstract_match = self._check_abstract_concept(word_lower)
        if abstract_match:
            return WordAnalysis(
                word=word,
                category=WordCategory.ABSTRACT_CONCEPT,
                confidence=abstract_match[1],
                reasoning=f"Matches {abstract_match[0]} pattern",
                suggested_strategy="Use symbolic representation or metaphorical emoji sequence"
            )
        
        # Action verb check
        if word_lower in self.action_patterns:
            return WordAnalysis(
                word=word,
                category=WordCategory.ACTION_VERB,
                confidence=0.9,
                reasoning="Common action verb",
                suggested_strategy="Use action emoji or person performing action"
            )
        
        # Technical term check
        if self._is_technical_term(word_lower):
            return WordAnalysis(
                word=word,
                category=WordCategory.TECHNICAL_TERM,
                confidence=0.7,
                reasoning="Technical suffix pattern",
                suggested_strategy="Use symbols representing the field or concept"
            )
        
        # Compound word check
        if self._is_compound_word(word_lower):
            return WordAnalysis(
                word=word,
                category=WordCategory.COMPOUND_WORD,
                confidence=0.6,
                reasoning="Contains compound indicators",
                suggested_strategy="Break into components and combine emoji"
            )
        
        # Default to descriptive adjective
        return WordAnalysis(
            word=word,
            category=WordCategory.DESCRIPTIVE_ADJ,
            confidence=0.5,
            reasoning="Default classification",
            suggested_strategy="Use descriptive emoji sequence"
        )
    
    def _is_numeric_word(self, word: str) -> bool:
        """Check if word represents a number"""
        numeric_words = {
            'zero', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'ten',
            'eleven', 'twelve', 'thirteen', 'fourteen', 'fifteen', 'sixteen', 'seventeen', 'eighteen', 'nineteen', 'twenty',
            'thirty', 'forty', 'fifty', 'sixty', 'seventy', 'eighty', 'ninety', 'hundred', 'thousand', 'million'
        }
        return word in numeric_words
    
    def _check_concrete_object(self, word: str) -> Optional[Tuple[str, float]]:
        """Check if word matches concrete object patterns"""
        for category, words in self.concrete_patterns.items():
            if word in words:
                return (category, 0.9)
            # Check for partial matches or related words
            for obj_word in words:
                if word in obj_word or obj_word in word:
                    return (category, 0.6)
        return None
    
    def _check_abstract_concept(self, word: str) -> Optional[Tuple[str, float]]:
        """Check if word matches abstract concept patterns"""
        for category, words in self.abstract_patterns.items():
            if word in words:
                return (category, 0.9)
        return None
    
    def _is_technical_term(self, word: str) -> bool:
        """Check if word appears to be a technical term"""
        return any(word.endswith(suffix) for suffix in self.technical_suffixes)
    
    def _is_compound_word(self, word: str) -> bool:
        """Check if word appears to be a compound word"""
        return any(indicator in word for indicator in self.compound_indicators)

def create_category_specific_prompt(words_with_analysis: List[Tuple[str, WordAnalysis]], existing_emojis: str) -> str:
    """Create a prompt optimized for specific word categories"""
    
    # Group words by category
    categories = {}
    for word, analysis in words_with_analysis:
        if analysis.category not in categories:
            categories[analysis.category] = []
        categories[analysis.category].append((word, analysis))
    
    prompt_parts = [
        "# Role",
        "You are an expert in semantic analysis and emoji composition with specialized knowledge of different word types.",
        "",
        "# Input Words by Category"
    ]
    
    for category, word_list in categories.items():
        prompt_parts.append(f"\n## {category.value.replace('_', ' ').title()} Words:")
        for word, analysis in word_list:
            prompt_parts.append(f"- {word}: {analysis.suggested_strategy}")
    
    prompt_parts.extend([
        f"\n# Existing Emojis (avoid these):",
        existing_emojis,
        "",
        "# Category-Specific Guidelines:",
        "",
        "## Concrete Objects",
        "- Use direct emoji when available (apple → 🍎)",
        "- For missing objects, combine descriptive emoji (spatula → 🍳🥄)",
        "",
        "## Abstract Concepts", 
        "- Use symbolic representations (freedom → 🗽💫)",
        "- Combine metaphorical emoji (justice → ⚖️👥)",
        "- Focus on emotional or symbolic associations",
        "",
        "## Action Verbs",
        "- Show the action being performed (run → 🏃‍♂️)",
        "- Use tools/objects associated with action (write → ✍️)",
        "",
        "## Technical Terms",
        "- Use field-specific symbols (algorithm → ⚙️🧮)",
        "- Combine academic/scientific emoji (biology → 🧬🔬)",
        "",
        "## Compound Words",
        "- Break into semantic components (sunflower → ☀️🌻)",
        "- Maintain logical flow of components",
        "",
        "# Quality Priorities:",
        "1. Semantic accuracy over brevity",
        "2. Universal recognition over personal interpretation", 
        "3. Cultural neutrality over regional specificity",
        "4. Intuitive mapping over abstract symbolism",
        "",
        "# Output Format",
        "Return only a JSON array of {\"word\":\"emoji_combo\"} objects."
    ])
    
    return "\n".join(prompt_parts)
