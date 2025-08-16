#!/usr/bin/env python3
"""
Collision detection and resolution for emoji mappings.
Handles tracking used emojis and resolving conflicts.
"""

import logging
from collections import defaultdict
from typing import Dict, List, Optional, Set, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from .file_manager import NewMapping
    
from .config import RETRY_EMOJI_MARKER

logger = logging.getLogger(__name__)

class CollisionManager:
    """Manages emoji collision detection and resolution"""
    
    def __init__(self):
        """Initialize collision manager"""
        self.session_used_emojis: Set[str] = set()
    
    def track_emoji_usage(self, emoji: str) -> None:
        """Track an emoji as used in the current session"""
        if emoji:
            self.session_used_emojis.add(emoji)
    
    def get_all_used_emojis(self, existing_emojis: Set[str]) -> Set[str]:
        """Get all used emojis (both existing and from current session)"""
        return existing_emojis.union(self.session_used_emojis)
    
    def detect_collisions_in_batch(self, mappings: List['NewMapping'], existing_emojis: Set[str], emoji_to_word: Optional[Dict[str, str]] = None) -> Tuple[List['NewMapping'], List[Tuple[str, str, str]]]:
        """
        Detect emoji collisions within a batch and against existing mappings
        
        Args:
            mappings: List of new mappings to check
            existing_emojis: Set of already used emojis
            emoji_to_word: Optional mapping from emoji to word for better collision reporting
        
        Returns:
            Tuple of (accepted_mappings, collision_tuples)
        """
        # Create reverse mapping for existing emojis
        current_emoji_to_word = emoji_to_word or {}
        
        accepted_mappings = []
        collisions_to_resolve = []
        
        for mapping in mappings:
            if not mapping.suggested_emojis:
                # Skip mappings without emojis (errors, etc.)
                continue
            
            # Check for collision with existing mappings
            if mapping.suggested_emojis in existing_emojis:
                existing_word = current_emoji_to_word.get(mapping.suggested_emojis, "existing_word")
                # Skip collision if it's the same word (duplicate mapping)
                if existing_word != mapping.word:
                    logger.warning(f"Emoji collision detected: '{mapping.word}' wants '{mapping.suggested_emojis}' but it's already used by '{existing_word}'")
                    collisions_to_resolve.append((existing_word, mapping.word, mapping.suggested_emojis))
                else:
                    logger.debug(f"Skipping duplicate mapping: '{mapping.word}' already has emoji '{mapping.suggested_emojis}'")
                    # This is a duplicate, not a conflict - accept the mapping
                    accepted_mappings.append(mapping)
            else:
                # Check for collision within this batch
                batch_collision = False
                for accepted in accepted_mappings:
                    if accepted.suggested_emojis == mapping.suggested_emojis:
                        # Skip collision if it's the same word (duplicate)
                        if accepted.word != mapping.word:
                            logger.warning(f"Batch collision detected: '{mapping.word}' and '{accepted.word}' both want '{mapping.suggested_emojis}'")
                            collisions_to_resolve.append((accepted.word, mapping.word, mapping.suggested_emojis))
                            # Remove the previously accepted mapping since we'll resolve this collision
                            accepted_mappings = [m for m in accepted_mappings if m != accepted]
                            batch_collision = True
                        else:
                            logger.debug(f"Skipping duplicate batch mapping: '{mapping.word}' already processed with emoji '{mapping.suggested_emojis}'")
                            # This is a duplicate, skip it
                            batch_collision = True  # Set to true to prevent adding it again
                        break
                
                if not batch_collision:
                    accepted_mappings.append(mapping)
                    # Track this emoji to avoid further collisions in this batch
                    self.track_emoji_usage(mapping.suggested_emojis)
        
        return accepted_mappings, collisions_to_resolve
    
    def validate_collision_resolution(self, resolved_mappings: List['NewMapping']) -> Tuple[List['NewMapping'], List[Tuple[str, str, str]]]:
        """
        Validate that collision resolution didn't create new collisions
        
        Args:
            resolved_mappings: Mappings returned from collision resolution
        
        Returns:
            Tuple of (clean_mappings, new_collision_tuples)
        """
        # Check if LLM created NEW collisions in its response
        emoji_to_words = defaultdict(list)
        for mapping in resolved_mappings:
            if mapping.suggested_emojis:  # Skip empty emojis
                emoji_to_words[mapping.suggested_emojis].append(mapping.word)
        
        # Find new collisions created by LLM
        new_collisions = {emoji: words for emoji, words in emoji_to_words.items() if len(words) > 1}
        
        if new_collisions:
            logger.error(f"🚨 CRITICAL: LLM created NEW collisions while resolving existing ones!")
            
            # Collect all problem words
            all_problem_words = set()
            new_collision_tuples = []
            
            for emoji, words in new_collisions.items():
                logger.error(f"   {emoji} -> {words}")
                all_problem_words.update(words)
                
                # Create collision pairs from all words sharing this emoji
                for i in range(len(words)):
                    for j in range(i + 1, len(words)):
                        new_collision_tuples.append((words[i], words[j], emoji))
            
            # Remove all problem mappings from resolved_mappings
            clean_mappings = [m for m in resolved_mappings if m.word not in all_problem_words]
            
            logger.warning(f"⚠️  Found {len(new_collision_tuples)} new collision pairs, will retry in next batch")
            
            return clean_mappings, new_collision_tuples
        
        return resolved_mappings, []
    
    def create_collision_tuples_from_missing_words(self, missing_words: List[str]) -> List[Tuple[str, str, str]]:
        """
        Create collision tuples for missing words so they get processed together
        
        Args:
            missing_words: Words that need to be processed
        
        Returns:
            List of collision tuples with RETRY marker
        """
        collision_tuples = []
        
        # Group missing words into collision pairs so they get processed in the same batch
        for i in range(0, len(missing_words), 2):
            if i + 1 < len(missing_words):
                # Pair up missing words with a dummy emoji to force them into same batch
                collision_tuples.append((missing_words[i], missing_words[i + 1], RETRY_EMOJI_MARKER))
            else:
                # Single remaining word - handle it specially by creating a single-word tuple
                # We'll modify the other methods to handle this case
                collision_tuples.append((missing_words[i], None, RETRY_EMOJI_MARKER))
        
        return collision_tuples
    
    def format_collisions_for_prompt(self, collision_batch: List[Tuple[str, str, str]]) -> str:
        """Format collision tuples for inclusion in LLM prompt"""
        collisions_text = "\n".join([
            f"{i+1}. CONFLICT: '{word1}' vs '{word2}' both want '{emoji}'" if emoji != RETRY_EMOJI_MARKER 
            else f"{i+1}. RETRY: '{word1}'{' and \'' + word2 + '\'' if word2 else ''} need{'s' if not word2 else ''} new emoji mapping{'s' if word2 else ''}"
            for i, (word1, word2, emoji) in enumerate(collision_batch)
        ])
        return collisions_text
    
    def get_collision_words(self, collision_batch: List[Tuple[str, str, str]]) -> Set[str]:
        """Get all unique words involved in a batch of collisions"""
        collision_words = set()
        for word1, word2, _ in collision_batch:
            collision_words.add(word1)
            if word2 is not None:  # Handle None case for single words
                collision_words.add(word2)
        return collision_words
