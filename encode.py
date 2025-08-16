"""Text-to-Emoji Encoder

This module provides context-aware encoding of English text to emoji sequences.
It includes morphological transformation detection to preserve meaning through
modifiers and handles various word forms (plurals, tenses, comparatives, etc.).

The encoder analyzes word morphology to determine the appropriate base form
and applies morphological modifiers to emoji sequences when necessary.
"""

# Standard library imports
import re
import sys
from typing import Optional, Tuple

# Local imports
from lib.word_normalizer import WordNormalizer
from lib.config import CHARACTER_FALLBACK_MAPPINGS, MORPHOLOGICAL_MODIFIERS
from lib.emoji_mappings import get_word_to_emoji
from lib.morphology import identify_transformation_type, is_likely_verb, is_agent_noun_er, is_agent_noun_or

# Load mappings and initialize normalizer at module level
word_to_emoji = get_word_to_emoji()
normalizer = WordNormalizer()

class ContextualEncoder:
    """Morphological transformation encoder.
    
    This encoder handles word normalization and applies morphological
    modifiers to preserve grammatical information in emoji sequences.
    
    Attributes:
        normalizer: Word normalizer instance for consistent lookups
    """
    
    def __init__(self) -> None:
        """Initialize the encoder with word normalizer."""
        self.normalizer = WordNormalizer()
    
    
    def _detect_morphological_transformation(self, word: str) -> Tuple[str, str]:
        """Detect morphological transformation and return base word + modifier.
        
        Args:
            word: Original word to analyze
            
        Returns:
            Tuple of (base_word, modifier_emoji)
        """
        original_word = word
        
        # Get normalized form from word normalizer
        base_word = self.normalizer.normalize_word(word)
        
        # If no change, no morphological transformation detected
        if word == base_word:
            return word, ''
        
        # Detect specific transformations
        modifier = self._identify_transformation_type(original_word, base_word)
        
        return base_word, modifier
    
    def _identify_transformation_type(self, original: str, base: str) -> str:
        """Identify the type of morphological transformation.
        
        Args:
            original: Original word form
            base: Base/normalized form from word normalizer
            
        Returns:
            Appropriate modifier emoji for the transformation
        """
        return identify_transformation_type(original, base)
    
    
    def encode_with_context(self, text: str) -> str:
        """Encode text with morphological transformation detection.
        
        Processes input text and converts words to emoji sequences while
        preserving morphological information through modifier emojis.
        
        Args:
            text: Input text to encode to emoji sequences
            
        Returns:
            Encoded text with emoji sequences and morphological modifiers
            
        Note:
            This method preserves punctuation and spacing while applying
            morphological transformation detection to alphabetic tokens.
        """
        if not text:
            return text
            
        # Tokenize input to separate words and non-word characters
        # Handle contractions as single tokens
        tokens = re.findall(r"\w+'t\b|\b\w+\b|\W+", text)
        output = []
        
        for token in tokens:
            if token.strip().replace("'", "").isalnum():  # Handle contractions with apostrophes and numbers
                word = token.lower()
                is_capitalized = token[0].isupper()
                
                # Detect morphological transformation and get base form
                base_word, modifier = self._detect_morphological_transformation(word)
                
                # Look up emoji for base word
                emoji_sequence = self._lookup_emoji(word, base_word, token)
                
                # Apply morphological modifier if we found an emoji and have a transformation
                if emoji_sequence != token:
                    if modifier:
                        emoji_sequence += modifier
                    
                    # Add capitalization modifier if needed, but only if we didn't use character fallback
                    # Character fallback handles capitalization individually per character
                    if is_capitalized and not self._is_character_fallback_result(emoji_sequence):
                        emoji_sequence += MORPHOLOGICAL_MODIFIERS['capitalized']
                
                # Handle list-type emoji sequences
                if isinstance(emoji_sequence, list):
                    output.append(''.join(emoji_sequence))
                else:
                    output.append(emoji_sequence)
            else:
                # Check if this token contains underscore-separated words that should be encoded
                processed_token = self._process_underscore_separated_token(token)
                output.append(processed_token)
        
        return ''.join(output)
    
    
    def _lookup_emoji(self, word: str, base_word: str, fallback: str) -> str:
        """Look up emoji for word with character-by-character fallback strategy.
        
        Args:
            word: Original word to look up
            base_word: Normalized/base form of the word
            fallback: Fallback token to use if no emoji found
            
        Returns:
            Emoji sequence or character-by-character emoji fallback
        """
        # For single characters (letters or digits), always use character fallback
        if len(word) == 1 and (word.isalpha() or word.isdigit()):
            if self._is_fallback_eligible(fallback):
                return self._encode_character_by_character(fallback)
        
        # Try exact match first (preserves case-specific mappings)
        emoji_sequence = word_to_emoji.get(word)
        
        if emoji_sequence is None:
            # Try normalized/base form
            emoji_sequence = word_to_emoji.get(base_word)
        
        if emoji_sequence is None:
            # Use character-by-character fallback for alphabetic words and numbers
            if self._is_fallback_eligible(fallback):
                return self._encode_character_by_character(fallback)
            else:
                # Not eligible for character fallback, return original token
                return fallback
        
        return emoji_sequence
    
    def _is_fallback_eligible(self, token: str) -> bool:
        """Check if a token is eligible for character-by-character fallback.
        
        Args:
            token: Token to check
            
        Returns:
            True if token should use character fallback
        """
        # Remove apostrophes and spaces for checking
        cleaned = token.replace("'", "").replace(" ", "")
        
        # Must contain only letters or digits (no punctuation or special chars)
        return cleaned.isalnum() and len(cleaned) > 0
    
    def _encode_character_by_character(self, token: str) -> str:
        """Encode a token character by character using emoji mappings.
        
        Each character gets its own emoji representation. For uppercase letters,
        we add the capitalization modifier after each letter's emoji.
        
        Args:
            token: Token to encode character by character
            
        Returns:
            String of emoji characters representing each character in the token
        """
        result = []
        
        for char in token:
            if char in CHARACTER_FALLBACK_MAPPINGS:
                emoji_char = CHARACTER_FALLBACK_MAPPINGS[char]
                result.append(emoji_char)
            elif char.isupper() and char.lower() in CHARACTER_FALLBACK_MAPPINGS:
                # For uppercase letters, use lowercase emoji + capitalization modifier
                emoji_char = CHARACTER_FALLBACK_MAPPINGS[char.lower()]
                result.append(emoji_char + MORPHOLOGICAL_MODIFIERS['capitalized'])
            else:
                # For characters not in our mapping (like apostrophes), keep as-is
                result.append(char)
        
        return ''.join(result)
    
    def _is_character_fallback_result(self, emoji_sequence: str) -> bool:
        """Check if an emoji sequence is the result of character-by-character fallback.
        
        Args:
            emoji_sequence: The emoji sequence to check
            
        Returns:
            True if this appears to be a character fallback result
        """
        # Check if the sequence contains only regional indicator emojis (🇦-🇿) 
        # and number emojis (0⃣-9⃣) and capitalization modifiers (🔠)
        character_emojis = set(CHARACTER_FALLBACK_MAPPINGS.values())
        cap_modifier = MORPHOLOGICAL_MODIFIERS['capitalized']
        
        # Parse the sequence to check if it's made up of character emojis
        remaining = emoji_sequence
        while remaining:
            found_char_emoji = False
            
            # Check for character emojis with optional capitalization modifier
            for char_emoji in character_emojis:
                if remaining.startswith(char_emoji):
                    remaining = remaining[len(char_emoji):]
                    
                    # Check if followed by capitalization modifier
                    if remaining.startswith(cap_modifier):
                        remaining = remaining[len(cap_modifier):]
                    
                    found_char_emoji = True
                    break
            
            if not found_char_emoji:
                return False
        
        return True
    
    def _lookup_emoji_with_source(self, word: str, base_word: str, fallback: str) -> Tuple[str, bool]:
        """Look up emoji for word with fallback strategy, tracking which form was used.
        
        Args:
            word: Original word to look up
            base_word: Normalized/base form of the word
            fallback: Fallback token to use if no emoji found
            
        Returns:
            Tuple of (emoji_sequence, used_base_form)
            used_base_form is True if we used the base word emoji, False if we used direct mapping
        """
        # Try exact match first (preserves case-specific mappings)
        emoji_sequence = word_to_emoji.get(word)
        
        if emoji_sequence is not None:
            # Found direct mapping for original word
            return emoji_sequence, False
        
        # Try normalized/base form
        emoji_sequence = word_to_emoji.get(base_word)
        
        if emoji_sequence is not None:
            # Found mapping using base form
            return emoji_sequence, True
        
        # No emoji found, return original token
        return fallback, False
    
    def _process_underscore_separated_token(self, token: str) -> str:
        """Process tokens that may contain underscore-separated words.
        
        This method handles cases like 'Kult_Entertainment' by:
        1. Checking if the token contains underscores and alphabetic segments
        2. Splitting on underscores and encoding each alphabetic segment
        3. Preserving the original structure with non-alphabetic parts
        
        Args:
            token: Token that may contain underscore-separated words
            
        Returns:
            Processed token with encoded word segments
        """
        # Check if token contains underscores and has alphabetic parts
        if '_' not in token:
            return token
            
        # Split on underscores and process each part
        parts = token.split('_')
        processed_parts = []
        
        for part in parts:
            # Only process parts that are purely alphabetic (potential words)
            if part and part.isalpha():
                # Treat as a word and apply full morphological processing
                is_capitalized = part[0].isupper()
                word = part.lower()
                
                # Detect morphological transformation and get base form
                base_word, modifier = self._detect_morphological_transformation(word)
                
                # Look up emoji for base word
                emoji_sequence = self._lookup_emoji(word, base_word, part)
                
                # Apply morphological modifier if we found an emoji and have a transformation
                if emoji_sequence != part:
                    if modifier:
                        emoji_sequence += modifier
                    
                    # Add capitalization modifier if needed, but only if we didn't use character fallback
                    # Character fallback handles capitalization individually per character
                    if is_capitalized and not self._is_character_fallback_result(emoji_sequence):
                        emoji_sequence += MORPHOLOGICAL_MODIFIERS['capitalized']
                
                processed_parts.append(emoji_sequence)
            else:
                # Keep non-alphabetic parts as-is
                processed_parts.append(part)
        
        # Rejoin with underscores
        return '_'.join(processed_parts)


# Create global encoder instance for module-level functions
contextual_encoder = ContextualEncoder()


def encode(text: str) -> str:
    """Encode text using context-aware grammar detection.
    
    This is the main public interface for encoding English text to emoji
    sequences with intelligent grammatical context preservation.
    
    Args:
        text: Input English text to encode
        
    Returns:
        Encoded text with emoji sequences and contextual modifiers
        
    Example:
        >>> encode("The cat runs faster than the dog")
        "The 🐱 🏃 🏃➕ than the 🐕"
    """
    return contextual_encoder.encode_with_context(text)


def encode_simple(text: str) -> str:
    """Simple encoding without context detection (legacy).
    
    Provides backward compatibility for applications that need simple
    word-to-emoji mapping without grammatical context awareness.
    
    Args:
        text: Input text to encode
        
    Returns:
        Encoded text with basic word-to-emoji substitution
        
    Note:
        This function is deprecated. Use encode() for better results.
    """
    if not text:
        return text
        
    # Tokenize input to separate words and non-word characters
    tokens = re.findall(r'\b\w+\b|\W+', text)
    output = []

    for token in tokens:
        if token.strip().isalpha():
            word = token.lower()
            
            # Try direct word lookup first
            emoji_char = word_to_emoji.get(word)
            
            # If not found, try normalized form
            if emoji_char is None:
                normalized_word = normalizer.normalize_word(word)
                emoji_char = word_to_emoji.get(normalized_word, token)
            
            # Handle list-type emoji sequences
            if isinstance(emoji_char, list):
                output.append(''.join(emoji_char))
            else:
                output.append(emoji_char)
        else:
            # Preserve non-alphabetic tokens
            output.append(token)

    return ''.join(output)

def main() -> None:
    """Command-line interface for text-to-emoji encoding.
    
    Supports multiple input methods:
    - Command-line arguments: python encode.py "text to encode"
    - Piped input: echo "text to encode" | python encode.py
    - Interactive mode: python encode.py (prompts for input)
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
            sample = input('What do you want to encode to Emo? ')
            show_labels = True
        
        if not sample.strip():
            if show_labels:
                print("No input provided.")
            return
        
        # Encode using context-aware method
        encoded = encode(sample)
        
        # Display results
        if show_labels:
            print(f"Original: {sample}")
            print(f"Encoded : {encoded}")
        else:
            # For piped input, just output the encoded result
            print(encoded)
        
    except KeyboardInterrupt:
        if not sys.stdin.isatty():
            # Don't show interrupt message for piped input
            pass
        else:
            print("\nEncoding interrupted by user.")
    except Exception as e:
        print(f"Error during encoding: {e}", file=sys.stderr)


if __name__ == "__main__":
    main()
