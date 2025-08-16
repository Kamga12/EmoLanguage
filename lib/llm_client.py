#!/usr/bin/env python3
"""
LLM Client for handling OpenAI API interactions with local LLM server.
Provides retry logic, response parsing, and error handling.
"""

import json
import logging
import re
import time
from typing import Dict, List, Optional, Any
from openai import OpenAI
from lib.utils import truncate_prompt_for_logging

logger = logging.getLogger(__name__)

class LLMClient:
    """Handles LLM interactions with built-in retry logic and response parsing"""
    
    def __init__(self, base_url: str = "http://127.0.0.1:1234", model: str = "openai/gpt-oss-20b"):
        """Initialize the LLM client"""
        self.client = OpenAI(base_url=f"{base_url}/v1", api_key="not-needed")
        self.model = model
        self.default_max_retries = 3
    
    def _extract_json_from_markdown(self, text: str) -> List[str]:
        """Extract JSON content from markdown code blocks in LLM responses"""
        blocks = []
        
        # 1) Prefer ```json fenced blocks
        for m in re.finditer(r"```json\s*(.*?)\s*```", text, re.DOTALL | re.IGNORECASE):
            blocks.append(m.group(1))
        if blocks:
            return blocks

        # 2) Any fenced code blocks
        for m in re.finditer(r"```\w*\s*(.*?)\s*```", text, re.DOTALL):
            blocks.append(m.group(1))
        if blocks:
            return blocks
        
        # 3) Handle special LLM response tokens (e.g., <|channel|>final<|message|>)
        # Look for content after final message marker
        final_match = re.search(r'<\|[^|]*\|>final<\|[^|]*\|>(.*?)(?:<\|[^|]*\|>|$)', text, re.DOTALL)
        if final_match:
            blocks.append(final_match.group(1).strip())
            return blocks
        
        # 4) Return the original text if no code blocks found
        return [text]
    
    def _parse_json_response(self, response_text: str) -> Optional[List[Dict[str, Any]]]:
        """Parse JSON array from LLM response, handling markdown code blocks"""
        if not response_text:
            return None
        
        # Extract JSON from markdown code blocks if present
        json_blocks = self._extract_json_from_markdown(response_text)
        
        # Try to parse JSON from extracted blocks
        for block in json_blocks:
            # Try to find valid JSON arrays in the block
            # Look for arrays that start with [ and contain objects with string keys
            for match in re.finditer(r'\[.*?\]', block, re.DOTALL):
                json_candidate = match.group(0)
                try:
                    parsed = json.loads(json_candidate)
                    # Validate that it's an array of objects with string keys (our expected format)
                    if (isinstance(parsed, list) and 
                        len(parsed) > 0 and 
                        all(isinstance(item, dict) and 
                            all(isinstance(k, str) for k in item.keys()) 
                            for item in parsed)):
                        return parsed
                except json.JSONDecodeError:
                    continue
        
        # Fallback to original method if markdown extraction failed
        start_idx = response_text.find('[')
        end_idx = response_text.rfind(']') + 1
        if start_idx >= 0 and end_idx > start_idx:
            json_str = response_text[start_idx:end_idx]
            try:
                parsed = json.loads(json_str)
                # Validate format
                if (isinstance(parsed, list) and 
                    len(parsed) > 0 and 
                    all(isinstance(item, dict) and 
                        all(isinstance(k, str) for k in item.keys()) 
                        for item in parsed)):
                    return parsed
            except json.JSONDecodeError:
                pass
        
        return None
    
    def parse_word_emoji_mappings(self, response_text: str) -> Optional[Dict[str, str]]:
        """
        Parse word-to-emoji mappings from LLM response.
        
        Handles new format with match scores:
        [{"word": "cat", "emoji_combo": "🐱", "match_score": 0.95}, ...]
        
        Also handles legacy formats for backward compatibility:
        [{"word1": "emoji(s)"}, {"word2": "emoji(s)"}, ...]
        [{"word":"anger","emoji_combo":"🔥😡"}, ...]
        
        Returns:
            Dictionary mapping words to emojis, or None if parsing failed
        """
        parsed_response = self._parse_json_response(response_text)
        if parsed_response is None:
            logger.error("Failed to parse JSON response")
            return None
        
        word_to_emoji = {}
        for i, item in enumerate(parsed_response):
            if isinstance(item, dict):
                # Handle new format with match_score (3 fields: word, emoji_combo, match_score)
                if len(item) == 3 and 'word' in item and 'emoji_combo' in item and 'match_score' in item:
                    word = item['word']
                    emoji = item['emoji_combo']
                    match_score = item.get('match_score', 0.0)
                    if word and emoji:
                        word_to_emoji[word] = emoji
                        logger.debug(f"✅ Parsed new format: '{word}' -> '{emoji}' (score: {match_score:.2f})")
                        continue
                
                # Handle legacy single key-value pair format
                elif len(item) == 1:
                    word, emoji = next(iter(item.items()))
                    if word and emoji:
                        word_to_emoji[word] = emoji
                        logger.debug(f"✅ Parsed legacy single format: '{word}' -> '{emoji}'")
                        continue
                
                # Handle legacy two-field format (word/emoji_combo without match_score)
                elif len(item) == 2:
                    word_key = None
                    emoji_key = None
                    word_value = None
                    emoji_value = None
                    
                    # Find word key (starts with 'w') and emoji key (starts with 'e')
                    for key, value in item.items():
                        key_lower = key.lower()
                        if key_lower.startswith('w') and value:  # word, words, etc.
                            word_key = key
                            word_value = value
                        elif key_lower.startswith('e') and value:  # emoji, emoji_combo, emojis, etc.
                            emoji_key = key
                            emoji_value = value
                    
                    if word_value and emoji_value:
                        word_to_emoji[word_value] = emoji_value
                        logger.debug(f"✅ Parsed legacy two-field format: '{word_value}' -> '{emoji_value}'")
                        continue
                    else:
                        logger.warning(f"⚠️ Could not extract word/emoji from legacy item: {item}")
                else:
                    logger.warning(f"⚠️ Unexpected response format in item {i}: {item}")
            else:
                logger.warning(f"⚠️ Non-dict item at index {i}: {item}")
        
        logger.info(f"🔍 Successfully parsed {len(word_to_emoji)} word-emoji mappings")
        return word_to_emoji if word_to_emoji else None
    
    def parse_word_emoji_mappings_with_scores(self, response_text: str) -> Optional[List[Dict[str, Any]]]:
        """
        Parse word-to-emoji mappings with match scores from LLM response.
        
        Expected format:
        [{"word": "cat", "emoji_combo": "🐱", "match_score": 0.95}, ...]
        
        Returns:
            List of dictionaries with word, emoji_combo, and match_score keys, or None if parsing failed
        """
        parsed_response = self._parse_json_response(response_text)
        if parsed_response is None:
            logger.error("Failed to parse JSON response")
            return None
        
        mappings_with_scores = []
        for i, item in enumerate(parsed_response):
            if isinstance(item, dict):
                # Handle new format with match_score (3 fields: word, emoji_combo, match_score)
                if len(item) == 3 and 'word' in item and 'emoji_combo' in item and 'match_score' in item:
                    word = item['word']
                    emoji = item['emoji_combo']
                    match_score = item.get('match_score', 0.0)
                    
                    if word and emoji and isinstance(match_score, (int, float)):
                        mappings_with_scores.append({
                            'word': word,
                            'emoji_combo': emoji,
                            'match_score': float(match_score)
                        })
                        logger.debug(f"✅ Parsed with score: '{word}' -> '{emoji}' (score: {match_score:.2f})")
                        continue
                    else:
                        logger.warning(f"⚠️ Invalid values in item {i}: word='{word}', emoji='{emoji}', score={match_score}")
                else:
                    logger.warning(f"⚠️ Expected 3-field format with word/emoji_combo/match_score, got: {item}")
            else:
                logger.warning(f"⚠️ Non-dict item at index {i}: {item}")
        
        logger.info(f"🔍 Successfully parsed {len(mappings_with_scores)} word-emoji mappings with scores")
        return mappings_with_scores if mappings_with_scores else None
    
    def call_llm_for_word_mappings(self,
                                  prompt: str, 
                                  temperature: float = 0.8, 
                                  max_tokens: int = 100000, 
                                  max_retries: Optional[int] = None) -> Optional[Dict[str, str]]:
        """
        Make LLM call specifically for word-to-emoji mappings with unified response parsing
        
        Args:
            prompt: The prompt to send to the LLM
            temperature: Sampling temperature
            max_tokens: Maximum tokens in response
            max_retries: Maximum retry attempts (uses default if None)
        
        Returns:
            Dictionary mapping words to emojis, or None if failed
        """
        if max_retries is None:
            max_retries = self.default_max_retries
        
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                # Log prompt details with truncation for readability
                truncated_prompt = truncate_prompt_for_logging(prompt, max_emoji_display=10)
                logger.info("📝 PROMPT SENT TO LLM:")
                logger.info("=" * 50)
                logger.info(truncated_prompt)
                logger.info("=" * 50)
                
                start_time = time.time()
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=temperature,
                    max_tokens=max_tokens
                )
                elapsed = time.time() - start_time
                
                content = response.choices[0].message.content
                result_text = content.strip() if content else ""
                
                # Log response details
                logger.info("🤖 RAW LLM RESPONSE:")
                logger.info("=" * 50)
                logger.info(result_text)
                logger.info("=" * 50)
                logger.info(f"⏱️ LLM call took {elapsed:.2f} seconds")
                
                # Parse word-emoji mappings using unified parser
                word_mappings = self.parse_word_emoji_mappings(result_text)
                
                if word_mappings is not None:
                    return word_mappings
                else:
                    raise ValueError("No valid word-emoji mappings found in response")
                    
            except Exception as e:
                retry_count += 1
                logger.error(f"Error in LLM call (attempt {retry_count}): {e}")
                if retry_count < max_retries:
                    logger.info(f"Retrying LLM call immediately...")
                else:
                    logger.error(f"Failed after {max_retries} attempts")
                    return None
        
        return None
    
    def call_llm_for_word_mappings_with_scores(self, 
                                              prompt: str, 
                                              temperature: float = 0.8, 
                                              max_tokens: int = 100000, 
                                              max_retries: Optional[int] = None) -> Optional[List[Dict[str, Any]]]:
        """
        Make LLM call for word-to-emoji mappings with match scores included
        
        Args:
            prompt: The prompt to send to the LLM
            temperature: Sampling temperature
            max_tokens: Maximum tokens in response
            max_retries: Maximum retry attempts (uses default if None)
        
        Returns:
            List of dictionaries with word, emoji_combo, and match_score keys, or None if failed
        """
        if max_retries is None:
            max_retries = self.default_max_retries
        
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                # Log prompt details with truncation for readability
                truncated_prompt = truncate_prompt_for_logging(prompt, max_emoji_display=10)
                logger.info("📝 PROMPT SENT TO LLM:")
                logger.info("=" * 50)
                logger.info(truncated_prompt)
                logger.info("=" * 50)
                
                start_time = time.time()
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=temperature,
                    max_tokens=max_tokens
                )
                elapsed = time.time() - start_time
                
                content = response.choices[0].message.content
                result_text = content.strip() if content else ""
                
                # Log response details
                logger.info("🤖 RAW LLM RESPONSE:")
                logger.info("=" * 50)
                logger.info(result_text)
                logger.info("=" * 50)
                logger.info(f"⏱️ LLM call took {elapsed:.2f} seconds")
                
                # Parse word-emoji mappings with scores
                word_mappings_with_scores = self.parse_word_emoji_mappings_with_scores(result_text)
                
                if word_mappings_with_scores is not None:
                    return word_mappings_with_scores
                else:
                    raise ValueError("No valid word-emoji mappings with scores found in response")
                    
            except Exception as e:
                retry_count += 1
                logger.error(f"Error in LLM call (attempt {retry_count}): {e}")
                if retry_count < max_retries:
                    logger.info(f"Retrying LLM call immediately...")
                else:
                    logger.error(f"Failed after {max_retries} attempts")
                    return None
        
        return None
