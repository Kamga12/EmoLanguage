#!/usr/bin/env python3
"""
Mapping Quality Validator

This module provides quality assessment and validation for emoji mappings
to ensure high-quality, semantically appropriate word-to-emoji assignments.
"""

import re
import json
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum

class QualityIssue(Enum):
    """Types of quality issues that can be detected"""
    SEMANTIC_MISMATCH = "semantic_mismatch"       # Emoji doesn't match word meaning
    OVER_COMPLEX = "over_complex"                 # Too many emoji for simple word
    UNDER_SPECIFIC = "under_specific"             # Too generic for specific word  
    CULTURAL_BIAS = "cultural_bias"               # Culture-specific emoji usage
    VISUAL_UNCLEAR = "visual_unclear"             # Hard to interpret visually
    INCONSISTENT = "inconsistent"                 # Inconsistent with similar words
    REDUNDANT = "redundant"                       # Unnecessarily repetitive
    INAPPROPRIATE = "inappropriate"               # Contains problematic emoji

@dataclass
class QualityScore:
    """Quality assessment for a mapping"""
    word: str
    emoji: str
    overall_score: float  # 0-100
    semantic_accuracy: float
    visual_clarity: float
    consistency: float
    complexity_appropriateness: float
    issues: List[QualityIssue]
    suggestions: List[str]

class MappingQualityValidator:
    """Validates and scores emoji mapping quality"""
    
    def __init__(self):
        # Emoji categories for analysis
        self.emoji_categories = {
            'faces': ['😀', '😃', '😄', '😁', '😆', '😅', '🤣', '😂', '🙂', '🙃', '😉', '😊'],
            'animals': ['🐶', '🐱', '🐭', '🐹', '🐰', '🦊', '🐻', '🐼', '🐨', '🐯', '🦁', '🐮'],
            'food': ['🍎', '🍊', '🍋', '🍌', '🍉', '🍇', '🍓', '🫐', '🍈', '🍒', '🍑', '🥭'],
            'objects': ['📱', '💻', '🖥️', '🖨️', '⌨️', '🖱️', '🖲️', '💽', '💾', '💿', '📀'],
            'symbols': ['❤️', '💛', '💚', '💙', '💜', '🖤', '🤍', '🤎', '💔', '❣️', '💕'],
            'flags': ['🏳️', '🏴', '🏳️‍🌈', '🏳️‍⚧️', '🏴‍☠️'],
            'skin_tones': ['🏻', '🏼', '🏽', '🏾', '🏿']
        }
        
        # Problematic emoji patterns
        self.problematic_patterns = {
            'excessive_repetition': r'(.)\1{4,}',  # Same emoji 5+ times
            'mixed_skin_tones': r'🏻.*🏽|🏽.*🏻',  # Mixed skin tones
            'flag_overuse': r'🇦🇺|🇨🇦|🇺🇸|🇬🇧',  # National flags (usually inappropriate)
        }
        
        # Word complexity indicators
        self.simple_words = {
            'basic_verbs': ['go', 'do', 'see', 'get', 'use', 'run', 'eat', 'sit'],
            'basic_nouns': ['cat', 'dog', 'car', 'house', 'book', 'tree', 'sun', 'moon'],
            'basic_adjectives': ['big', 'small', 'good', 'bad', 'hot', 'cold', 'new', 'old']
        }
        
        # Quality benchmarks
        self.quality_thresholds = {
            'excellent': 85,
            'good': 70,
            'acceptable': 55,
            'poor': 40
        }
    
    def validate_mapping(self, word: str, emoji: str, context_mappings: Optional[Dict[str, str]] = None) -> QualityScore:
        """Validate a single word-emoji mapping"""
        issues = []
        suggestions = []
        
        # Calculate component scores
        semantic_score = self._score_semantic_accuracy(word, emoji)
        visual_score = self._score_visual_clarity(emoji)
        consistency_score = self._score_consistency(word, emoji, context_mappings or {})
        complexity_score = self._score_complexity_appropriateness(word, emoji)
        
        # Detect specific issues
        issues.extend(self._detect_complexity_issues(word, emoji))
        issues.extend(self._detect_cultural_issues(emoji))
        issues.extend(self._detect_clarity_issues(emoji))
        issues.extend(self._detect_pattern_issues(emoji))
        
        # Generate suggestions based on issues
        suggestions.extend(self._generate_suggestions(word, emoji, issues))
        
        # Calculate overall score
        overall_score = (
            semantic_score * 0.4 +
            visual_score * 0.25 +
            consistency_score * 0.2 +
            complexity_score * 0.15
        )
        
        # Penalty for severe issues
        severe_penalty = len([i for i in issues if i in [QualityIssue.SEMANTIC_MISMATCH, QualityIssue.INAPPROPRIATE]]) * 20
        overall_score = max(0, overall_score - severe_penalty)
        
        return QualityScore(
            word=word,
            emoji=emoji,
            overall_score=overall_score,
            semantic_accuracy=semantic_score,
            visual_clarity=visual_score,
            consistency=consistency_score,
            complexity_appropriateness=complexity_score,
            issues=issues,
            suggestions=suggestions
        )
    
    def _score_semantic_accuracy(self, word: str, emoji: str) -> float:
        """Score how well the emoji represents the word's meaning"""
        # This is a simplified heuristic - in practice would use semantic embedding similarity
        
        word_lower = word.lower()
        
        # Direct matches get high scores
        obvious_matches = {
            'cat': '🐱', 'dog': '🐶', 'sun': '☀️', 'moon': '🌙',
            'car': '🚗', 'house': '🏠', 'tree': '🌳', 'flower': '🌸'
        }
        
        if word_lower in obvious_matches and obvious_matches[word_lower] in emoji:
            return 95.0
        
        # Category-based scoring
        if word_lower in ['happy', 'joy', 'smile'] and any(face in emoji for face in ['😊', '😀', '😃', '😄']):
            return 90.0
        
        if word_lower in ['sad', 'cry', 'tears'] and any(face in emoji for face in ['😢', '😭', '☹️']):
            return 90.0
        
        # Length-based penalties for mismatches
        if len(emoji) == 1 and len(word) > 8:
            return 60.0  # Simple emoji for complex word might be under-specific
        
        if len(emoji) > 6 and len(word) <= 4:
            return 65.0  # Complex emoji for simple word might be over-complex
        
        # Default moderate score
        return 75.0
    
    def _score_visual_clarity(self, emoji: str) -> float:
        """Score how visually clear and interpretable the emoji sequence is"""
        score = 100.0
        
        # Length penalties
        if len(emoji) > 8:
            score -= 10  # Very long sequences harder to read
        elif len(emoji) > 12:
            score -= 25  # Extremely long sequences
        
        # Repetition check
        if re.search(self.problematic_patterns['excessive_repetition'], emoji):
            score -= 30
        
        # Mixed complexity penalty
        simple_emoji = sum(1 for char in emoji if len(char.encode('utf-8')) <= 3)
        complex_emoji = len(emoji) - simple_emoji
        if simple_emoji > 0 and complex_emoji > 0 and len(emoji) > 4:
            score -= 15  # Mixing simple and complex emoji can be confusing
        
        return max(0, score)
    
    def _score_consistency(self, word: str, emoji: str, context_mappings: Dict[str, str]) -> float:
        """Score consistency with similar words in the mapping set"""
        if not context_mappings:
            return 80.0  # Neutral score when no context available
        
        # Find similar words (simplified - could use more sophisticated similarity)
        similar_words = [w for w in context_mappings.keys() if self._words_similar(word, w)]
        
        if not similar_words:
            return 80.0
        
        # Check if emoji patterns are consistent
        similar_emoji = [context_mappings[w] for w in similar_words]
        
        # Look for pattern consistency (simplified)
        if len(emoji) == 1:
            single_emoji_count = sum(1 for e in similar_emoji if len(e) == 1)
            if single_emoji_count / len(similar_emoji) > 0.5:
                return 90.0  # Consistent with similar words using single emoji
        
        return 75.0  # Default moderate consistency score
    
    def _score_complexity_appropriateness(self, word: str, emoji: str) -> float:
        """Score whether emoji complexity matches word complexity"""
        word_complexity = self._assess_word_complexity(word)
        emoji_complexity = len(emoji)
        
        # Ideal complexity mapping
        if word_complexity == 'simple' and emoji_complexity <= 2:
            return 95.0
        elif word_complexity == 'medium' and 2 <= emoji_complexity <= 4:
            return 95.0
        elif word_complexity == 'complex' and 3 <= emoji_complexity <= 6:
            return 95.0
        
        # Mismatched complexity penalties
        if word_complexity == 'simple' and emoji_complexity > 4:
            return 60.0  # Over-complex for simple word
        elif word_complexity == 'complex' and emoji_complexity == 1:
            return 65.0  # Under-specific for complex word
        
        return 80.0  # Moderate score for other cases
    
    def _assess_word_complexity(self, word: str) -> str:
        """Assess the complexity level of a word"""
        if len(word) <= 4 or any(word.lower() in word_list for word_list in self.simple_words.values()):
            return 'simple'
        elif len(word) <= 8:
            return 'medium'
        else:
            return 'complex'
    
    def _words_similar(self, word1: str, word2: str) -> bool:
        """Check if two words are semantically similar (simplified)"""
        # This is a very basic similarity check - could be enhanced with NLP
        if abs(len(word1) - len(word2)) > 3:
            return False
        
        # Check for common prefixes/suffixes
        if len(word1) >= 4 and len(word2) >= 4:
            if word1[:3] == word2[:3] or word1[-3:] == word2[-3:]:
                return True
        
        return False
    
    def _detect_complexity_issues(self, word: str, emoji: str) -> List[QualityIssue]:
        """Detect complexity-related issues"""
        issues = []
        
        word_complexity = self._assess_word_complexity(word)
        emoji_length = len(emoji)
        
        if word_complexity == 'simple' and emoji_length > 5:
            issues.append(QualityIssue.OVER_COMPLEX)
        elif word_complexity == 'complex' and emoji_length == 1:
            issues.append(QualityIssue.UNDER_SPECIFIC)
        
        return issues
    
    def _detect_cultural_issues(self, emoji: str) -> List[QualityIssue]:
        """Detect cultural bias or inappropriate content"""
        issues = []
        
        # Check for flag usage (usually inappropriate unless word is country/nationality)
        if any(flag in emoji for flag in self.emoji_categories['flags'][2:]):  # Skip generic flags
            issues.append(QualityIssue.CULTURAL_BIAS)
        
        # Check for mixed skin tones
        if re.search(self.problematic_patterns['mixed_skin_tones'], emoji):
            issues.append(QualityIssue.CULTURAL_BIAS)
        
        return issues
    
    def _detect_clarity_issues(self, emoji: str) -> List[QualityIssue]:
        """Detect visual clarity issues"""
        issues = []
        
        if len(emoji) > 10:
            issues.append(QualityIssue.VISUAL_UNCLEAR)
        
        if re.search(self.problematic_patterns['excessive_repetition'], emoji):
            issues.append(QualityIssue.REDUNDANT)
        
        return issues
    
    def _detect_pattern_issues(self, emoji: str) -> List[QualityIssue]:
        """Detect problematic patterns in emoji usage"""
        issues = []
        
        for pattern_name, pattern in self.problematic_patterns.items():
            if re.search(pattern, emoji):
                if pattern_name == 'excessive_repetition':
                    issues.append(QualityIssue.REDUNDANT)
                elif pattern_name in ['mixed_skin_tones', 'flag_overuse']:
                    issues.append(QualityIssue.CULTURAL_BIAS)
        
        return issues
    
    def _generate_suggestions(self, word: str, emoji: str, issues: List[QualityIssue]) -> List[str]:
        """Generate improvement suggestions based on detected issues"""
        suggestions = []
        
        if QualityIssue.OVER_COMPLEX in issues:
            suggestions.append("Consider using fewer emoji for this simple word")
        
        if QualityIssue.UNDER_SPECIFIC in issues:
            suggestions.append("Add more descriptive emoji to better represent this complex word")
        
        if QualityIssue.CULTURAL_BIAS in issues:
            suggestions.append("Use culturally neutral emoji without flags or skin tones")
        
        if QualityIssue.VISUAL_UNCLEAR in issues:
            suggestions.append("Simplify the emoji sequence for better visual clarity")
        
        if QualityIssue.REDUNDANT in issues:
            suggestions.append("Remove repetitive emoji and use varied symbols")
        
        return suggestions

def validate_mapping_batch(mappings: Dict[str, str], sample_size: int = 100) -> Dict:
    """Validate a batch of mappings and return quality statistics"""
    validator = MappingQualityValidator()
    
    # Sample mappings for validation
    import random
    sample_items = random.sample(list(mappings.items()), min(sample_size, len(mappings)))
    
    results = []
    for word, emoji in sample_items:
        score = validator.validate_mapping(word, emoji, mappings)
        results.append(score)
    
    # Calculate statistics
    scores = [r.overall_score for r in results]
    
    stats = {
        'total_validated': len(results),
        'average_score': sum(scores) / len(scores),
        'excellent_count': len([s for s in scores if s >= 85]),
        'good_count': len([s for s in scores if 70 <= s < 85]),
        'acceptable_count': len([s for s in scores if 55 <= s < 70]),
        'poor_count': len([s for s in scores if s < 55]),
        'common_issues': {},
        'top_suggestions': [],
        'worst_mappings': sorted(results, key=lambda x: x.overall_score)[:5]
    }
    
    # Analyze common issues
    all_issues = []
    all_suggestions = []
    for result in results:
        all_issues.extend(result.issues)
        all_suggestions.extend(result.suggestions)
    
    from collections import Counter
    stats['common_issues'] = dict(Counter(all_issues).most_common(5))
    stats['top_suggestions'] = list(set(all_suggestions))
    
    return stats
