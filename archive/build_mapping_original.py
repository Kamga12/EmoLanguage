#!/usr/bin/env python3
"""
Semantic Mapping Generator

This system uses an LLM to generate word-to-emoji mappings from scratch for words in documents/dictionary.txt.
It creates semantically intuitive mappings and saves them to logs/ for analysis.

REFACTORED VERSION: Now uses modular architecture with separated concerns.
"""

import logging
import argparse
from pathlib import Path

from lib.semantic_mapping_generator import SemanticMappingGenerator
from lib.config import (
    DEFAULT_BASE_URL,
    DEFAULT_MODEL, 
    DEFAULT_MAPPING_BATCH_SIZE,
    DEFAULT_COLLISION_BATCH_SIZE,
    DEFAULT_DICTIONARY_PATH,
    LOG_FORMAT,
    LOG_LEVEL
)

# Configure logging
logging.basicConfig(level=getattr(logging, LOG_LEVEL), format=LOG_FORMAT)
logger = logging.getLogger(__name__)
    def find_and_remove_duplicate_emojis(self, mapping_path: Path) -> tuple[List[str], List[tuple[str, str, str]]]:
        """Find duplicate emoji values in mapping.json and return all words for collision resolution."""
        if not mapping_path.exists():
            return [], []
        with open(mapping_path, 'r', encoding='utf-8') as f:
            word_to_emoji = json.load(f)
        # Find emojis that are used more than once
        from collections import defaultdict
        emoji_to_words = defaultdict(list)
        for word, emoji in word_to_emoji.items():
            emoji_to_words[emoji].append(word)
        duplicates = {emoji: words for emoji, words in emoji_to_words.items() if len(words) > 1}
        if not duplicates:
            return [], []
        
        # Remove ALL words with duplicate emojis and create collision tuples for LLM resolution
        words_to_reprocess = []
        collision_tuples = []
        for emoji, words in duplicates.items():
            logger.info(f"Emoji '{emoji}' used by {len(words)} words: {words} - will resolve via LLM collision resolution")
            
            # Create collision pairs from all words sharing this emoji
            for i in range(len(words)):
                for j in range(i + 1, len(words)):
                    collision_tuples.append((words[i], words[j], emoji))
            
            # Remove all words with this duplicate emoji
            for word in words:
                word_to_emoji.pop(word, None)
                words_to_reprocess.append(word)
        
        # Save the cleaned mapping (with all duplicates removed)
        with open(mapping_path, 'w', encoding='utf-8') as f:
            json.dump(word_to_emoji, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Removed {len(words_to_reprocess)} words with duplicate emojis from mapping.json.")
        logger.info(f"Created {len(collision_tuples)} collision pairs for LLM resolution: {collision_tuples}")
        return words_to_reprocess, collision_tuples
    def __init__(self, base_url: str = "http://127.0.0.1:1234", model: str = "openai/gpt-oss-20b"):
        """Initialize the semantic mapping generator"""
        self.client = OpenAI(base_url=f"{base_url}/v1", api_key="not-needed")
        self.model = model
        self.output_path = Path("logs")
        self.output_path.mkdir(exist_ok=True)
        self.checkpoint_path = self.output_path / "generation_checkpoint.json"
        self.normalizer = WordNormalizer()  # Initialize the word normalizer
        
        # Track used emojis during a generation session to avoid real-time conflicts
        self.session_used_emojis = set()
    
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
        
        # 3) Return the original text if no code blocks found
        return [text]
    
    def generate_mappings_batch(self, words: List[str]) -> List[NewMapping]:
        """Generate multiple word-to-emoji mappings in a single LLM call for efficiency"""
        
        if not words:
            return []
        
        # Load existing emoji mappings to avoid duplicates (invert mapping.json in memory)
        existing_emojis = set()
        try:
            with open("mappings/mapping.json", 'r', encoding='utf-8') as f:
                word_to_emoji = json.load(f)
                existing_emojis = set(word_to_emoji.values())
        except FileNotFoundError:
            logger.info("No existing emoji mappings found for batch, starting fresh")
        # Include session-used emojis to avoid conflicts within the current generation session
        all_used_emojis = existing_emojis.union(self.session_used_emojis)
        
        # Use ALL existing emojis without any sampling or limits
        all_emojis_list = list(all_used_emojis)
        existing_sample_text = ", ".join(all_emojis_list) if all_emojis_list else "None (these are the first mappings)"
        
        logger.debug(f"Sending {len(all_emojis_list)} emojis to LLM ({len(self.session_used_emojis)} from session, {len(all_emojis_list) - len(self.session_used_emojis)} from file)")
        
        # Create the batch generation prompt
        words_text = "\n".join([f"{i+1}. {word}" for i, word in enumerate(words)])
        
        prompt = f"""
You are an expert in semantic analysis and emoji communication. Please generate the best possible emoji mappings for these {len(words)} words:

{words_text}

🚨 CREATIVITY ENCOURAGEMENT - READ THIS CAREFULLY:
• YOU SHOULD CREATE NEW EMOJI COMBINATIONS when needed!
• The "existing emojis" list below shows what's ALREADY TAKEN by other words
• This is NOT a forbidden list - it's an "avoid duplicates" reference  
• You are ENCOURAGED to use any emojis NOT in that list
• Feel free to combine multiple emojis creatively for better semantic representation
• Your goal is to find the BEST representation, not avoid emojis entirely
• Ensure each word in this batch gets a UNIQUE emoji/combination

📋 EXISTING EMOJIS ALREADY USED (avoid these for uniqueness): {existing_sample_text}

For each word, provide:

1. EMOJIS: The best emoji(s) to represent this word that:
   - Have clear semantic connection to the word's meaning
   - Are universally recognizable and culturally appropriate
   - Work well for encoding/decoding text
   - Are as simple as possible while being clear
   - Use as many emojis as needed for the best representation (prefer fewer when possible)
   - Are UNIQUE (not in existing emojis list AND unique within this batch)

🎯 EMOJI CREATIVITY GUIDELINES:

• BE CREATIVE with combinations! Examples of good creative combinations:
  - "birthday" → 🎂🎉 (cake + celebration)
  - "homework" → 📚✏️ (books + pencil)
  - "sunset" → 🌅🌇 (sunrise + evening)
  - "friendship" → 👥❤️ (people + love)
  - "cooking" → 👨‍🍳🍳 (chef + cooking)
  - "teacher" → 👨‍🏫📚 (teacher + books)
  - "library" → 📚🏛️ (books + building)
  - "swimming" → 🏊‍♂️💦 (swimmer + water)
  - "nighttime" → 🌙✨ (moon + stars)
  - "celebration" → 🎉🎊 (party popper + confetti)
- "teamwork" → 👥🤝 (people + handshake)

• SINGLE EMOJIS are preferred when they clearly represent the concept
• EMOJI COMBINATIONS are encouraged when single emojis are insufficient  
• AVOID using emojis from the "existing emojis" list above
• ENSURE each word gets a different emoji/combination within this batch

🎯 SEMANTIC PRIORITIZATION RULES:

When choosing emojis, follow these priority guidelines:

• DIRECT/LITERAL over ABSTRACT: Words with direct physical representations get the literal emoji
  - "abacus" gets 🧮 (not calculator-related emojis)
  - "fox" gets 🦊 (not clever/cunning symbols)
  - "tree" gets 🌳 (not growth/nature abstractions)

• CONCRETE over ABSTRACT: Physical objects take priority over conceptual meanings
  - "clock" gets 🕐 (not time management symbols)
  - "book" gets 📖 (not knowledge symbols)
  - "hammer" gets 🔨 (not construction symbols)

• SPECIFIC over GENERAL: More specific words claim the most direct emoji
  - "rose" gets 🌹 (over generic flower)
  - "bicycle" gets 🚲 (over generic transport)
  - "guitar" gets 🎸 (over generic music)

• COMMON USAGE over RARE: Everyday words get priority for obvious emojis
  - "house" gets 🏠 (over "dwelling" or "residence")
  - "car" gets 🚗 (over "automobile" or "vehicle")
  - "dog" gets 🐕 (over "canine" or "hound")

Respond with a JSON array containing one object for each word in order:
[
{{
    "word": "<word>",
    "emojis": "<emoji_string>"
}},
...
]

Focus on semantically intuitive, culturally universal, simple and memorable mappings that are UNIQUE.
"""

        # Log the batch prompt being sent to LLM (truncate the emoji list)
        logger.info("📤 BATCH PROMPT BEING SENT TO LLM:")
        logger.info("=" * 50)
        prompt_lines = prompt.split('\n')
        truncated_prompt_lines = []
        for line in prompt_lines:
            if line.startswith('📋 EXISTING EMOJIS ALREADY USED (avoid these for uniqueness):'):
                # Truncate the long emoji list
                emoji_part = line.split(': ', 1)[1] if ': ' in line else ''
                if len(emoji_part) > 100:
                    truncated_part = emoji_part[:100] + f"... [TRUNCATED - {len(emoji_part) - 100} more characters]"
                    truncated_prompt_lines.append(f"📋 EXISTING EMOJIS ALREADY USED (avoid these for uniqueness): {truncated_part}")
                else:
                    truncated_prompt_lines.append(line)
            else:
                truncated_prompt_lines.append(line)
        
        truncated_prompt = '\n'.join(truncated_prompt_lines)
        logger.info(truncated_prompt)
        logger.info("=" * 50)

        retry_count = 0
        
        while True:
            try:
                import time
                start_time = time.time()
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.8,
                    max_tokens=80000  # Increased for batch processing
                )
                elapsed = time.time() - start_time
                content = response.choices[0].message.content
                result_text = content.strip() if content else ""
                # Log the raw batch response
                logger.info("🤖 RAW BATCH LLM RESPONSE:")
                logger.info("=" * 50)
                logger.info(result_text)
                logger.info("=" * 50)
                logger.info(f"⏱️ LLM call took {elapsed:.2f} seconds")
                
                # Extract JSON from markdown code blocks if present
                json_blocks = self._extract_json_from_markdown(result_text)
                json_str = None
                results = None
                
                # Try to parse JSON from extracted blocks
                for block in json_blocks:
                    try:
                        # Try to find JSON array in the block
                        start_idx = block.find('[')
                        end_idx = block.rfind(']') + 1
                        if start_idx >= 0 and end_idx > start_idx:
                            json_str = block[start_idx:end_idx]
                            results = json.loads(json_str)
                            break
                    except json.JSONDecodeError:
                        continue
                
                # Fallback to original method if markdown extraction failed
                if results is None:
                    start_idx = result_text.find('[')
                    end_idx = result_text.rfind(']') + 1
                    if start_idx >= 0 and end_idx > start_idx:
                        json_str = result_text[start_idx:end_idx]
                        results = json.loads(json_str)
                
                if results is not None:
                    # ...removed prettified JSON response logging...
                    
                    # Validate we have enough results
                    if len(results) < len(words):
                        raise ValueError(f"LLM returned {len(results)} results but expected {len(words)}")
                    
                    # Convert to NewMapping objects
                    mappings = []
                    for i, word in enumerate(words):
                        if i < len(results):
                            result = results[i]
                            mappings.append(NewMapping(
                                word=word,
                                suggested_emojis=result.get('emojis', ''),
                                category='batch'  
                            ))
                        else:
                            # This should not happen given the validation above
                            logger.error(f"Missing result for word '{word}' despite validation")
                            mappings.append(NewMapping(
                                word=word,
                                suggested_emojis='',
                                category='error'
                            ))
                    
                    # Track newly generated emojis in session
                    for mapping in mappings:
                        if mapping.suggested_emojis:
                            self.session_used_emojis.add(mapping.suggested_emojis)
                    
                    # Final validation that we have mappings for all input words
                    mapped_words = set(m.word for m in mappings)
                    input_words = set(words)
                    missing_words = input_words - mapped_words
                    
                    if missing_words:
                        logger.error(f"CRITICAL: Missing mappings for words: {list(missing_words)}")
                        # Add error mappings for missing words
                        for word in missing_words:
                            mappings.append(NewMapping(
                                word=word,
                                suggested_emojis='',
                                category='error'
                            ))
                    
                    return mappings
                else:
                    raise ValueError("No valid JSON array found in response")
                    
            except Exception as e:
                retry_count += 1
                logger.error(f"Error generating batch of {len(words)} mappings (attempt {retry_count}): {e}")
                logger.info(f"Retrying batch generation immediately...")
    
    def resolve_emoji_collisions_with_llm(self, collisions: List[tuple[str, str, str]], collision_size: int = 10) -> List[NewMapping]:
        """Use LLM to intelligently resolve emoji collisions by deciding which word keeps the emoji and providing alternatives"""
        if not collisions:
            return []
        # Load existing emoji mappings to avoid new conflicts (invert mapping.json in memory)
        existing_emojis = set()
        try:
            with open("mappings/mapping.json", 'r', encoding='utf-8') as f:
                word_to_emoji = json.load(f)
                existing_emojis = set(word_to_emoji.values())
        except FileNotFoundError:
            pass
        all_used_emojis = existing_emojis.union(self.session_used_emojis)
        all_emojis_list = list(all_used_emojis)
        existing_sample_text = ", ".join(all_emojis_list) if all_emojis_list else "None (these are the first mappings)"
        all_resolved_mappings = []
        collisions_to_process = list(collisions)  # Copy so we can modify it
        
        while collisions_to_process:
            # Take a batch of collisions
            batch_start = 0
            batch_end = min(collision_size, len(collisions_to_process))
            collision_batch = collisions_to_process[batch_start:batch_end]
            collisions_to_process = collisions_to_process[batch_end:]
            
            logger.info(f"🔧 Resolving collision batch: {len(collision_batch)} conflicts (remaining: {len(collisions_to_process)})")
            
            # Create collision resolution prompt for this batch
            collisions_text = "\n".join([
                f"{i+1}. CONFLICT: '{word1}' vs '{word2}' both want '{emoji}'" if emoji != '🔄_RETRY' 
                else f"{i+1}. RETRY: '{word1}' and '{word2}' need new emoji mappings"
                for i, (word1, word2, emoji) in enumerate(collision_batch)
            ])
            batch_resolved_mappings, new_collisions = self._resolve_collision_batch(collision_batch, collisions_text, existing_sample_text)
            all_resolved_mappings.extend(batch_resolved_mappings)
            
            # If LLM created new collisions, add them back to the processing queue
            if new_collisions:
                logger.info(f"⚠️  Adding {len(new_collisions)} new collision pairs back to queue")
                collisions_to_process.extend(new_collisions)
        logger.info(f"✅ Successfully resolved {len(collisions)} total collisions into {len(all_resolved_mappings)} mappings")
        return all_resolved_mappings
    
    def _resolve_collision_batch(self, collision_batch: List[tuple[str, str, str]], collisions_text: str, existing_sample_text: str) -> tuple[List[NewMapping], List[tuple[str, str, str]]]:
        
        prompt = f"""
You are an expert in semantic analysis and emoji communication. There are emoji conflicts and retry requests that need resolution.

🚨 CONFLICTS AND RETRIES TO RESOLVE:

{collisions_text}

🎯 YOUR TASK:
For each item, either:
1. CONFLICT: Decide which word has the STRONGER semantic connection to the disputed emoji, and provide alternative for the other
2. RETRY: Provide new emoji mappings for both words (previous attempt failed or was incomplete)

🚨 CREATIVITY ENCOURAGEMENT - READ THIS CAREFULLY:
• YOU SHOULD CREATE NEW EMOJI COMBINATIONS when needed for alternatives!
• The "existing emojis" list below shows what's ALREADY TAKEN by other words
• This is NOT a forbidden list - it's an "avoid duplicates" reference. If your word and an emoji(s) are a better fit, use it.
• You are ENCOURAGED to use any emoji(s) combinations NOT in that list.
• Feel free to combine multiple emojis creatively for better semantic representation
• Your goal is to find the BEST representation, not avoid emojis entirely

🚨 CRITICAL: AVOID CREATING NEW COLLISIONS!
• Each emoji (or emoji combination) in your response MUST BE UNIQUE
• Double-check your output before submitting - no duplicates allowed!
• If you accidentally create a duplicate, fix it immediately

📋 EXISTING EMOJIS ALREADY USED (avoid these for alternatives): {existing_sample_text}

🎯 SEMANTIC PRIORITIZATION RULES:

When deciding which word keeps the disputed emoji, follow these priority guidelines:

• DIRECT/LITERAL over ABSTRACT: Words with direct physical representations get the literal emoji
  - "abacus" gets 🧮 over "calculation" or "mathematics"
  - "fox" gets 🦊 over "cunning" or "clever"
  - "tree" gets 🌳 over "growth" or "nature"

• CONCRETE over ABSTRACT: Physical objects take priority over conceptual meanings
  - "clock" gets 🕐 over "time" or "punctuality"
  - "book" gets 📖 over "knowledge" or "education"
  - "hammer" gets 🔨 over "construction" or "building"

• SPECIFIC over GENERAL: More specific words claim the most direct emoji
  - "rose" gets 🌹 over "flower" or "beauty"
  - "bicycle" gets 🚲 over "transport" or "exercise"
  - "guitar" gets 🎸 over "music" or "instrument"

• COMMON USAGE over RARE: Everyday words get priority for obvious emojis
  - "house" gets 🏠 over "dwelling" or "residence"
  - "car" gets 🚗 over "automobile" or "vehicle"
  - "dog" gets 🐕 over "canine" or "hound"

🎯 ALTERNATIVE EMOJI GUIDELINES:

For any word that needs a new emoji mapping, provide a creative alternative that:
• Has clear semantic connection to the word's meaning
• Is universally recognizable and culturally appropriate
• Uses as many emojis as needed for the best representation (prefer fewer when possible)
• Is as semantically strong as possible given the constraints
• We want words to have clear and distinct emoji representations.
• We encourage creativity and experimentation with emoji combinations.
• We want to try to avoid creating new collisions between emoji mappings.

Examples of GOOD creative alternative mappings:
  - If "teacher" loses 👨‍🏫, try → 📚🎓 (books + graduation)
  - If "library" loses 📚, try → 🏛️📖 (building + book)
  - If "swimming" loses 🏊‍♂️, try → 💦🌊 (water + wave)
  - If "celebration" loses 🎉, try → 🎊✨ (confetti + sparkles)
  
Examples of GOOD creative combinations:
  - "birthday" → 🎂🎉 (cake + celebration)
  - "homework" → 📚✏️ (books + pencil)
  - "sunset" → 🌅🌇 (sunrise + evening)
  - "friendship" → 👥❤️ (people + love)
  - "cooking" → 👨‍🍳🍳 (chef + cooking)
  - "teacher" → 👨‍🏫📚 (teacher + books)
  - "library" → 📚🏛️ (books + building)
  - "swimming" → 🏊‍♂️💦 (swimmer + water)
  - "nighttime" → 🌙✨ (moon + stars)
  - "celebration" → 🎉🎊 (party popper + confetti)
  - "teamwork" → 👥🤝 (people + handshake)

Respond with a JSON array of word-to-emoji mappings for ALL words in the conflicts/retries:
[
{{"word1": "emoji1"}},
{{"word2": "emoji2"}}
]

For each conflict, include both the winner (with original emoji) AND the loser (with alternative emoji).
For each retry, provide new unique emoji mappings for both words.
Focus on semantically intuitive, logical decisions that prioritize the most natural word-emoji pairings.
"""

        logger.info(f"🔧 Resolving {len(collision_batch)} emoji collisions with LLM...")
        logger.debug("📤 COLLISION RESOLUTION PROMPT:")
        logger.debug("=" * 50)
        logger.debug(prompt[:2000] + "..." if len(prompt) > 2000 else prompt)
        logger.debug("=" * 50)

        retry_count = 0
        max_retries = 3
        
        while retry_count < max_retries:
            try:
                import time
                start_time = time.time()
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.8,  # Lower temperature for more consistent decisions
                    max_tokens=80000
                )
                elapsed = time.time() - start_time
                content = response.choices[0].message.content
                result_text = content.strip() if content else ""
                # Log the raw collision resolution response
                logger.info("🤖 RAW COLLISION RESOLUTION LLM RESPONSE:")
                logger.info("=" * 50)
                logger.info(result_text)
                logger.info("=" * 50)
                logger.info(f"⏱️ LLM call took {elapsed:.2f} seconds")
                
                # Extract JSON from markdown code blocks if present
                json_blocks = self._extract_json_from_markdown(result_text)
                json_str = None
                resolutions = None
                
                # Try to parse JSON from extracted blocks
                for block in json_blocks:
                    try:
                        # Try to find JSON array in the block
                        start_idx = block.find('[')
                        end_idx = block.rfind(']') + 1
                        if start_idx >= 0 and end_idx > start_idx:
                            json_str = block[start_idx:end_idx]
                            resolutions = json.loads(json_str)
                            break
                    except json.JSONDecodeError:
                        continue
                
                # Fallback to original method if markdown extraction failed
                if resolutions is None:
                    start_idx = result_text.find('[')
                    end_idx = result_text.rfind(']') + 1
                    if start_idx >= 0 and end_idx > start_idx:
                        json_str = result_text[start_idx:end_idx]
                        resolutions = json.loads(json_str)
                
                if resolutions is not None:
                    # Validate we have at least 2 mappings per collision (winner + alternative)
                    expected_mappings = len(collision_batch) * 2
                    if len(resolutions) < expected_mappings:
                        logger.warning(f"LLM returned {len(resolutions)} mappings but expected {expected_mappings} for {len(collision_batch)} collisions")
                    
                    # Convert simplified JSON format to NewMapping objects
                    resolved_mappings = []
                    collision_words = set()
                    
                    # Collect all words involved in collisions
                    for word1, word2, disputed_emoji in collision_batch:
                        collision_words.add(word1)
                        collision_words.add(word2)
                    
                    # Process each mapping in the LLM response
                    for resolution in resolutions:
                        # Handle both formats: {"word": "emoji"} or {"word": "emoji", "emoji": "..."}
                        if len(resolution) == 1:
                            # Simple format: {"word": "emoji"}
                            word = list(resolution.keys())[0]
                            emoji = resolution[word]
                        else:
                            # Handle other possible key names
                            word = resolution.get('word', '')
                            emoji = resolution.get('emoji', '') or resolution.get('emojis', '')
                            
                            # If word/emoji not found, try first key-value pair
                            if not word or not emoji:
                                items = list(resolution.items())
                                if items:
                                    word, emoji = items[0]
                        
                        # Only include words that were part of the collision
                        if word in collision_words and emoji:
                            # Determine category based on whether this word got the original disputed emoji
                            category = 'collision_winner'
                            
                            # Check if this word got an alternative emoji (not the disputed one)
                            for word1, word2, disputed_emoji in collision_batch:
                                if word in [word1, word2]:
                                    if disputed_emoji == '🔄_RETRY':
                                        # This is a retry case - all words get alternatives
                                        category = 'collision_retry'
                                    elif emoji != disputed_emoji:
                                        category = 'collision_alternative'
                                    break
                            
                            resolved_mappings.append(NewMapping(
                                word=word,
                                suggested_emojis=emoji,
                                category=category
                            ))
                    
                    # Track newly generated emojis in session
                    for mapping in resolved_mappings:
                        if mapping.suggested_emojis:
                            self.session_used_emojis.add(mapping.suggested_emojis)
                    
                    # Validate that ALL collision words got mappings
                    collision_words = set()
                    for word1, word2, _ in collision_batch:
                        collision_words.add(word1)
                        collision_words.add(word2)
                    
                    resolved_words = set(m.word for m in resolved_mappings)
                    missing_words = collision_words - resolved_words
                    
                    # CRITICAL: Check if LLM created NEW collisions in its response
                    emoji_to_words = {}
                    for mapping in resolved_mappings:
                        if mapping.suggested_emojis:  # Skip empty emojis
                            emoji = mapping.suggested_emojis
                            if emoji not in emoji_to_words:
                                emoji_to_words[emoji] = []
                            emoji_to_words[emoji].append(mapping.word)
                    
                    # Find new collisions created by LLM
                    new_collisions = {emoji: words for emoji, words in emoji_to_words.items() if len(words) > 1}
                    
                    # Handle missing words and new collisions together
                    if missing_words or new_collisions:
                        all_problem_words = set(missing_words) if missing_words else set()
                        new_collision_tuples = []
                        
                        if missing_words:
                            logger.warning(f"⚠️  LLM collision resolution is missing {len(missing_words)} words: {list(missing_words)}")
                        
                        if new_collisions:
                            logger.error(f"🚨 CRITICAL: LLM created NEW collisions while resolving existing ones!")
                            for emoji, words in new_collisions.items():
                                logger.error(f"   {emoji} -> {words}")
                                all_problem_words.update(words)
                                
                                # Create collision pairs from all words sharing this emoji
                                for i in range(len(words)):
                                    for j in range(i + 1, len(words)):
                                        new_collision_tuples.append((words[i], words[j], emoji))
                        
                        # Add missing words as collision pairs with themselves (will be processed together)
                        if missing_words:
                            # Convert set to list for indexing
                            missing_words_list = list(missing_words)
                            # Group missing words into collision pairs so they get processed in the same batch
                            for i in range(0, len(missing_words_list), 2):
                                if i + 1 < len(missing_words_list):
                                    # Pair up missing words with a dummy emoji to force them into same batch
                                    new_collision_tuples.append((missing_words_list[i], missing_words_list[i + 1], '🔄_RETRY'))
                                else:
                                    # Single remaining word - pair with first word from new collisions if available
                                    if new_collisions:
                                        first_collision_word = list(new_collisions.values())[0][0]
                                        new_collision_tuples.append((missing_words_list[i], first_collision_word, '🔄_RETRY'))
                                    else:
                                        # Last resort: create a single-word "collision" 
                                        new_collision_tuples.append((missing_words_list[i], missing_words_list[i], '🔄_RETRY'))
                        
                        # Remove all problem mappings from resolved_mappings
                        resolved_mappings = [m for m in resolved_mappings if m.word not in all_problem_words]
                        
                        logger.warning(f"⚠️  Found {len(new_collision_tuples)} collision pairs (including missing words), will retry in next batch")
                        logger.info(f"🔄 All problem words will be processed together: {sorted(all_problem_words)}")
                        
                        # Return both resolved mappings and new collisions for retry
                        return resolved_mappings, new_collision_tuples
                    
                    logger.info(f"✅ Successfully resolved {len(collision_batch)} collisions into {len(resolved_mappings)} mappings")
                    return resolved_mappings, []  # No new collisions
                else:
                    raise ValueError("No valid JSON array found in collision resolution response")
                    
            except Exception as e:
                retry_count += 1
                logger.error(f"Error resolving collisions (attempt {retry_count}): {e}")
                if retry_count < max_retries:
                    logger.info(f"Retrying collision resolution immediately...")
                else:
                    logger.error(f"Failed to resolve collisions after {max_retries} attempts")
                    return [], []
        
        return [], []
    
    def handle_emoji_collisions(self, batch_mappings: List[NewMapping], collision_size: int = 10) -> tuple[List[NewMapping], List[str]]:
        """Check for emoji collisions and use LLM to resolve them intelligently"""
        # Load current emoji mappings from disk (invert mapping.json in memory)
        current_emoji_to_word = {}
        try:
            with open("mappings/mapping.json", 'r', encoding='utf-8') as f:
                word_to_emoji = json.load(f)
                current_emoji_to_word = {v: k for k, v in word_to_emoji.items()}
        except FileNotFoundError:
            pass  # No existing mappings yet
        
        accepted_mappings = []
        collisions_to_resolve = []
        
        for mapping in batch_mappings:
            if not mapping.suggested_emojis:
                # Skip mappings without emojis (errors, etc.)
                continue
            
            # Check for collision with existing mappings
            if mapping.suggested_emojis in current_emoji_to_word:
                existing_word = current_emoji_to_word[mapping.suggested_emojis]
                logger.warning(f"Emoji collision detected: '{mapping.word}' wants '{mapping.suggested_emojis}' but it's already used by '{existing_word}'")
                collisions_to_resolve.append((existing_word, mapping.word, mapping.suggested_emojis))
            else:
                # Check for collision within this batch
                batch_collision = False
                for accepted in accepted_mappings:
                    if accepted.suggested_emojis == mapping.suggested_emojis:
                        logger.warning(f"Batch collision detected: '{mapping.word}' and '{accepted.word}' both want '{mapping.suggested_emojis}'")
                        collisions_to_resolve.append((accepted.word, mapping.word, mapping.suggested_emojis))
                        # Remove the previously accepted mapping since we'll resolve this collision
                        accepted_mappings = [m for m in accepted_mappings if m != accepted]
                        batch_collision = True
                        break
                
                if not batch_collision:
                    accepted_mappings.append(mapping)
                    # Add to current mappings to avoid further collisions in this batch
                    current_emoji_to_word[mapping.suggested_emojis] = mapping.word
        
        # If there are collisions, resolve them with LLM
        if collisions_to_resolve:
            logger.info(f"🔧 Found {len(collisions_to_resolve)} collisions, resolving with LLM...")
            resolved_mappings = self.resolve_emoji_collisions_with_llm(collisions_to_resolve, collision_size=collision_size)
            
            # Separate successful mappings from error mappings that need re-queuing
            successful_mappings = [m for m in resolved_mappings if m.suggested_emojis]
            error_mappings = [m for m in resolved_mappings if not m.suggested_emojis]
            
            accepted_mappings.extend(successful_mappings)
            words_to_requeue = [m.word for m in error_mappings]
        else:
            words_to_requeue = []
        
        logger.info(f"Collision handling complete: {len(accepted_mappings)} accepted, {len(collisions_to_resolve)} resolved, {len(words_to_requeue)} to re-queue")
        return accepted_mappings, words_to_requeue
    
    def generate_dictionary_mappings(self, mapping_size: int = 500, collision_size: int = 10, dictionary_path: str = "documents/dictionary.txt") -> List[NewMapping]:
        """Generate mappings for all words in documents/dictionary.txt using batch processing with collision handling"""
        logger.info(f"Reading words from {dictionary_path}...")
        
        # Read words from dictionary.txt
        try:
            with open(dictionary_path, 'r', encoding='utf-8') as f:
                dictionary_words = [line.strip() for line in f if line.strip()]
        except FileNotFoundError:
            logger.error(f"Dictionary file '{dictionary_path}' not found")
            raise
        
        logger.info(f"Loaded {len(dictionary_words)} words from dictionary")
        
        # Get words that already have mappings
        mapping_path = Path("mappings/mapping.json")
        duplicate_collision_tuples = []
        try:
            with open(mapping_path, 'r', encoding='utf-8') as f:
                existing_mappings = json.load(f)
            # Remove all words with duplicate emojis and get them for collision resolution
            words_with_duplicate_emojis, duplicate_collision_tuples = self.find_and_remove_duplicate_emojis(mapping_path)
            # Reload mapping after cleaning
            with open(mapping_path, 'r', encoding='utf-8') as f:
                cleaned_mappings = json.load(f)
            # Filter out words that already exist in mappings, but add back the duplicate-emoji words
            original_count = len(dictionary_words)
            words_to_process = [word for word in dictionary_words if word not in cleaned_mappings]
            # Add back the duplicate-emoji words for reprocessing
            for word in words_with_duplicate_emojis:
                if word not in words_to_process:
                    words_to_process.append(word)
            filtered_count = len(words_to_process)
            logger.info(f"Found {len(cleaned_mappings)} existing mappings after duplicate removal")
            logger.info(f"Filtered out {original_count - filtered_count} already-mapped words (after duplicate removal)")
            logger.info(f"Remaining words to process: {filtered_count}")
            if len(duplicate_collision_tuples) > 0:
                logger.info(f"Will resolve {len(duplicate_collision_tuples)} duplicate emoji collisions first")
            if filtered_count == 0 and len(duplicate_collision_tuples) == 0:
                logger.info("All dictionary words already have mappings!")
                return []
        except FileNotFoundError:
            logger.info("No existing mapping.json found, processing all words")
            words_to_process = dictionary_words
            duplicate_collision_tuples = []
        
        all_mappings = []
        
        # First, resolve any duplicate emoji collisions found in existing mappings
        if duplicate_collision_tuples:
            logger.info(f"🔧 Resolving {len(duplicate_collision_tuples)} duplicate emoji collisions first...")
            resolved_duplicate_mappings = self.resolve_emoji_collisions_with_llm(duplicate_collision_tuples, collision_size=collision_size)
            
            # Save the resolved duplicate mappings
            if resolved_duplicate_mappings:
                successful_duplicate_mappings = [m for m in resolved_duplicate_mappings if m.suggested_emojis]
                if successful_duplicate_mappings:
                    self.save_word_to_emoji_mapping(successful_duplicate_mappings)
                    all_mappings.extend(successful_duplicate_mappings)
                    logger.info(f"✅ Resolved {len(successful_duplicate_mappings)} duplicate emoji collisions")
                
                # Handle any words that still failed resolution
                failed_duplicate_words = [m.word for m in resolved_duplicate_mappings if not m.suggested_emojis]
                if failed_duplicate_words:
                    logger.warning(f"⚠️ {len(failed_duplicate_words)} words from duplicate resolution still need processing: {failed_duplicate_words}")
                    # Add them to the main processing queue
                    for word in failed_duplicate_words:
                        if word not in words_to_process:
                            words_to_process.append(word)
        
        # Process words until all are complete (handles collision re-queuing)
        while words_to_process:
            logger.info(f"Processing {len(words_to_process)} remaining words...")
            # Process in batches
            total_batches = (len(words_to_process) + mapping_size - 1) // mapping_size  # Ceiling division
            for batch_num in range(total_batches):
                start_idx = batch_num * mapping_size
                end_idx = min(start_idx + mapping_size, len(words_to_process))
                batch_words = words_to_process[start_idx:end_idx]
                logger.info(f"Processing batch {batch_num + 1}/{total_batches} ({len(batch_words)} words)")
                # Generate mappings for this batch
                batch_mappings = self.generate_mappings_batch(batch_words)
                
                # Separate successful mappings from failed ones that need re-queuing
                successful_mappings = [m for m in batch_mappings if m.suggested_emojis]
                failed_mappings = [m for m in batch_mappings if not m.suggested_emojis]
                
                if failed_mappings:
                    logger.warning(f"⚠️  {len(failed_mappings)} words failed to get emojis from batch generation: {[m.word for m in failed_mappings]}")
                
                # Check for emoji collisions and handle them
                accepted_mappings, collision_words = self.handle_emoji_collisions(successful_mappings, collision_size=collision_size)
                all_mappings.extend(accepted_mappings)
                
                # Add failed mapping words to collision_words for re-queuing
                failed_words = [m.word for m in failed_mappings]
                collision_words.extend(failed_words)
                
                # Save accepted mappings to disk
                if accepted_mappings:
                    self.save_word_to_emoji_mapping(accepted_mappings)
                    logger.info(f"Saved {len(accepted_mappings)} new mappings")
                
                # Add collision words back to processing queue
                if collision_words:
                    logger.info(f"Re-queuing {len(collision_words)} words due to emoji collisions: {collision_words}")
                    # Remove processed words from the queue
                    processed_words = {m.word for m in batch_mappings}
                    words_to_process = [w for w in words_to_process if w not in processed_words]
                    # Add collision words to the BEGINNING for priority processing
                    words_to_process = collision_words + words_to_process
                else:
                    # Remove successfully processed words from the queue
                    processed_words = {m.word for m in accepted_mappings}
                    words_to_process = [w for w in words_to_process if w not in processed_words]
                
                logger.info(f"Batch {batch_num + 1} complete ({len(all_mappings)} total mappings, {len(words_to_process)} remaining)")
        
        logger.info(f"Completed generation of {len(all_mappings)} mappings")
        return all_mappings
    
    def save_mappings(self, mappings: List[NewMapping], filename = None):
        """Save generated mappings to file"""
        if filename is None:
            timestamp = int(time.time())
            filename = f"generated_mappings_{timestamp}.json"
        
        output_path = self.output_path / filename
        
        # Convert mappings to serializable format
        mappings_data = []
        for mapping in mappings:
            mappings_data.append({
                'word': mapping.word,
                'suggested_emojis': mapping.suggested_emojis,
                'category': mapping.category
            })
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(mappings_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved {len(mappings)} generated mappings to {output_path}")
        
        # Also save as simple word-to-emoji mapping file
        self.save_word_to_emoji_mapping(mappings)
        
        return output_path
    
    
    def save_word_to_emoji_mapping(self, mappings: List[NewMapping]):
        """Save mappings directly to core mappings/mapping.json"""
        # Load existing mappings if they exist
        word_to_emoji = {}
        mappings_dir = Path("mappings")
        mappings_dir.mkdir(exist_ok=True)
        mapping_path = mappings_dir / "mapping.json"
        try:
            if mapping_path.exists():
                with open(mapping_path, 'r', encoding='utf-8') as f:
                    word_to_emoji = json.load(f)
        except Exception as e:
            logger.warning(f"Could not load existing mapping.json: {e}")
            word_to_emoji = {}
        # Add new mappings
        emoji_collisions = {}  # Track which words collide on same emoji
        emoji_to_word = {v: k for k, v in word_to_emoji.items()}
        for mapping in mappings:
            if mapping.suggested_emojis:
                logger.info(f"Adding mapping: {mapping.word} -> {mapping.suggested_emojis}")
                word_to_emoji[mapping.word] = mapping.suggested_emojis
                if mapping.suggested_emojis in emoji_to_word:
                    existing_word = emoji_to_word[mapping.suggested_emojis]
                    if mapping.suggested_emojis not in emoji_collisions:
                        emoji_collisions[mapping.suggested_emojis] = [existing_word]
                    emoji_collisions[mapping.suggested_emojis].append(mapping.word)
                emoji_to_word[mapping.suggested_emojis] = mapping.word  # Last writer wins
        
        with open(mapping_path, 'w', encoding='utf-8') as f:
            json.dump(word_to_emoji, f, indent=2, ensure_ascii=False)
        total_collisions = sum(len(words) - 1 for words in emoji_collisions.values())
        logger.info(f"Saved {len(word_to_emoji)} word-to-emoji mappings to {mapping_path}")
        if total_collisions > 0:
            logger.info(f"⚠️  Total emoji collisions: {total_collisions} (affecting {len(emoji_collisions)} emojis)")
        return mapping_path
    
    def analyze_mappings(self, mappings: List[NewMapping]) -> Dict:
        """Analyze the generated mappings and generate statistics"""
        if not mappings:
            return {}
        
        total_mappings = len(mappings)
        successful_mappings = [m for m in mappings if m.suggested_emojis]
        
        # Count by category
        category_counts = {}
        for mapping in mappings:
            category = mapping.category
            category_counts[category] = category_counts.get(category, 0) + 1
        
        return {
            'total_mappings': total_mappings,
            'successful_mappings': len(successful_mappings),
            'category_counts': category_counts,
            'success_rate': len(successful_mappings) / total_mappings if total_mappings > 0 else 0
        }
    
    def create_generation_report(self, mappings: List[NewMapping]) -> str:
        """Create a simple generation report in markdown"""
        analysis = self.analyze_mappings(mappings)
        report = f"""# Emoji Mapping Generation Report\n\n## Overview\n- **Total words processed**: {analysis['total_mappings']}\n- **Successful mappings**: {analysis['successful_mappings']}\n- **Success rate**: {analysis['success_rate']:.1%}\n"""
        report += "\n## Sample Mappings (first 20):\n\n| Word | Emoji |\n|------|-------|\n"
        for mapping in mappings[:20]:
            report += f"| {mapping.word} | {mapping.suggested_emojis} |\n"
        return report

def main():
    """Main function for command-line usage"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate semantic mappings from documents/dictionary.txt using local LLM")
    parser.add_argument("--base-url", default="http://127.0.0.1:1234",
                       help="Base URL for local LLM server (default: http://127.0.0.1:1234)")
    parser.add_argument("--model", default="openai/gpt-oss-20b",
                       help="Model name to use (default: openai/gpt-oss-20b)")
    parser.add_argument("--mapping-size", type=int, default=50,
                       help="Number of words to process in each mapping batch (default: 50)")
    parser.add_argument("--collision-size", type=int, default=10,
                       help="Number of collision pairs to send to the LLM at once (default: 10)")
    parser.add_argument("--dictionary", default="documents/dictionary.txt",
                       help="Path to dictionary file (default: documents/dictionary.txt)")
    parser.add_argument("--dry-run", "-d", action="store_true",
                       help="Show what would be processed without making changes")
    
    args = parser.parse_args()
    
    try:
        # Initialize generator
        generator = SemanticMappingGenerator(base_url=args.base_url, model=args.model)
        
        print(f"🎯 Generating emoji mappings for all words from {args.dictionary}...")
        
        if args.dry_run:
            print(f"\n🔍 DRY RUN MODE - Processing dictionary words but won't save results...\n")
        
        # Generate mappings from dictionary
        mappings = generator.generate_dictionary_mappings(
            mapping_size=args.mapping_size,
            collision_size=args.collision_size,
            dictionary_path=args.dictionary
        )
        
        if not args.dry_run:
            # Save mappings
            mappings_file = generator.save_mappings(mappings)
            
            # Generate report
            report = generator.create_generation_report(mappings)
            report_path = generator.output_path / "generation_report.md"
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(report)
            
            print(f"\n✅ Generation complete!")
            print(f"📄 Detailed mappings saved to: {mappings_file}")
            print(f"📊 Report saved to: {report_path}")
            print(f"🗂️ Core mappings saved to: mappings/word_to_emoji.json")
            print(f"🔄 Reverse mappings saved to: mappings/emoji_to_word.json")
            print(f"\n🚀 Ready to use! Try: python3 encode.py \"Hello world\"")
            
        else:
            print(f"\n🔍 DRY RUN complete - no files saved!")
            
            # Show some sample results in dry-run
            print(f"\n📋 Sample Results:")
            sample_mappings = mappings[:10] if len(mappings) >= 10 else mappings
            for i, mapping in enumerate(sample_mappings, 1):
                print(f"\n{i}. \"{mapping.word}\" → {mapping.suggested_emojis}")
                print(f"   Category: {mapping.category}")
            
            print(f"\n💡 To save results, run without --dry-run flag")
        
        # Print summary
        analysis = generator.analyze_mappings(mappings)
        print(f"\n📊 Summary:")
        print(f"   • Total words processed: {analysis['total_mappings']}")
        print(f"   • Successful mappings: {analysis['successful_mappings']}")
        print(f"   • Success rate: {analysis['success_rate']:.1%}")
        print(f"   • Average confidence: {analysis['average_confidence']:.2f}")
        print(f"   • High confidence mappings: {analysis['high_confidence_count']}")
        
        return 0
        
    except Exception as e:
        logger.error(f"Error during generation: {e}")
        return 1

if __name__ == "__main__":
    exit(main())
