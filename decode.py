"""Emoji-to-Text Decoder

This module provides context-aware decoding of emoji sequences back to English text.
It includes grammar reconstruction capabilities to restore proper word forms based
on surrounding context (plurals, tenses, comparatives, etc.).

The decoder uses pattern matching and context analysis to intelligently reconstruct
original text while handling complex emoji combinations and contextual modifiers.
"""

# Standard library imports
import re
from typing import Dict, List, Optional, Set, Tuple, Union

# Local imports
from lib.config import (
    CHARACTER_FALLBACK_REVERSE,
    MORPHOLOGICAL_MODIFIERS_REVERSE,
    PLURAL_CONTEXTS,
    PAST_CONTEXTS,
    FUTURE_CONTEXTS,
    IRREGULAR_COMPARATIVES,
    IRREGULAR_SUPERLATIVES,
    IRREGULAR_PLURALS
)
from lib.emoji_mappings import get_cached_mappings
from lib.morphology import (
    apply_morphological_transformations,
    make_plural_simple
)

# Load mappings at module level for efficiency
word_to_emoji, emoji_to_word = get_cached_mappings()

class ContextualDecoder:
    """Enhanced decoder with context-aware grammar reconstruction.
    
    This decoder processes emoji sequences and reconstructs proper English text
    by analyzing contextual clues and applying grammatical rules. It handles:
    - Context modifier extraction
    - Grammar form reconstruction (plurals, tenses, comparatives)
    - Multi-emoji sequence parsing
    - Surrounding word context analysis
    
    Attributes:
        emoji_pattern: Compiled regex for efficient emoji matching
        emoji_keys: Sorted emoji keys for longest-first matching
    """
    
    def __init__(self) -> None:
        """Initialize the contextual decoder with optimized emoji patterns."""
        # Sort emoji keys by length (longest first) for proper matching
        # This ensures multi-character emoji sequences are matched before single ones
        self.emoji_keys = sorted(emoji_to_word.keys(), key=len, reverse=True)
        
        # Add character fallback emojis to emoji keys for pattern matching
        all_emoji_keys = list(self.emoji_keys) + list(CHARACTER_FALLBACK_REVERSE.keys())
        
        # Also include morphological modifiers to ensure proper pattern matching
        all_emoji_keys.extend(MORPHOLOGICAL_MODIFIERS_REVERSE.keys())
        
        # Remove duplicates and sort by length (longest first) for proper matching
        all_emoji_keys = sorted(set(all_emoji_keys), key=len, reverse=True)
        
        # Compile regex pattern once for performance
        # Use alternation with escaped emoji sequences
        self.emoji_pattern = re.compile(
            "|".join(map(re.escape, all_emoji_keys))
        )
    
    def extract_morphological_modifiers(self, emoji_sequence: str) -> Tuple[str, Dict[str, str]]:
        """Extract morphological modifiers from emoji sequence.
        
        Analyzes an emoji sequence to identify and extract morphological modifiers
        that indicate word transformations (plural, tense, comparative, etc.).
        
        Args:
            emoji_sequence: The emoji sequence to analyze
            
        Returns:
            Tuple of (base_emoji_sequence, transformations_dict)
        """
        base_emoji = emoji_sequence
        transformations = {}
        
        # Check for morphological modifier emojis at the end of the sequence
        # Sort by length (longest first) to match multi-emoji modifiers first
        sorted_modifiers = sorted(MORPHOLOGICAL_MODIFIERS_REVERSE.items(), key=lambda x: len(x[0]), reverse=True)
        
        # Keep looking for modifiers until we can't find any more
        while base_emoji:
            found_modifier = False
            for modifier, meaning in sorted_modifiers:
                if base_emoji.endswith(modifier):
                    base_emoji = base_emoji[:-len(modifier)]
                    transformations[meaning] = modifier
                    found_modifier = True
                    break
            
            if not found_modifier:
                break
        
        return base_emoji, transformations
    
    def apply_grammar_rules(
        self, 
        base_word: str, 
        context: Dict[str, bool], 
        surrounding_words: List[str]
    ) -> str:
        """Apply grammar rules to reconstruct proper word form.
        
        Transforms the base word according to grammatical context indicators
        and surrounding word patterns to restore the original inflected form.
        
        Args:
            base_word: The base form of the word to transform
            context: Dictionary of boolean flags indicating grammatical context
            surrounding_words: List of nearby words for additional context
            
        Returns:
            The grammatically correct form of the word
        """
        if not base_word:
            return base_word
        
        word = base_word
        
        # Apply comparative transformations
        if context['is_comparative']:
            word = self._apply_comparative_form(base_word)
            
        # Apply superlative transformations
        elif context['is_superlative']:
            word = self._apply_superlative_form(base_word)
        
        # If no comparative/superlative and we have surrounding context indicating plural
        elif not context['is_comparative'] and not context['is_superlative']:
            # Apply plural transformations based on context
            word = self._apply_plural_context(word, surrounding_words)
        
        # Apply tense transformations (simplified for now)
        word = self._apply_tense_context(word, context, surrounding_words)
        
        return word
    
    def _apply_comparative_form(self, base_word: str) -> str:
        """Apply comparative form transformation.
        
        Args:
            base_word: Base word to transform
            
        Returns:
            Comparative form of the word
        """
        # Handle irregular comparatives
        if base_word in IRREGULAR_COMPARATIVES:
            return IRREGULAR_COMPARATIVES[base_word]
        
        # Apply regular comparative rules
        if base_word.endswith('y'):
            return base_word[:-1] + 'ier'
        elif base_word.endswith('e'):
            return base_word + 'r'
        else:
            return base_word + 'er'
    
    def _apply_superlative_form(self, base_word: str) -> str:
        """Apply superlative form transformation.
        
        Args:
            base_word: Base word to transform
            
        Returns:
            Superlative form of the word
        """
        # Handle irregular superlatives
        if base_word in IRREGULAR_SUPERLATIVES:
            return IRREGULAR_SUPERLATIVES[base_word]
        
        # Apply regular superlative rules
        if base_word.endswith('y'):
            return base_word[:-1] + 'iest'
        elif base_word.endswith('e'):
            return base_word + 'st'
        else:
            return base_word + 'est'
    
    def _apply_plural_context(self, word: str, surrounding_words: List[str]) -> str:
        """Apply plural transformation based on surrounding context.
        
        Args:
            word: Current word form
            surrounding_words: List of nearby words for context
            
        Returns:
            Pluralized word if context indicates plural usage
        """
        # Check if plural context is detected from surrounding words
        plural_detected = any(
            ctx.lower() in PLURAL_CONTEXTS 
            for ctx in surrounding_words
        )
        
        if plural_detected and not word.endswith(('s', 'es')):
            return make_plural_simple(word)
        
        return word
    
    def _make_plural(self, word: str) -> str:
        """Convert a word to its plural form.
        
        Args:
            word: Singular word to pluralize
            
        Returns:
            Plural form of the word
        """
        # Handle irregular plurals
        if word in IRREGULAR_PLURALS:
            return IRREGULAR_PLURALS[word]
        
        # Apply regular plural rules
        if word.endswith('y') and len(word) > 1 and word[-2] not in 'aeiou':
            return word[:-1] + 'ies'
        elif word.endswith(('s', 'sh', 'ch', 'x', 'z')):
            return word + 'es'
        elif word.endswith('f'):
            return word[:-1] + 'ves'
        elif word.endswith('fe'):
            return word[:-2] + 'ves'
        else:
            return word + 's'
    
    def _apply_tense_context(
        self, 
        word: str, 
        context: Dict[str, bool], 
        surrounding_words: List[str]
    ) -> str:
        """Apply tense transformation based on context (simplified implementation).
        
        Args:
            word: Current word form
            context: Grammatical context flags
            surrounding_words: List of nearby words for context
            
        Returns:
            Word with appropriate tense (currently returns unchanged)
            
        Note:
            This is a simplified implementation. Full tense reconstruction
            would require more sophisticated morphological analysis.
        """
        # Detect past tense indicators
        past_detected = (
            context['is_past'] or 
            any(ctx.lower() in PAST_CONTEXTS for ctx in surrounding_words)
        )
        
        # Future tense detection
        future_detected = (
            context['is_future'] or 
            any(ctx.lower() in FUTURE_CONTEXTS for ctx in surrounding_words)
        )
        
        # TODO: Implement proper tense reconstruction
        # This would require a more sophisticated approach with verb conjugation
        # rules and irregular verb handling
        
        return word
    
    def decode_with_context(self, text: str) -> str:
        """Decode emoji text with morphological reconstruction.
        
        Processes emoji sequences in the input text and reconstructs proper
        English text by applying stored morphological transformations.
        
        Args:
            text: Input text containing emoji sequences to decode
            
        Returns:
            Decoded English text with proper morphological forms
            
        Note:
            This method preserves spacing and handles multi-emoji sequences
            while reconstructing original word forms from base + modifier.
        """
        if not text:
            return text
            
        # Tokenize input while preserving whitespace
        tokens = re.findall(r'\s+|[^\s]+', text)
        output = []
        
        for token in tokens:
            if token.isspace():
                output.append(token)
                continue
            
            # Process non-whitespace tokens for emoji sequences
            decoded_token = self._decode_token_with_underscore_handling(token)
            output.append(decoded_token)
        
        return ''.join(output)
    
    def _decode_token(self, token: str) -> str:
        """Decode a single token that may contain emoji sequences.
        
        Args:
            token: Token to decode (no whitespace)
            
        Returns:
            Decoded token with reconstructed words
        """
        if not token:
            return token
        
        # Check if this token is primarily character fallback sequence
        if self._is_character_fallback_sequence(token):
            return self._decode_character_fallback_token(token)
            
        decoded_parts = []
        remaining = token
        
        # Parse token for emoji sequences, prioritizing base+modifier combinations
        while remaining:
            # Try to find the longest emoji sequence that starts here
            best_match = None
            best_length = 0
            best_match_info = None
            
            # First check for character emoji sequences (with potential modifiers)
            char_emoji = self._find_character_emoji(remaining)
            if char_emoji:
                # Found a character emoji, check for modifiers after it
                potential_sequence = char_emoji
                after_char = remaining[len(char_emoji):]
                
                # Look for morphological modifiers immediately after
                for modifier in sorted(MORPHOLOGICAL_MODIFIERS_REVERSE.keys(), key=len, reverse=True):
                    if after_char.startswith(modifier):
                        potential_sequence = char_emoji + modifier
                        break
                
                # Character emoji sequences get priority
                if len(potential_sequence) > best_length:
                    best_match = potential_sequence
                    best_length = len(potential_sequence)
            
            # Then check dictionary emoji sequences
            for emoji_key in self.emoji_keys:
                if remaining.startswith(emoji_key):
                    # Check if this emoji could be a base for a modifier
                    potential_sequence = emoji_key
                    after_base = remaining[len(emoji_key):]
                    found_modifiers = []
                    
                    # Look for multiple morphological modifiers immediately after
                    # Keep looking for modifiers until we can't find any more
                    remaining_after_base = after_base
                    while remaining_after_base:
                        found_modifier = False
                        # Try to find a modifier at the start of the remaining text
                        for modifier in sorted(MORPHOLOGICAL_MODIFIERS_REVERSE.keys(), key=len, reverse=True):
                            if remaining_after_base.startswith(modifier):
                                potential_sequence += modifier
                                found_modifiers.append(modifier)
                                remaining_after_base = remaining_after_base[len(modifier):]
                                found_modifier = True
                                break
                        if not found_modifier:
                            break
                    
                    # Only use if longer than character emoji match (character emojis get priority)
                    if len(potential_sequence) > best_length:
                        best_match = potential_sequence
                        best_length = len(potential_sequence)
                        # Store the base emoji and all modifiers found
                        best_match_info = (emoji_key, found_modifiers)
            
            if best_match:
                # Process the best emoji sequence we found
                emoji_sequence = best_match
                
                # Use the stored base emoji and modifier info if available
                if best_match_info:
                    base_emoji, found_modifiers = best_match_info
                    if found_modifiers:
                        # Create transformations dict from all modifiers we found
                        transformations = {}
                        for modifier in found_modifiers:
                            modifier_meaning = MORPHOLOGICAL_MODIFIERS_REVERSE[modifier]
                            transformations[modifier_meaning] = modifier
                    else:
                        transformations = {}
                else:
                    # Fallback to the old method
                    base_emoji, transformations = self.extract_morphological_modifiers(emoji_sequence)
                
                # First, try character fallback decoding (for sequences of character emojis)
                character_decoded = self._decode_character_sequence(emoji_sequence, transformations)
                if character_decoded:
                    decoded_parts.append(character_decoded)
                else:
                    # Look up base word from emoji mapping
                    base_word = emoji_to_word.get(base_emoji)
                    
                    if base_word:
                        # Apply morphological transformations to reconstruct original form
                        reconstructed_word = self._apply_morphological_transformations(
                            base_word, transformations
                        )
                        decoded_parts.append(reconstructed_word)
                    else:
                        # Unknown emoji sequence, preserve it
                        decoded_parts.append(emoji_sequence)
                
                remaining = remaining[len(emoji_sequence):]
            else:
                # Check for individual character emojis (fallback decoding)
                char_emoji = self._find_character_emoji(remaining)
                if char_emoji:
                    # Decode single character emoji
                    char = CHARACTER_FALLBACK_REVERSE[char_emoji]
                    decoded_parts.append(char)
                    remaining = remaining[len(char_emoji):]
                else:
                    # No emoji match found - preserve the character
                    decoded_parts.append(remaining[0])
                    remaining = remaining[1:]
        
        # Join all parts together without spaces
        # This preserves punctuation directly attached to words
        return ''.join(decoded_parts)
    
    def _is_character_fallback_sequence(self, token: str) -> bool:
        """Check if a token is primarily a character fallback sequence.
        
        Args:
            token: Token to analyze
            
        Returns:
            True if token appears to be character fallback encoding
        """
        # Check if most of the token consists of character emojis
        total_length = len(token)
        character_emoji_length = 0
        remaining = token
        
        while remaining:
            char_emoji = self._find_character_emoji(remaining)
            if char_emoji:
                character_emoji_length += len(char_emoji)
                remaining = remaining[len(char_emoji):]
            else:
                # Skip over morphological modifiers
                found_modifier = False
                for modifier in sorted(MORPHOLOGICAL_MODIFIERS_REVERSE.keys(), key=len, reverse=True):
                    if remaining.startswith(modifier):
                        remaining = remaining[len(modifier):]
                        found_modifier = True
                        break
                if not found_modifier:
                    break
        
        # If 50% or more of the token is character emojis, treat as character sequence
        return character_emoji_length >= total_length * 0.5
    
    def _decode_character_fallback_token(self, token: str) -> str:
        """Decode a token that's primarily character fallback encoding.
        
        This method handles character sequences with per-character modifiers correctly,
        avoiding inappropriate word-level morphological transformations.
        
        Args:
            token: Token to decode (expected to be character fallback)
            
        Returns:
            Decoded text with proper character handling
        """
        result = []
        remaining = token
        
        while remaining:
            # Look for character emoji
            char_emoji = self._find_character_emoji(remaining)
            if char_emoji:
                char = CHARACTER_FALLBACK_REVERSE[char_emoji]
                remaining = remaining[len(char_emoji):]
                
                # Check for capitalization modifier immediately after
                if remaining.startswith('🔠'):
                    char = char.upper()
                    remaining = remaining[len('🔠'):]
                
                result.append(char)
            else:
                # Check for standalone modifiers (these should be consumed with chars)
                found_modifier = False
                for modifier, meaning in MORPHOLOGICAL_MODIFIERS_REVERSE.items():
                    if remaining.startswith(modifier):
                        # Skip all morphological modifiers that don't apply to character sequences
                        # Capitalization modifiers should only be applied immediately after character emojis
                        remaining = remaining[len(modifier):]
                        found_modifier = True
                        break
                
                if not found_modifier:
                    # Preserve unknown characters
                    result.append(remaining[0])
                    remaining = remaining[1:]
        
        return ''.join(result)
    
    def _find_character_emoji(self, text: str) -> Optional[str]:
        """Find character emoji at the beginning of text.
        
        Args:
            text: Text to search for character emoji
            
        Returns:
            Character emoji if found, None otherwise
        """
        for emoji_char in sorted(CHARACTER_FALLBACK_REVERSE.keys(), key=len, reverse=True):
            if text.startswith(emoji_char):
                return emoji_char
        return None
    
    def _decode_character_sequence(self, emoji_sequence: str, transformations: Dict[str, str]) -> Optional[str]:
        """Decode a sequence that might be character-by-character encoding.
        
        Args:
            emoji_sequence: Emoji sequence to decode
            transformations: Any morphological transformations found
            
        Returns:
            Decoded character sequence if it's a character fallback, None otherwise
        """
        # Remove morphological modifiers to get the base emoji sequence
        base_emoji = emoji_sequence
        for modifier in transformations.values():
            if base_emoji.endswith(modifier):
                base_emoji = base_emoji[:-len(modifier)]
        
        # Try to decode as character-by-character sequence
        decoded_chars = []
        remaining = base_emoji
        
        while remaining:
            char_emoji = self._find_character_emoji(remaining)
            if char_emoji:
                decoded_chars.append(CHARACTER_FALLBACK_REVERSE[char_emoji])
                remaining = remaining[len(char_emoji):]
            else:
                # If any character can't be decoded, this isn't a character sequence
                return None
        
        if decoded_chars:
            # Reconstruct the word with transformations
            word = ''.join(decoded_chars)
            
            # Apply morphological transformations (including capitalization)
            reconstructed_word = self._apply_morphological_transformations(word, transformations)
            
            return reconstructed_word
        
        return None
    
    def _fix_subject_verb_agreement(self, tokens: List[str]) -> List[str]:
        """Fix subject-verb agreement, particularly for plurals.
        
        Args:
            tokens: List of decoded tokens (words and spaces)
            
        Returns:
            List of tokens with corrected subject-verb agreement
        """
        result = tokens.copy()
        
        # Find word tokens (skip spaces)
        word_positions = []
        for i, token in enumerate(tokens):
            if not token.isspace() and token.strip().isalpha():
                word_positions.append((i, token.strip().lower()))
        
        # Look for plural verb patterns and fix preceding subjects
        for i, (pos, word) in enumerate(word_positions):
            if word in PLURAL_CONTEXTS:  # Found a plural verb like "are"
                # Look for the subject (previous word)
                if i > 0:
                    prev_pos, prev_word = word_positions[i-1]
                    # Pluralize the subject if it's not already plural
                    if not prev_word.endswith(('s', 'es')):
                        pluralized = self._make_plural(prev_word)
                        result[prev_pos] = pluralized
        
        return result
    
    def _apply_morphological_transformations(self, base_word: str, transformations: Dict[str, str]) -> str:
        """Apply multiple morphological transformations to reconstruct original word form.
        
        Args:
            base_word: Base/normalized word form
            transformations: Dictionary of transformations to apply
            
        Returns:
            Reconstructed word with applied transformations
        """
        return apply_morphological_transformations(base_word, transformations)
    
    def _decode_token_with_underscore_handling(self, token: str) -> str:
        """Decode a token that may contain underscore-separated emoji sequences.
        
        This method handles cases like 'Ⓚ🔠ⓊⓁⓉ_🎭🤹‍♂️🔠' by:
        1. Checking if the token contains underscores
        2. Splitting on underscores and decoding each part separately
        3. Preserving the original structure with underscores
        
        Args:
            token: Token that may contain underscore-separated emoji sequences
            
        Returns:
            Decoded token with proper morphological reconstruction
        """
        # Check if token contains underscores
        if '_' not in token:
            return self._decode_token(token)
            
        # Split on underscores and process each part
        parts = token.split('_')
        decoded_parts = []
        
        for part in parts:
            # Decode each part separately
            if part:  # Skip empty parts
                decoded_part = self._decode_token(part)
                decoded_parts.append(decoded_part)
            else:
                decoded_parts.append(part)
        
        # Rejoin with underscores
        return '_'.join(decoded_parts)
    
    def _make_plural_s(self, word: str) -> str:
        """Add simple 's' plural."""
        return word + 's'
    
    def _make_plural_es(self, word: str) -> str:
        """Add 'es' plural."""
        return word + 'es'
    
    def _make_plural_ies(self, word: str) -> str:
        """Convert 'y' to 'ies' plural."""
        if word.endswith('y'):
            return word[:-1] + 'ies'
        return word + 'ies'
    
    def _make_irregular_plural(self, word: str) -> str:
        """Handle irregular plurals."""
        irregular_plurals = {
            'child': 'children', 'foot': 'feet', 'tooth': 'teeth',
            'goose': 'geese', 'mouse': 'mice', 'man': 'men',
            'woman': 'women', 'person': 'people', 'ox': 'oxen'
        }
        return irregular_plurals.get(word, word + 's')
    
    def _make_verb_s(self, word: str) -> str:
        """Add 's' for 3rd person singular verb."""
        # Handle irregular verb forms that are already in 3rd person singular
        irregular_verb_forms = {
            'does': 'does',  # does is already 3rd person singular of do
            'goes': 'goes',  # goes is already 3rd person singular of go  
            'has': 'has',    # has is already 3rd person singular of have
            'is': 'is',      # is is already 3rd person singular of be
        }
        
        # If the word is already in irregular 3rd person form, return as-is
        if word in irregular_verb_forms:
            return word
        
        # Handle irregular verb base forms that need special 3rd person forms
        irregular_verb_bases = {
            'do': 'does',
            'go': 'goes', 
            'have': 'has',
            'be': 'is',
        }
        
        if word in irregular_verb_bases:
            return irregular_verb_bases[word]
        
        # Apply regular verb_s transformation rules
        if word.endswith(('s', 'sh', 'ch', 'x', 'z')):
            return word + 'es'
        elif word.endswith('y') and len(word) > 1 and word[-2] not in 'aeiou':
            return word[:-1] + 'ies'
        else:
            return word + 's'
    
    def _make_verb_ed(self, word: str) -> str:
        """Add 'ed' for past tense."""
        if word.endswith('e'):
            return word + 'd'
        elif word.endswith('y') and len(word) > 1 and word[-2] not in 'aeiou':
            return word[:-1] + 'ied'
        else:
            return word + 'ed'
    
    def _make_verb_ing(self, word: str) -> str:
        """Add 'ing' for progressive form."""
        if word.endswith('e') and len(word) > 2:
            return word[:-1] + 'ing'
        else:
            return word + 'ing'
    
    def _make_comparative(self, word: str) -> str:
        """Make comparative form."""
        # Handle irregular comparatives
        if word in IRREGULAR_COMPARATIVES:
            return IRREGULAR_COMPARATIVES[word]
        
        # Regular comparative rules
        if word.endswith('y'):
            return word[:-1] + 'ier'
        elif word.endswith('e'):
            return word + 'r'
        else:
            return word + 'er'
    
    def _make_superlative(self, word: str) -> str:
        """Make superlative form."""
        # Handle irregular superlatives
        if word in IRREGULAR_SUPERLATIVES:
            return IRREGULAR_SUPERLATIVES[word]
        
        # Regular superlative rules
        if word.endswith('y'):
            return word[:-1] + 'iest'
        elif word.endswith('e'):
            return word + 'st'
        else:
            return word + 'est'
    
    def _make_adverb_ly(self, word: str) -> str:
        """Make adverb with 'ly' suffix."""
        if word.endswith('y'):
            return word[:-1] + 'ily'
        else:
            return word + 'ly'

# Create global decoder instance for module-level functions
contextual_decoder = ContextualDecoder()


def decode(text: str) -> str:
    """Decode emoji text using context-aware grammar reconstruction.
    
    This is the main public interface for decoding emoji sequences back
    to English text with intelligent grammar reconstruction.
    
    Args:
        text: Input text containing emoji sequences
        
    Returns:
        Decoded English text with proper grammar
        
    Example:
        >>> decode("🐱 🏃➕ 🏠")
        "cat runs home"
    """
    return contextual_decoder.decode_with_context(text)


def decode_simple(text: str) -> str:
    """Simple decoding without context reconstruction (legacy).
    
    Provides backward compatibility for applications that need simple
    emoji-to-word mapping without grammatical reconstruction.
    
    Args:
        text: Input text containing emoji sequences
        
    Returns:
        Decoded text with basic word substitution only
        
    Note:
        This function is deprecated. Use decode() for better results.
    """
    if not text:
        return text
        
    # Tokenize input while preserving whitespace
    tokens = re.findall(r'\s+|[^\s]+', text)
    output = []

    for token in tokens:
        if token.isspace():
            output.append(token)
            continue

        decoded = ""
        remaining = token
        
        # Simple emoji-to-word substitution without context
        while remaining:
            match = contextual_decoder.emoji_pattern.match(remaining)
            if match:
                emoji_seq = match.group(0)
                decoded += emoji_to_word.get(emoji_seq, emoji_seq) + " "
                remaining = remaining[len(emoji_seq):]
            else:
                # No match found, preserve character
                decoded += remaining[0]
                remaining = remaining[1:]
                
        output.append(decoded.strip())

    return ''.join(output)

def main() -> None:
    """Command-line interface for emoji decoding.
    
    Supports multiple input methods:
    - Command-line arguments: python decode.py "emojis to decode"
    - Piped input: echo "🐱🏃" | python decode.py
    - Interactive mode: python decode.py (prompts for input)
    """
    import sys
    
    try:
        if len(sys.argv) > 1:
            # Command-line argument mode
            sample = ' '.join(sys.argv[1:])
            show_labels = True
        elif not sys.stdin.isatty():
            # Piped input mode
            sample = sys.stdin.read().strip()
            show_labels = False  # For piped input, just output the result
        else:
            # Interactive mode
            sample = input('What do you want to decode from Emo? ')
            show_labels = True
        
        if not sample.strip():
            if show_labels:
                print("No input provided.")
            return
        
        # Decode using context-aware method
        decoded = decode(sample)
        
        # Display results
        if show_labels:
            print(f"Original: {sample}")
            print(f"Decoded : {decoded}")
        else:
            # For piped input, just output the decoded result
            print(decoded)
        
    except KeyboardInterrupt:
        if not sys.stdin.isatty():
            # Don't show interrupt message for piped input
            pass
        else:
            print("\nDecoding interrupted by user.")
    except Exception as e:
        print(f"Error during decoding: {e}", file=sys.stderr)


if __name__ == "__main__":
    main()
