#!/usr/bin/env python3
"""
Duplicate Emoji Mapping Resolver

This module provides intelligent resolution of duplicate emoji mappings where multiple
words map to the same emoji sequence. It uses an LLM to analyze semantic relationships
and reassign emojis while maintaining accuracy and ensuring one-to-one reversibility.

The system handles complex collision scenarios through:
- Batch processing for efficiency
- Recursive collision detection and resolution
- Semantic analysis for optimal emoji reassignment
- Iterative processing until all conflicts are resolved
- Comprehensive logging and error handling

Key Features:
- LLM-powered semantic conflict resolution
- Sub-batch handling for large conflict groups
- Collision detection with recursive resolution
- Incremental progress saving
- Emergency fallback mechanisms
"""

# Standard library imports
import argparse
import hashlib
import json
import logging
import os
import time
import unicodedata
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Third-party imports
from openai import OpenAI

# Local imports
from lib.word_normalizer import WordNormalizer

# Constants
DEFAULT_BASE_URL = "http://127.0.0.1:1234"
DEFAULT_MODEL = "openai/gpt-oss-20b"
DEFAULT_BATCH_SIZE = 8
MAX_RECURSION_DEPTH = 10
MAX_LLM_RETRIES = 3
RETRY_DELAY_BASE = 5

# File paths
MAPPING_FILE_PATH = "mappings/mapping.json"
LOGS_DIR = "logs"
BACKUPS_DIR = "mappings/backups"

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class DuplicateConflict:
    """Represents a duplicate emoji mapping conflict and its resolution.
    
    This dataclass encapsulates all information about a collision between
    multiple words mapping to the same emoji, including the LLM's resolution
    strategy and confidence assessment.
    
    Attributes:
        emoji: The original emoji that caused the conflict
        emoji_description: Human-readable description of the emoji
        conflicting_words: List of words that were mapped to the same emoji
        resolved_mappings: Dictionary mapping each word to its new emoji
        reasoning: Explanation of the resolution strategy used
        confidence: Confidence score (0.0-1.0) for the resolution quality
    """
    emoji: str
    emoji_description: str
    conflicting_words: List[str]
    resolved_mappings: Dict[str, str]  # word -> emoji
    reasoning: str
    confidence: float

class DuplicateMappingResolver:
    def __init__(self, base_url: str = "http://127.0.0.1:1234", model: str = "openai/gpt-oss-20b", save_after_each_query: bool = True, batch_size: int = 8):
        """Initialize the duplicate mapping resolver"""
        self.client = OpenAI(base_url=f"{base_url}/v1", api_key="not-needed")
        self.model = model
        self.mapping_path = Path("mappings/mapping.json")
        self.output_path = Path("logs")
        self.output_path.mkdir(exist_ok=True)
        self.save_after_each_query = save_after_each_query
        self.batch_size = batch_size
        # Create backup paths for incremental saves
        self.backup_path = Path("mappings/backups")
        self.backup_path.mkdir(exist_ok=True)
        # Initialize word normalizer for transformation elimination awareness
        self.normalizer = WordNormalizer()
        # Load current mappings
        self.word_to_emoji = {}
        self.emoji_to_word = {}
        self.load_mappings()
    
    def load_mappings(self):
        """Load current word-to-emoji mappings from mapping.json and build reverse in memory"""
        try:
            with open(self.mapping_path, 'r', encoding='utf-8') as f:
                self.word_to_emoji = json.load(f)
            logger.info(f"Loaded {len(self.word_to_emoji)} word-to-emoji mappings")
            self.emoji_to_word = {v: k for k, v in self.word_to_emoji.items()}
            logger.info(f"Built {len(self.emoji_to_word)} emoji-to-word mappings in memory")
        except FileNotFoundError as e:
            logger.error(f"Could not load mapping file: {e}")
            raise
    
    def get_emoji_description(self, emoji_str: str) -> str:
        """Get a human-readable description of emoji characters"""
        descriptions = []
        for char in emoji_str:
            try:
                name = unicodedata.name(char, "UNKNOWN")
                if name != "UNKNOWN":
                    # Clean up the name
                    name = name.replace("_", " ").title()
                    descriptions.append(name)
            except ValueError:
                continue
        return " + ".join(descriptions) if descriptions else "Unknown emoji"
    
    
    def find_duplicate_mappings(self) -> Dict[str, List[str]]:
        """Find all emoji that map to multiple words"""
        emoji_to_words = defaultdict(list)
        
        # Build reverse mapping to find duplicates
        for word, emoji in self.word_to_emoji.items():
            emoji_to_words[emoji].append(word)
        
        # Filter to only duplicates
        duplicates = {emoji: words for emoji, words in emoji_to_words.items() 
                     if len(words) > 1}
        
        logger.info(f"Found {len(duplicates)} emoji with duplicate word mappings")
        
        # Log details
        for emoji, words in duplicates.items():
            logger.info(f"  {emoji} maps to: {', '.join(words)}")
        
        return duplicates
    
    def resolve_duplicate_conflicts_batch(self, conflicts: List[Tuple[str, List[str]]]) -> List[DuplicateConflict]:
        """Use LLM to resolve a batch of duplicate emoji mapping conflicts"""
        
        if not conflicts:
            return []
        
        # Check for large conflict groups that need sub-batching
        sub_batched_conflicts = self._create_sub_batches(conflicts)
        
        # If we need to sub-batch, process recursively
        if len(sub_batched_conflicts) > len(conflicts):
            logger.info(f"🔄 Large conflict groups detected, processing {len(sub_batched_conflicts)} sub-batches instead of {len(conflicts)} original conflicts")
            all_resolutions = []
            for sub_batch in self._group_sub_batches_by_size(sub_batched_conflicts):
                batch_resolutions = self._process_single_batch(sub_batch)
                all_resolutions.extend(batch_resolutions)
            return all_resolutions
        
        # Process as normal batch
        return self._process_single_batch(conflicts)
    
    def _create_sub_batches(self, conflicts: List[Tuple[str, List[str]]], max_words_per_group: int = None) -> List[Tuple[str, List[str]]]:
        """Split large conflict groups into smaller chunks respecting batch size"""
        if max_words_per_group is None:
            max_words_per_group = self.batch_size  # Use the actual batch size
        
        sub_batched_conflicts = []
        
        for emoji, conflicting_words in conflicts:
            if len(conflicting_words) <= max_words_per_group:
                # Small enough group, keep as is
                sub_batched_conflicts.append((emoji, conflicting_words))
            else:
                # Large group, split into sub-batches
                logger.info(f"🔄 Splitting large conflict group {emoji} with {len(conflicting_words)} words into sub-batches (max {max_words_per_group} words each)")
                
                # Split words into chunks of max_words_per_group
                for i in range(0, len(conflicting_words), max_words_per_group):
                    chunk = conflicting_words[i:i + max_words_per_group]
                    # Create a unique identifier for the sub-batch by appending chunk index
                    sub_batch_emoji = f"{emoji}#sub{i // max_words_per_group + 1}"
                    sub_batched_conflicts.append((sub_batch_emoji, chunk))
                    logger.info(f"  📦 Created sub-batch {sub_batch_emoji} with {len(chunk)} words: {chunk}")
        
        return sub_batched_conflicts
    
    def _group_sub_batches_by_size(self, sub_batched_conflicts: List[Tuple[str, List[str]]]) -> List[List[Tuple[str, List[str]]]]:
        """Group sub-batches to respect the overall batch_size limit"""
        batches = []
        current_batch = []
        current_word_count = 0
        
        for emoji_key, words in sub_batched_conflicts:
            word_count = len(words)
            
            # If adding this sub-batch would exceed batch_size, start new batch
            if current_batch and current_word_count + word_count > self.batch_size:
                batches.append(current_batch)
                current_batch = []
                current_word_count = 0
            
            current_batch.append((emoji_key, words))
            current_word_count += word_count
        
        # Add remaining batch
        if current_batch:
            batches.append(current_batch)
        
        logger.info(f"📊 Grouped sub-batches into {len(batches)} batches respecting batch_size limit of {self.batch_size}")
        return batches
    
    def _process_single_batch(self, conflicts: List[Tuple[str, List[str]]]) -> List[DuplicateConflict]:
        """Process a single batch of conflicts through the LLM"""
        
        # Prepare batch information
        conflicts_info = []
        for i, (emoji, conflicting_words) in enumerate(conflicts):
            # Handle sub-batch emoji keys by extracting original emoji
            original_emoji = emoji.split('#')[0] if '#sub' in emoji else emoji
            emoji_description = self.get_emoji_description(original_emoji)
            words_list = ", ".join([f'"{word}"' for word in conflicting_words])
            conflicts_info.append({
                "index": i + 1,
                "emoji": original_emoji,
                "emoji_key": emoji,  # Keep track of sub-batch key
                "description": emoji_description,
                "words": conflicting_words,
                "words_formatted": words_list
            })
        
        # Get comprehensive list of existing mappings to avoid conflicts  
        original_emojis = {info['emoji'] for info in conflicts_info}
        existing_emojis = set(self.word_to_emoji.values()) - original_emojis
        
        # Include ALL existing emojis in the avoidance list (no sampling)
        sorted_existing = sorted(list(existing_emojis))
        existing_sample_text = ", ".join(sorted_existing)  # Include ALL emojis
        
        total_emojis_used = len(existing_emojis)
        logger.info(f"📊 Including ALL {total_emojis_used} existing emojis in avoidance list")
        logger.debug(f"Avoidance list length: {len(existing_sample_text)} characters")
        
        # Build conflicts description for prompt
        conflicts_text = ""
        for info in conflicts_info:
            conflicts_text += f"\n{info['index']}. Emoji: {info['emoji']} ({info['description']})\n   Conflicting words: {info['words_formatted']}\n"
        
        # Extract all words from conflicts for clear display
        all_conflict_words = []
        for _, conflicting_words in conflicts:
            all_conflict_words.extend(conflicting_words)
        
        # Create batch resolution prompt with creativity encouragement
        prompt = f"""
You are an expert in semantic analysis and emoji communication. You must assign emojis to these EXACT words: {', '.join(all_conflict_words)}

Words to assign: {conflicts_text}

🚨 CREATIVITY ENCOURAGEMENT - READ THIS CAREFULLY:
• YOU SHOULD CREATE NEW EMOJI COMBINATIONS when needed!
• The "existing emojis" list below shows what's ALREADY TAKEN by other words
• This is NOT a forbidden list - it's an "avoid duplicates" reference
• You are ENCOURAGED to use any emojis NOT in that list
• Feel free to combine 2-3 emojis creatively for better semantic representation
• Your goal is to find the BEST representation, not avoid emojis entirely

📋 EXISTING EMOJIS ALREADY USED (avoid these for uniqueness): {existing_sample_text}

🎯 EMOJI CREATIVITY GUIDELINES:

• BE CREATIVE with combinations! Examples of good creative combinations:
  - "birthday" → 🎂🎉 (cake + celebration)
  - "homework" → 📚✏️ (books + pencil)
  - "sunset" → 🌅🌇 (sunrise + evening)
  - "friendship" → 👥❤️ (people + love)
  - "cooking" → 👨‍🍳🍳 (chef + cooking)

• SINGLE EMOJIS are preferred when they clearly represent the concept
• COMBINATIONS (2-3 emojis) are encouraged when single emojis are insufficient
• AVOID using emojis from the "existing emojis" list above
• ENSURE each word gets a different emoji/combination within this batch

Assign a unique emoji to each of these words:
{', '.join(all_conflict_words)}

Respond with ONLY this JSON format using the EXACT word names as keys:
{{
    "{all_conflict_words[0] if all_conflict_words else 'word1'}": "emoji(s)",
    "{all_conflict_words[1] if len(all_conflict_words) > 1 else 'word2'}": "emoji(s)",
    "{all_conflict_words[2] if len(all_conflict_words) > 2 else 'word3'}": "emoji(s)"
    ...
}}

Rules:
- Use the EXACT word names as keys in the JSON
- Each word gets one unique emoji sequence (no duplicate sequences)
- Emoji sequences can be 1-3 emojis long, order matters (🎂🎉 ≠ 🎉🎂)
- Don't use any emoji sequence from the existing list above
- Choose semantically appropriate emoji sequences
- IMPORTANT: If an emoji is absolutely perfect for a word (like 🦊 for "fox" or 🧮 for "calculator"), that word should definitely keep the original emoji - prioritize semantic accuracy
- Other less semantically perfect words should get reassigned to new appropriate emojis
- Prefer single emojis when possible, use combinations only when needed for clarity
- BE CREATIVE and find the BEST representation for each word
- Include ALL words: {', '.join(all_conflict_words)}
"""
        
        # Log the prompt being sent to LLM (filter out the long emoji avoidance list)
        logger.info(f"📤 Sending batch prompt to LLM ({len(prompt)} characters):")
        logger.info(f"--- BATCH PROMPT START ---")
        
        # Filter out the long emoji avoidance line for terminal output
        prompt_lines = prompt.split('\n')
        filtered_lines = []
        for line in prompt_lines:
            if line.startswith('These emojis are already used by other words, DO NOT suggest them:'):
                filtered_lines.append('These emojis are already used by other words, DO NOT suggest them: [FULL LIST OF ALL EXISTING EMOJIS - FILTERED FROM LOG]')
            elif line.startswith('Existing emojis to AVOID:'):
                filtered_lines.append('Existing emojis to AVOID: [FULL LIST OF ALL EXISTING EMOJIS - FILTERED FROM LOG]')
            elif line.startswith('📋 EXISTING EMOJIS ALREADY USED (avoid these for uniqueness):'):
                filtered_lines.append('📋 EXISTING EMOJIS ALREADY USED (avoid these for uniqueness): [TRUNCATED - FULL LIST FILTERED FROM LOG]')
            else:
                filtered_lines.append(line)
        
        filtered_prompt = '\n'.join(filtered_lines)
        logger.info(filtered_prompt)
        logger.info(f"--- BATCH PROMPT END ---")

        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                # Start timing the LLM request
                llm_start_time = time.time()
                
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    #temperature=0.3,
                   # max_tokens=50000
                )
                
                # Calculate and log LLM response time
                llm_response_time = time.time() - llm_start_time
                logger.info(f"⏱️  LLM batch response time: {llm_response_time:.2f} seconds")
                
                result_text = response.choices[0].message.content.strip()
                
                # Validate result text
                if not result_text:
                    raise ValueError("Empty response from LLM")
                
                # Extract JSON from the response with better parsing
                json_result = self._parse_json_response(result_text)
                
                if not json_result:
                    raise ValueError("No valid JSON found in response")
                
                # Pretty print the JSON response for debugging
                logger.info(f"🤖 LLM JSON Response (pretty printed):")
                logger.info(json.dumps(json_result, indent=2, ensure_ascii=False))
                
                # Validate that we have a proper mapping structure
                if not isinstance(json_result, dict):
                    raise ValueError(f"Expected JSON object, got {type(json_result)}")
                
                # Validate all required words are present
                all_words = set()
                for _, conflicting_words in conflicts:
                    all_words.update(conflicting_words)
                
                missing_words = []
                for word in all_words:
                    if word not in json_result or not json_result[word].strip():
                        missing_words.append(word)
                
                if missing_words:
                    logger.warning(f"⚠️  Missing mappings for words: {missing_words}")
                    raise ValueError(f"Incomplete mappings for {len(missing_words)} words")
                
                # All validation passed - process the result
                all_word_mappings = json_result
                
                # Convert to individual DuplicateConflict objects
                resolved_conflicts = []
                
                # Log the overall batch response
                logger.info(f"🤖 LLM Batch Resolution for {len(conflicts)} conflicts:")
                
                for i, (original_emoji, conflicting_words) in enumerate(conflicts):
                    # Extract original emoji from sub-batch key if needed
                    display_emoji = original_emoji.split('#')[0] if '#sub' in original_emoji else original_emoji
                    
                    # Extract mappings for this conflict's words
                    resolved_mappings = {}
                    found_words = 0
                    
                    for word in conflicting_words:
                        if word in all_word_mappings:
                            resolved_mappings[word] = all_word_mappings[word]
                            found_words += 1
                    
                    if found_words == len(conflicting_words):
                        # All words for this conflict were resolved
                        conflict_confidence = 0.85  # Default confidence for simplified format
                        
                        # Log detailed resolution for this conflict
                        emoji_description = self.get_emoji_description(display_emoji)
                        logger.info(f"\n  📋 Conflict {i + 1}: {display_emoji} ({emoji_description})")
                        if '#sub' in original_emoji:
                            logger.info(f"    🔄 Sub-batch: {original_emoji}")
                        for word, new_emoji in resolved_mappings.items():
                            if new_emoji == display_emoji:
                                logger.info(f"    ✅ '{word}' keeps original → {new_emoji}")
                            else:
                                logger.info(f"    🔄 '{word}' reassigned → {new_emoji}")
                        logger.info(f"    🎯 Confidence: {conflict_confidence:.2f}")
                        
                        # Create DuplicateConflict object using display_emoji
                        resolved_conflicts.append(DuplicateConflict(
                            emoji=display_emoji,
                            emoji_description=emoji_description,
                            conflicting_words=conflicting_words,
                            resolved_mappings=resolved_mappings,
                            reasoning="Resolved using LLM with validation",
                            confidence=conflict_confidence
                        ))
                    else:
                        logger.warning(f"⚠️  Incomplete resolution for conflict {i + 1}: {display_emoji} - only {found_words}/{len(conflicting_words)} words resolved")
                        # Create emergency resolution for incomplete response
                        resolved_conflicts.append(self._create_emergency_resolution(display_emoji, conflicting_words))
                
                return resolved_conflicts
                
            except (json.JSONDecodeError, ValueError, KeyError, AttributeError) as e:
                retry_count += 1
                logger.error(f"❌ JSON parsing/validation error (attempt {retry_count}/{max_retries}): {e}")
                
                if retry_count < max_retries:
                    logger.info(f"⏳ Retrying with same complete prompt after 5 second delay...")
                    time.sleep(5)
                    # Keep using the same complete prompt with full emoji avoidance list
                    # Do not change the prompt - the issue is likely LLM response formatting, not the prompt
                else:
                    logger.error(f"❌ Failed to get valid response after {max_retries} attempts")
                    # Log failed resolution attempt
                    self._log_failed_resolution(conflicts, f"JSON parsing failed: {e}")
                    # Return emergency resolutions for all conflicts
                    return [self._create_emergency_resolution(emoji.split('#')[0] if '#sub' in emoji else emoji, words) for emoji, words in conflicts]
                    
            except Exception as e:
                retry_count += 1
                logger.error(f"❌ LLM API error (attempt {retry_count}/{max_retries}): {e}")
                
                if retry_count < max_retries:
                    logger.info(f"⏳ Retrying LLM request after {5 * retry_count} second delay...")
                    time.sleep(5 * retry_count)  # Exponential backoff
                else:
                    logger.error(f"❌ Failed to get response from LLM after {max_retries} attempts")
                    # Log failed resolution attempt
                    self._log_failed_resolution(conflicts, f"LLM API failed: {e}")
                    # Return emergency resolutions for all conflicts
                    return [self._create_emergency_resolution(emoji.split('#')[0] if '#sub' in emoji else emoji, words) for emoji, words in conflicts]
        
        # Should not reach here, but just in case
        logger.error("❌ Unexpected exit from retry loop")
        return [self._create_emergency_resolution(emoji.split('#')[0] if '#sub' in emoji else emoji, words) for emoji, words in conflicts]
    
    def resolve_duplicate_conflict(self, emoji: str, conflicting_words: List[str]) -> DuplicateConflict:
        """Use LLM to resolve a duplicate emoji mapping conflict"""
        
        emoji_description = self.get_emoji_description(emoji)
        words_list = ", ".join([f'"{word}"' for word in conflicting_words])
        
        # Get a comprehensive list of existing mappings to avoid conflicts
        original_emojis = {emoji}  # The emoji we're resolving
        existing_emojis = set(self.word_to_emoji.values()) - original_emojis
        
        # Include ALL existing emojis in the avoidance list (no sampling)
        sorted_existing = sorted(list(existing_emojis))
        existing_sample_text = ", ".join(sorted_existing)  # Include ALL emojis
        
        # Log complete information
        total_emojis_used = len(existing_emojis)
        logger.info(f"📊 Including ALL {total_emojis_used} existing emojis in avoidance list")
        logger.debug(f"Avoidance list length: {len(existing_sample_text)} characters")
        
        # Create resolution prompt
        prompt = f"""
You are an expert in semantic analysis and emoji communication. You need to resolve a duplicate emoji mapping conflict where multiple words are mapped to the same emoji, breaking the reversibility requirement.

CONFLICT:
- Emoji: {emoji}
- Description: {emoji_description}  
- Conflicting words: {words_list}

🚨 CREATIVITY ENCOURAGEMENT - READ THIS CAREFULLY:
• YOU SHOULD CREATE NEW EMOJI COMBINATIONS when needed!
• The "existing emojis" list below shows what's ALREADY TAKEN by other words
• This is NOT a forbidden list - it's an "avoid duplicates" reference
• You are ENCOURAGED to use any emojis NOT in that list
• Feel free to combine 2-3 emojis creatively for better semantic representation
• Your goal is to find the BEST representation, not avoid emojis entirely

📋 EXISTING EMOJIS ALREADY USED (avoid these for uniqueness):
{existing_sample_text}

🎯 EMOJI CREATIVITY GUIDELINES:

• BE CREATIVE with combinations! Examples of good creative combinations:
  - "birthday" → 🎂🎉 (cake + celebration)
  - "homework" → 📚✏️ (books + pencil)
  - "sunset" → 🌅🌇 (sunrise + evening)
  - "friendship" → 👥❤️ (people + love)
  - "cooking" → 👨‍🍳🍳 (chef + cooking)

• SINGLE EMOJIS are preferred when they clearly represent the concept
• COMBINATIONS (2-3 emojis) are encouraged when single emojis are insufficient
• AVOID using emojis from the "existing emojis" list above

TASK: Resolve this conflict by assigning each word a unique emoji or emoji combination that:
1. Has clear semantic connection to the word's meaning
2. Is universally recognizable and culturally appropriate
3. Works well for encoding/decoding text
4. Uses 1-3 emojis maximum (prefer the fewest emojis possible)
5. Is UNIQUE and doesn't conflict with existing mappings

REQUIREMENTS:
- Each word must map to a unique emoji sequence (no duplicate sequences)
- Emoji sequences can be 1-3 emojis long, order matters for uniqueness
- All emoji assignments must be semantically accurate and intuitive
- Prioritize single emojis over combinations when possible
- Use emoji combinations (2-3 emojis) only when a single emoji cannot adequately represent the concept
- Consider cultural universality and visual clarity
- AVOID ALL EXISTING EMOJI SEQUENCES listed above
- CRITICAL: If the original emoji is absolutely perfect for one of the words (like {emoji} for a word that directly represents it), that word should definitely keep the original emoji. Prioritize semantic accuracy over avoiding duplicates initially - we'll handle remaining duplicates later.
- BE CREATIVE and find the BEST representation for each word

Please respond in this exact JSON format:
{{
    "word1": "emoji1",
    "word2": "emoji2", 
    "word3": "emoji3"
}}

Guidelines for emoji assignment:
- Choose the most semantically appropriate emoji(s) for each word
- For single emoji assignments, select emojis that directly represent the concept
- For multi-emoji assignments, combine emojis that together convey the meaning
- Prioritize semantic clarity and cultural universality
- IMPORTANT: The most semantically perfect word should keep the original emoji {emoji}
- Other words should get reassigned to new appropriate emojis
- BE CREATIVE with combinations to find perfect representations

Example resolutions with single emojis:
- "cat" → 🐱, "kitten" → 🐾 (direct representation vs related concept)
- "happy" → 😊, "joy" → 🎉 (emotion vs celebration)
- "house" → 🏠, "home" → 🏡 (building vs dwelling)
- "fox" → 🦊, "animal" → 🐾 (specific vs general)
- "calculator" → 🧮, "compute" → 💻 (tool vs action)

Example resolutions with emoji combinations:
- "birthday" → 🎂🎉 (cake + celebration)
- "software" → 💻⚙️ (computer + gear)
- "friendship" → 👥❤️ (people + love)
- "morning" → 🌅☀️ (sunrise + sun)
- "teacher" → 👨‍🏫📚 (teacher + books)
- "library" → 📚🏛️ (books + building)
- "teamwork" → 👥🤝 (people + handshake)

Prioritize single emojis when they adequately represent the concept, use combinations when they provide better semantic representation.
"""
        
        # Log the prompt being sent to LLM (filter out the long emoji avoidance list)
        logger.info(f"📤 Sending single conflict prompt to LLM ({len(prompt)} characters):")
        logger.info(f"--- SINGLE PROMPT START ---")
        
        # Filter out the long emoji avoidance line for terminal output
        prompt_lines = prompt.split('\n')
        filtered_lines = []
        for line in prompt_lines:
            if line.startswith('These emojis are already used by other words, DO NOT suggest them:'):
                filtered_lines.append('These emojis are already used by other words, DO NOT suggest them: [FULL LIST OF ALL EXISTING EMOJIS - FILTERED FROM LOG]')
            elif line.startswith('📋 EXISTING EMOJIS ALREADY USED (avoid these for uniqueness):'):
                filtered_lines.append('📋 EXISTING EMOJIS ALREADY USED (avoid these for uniqueness): [TRUNCATED - FULL LIST FILTERED FROM LOG]')
            else:
                filtered_lines.append(line)
        
        filtered_prompt = '\n'.join(filtered_lines)
        logger.info(filtered_prompt)
        logger.info(f"--- SINGLE PROMPT END ---")

        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                # Start timing the LLM request
                llm_start_time = time.time()
                
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.3,
                    max_tokens=30000
                )
                
                # Calculate and log LLM response time
                llm_response_time = time.time() - llm_start_time
                logger.info(f"⏱️  LLM single response time: {llm_response_time:.2f} seconds")
                
                result_text = response.choices[0].message.content.strip()
                
                # Validate result text
                if not result_text:
                    raise ValueError("Empty response from LLM")
                
                # Extract JSON from the response with better parsing
                json_result = self._parse_json_response(result_text)
                
                if not json_result:
                    raise ValueError("No valid JSON found in response")
                
                # Pretty print the JSON response for debugging
                logger.info(f"🤖 LLM JSON Response (pretty printed):")
                logger.info(json.dumps(json_result, indent=2, ensure_ascii=False))
                
                # Validate that we have a proper mapping structure
                if not isinstance(json_result, dict):
                    raise ValueError(f"Expected JSON object, got {type(json_result)}")
                
                # Validate all required words are present
                missing_words = []
                for word in conflicting_words:
                    if word not in json_result or not json_result[word].strip():
                        missing_words.append(word)
                
                if missing_words:
                    logger.warning(f"⚠️  Missing mappings for words: {missing_words}")
                    raise ValueError(f"Incomplete mappings for {len(missing_words)} words")
                
                # All validation passed
                resolved_mappings = json_result
                
                # Log the detailed resolution from this LLM response
                logger.info(f"🤖 LLM Resolution for {emoji} ({emoji_description}):")
                for word, new_emoji in resolved_mappings.items():
                    if new_emoji == emoji:
                        logger.info(f"  ✅ '{word}' keeps original → {new_emoji}")
                    else:
                        logger.info(f"  🔄 '{word}' reassigned → {new_emoji}")
                
                # Use validated resolution
                reasoning = "Resolved using LLM with validation"
                confidence = 0.85  # Default confidence for valid resolution
                logger.info(f"  🎯 Confidence: {confidence:.2f}")
                
                return DuplicateConflict(
                    emoji=emoji,
                    emoji_description=emoji_description,
                    conflicting_words=conflicting_words,
                    resolved_mappings=resolved_mappings,
                    reasoning=reasoning,
                    confidence=confidence
                )
                
            except (json.JSONDecodeError, ValueError, KeyError, AttributeError) as e:
                retry_count += 1
                logger.error(f"❌ JSON parsing/validation error (attempt {retry_count}/{max_retries}): {e}")
                
                if retry_count < max_retries:
                    logger.info(f"⏳ Retrying with same complete prompt after 5 second delay...")
                    time.sleep(5)
                    # Keep using the same complete prompt with full emoji avoidance list
                    # Do not change the prompt - the issue is likely LLM response formatting, not the prompt
                else:
                    logger.error(f"❌ Failed to get valid response after {max_retries} attempts")
                    # Log failed resolution attempt
                    self._log_failed_resolution([(emoji, conflicting_words)], f"JSON parsing failed: {e}")
                    # Use emergency resolution as last resort
                    return self._create_emergency_resolution(emoji, conflicting_words)
                    
            except Exception as e:
                retry_count += 1
                logger.error(f"❌ LLM API error (attempt {retry_count}/{max_retries}): {e}")
                
                if retry_count < max_retries:
                    logger.info(f"⏳ Retrying LLM request after {5 * retry_count} second delay...")
                    time.sleep(5 * retry_count)  # Exponential backoff
                else:
                    logger.error(f"❌ Failed to get response from LLM after {max_retries} attempts")
                    # Log failed resolution attempt
                    self._log_failed_resolution([(emoji, conflicting_words)], f"LLM API failed: {e}")
                    # Use emergency resolution as last resort
                    return self._create_emergency_resolution(emoji, conflicting_words)
        
        # Should not reach here, but just in case
        logger.error("❌ Unexpected exit from retry loop")
        return self._create_emergency_resolution(emoji, conflicting_words)
    
    def resolve_all_duplicates(self, max_iterations: int = 5) -> List[DuplicateConflict]:
        """Resolve all duplicate emoji mappings with iterative conflict detection"""
        all_resolutions = []
        iteration = 0
        
        while iteration < max_iterations:
            iteration += 1
            logger.info(f"\n=== Resolution Iteration {iteration} ===")
            
            duplicates = self.find_duplicate_mappings()
            
            if not duplicates:
                logger.info("✅ No duplicate mappings found!")
                break
            
            logger.info(f"Found {len(duplicates)} conflicts to resolve in iteration {iteration}")
            
            # Process duplicates in batches based on total word count
            batch_resolutions = []
            duplicate_items = list(duplicates.items())
            
            # Create batches limited by total word count
            batches = self.create_word_limited_batches(duplicate_items, self.batch_size)
            
            for batch_num, current_batch in enumerate(batches, 1):
                total_words = sum(len(conflicting_words) for _, conflicting_words in current_batch)
                logger.info(f"\n📦 Processing batch {batch_num}/{len(batches)}")
                logger.info(f"    {len(current_batch)} conflicts, {total_words} total words (limit: {self.batch_size})")
                
                # Log conflicts in this batch
                for emoji, conflicting_words in current_batch:
                    logger.info(f"    📋 {emoji} → {conflicting_words} ({len(conflicting_words)} words)")
                
                # Get batch resolution from LLM
                logger.info(f"🤖 Sending batch of {total_words} words to LLM...")
                batch_resolved = self.resolve_duplicate_conflicts_batch(current_batch)
                
                # Apply collision detection and resolution for each conflict in the batch
                for i, resolution in enumerate(batch_resolved):
                    original_emoji, original_words = current_batch[i]
                    logger.info(f"\n🔍 Applying collision detection for {original_emoji} → {original_words}")
                    
                    # Use collision-aware resolution (this may recursively resolve new conflicts)
                    final_resolution = self.apply_collision_detection_to_resolution(resolution)
                    batch_resolutions.append(final_resolution)
                    
                    # Apply this resolution immediately to avoid conflicts with subsequent resolutions
                    self.apply_single_resolution(final_resolution)
                    all_resolutions.append(final_resolution)
                    
                    # Save progress after each resolution - FORCE UPDATE MAIN FILES
                    logger.info("💾 Updating main mapping files after resolution...")
                    self.save_main_mappings() # Save main files immediately
                    self.save_incremental_progress(iteration, all_resolutions)
                    
                    logger.info(f"✅ Conflict for {original_emoji} fully resolved and applied!")
                
                logger.info(f"✅ Batch {batch_num} completed ({len(batch_resolved)} conflicts resolved)")
                
                # Rate limiting between batches
                if batch_num < len(batches):
                    logger.info(f"⏳ Waiting 2 seconds before next batch...")
                    time.sleep(2)
            
            # Save main mappings after this batch (resolutions were already applied individually)
            if batch_resolutions:
                self.save_main_mappings()
            
            # Log summary of what was applied in this iteration
            logger.info(f"\n🎯 Iteration {iteration} Summary:")
            logger.info(f"  📊 Resolutions applied: {len(batch_resolutions)}")
            for resolution in batch_resolutions:
                changes = []
                for word, new_emoji in resolution.resolved_mappings.items():
                    if new_emoji == resolution.emoji:
                        changes.append(f"'{word}'→{new_emoji}")
                    else:
                        changes.append(f"'{word}'→{new_emoji}")
                logger.info(f"  🔧 {resolution.emoji}: {', '.join(changes)}")
            logger.info(f"  💾 Main mapping files updated")
            logger.info(f"")
            
            # Check if we need another iteration
            new_duplicates = self.find_duplicate_mappings()
            if not new_duplicates:
                logger.info(f"✅ All conflicts resolved after {iteration} iterations!")
                break
            elif len(new_duplicates) == len(duplicates):
                logger.warning(f"No progress made in iteration {iteration}, stopping to avoid infinite loop")
                break
        
        if iteration >= max_iterations:
            logger.warning(f"Reached maximum iterations ({max_iterations}), some conflicts may remain")
        
        return all_resolutions
    
    def validate_resolution(self, resolutions: List[DuplicateConflict]) -> Tuple[bool, List[str]]:
        """Validate that resolutions don't create new conflicts"""
        errors = []
        all_new_emojis = set()
        
        for resolution in resolutions:
            for word, emoji in resolution.resolved_mappings.items():
                if emoji in all_new_emojis:
                    errors.append(f"Resolution creates new conflict: {emoji} assigned to multiple words")
                all_new_emojis.add(emoji)
        
        # Check against existing mappings (excluding the original conflicts)
        original_emojis = {res.emoji for res in resolutions}
        existing_emojis = set(self.word_to_emoji.values()) - original_emojis
        
        for emoji in all_new_emojis:
            if emoji in existing_emojis:
                existing_word = self.emoji_to_word.get(emoji, "unknown")
                errors.append(f"Resolution conflicts with existing mapping: {emoji} -> {existing_word}")
        
        return len(errors) == 0, errors
    
    def filter_valid_resolutions(self, resolutions: List[DuplicateConflict]) -> List[DuplicateConflict]:
        """Filter resolutions to only include ones that don't create conflicts"""
        valid_resolutions = []
        for resolution in resolutions:
            # Validate this individual resolution
            is_valid, _ = self.validate_resolution([resolution])
            if is_valid:
                valid_resolutions.append(resolution)
            else:
                logger.warning(f"Skipping invalid resolution for {resolution.emoji}")
        return valid_resolutions
    
    def detect_new_collisions(self, resolution: DuplicateConflict) -> List[Tuple[str, List[str]]]:
        """Detect if a resolution creates new collisions with existing mappings"""
        new_collisions = []
        
        for word, new_emoji in resolution.resolved_mappings.items():
            # Check if this new emoji already exists in our mappings
            conflicting_words = []
            
            # Check against existing mappings (excluding the original conflict emoji)
            for existing_word, existing_emoji in self.word_to_emoji.items():
                if existing_emoji == new_emoji and existing_word != word and existing_emoji != resolution.emoji:
                    conflicting_words.append(existing_word)
            
            # If we found conflicts, add the new word too
            if conflicting_words:
                conflicting_words.append(word)
                new_collisions.append((new_emoji, conflicting_words))
                logger.warning(f"🔄 New collision detected: {new_emoji} now maps to {conflicting_words}")
        
        return new_collisions
    
    def create_word_limited_batches(self, duplicate_items: List[Tuple[str, List[str]]], max_words: int) -> List[List[Tuple[str, List[str]]]]:
        """Create batches of conflicts limited by total word count rather than number of conflicts"""
        batches = []
        current_batch = []
        current_word_count = 0
        
        for emoji, conflicting_words in duplicate_items:
            word_count = len(conflicting_words)
            
            # If this single conflict has too many words, split it
            if word_count > max_words:
                # Process any current batch first
                if current_batch:
                    batches.append(current_batch)
                    current_batch = []
                    current_word_count = 0
                
                # Split the large conflict into smaller chunks
                logger.info(f"🔄 Splitting large conflict {emoji} with {word_count} words into chunks of {max_words}")
                for i in range(0, word_count, max_words):
                    chunk_words = conflicting_words[i:i + max_words]
                    chunk_emoji = f"{emoji}#chunk{i // max_words + 1}" if i > 0 else emoji
                    batches.append([(chunk_emoji, chunk_words)])
                    logger.info(f"  📦 Created chunk: {chunk_emoji} with {len(chunk_words)} words")
                continue
            
            # If adding this conflict would exceed the limit, start a new batch
            if current_batch and current_word_count + word_count > max_words:
                batches.append(current_batch)
                current_batch = []
                current_word_count = 0
            
            # Add the conflict to current batch
            current_batch.append((emoji, conflicting_words))
            current_word_count += word_count
            
            # If we've reached exactly the max words, close this batch
            if current_word_count >= max_words:
                batches.append(current_batch)
                current_batch = []
                current_word_count = 0
        
        # Add any remaining conflicts
        if current_batch:
            batches.append(current_batch)
        
        # Log batch statistics
        logger.info(f"Created {len(batches)} batches with max {max_words} words per batch:")
        for i, batch in enumerate(batches, 1):
            total_words = sum(len(words) for _, words in batch)
            logger.info(f"  Batch {i}: {len(batch)} conflicts, {total_words} words")
            
            # Warn if any batch exceeds the limit
            if total_words > max_words:
                logger.warning(f"  ⚠️  Batch {i} exceeds limit: {total_words} > {max_words}")
        
        return batches
    
    def apply_collision_detection_to_resolution(self, resolution: DuplicateConflict, depth: int = 0) -> DuplicateConflict:
        """Apply collision detection to an existing resolution, resolving any new conflicts recursively"""
        if depth > 10:  # Prevent infinite recursion
            logger.error(f"⚠️  Maximum recursion depth reached for {resolution.emoji}, stopping")
            raise Exception("Maximum recursion depth reached")
        
        indent = "  " * depth
        logger.info(f"{indent}🔍 Checking resolution for {resolution.emoji} → {resolution.conflicting_words} (depth: {depth})")
        
        # Check for new collisions this resolution might create
        new_collisions = self.detect_new_collisions(resolution)
        
        if not new_collisions:
            logger.info(f"{indent}✅ Clean resolution for {resolution.emoji}")
            return resolution
        
        # We have new collisions - resolve them recursively
        logger.warning(f"{indent}⚠️  Resolution created {len(new_collisions)} new collisions, resolving recursively...")
        
        # Resolve each new collision
        for collision_emoji, collision_words in new_collisions:
            logger.info(f"{indent}🔄 Recursively resolving collision: {collision_emoji} → {collision_words}")
            
            # Recursively resolve this new collision (single conflict, not batch)
            nested_resolution = self.resolve_with_collision_detection(collision_emoji, collision_words, depth + 1)
            
            # Apply the nested resolution immediately to avoid further conflicts
            self.apply_single_resolution(nested_resolution)
            
        # After resolving nested collisions, check if our original resolution is still valid
        updated_collisions = self.detect_new_collisions(resolution)
        if updated_collisions:
            # Still have conflicts, retry the original resolution
            logger.info(f"{indent}🔄 Re-checking original resolution after nested fixes...")
            return self.apply_collision_detection_to_resolution(resolution, depth + 1)
        
        logger.info(f"{indent}✅ Final resolution for {resolution.emoji} is clean")
        return resolution
    
    def resolve_with_collision_detection(self, emoji: str, conflicting_words: List[str], depth: int = 0) -> DuplicateConflict:
        """Resolve conflicts with recursive collision detection"""
        if depth > 10:  # Prevent infinite recursion
            logger.error(f"⚠️  Maximum recursion depth reached for {emoji}, stopping")
            raise Exception("Maximum recursion depth reached")
        
        indent = "  " * depth
        logger.info(f"{indent}🔍 Resolving {emoji} → {conflicting_words} (depth: {depth})")
        
        # Check if we need to use batch processing for large conflicts
        if len(conflicting_words) > self.batch_size:
            logger.info(f"{indent}⚠️  Large collision with {len(conflicting_words)} words, using batch processing (limit: {self.batch_size})")
            # Use batch processing instead of single conflict resolution
            batch_conflicts = [(emoji, conflicting_words)]
            batch_resolutions = self.resolve_duplicate_conflicts_batch(batch_conflicts)
            if batch_resolutions:
                # Save mapping files immediately after getting batch resolutions
                self.save_main_mappings()
                return batch_resolutions[0]  # Return the first (and only) resolution
            else:
                # Fallback to emergency resolution
                logger.warning(f"{indent}❌ Batch processing failed, using emergency resolution")
                return self._create_emergency_resolution(emoji, conflicting_words)
        
        # Get initial resolution from LLM for smaller conflicts
        resolution = self.resolve_duplicate_conflict(emoji, conflicting_words)
        
        # Save mapping files immediately after getting resolution
        self.save_main_mappings()
        
        # Check for new collisions this resolution might create
        new_collisions = self.detect_new_collisions(resolution)
        
        if not new_collisions:
            logger.info(f"{indent}✅ Clean resolution for {emoji}")
            return resolution
        
        # We have new collisions - resolve them recursively
        logger.warning(f"{indent}⚠️  Resolution created {len(new_collisions)} new collisions, resolving recursively...")
        
        # Resolve each new collision (they will also be checked for batch size)
        for collision_emoji, collision_words in new_collisions:
            logger.info(f"{indent}🔄 Recursively resolving collision: {collision_emoji} → {collision_words} ({len(collision_words)} words)")
            
            # Recursively resolve this new collision (with batch size checking)
            nested_resolution = self.resolve_with_collision_detection(collision_emoji, collision_words, depth + 1)
            
            # Apply the nested resolution immediately to avoid further conflicts
            self.apply_single_resolution(nested_resolution)
            
        # After resolving nested collisions, check if our original resolution is still valid
        updated_collisions = self.detect_new_collisions(resolution)
        if updated_collisions:
            # Still have conflicts, retry the original resolution
            logger.info(f"{indent}🔄 Re-checking original resolution after nested fixes...")
            return self.resolve_with_collision_detection(emoji, conflicting_words, depth + 1)
        
        logger.info(f"{indent}✅ Final resolution for {emoji} is clean")
        return resolution
    
    def apply_single_resolution(self, resolution: DuplicateConflict):
        """Apply a single resolution to the working mappings immediately"""
        # Remove old mappings for conflicting words
        for word in resolution.conflicting_words:
            if resolution.emoji in self.emoji_to_word:
                del self.emoji_to_word[resolution.emoji]
        
        # Apply new mappings
        for word, new_emoji in resolution.resolved_mappings.items():
            old_emoji = self.word_to_emoji.get(word)
            
            # Update working mappings
            self.word_to_emoji[word] = new_emoji
            self.emoji_to_word[new_emoji] = word
            
            # Clean up old reverse mapping if it exists
            if old_emoji and old_emoji in self.emoji_to_word and self.emoji_to_word[old_emoji] == word:
                del self.emoji_to_word[old_emoji]
                
            logger.debug(f"Applied: '{word}': {old_emoji} → {new_emoji}")
        
        # Save to disk after each resolution
        self.save_main_mappings()
    
    def save_incremental_progress(self, iteration: int, resolutions_so_far: List[DuplicateConflict]):
        """Save incremental progress after each LLM query to prevent data loss"""
        if not self.save_after_each_query:
            return
        
        try:
            timestamp = int(time.time())
            
            # Save current working mappings as backup
            backup_word_path = self.backup_path / f"word_to_emoji_iter{iteration}_{timestamp}.json"
            backup_emoji_path = self.backup_path / f"emoji_to_word_iter{iteration}_{timestamp}.json"
            
            with open(backup_word_path, 'w', encoding='utf-8') as f:
                json.dump(self.word_to_emoji, f, indent=2, ensure_ascii=False)
            
            with open(backup_emoji_path, 'w', encoding='utf-8') as f:
                json.dump(self.emoji_to_word, f, indent=2, ensure_ascii=False)
            
            # Save current resolutions log
            if resolutions_so_far:
                resolutions_backup = self.output_path / f"resolutions_iter{iteration}_{timestamp}.json"
                self.save_resolutions(resolutions_so_far, resolutions_backup.name)
            
            logger.info(f"💾 Incremental progress saved: iteration {iteration}, {len(resolutions_so_far)} resolutions")
            
        except Exception as e:
            logger.error(f"Failed to save incremental progress: {e}")
    
    def save_main_mappings(self):
        """Save the main mapping file (called after each successful resolution)"""
        try:
            with open(self.mapping_path, 'w', encoding='utf-8') as f:
                json.dump(self.word_to_emoji, f, indent=2, ensure_ascii=False)
                f.flush()
                import os
                os.fsync(f.fileno())
            logger.info("✅ Main mapping file updated and synced to disk")
        except Exception as e:
            logger.error(f"Failed to save main mapping: {e}")
    
    def apply_resolutions_to_working_mappings(self, resolutions: List[DuplicateConflict]):
        """Apply resolutions to the working mappings (in-memory) for iterative processing"""
        for resolution in resolutions:
            # Remove old mappings for conflicting words
            for word in resolution.conflicting_words:
                if word in self.word_to_emoji:
                    old_emoji = self.word_to_emoji[word]
                    if old_emoji in self.emoji_to_word and self.emoji_to_word[old_emoji] == word:
                        del self.emoji_to_word[old_emoji]
                    del self.word_to_emoji[word]
            # Apply new mappings
            for word, new_emoji in resolution.resolved_mappings.items():
                self.word_to_emoji[word] = new_emoji
                self.emoji_to_word[new_emoji] = word
                logger.debug(f"Working mapping updated: '{word}' → {new_emoji}")
    
    def apply_resolutions(self, resolutions: List[DuplicateConflict], dry_run: bool = False) -> int:
        """Apply the resolved mappings to the mapping files"""
        if not resolutions:
            logger.info("No resolutions to apply")
            return 0
        
        # Validate first
        is_valid, errors = self.validate_resolution(resolutions)
        if not is_valid:
            logger.error("Resolution validation failed:")
            for error in errors:
                logger.error(f"  - {error}")
            logger.warning("Applying only the valid resolutions (ones that don't create conflicts)")
            
            # Filter to only valid resolutions
            valid_resolutions = self.filter_valid_resolutions(resolutions)
            if not valid_resolutions:
                logger.error("No valid resolutions found after filtering")
                return 0
            resolutions = valid_resolutions
        
        changes_made = 0
        new_word_to_emoji = self.word_to_emoji.copy()
        new_emoji_to_word = self.emoji_to_word.copy()
        
        for resolution in resolutions:
            # Remove old mappings for conflicting words
            for word in resolution.conflicting_words:
                if resolution.emoji in new_emoji_to_word:
                    del new_emoji_to_word[resolution.emoji]
            
            # Apply new mappings
            for word, new_emoji in resolution.resolved_mappings.items():
                old_emoji = new_word_to_emoji.get(word, "NOT_FOUND")
                
                if old_emoji != new_emoji:
                    if not dry_run:
                        # Update mappings
                        new_word_to_emoji[word] = new_emoji
                        new_emoji_to_word[new_emoji] = word
                    
                    changes_made += 1
                    logger.info(f"{'[DRY RUN] ' if dry_run else ''}Updated '{word}': {old_emoji} → {new_emoji}")
        
        if not dry_run and changes_made > 0:
            # Save updated mappings to main mapping file
            with open(self.mapping_path, 'w', encoding='utf-8') as f:
                json.dump(new_word_to_emoji, f, indent=2, ensure_ascii=False)
                f.flush()
                os.fsync(f.fileno())
            
            logger.info(f"✅ Successfully applied {changes_made} duplicate resolutions")
        elif dry_run:
            logger.info(f"[DRY RUN] Would apply {changes_made} duplicate resolutions")
        else:
            logger.info("No changes needed")
        
        return changes_made
    
    def save_resolutions(self, resolutions: List[DuplicateConflict], filename: str = None):
        """Save duplicate resolutions to file"""
        if filename is None:
            timestamp = int(time.time())
            filename = f"duplicate_resolutions_{timestamp}.json"
        
        output_path = self.output_path / filename
        
        # Convert resolutions to serializable format
        resolutions_data = []
        for resolution in resolutions:
            resolutions_data.append({
                'emoji': resolution.emoji,
                'emoji_description': resolution.emoji_description,
                'conflicting_words': resolution.conflicting_words,
                'resolved_mappings': resolution.resolved_mappings,
                'reasoning': resolution.reasoning,
                'confidence': resolution.confidence
            })
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(resolutions_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved {len(resolutions)} duplicate resolutions to {output_path}")
        return output_path
    
    def create_resolution_report(self, resolutions: List[DuplicateConflict]) -> str:
        """Create a comprehensive resolution report in markdown"""
        if not resolutions:
            return "# No Duplicate Mappings Found\n\nAll emoji mappings are unique!"
        
        report = f"""# Duplicate Mapping Resolution Report

## Overview
- **Total conflicts resolved**: {len(resolutions)}
- **Average confidence**: {sum(r.confidence for r in resolutions) / len(resolutions):.2f}

## Resolved Conflicts

Below are the detailed resolutions for each duplicate emoji mapping:

"""
        
        for i, resolution in enumerate(resolutions, 1):
            report += f"""
### Conflict {i}: {resolution.emoji} ({resolution.emoji_description})

**Original conflicting words**: {', '.join(resolution.conflicting_words)}

**Resolution**:
"""
            for word, emoji in resolution.resolved_mappings.items():
                report += f"- `{word}` → {emoji}\n"
            
            report += f"""
**Reasoning**: {resolution.reasoning}

**Confidence**: {resolution.confidence:.2f}

---
"""
        
        return report

    def _parse_json_response(self, response_text: str) -> Optional[Dict]:
        """Parse JSON response with robust error handling"""
        if not response_text:
            return None
            
        # Try to find JSON in the response
        start_idx = response_text.find('{')
        end_idx = response_text.rfind('}') + 1
        
        if start_idx < 0 or end_idx <= start_idx:
            logger.error("No JSON object found in response")
            logger.error(f"Raw response text ({len(response_text)} chars): {response_text[:1000]}{'...' if len(response_text) > 1000 else ''}")
            return None
            
        json_str = response_text[start_idx:end_idx]
        
        try:
            result = json.loads(json_str)
            logger.debug(f"Successfully parsed JSON with {len(result)} entries")
            # Pretty print the parsed JSON for debugging
            logger.debug(f"Parsed JSON (pretty printed):")
            logger.debug(json.dumps(result, indent=2, ensure_ascii=False))
            return result
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e}")
            logger.error(f"Failed JSON string ({len(json_str)} chars): {json_str[:500]}{'...' if len(json_str) > 500 else ''}")
            logger.error(f"Full response text ({len(response_text)} chars): {response_text[:1000]}{'...' if len(response_text) > 1000 else ''}")
            return None
    
    
    def _create_emergency_resolution(self, emoji: str, conflicting_words: List[str]) -> DuplicateConflict:
        """Create emergency resolution when all LLM attempts fail"""
        
        logger.warning(f"🚨 Creating emergency resolution for {emoji} → {conflicting_words}")
        
        emoji_description = self.get_emoji_description(emoji)
        emergency_mappings = {}
        
        # Strategy: Use word hash to create deterministic but unique emoji combinations
        base_emojis = ['⭐', '✨', '🔥', '💎', '🎯', '🚀', '🎪', '🎭', '🎨', '🎸']
        modifier_emojis = ['🔸', '🔹', '◾', '◽', '🔶', '🔷', '🟡', '🟢', '🔴', '🟣']
        
        for i, word in enumerate(conflicting_words):
            # Create deterministic hash-based emoji
            word_hash = hashlib.md5(f"{word}_{i}".encode()).hexdigest()[:4]
            base_idx = int(word_hash[:2], 16) % len(base_emojis)
            mod_idx = int(word_hash[2:4], 16) % len(modifier_emojis)
            
            emergency_emoji = base_emojis[base_idx] + modifier_emojis[mod_idx]
            
            # Ensure uniqueness within this emergency mapping
            counter = 0
            while emergency_emoji in emergency_mappings.values():
                counter += 1
                emergency_emoji = base_emojis[base_idx] + modifier_emojis[mod_idx] + f"{counter}️⃣"
                if counter > 10:  # Prevent infinite loop
                    emergency_emoji = f"🔤{i + 1}️⃣"  # Simple fallback
                    break
            
            emergency_mappings[word] = emergency_emoji
            logger.info(f"  🚨 Emergency: '{word}' → {emergency_emoji}")
        
        return DuplicateConflict(
            emoji=emoji,
            emoji_description=emoji_description,
            conflicting_words=conflicting_words,
            resolved_mappings=emergency_mappings,
            reasoning="Emergency resolution - LLM failed multiple times",
            confidence=0.3  # Low confidence for emergency resolution
        )
    
    def _log_failed_resolution(self, conflicts: List[Tuple[str, List[str]]], error_reason: str):
        """Log failed resolution attempts for debugging"""
        
        timestamp = int(time.time())
        log_path = self.output_path / f"failed_resolutions_{timestamp}.json"
        
        failed_data = {
            "timestamp": timestamp,
            "error_reason": error_reason,
            "conflicts": []
        }
        
        for emoji, words in conflicts:
            display_emoji = emoji.split('#')[0] if '#sub' in emoji else emoji
            failed_data["conflicts"].append({
                "emoji": display_emoji,
                "emoji_description": self.get_emoji_description(display_emoji),
                "conflicting_words": words
            })
        
        try:
            with open(log_path, 'w', encoding='utf-8') as f:
                json.dump(failed_data, f, indent=2, ensure_ascii=False)
            
            logger.warning(f"📝 Failed resolution logged to {log_path}")
            
        except Exception as e:
            logger.error(f"Failed to log failed resolution: {e}")

def main():
    """Main function for command-line usage"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Resolve duplicate emoji mappings using local LLM")
    parser.add_argument("--base-url", default="http://127.0.0.1:1234",
                       help="Base URL for local LLM server (default: http://127.0.0.1:1234)")
    parser.add_argument("--model", default="openai/gpt-oss-20b",
                       help="Model name to use (default: openai/gpt-oss-20b)")
    parser.add_argument("--dry-run", "-d", action="store_true",
                       help="Show what would be changed without making changes")
    parser.add_argument("--no-incremental-save", action="store_true",
                       help="Disable incremental saving after each LLM query (less safe but faster)")
    parser.add_argument("--batch-size", "-b", type=int, default=8,
                       help="Number of conflicts to send to LLM in each batch (default: 8)")
    
    args = parser.parse_args()
    
    try:
        # Initialize resolver
        save_incrementally = not args.no_incremental_save
        resolver = DuplicateMappingResolver(
            base_url=args.base_url, 
            model=args.model, 
            save_after_each_query=save_incrementally,
            batch_size=args.batch_size
        )
        
        if save_incrementally:
            print("💾 Incremental saving enabled - progress will be saved after each LLM query")
        else:
            print("⚠️  Incremental saving disabled - progress only saved at the end")
        
        print(f"📦 Batch size: {args.batch_size} words per LLM request (conflicts will be grouped to stay under this limit)")
        
        # Find and resolve duplicates
        print("🔍 Scanning for duplicate emoji mappings...")
        resolutions = resolver.resolve_all_duplicates()
        
        if not resolutions:
            print("✅ No duplicate mappings found! All emojis are unique.")
            return 0
        
        # Save resolutions
        resolutions_file = resolver.save_resolutions(resolutions)
        
        # Generate report
        report = resolver.create_resolution_report(resolutions)
        report_path = resolver.output_path / "duplicate_resolution_report.md"
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(f"\n✅ Resolution complete!")
        print(f"📄 Resolutions saved to: {resolutions_file}")
        print(f"📊 Report saved to: {report_path}")
        
        # Apply resolutions
        changes_made = resolver.apply_resolutions(resolutions, dry_run=args.dry_run)
        
        if args.dry_run:
            print(f"\n🔍 Dry run complete - {changes_made} changes would be applied")
            print("Run without --dry-run to apply the changes")
        elif changes_made > 0:
            print(f"\n✅ Successfully resolved {len(resolutions)} duplicate conflicts!")
            print(f"🔄 Applied {changes_made} mapping changes")
            print("🎯 All emoji mappings are now unique and reversible!")
        else:
            print("\nℹ️  No changes were needed")
        
        return 0
        
    except Exception as e:
        logger.error(f"Error resolving duplicates: {e}")
        return 1

if __name__ == "__main__":
    exit(main())
