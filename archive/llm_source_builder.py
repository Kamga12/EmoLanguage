# LLM-Enhanced Emoji Source Builder
# ✅ Integrates with local LLM API (OpenAI-compatible) at http://127.0.0.1:1234
# ✅ Uses semantic prompting to suggest appropriate emoji(s) for each word
# ✅ Handles API rate limiting and error recovery
# ✅ Batch processes words efficiently
# ✅ Ensures unique emoji string assignments
# ✅ Falls back to traditional embedding method if needed

import os
import json
import time
import emoji
import spacy
import torch
import multiprocessing
from tqdm import tqdm
from itertools import permutations
from typing import List, Dict, Set, Optional, Tuple
from dataclasses import dataclass
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import logging

# --------------------------
# Configuration
# --------------------------
@dataclass
class Config:
    # LLM API Configuration
    LLM_BASE_URL: str = "http://127.0.0.1:1234"
    LLM_MODEL: str = "local-model"  # Will be auto-detected from API
    
    # Rate limiting and batch processing
    BATCH_SIZE: int = 10
    REQUESTS_PER_SECOND: int = 5
    MAX_RETRIES: int = 3
    RETRY_DELAY: float = 1.0
    TIMEOUT: int = 30
    
    # Emoji mapping parameters
    MIN_SIMILARITY_FALLBACK: float = 0.28
    MAX_PERMUTATION_POOL: int = 100
    
    # Output configuration
    EMOJI_MAP_DIR: str = "mappings"

config = Config()

# --------------------------
# Logging setup
# --------------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --------------------------
# Environment setup
# --------------------------
cpu_cores = multiprocessing.cpu_count()
os.environ["OMP_NUM_THREADS"] = str(cpu_cores)
os.environ["MKL_NUM_THREADS"] = str(cpu_cores)
os.environ["TOKENIZERS_PARALLELISM"] = "true"
logger.info(f"Using {cpu_cores} CPU threads")

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
logger.info(f"Running on: {DEVICE.upper()}")

# --------------------------
# LLM API Client
# --------------------------
class LLMApiClient:
    def __init__(self, base_url: str, timeout: int = 30):
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.session = requests.Session()
        
        # Configure retry strategy
        retry_strategy = Retry(
            total=config.MAX_RETRIES,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        self.model_name = self._get_model_name()
        self.last_request_time = 0
        
    def _get_model_name(self) -> str:
        """Auto-detect the available model from the API"""
        try:
            response = self.session.get(
                f"{self.base_url}/v1/models",
                timeout=self.timeout
            )
            response.raise_for_status()
            models = response.json().get('data', [])
            if models:
                model_name = models[0].get('id', 'local-model')
                logger.info(f"Detected model: {model_name}")
                return model_name
            return 'local-model'
        except Exception as e:
            logger.warning(f"Could not detect model, using default: {e}")
            return 'local-model'
    
    def _rate_limit(self):
        """Enforce rate limiting"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        min_interval = 1.0 / config.REQUESTS_PER_SECOND
        
        if time_since_last < min_interval:
            sleep_time = min_interval - time_since_last
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def get_emoji_suggestions(self, words: List[str]) -> Dict[str, List[str]]:
        """Get emoji suggestions for a batch of words"""
        self._rate_limit()
        
        # Create the prompt for batch processing
        word_list = ", ".join(words)
        prompt = f"""You are an expert in semantic emoji mapping. For each English word provided, suggest 1-3 emojis that best represent its meaning semantically.

Rules:
1. Choose emojis that are semantically meaningful and intuitive
2. Prefer single emojis when they clearly represent the concept
3. Use 2-3 emojis only when a single emoji isn't sufficient
4. Avoid skin tone modifiers unless essential to meaning
5. Return ONLY emojis, no text explanations
6. Format as: word1: emoji(s), word2: emoji(s), etc.

Words: {word_list}

Response format example:
cat: 🐱
dog: 🐕
happy: 😊
computer: 💻
beautiful: 🌸✨"""

        try:
            response = self.session.post(
                f"{self.base_url}/v1/chat/completions",
                json={
                    "model": self.model_name,
                    "messages": [
                        {
                            "role": "system", 
                            "content": "You are a semantic emoji mapping expert. Provide concise emoji suggestions."
                        },
                        {"role": "user", "content": prompt}
                    ],
                    "max_tokens": 500,
                    "temperature": 0.3,
                    "top_p": 0.9,
                },
                timeout=self.timeout
            )
            
            response.raise_for_status()
            result = response.json()
            
            if 'choices' not in result or not result['choices']:
                logger.error(f"Invalid API response: {result}")
                return {}
            
            content = result['choices'][0]['message']['content'].strip()
            return self._parse_emoji_response(content, words)
            
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {e}")
            return {}
        except Exception as e:
            logger.error(f"Unexpected error in API call: {e}")
            return {}
    
    def _parse_emoji_response(self, content: str, words: List[str]) -> Dict[str, List[str]]:
        """Parse the LLM response to extract emoji mappings"""
        results = {}
        lines = content.split('\n')
        
        for line in lines:
            line = line.strip()
            if ':' in line:
                try:
                    word_part, emoji_part = line.split(':', 1)
                    word = word_part.strip().lower()
                    emoji_text = emoji_part.strip()
                    
                    # Extract individual emojis from the text
                    emojis = []
                    for char in emoji_text:
                        if char in emoji.EMOJI_DATA:
                            emojis.append(char)
                    
                    if word in [w.lower() for w in words] and emojis:
                        results[word] = emojis
                        
                except Exception as e:
                    logger.warning(f"Could not parse line '{line}': {e}")
                    continue
        
        return results

# --------------------------
# Fallback Embedding System
# --------------------------
class FallbackEmbeddingMapper:
    def __init__(self):
        try:
            from sentence_transformers import SentenceTransformer, util
            self.model = SentenceTransformer("all-MiniLM-L6-v2", device=DEVICE)
            self.util = util
            
            # Load emoji data
            mappings = {emj: data.get("en", "") for emj, data in emoji.EMOJI_DATA.items()}
            self.emoji_keys = list(mappings.keys())
            emoji_texts = list(mappings.values())
            self.emoji_embeddings = self.model.encode(
                emoji_texts, convert_to_tensor=True, device=DEVICE
            )
            
            logger.info("Fallback embedding system initialized")
        except ImportError:
            logger.warning("sentence-transformers not available, fallback disabled")
            self.model = None
    
    def get_emoji_suggestions(self, word: str) -> List[str]:
        """Get emoji suggestions using embedding similarity"""
        if not self.model:
            return []
        
        try:
            embedding = self.model.encode(word, convert_to_tensor=True, device=DEVICE)
            scores = self.util.pytorch_cos_sim(embedding, self.emoji_embeddings)[0]
            
            top_indices = scores.argsort(descending=True)
            top_emojis = []
            
            # Get top emojis above similarity threshold
            for i in top_indices:
                if float(scores[i]) >= config.MIN_SIMILARITY_FALLBACK:
                    top_emojis.append(self.emoji_keys[i])
                if len(top_emojis) >= 3:  # Limit to top 3
                    break
            
            # If no good matches, get top 3 anyway
            if not top_emojis:
                for i in top_indices[:3]:
                    top_emojis.append(self.emoji_keys[i])
            
            return top_emojis
            
        except Exception as e:
            logger.error(f"Embedding fallback failed for '{word}': {e}")
            return []

# --------------------------
# Main Emoji Mapper
# --------------------------
class EmojiMapper:
    def __init__(self):
        self.llm_client = LLMApiClient(config.LLM_BASE_URL, config.TIMEOUT)
        self.fallback_mapper = FallbackEmbeddingMapper()
        self.nlp = spacy.load("en_core_web_sm")
        
        self.word_to_emoji = {}
        self.used_emoji_strings = set()
        self.skipped_words = []
        self.api_success_count = 0
        self.fallback_count = 0
    
    def is_unique_combo(self, emoji_str: str) -> bool:
        """Check if emoji string is unique"""
        return emoji_str not in self.used_emoji_strings
    
    def mark_used_combo(self, emoji_str: str):
        """Mark emoji string as used"""
        self.used_emoji_strings.add(emoji_str)
    
    def process_word_batch(self, words: List[str]) -> Dict[str, str]:
        """Process a batch of words and return emoji mappings"""
        batch_results = {}
        
        # First, try LLM API
        llm_suggestions = self.llm_client.get_emoji_suggestions(words)
        
        for word in words:
            word_lower = word.lower()
            lemma = self.nlp(word_lower)[0].lemma_
            
            emoji_candidates = []
            
            # Get LLM suggestions first
            if word_lower in llm_suggestions:
                emoji_candidates = llm_suggestions[word_lower]
                logger.debug(f"LLM suggestions for '{word}': {emoji_candidates}")
            
            # Fallback to embedding if no LLM suggestions
            if not emoji_candidates and self.fallback_mapper.model:
                emoji_candidates = self.fallback_mapper.get_emoji_suggestions(lemma)
                if emoji_candidates:
                    self.fallback_count += 1
                    logger.debug(f"Fallback suggestions for '{word}': {emoji_candidates}")
            
            # Try to assign unique emoji
            assigned = False
            
            # Try single emojis first
            for emj in emoji_candidates:
                if self.is_unique_combo(emj):
                    batch_results[word] = emj
                    self.mark_used_combo(emj)
                    assigned = True
                    if word_lower in llm_suggestions:
                        self.api_success_count += 1
                    break
            
            # Try 2-emoji combinations if single emoji didn't work
            if not assigned and len(emoji_candidates) >= 2:
                for combo in permutations(emoji_candidates[:5], 2):  # Limit combinations
                    combined = ''.join(combo)
                    if self.is_unique_combo(combined):
                        batch_results[word] = combined
                        self.mark_used_combo(combined)
                        assigned = True
                        if word_lower in llm_suggestions:
                            self.api_success_count += 1
                        break
            
            if not assigned:
                self.skipped_words.append(word)
                logger.warning(f"Could not assign emoji to '{word}'")
        
        return batch_results
    
    def build_mappingspings(self, words: List[str]):
        """Build complete emoji mappings for all words"""
        logger.info(f"Processing {len(words)} words with LLM-enhanced mapping...")
        logger.info(f"Using LLM API at: {config.LLM_BASE_URL}")
        
        # Process words in batches
        for i in tqdm(range(0, len(words), config.BATCH_SIZE), desc="Processing batches"):
            batch = words[i:i + config.BATCH_SIZE]
            batch_mappings = self.process_word_batch(batch)
            self.word_to_emoji.update(batch_mappings)
            
            # Small delay between batches to be gentle on the API
            if i + config.BATCH_SIZE < len(words):
                time.sleep(0.1)
        
        logger.info(f"Mapping complete!")
        logger.info(f"LLM API successes: {self.api_success_count}")
        logger.info(f"Fallback mappings: {self.fallback_count}")
        logger.info(f"Total mapped: {len(self.word_to_emoji)}")
        logger.info(f"Skipped words: {len(self.skipped_words)}")

# --------------------------
# Main execution
# --------------------------
def main():
    """Main function to build emoji mappings"""
    logger.info("Starting LLM-Enhanced Emoji Mapping System")
    
    # Load dictionary words
    logger.info("Loading dictionary words...")
    try:
        with open("/usr/share/dict/words", "r") as f:
            words = [w.strip().lower() for w in f if w.strip().isalpha()]
        words = sorted(set(words), key=len)
        logger.info(f"Loaded {len(words)} unique words")
    except FileNotFoundError:
        logger.error("Dictionary file not found at /usr/share/dict/words")
        logger.info("You may need to install a dictionary package:")
        logger.info("  Ubuntu/Debian: sudo apt install wamerican")
        logger.info("  macOS: Dictionary should be available by default")
        return
    
    # Initialize mapper and build mappings
    mapper = EmojiMapper()
    mapper.build_mappingspings(words)
    
    # Apply manual overrides if they exist
    manual_path = os.path.join(config.EMOJI_MAP_DIR, "manual_overrides.json")
    if os.path.exists(manual_path):
        logger.info("Applying manual overrides...")
        with open(manual_path) as f:
            overrides = json.load(f)
            mapper.word_to_emoji.update(overrides)
    
    # Create reverse mapping
    emoji_to_word = {v: k for k, v in mapper.word_to_emoji.items()}
    
    # Save results
    os.makedirs(config.EMOJI_MAP_DIR, exist_ok=True)
    
    # Save forward mapping
    with open(os.path.join(config.EMOJI_MAP_DIR, "word_to_emoji.json"), "w") as f:
        json.dump(mapper.word_to_emoji, f, indent=2, ensure_ascii=False)
    
    # Save reverse mapping
    with open(os.path.join(config.EMOJI_MAP_DIR, "emoji_to_word.json"), "w") as f:
        json.dump(emoji_to_word, f, indent=2, ensure_ascii=False)
    
    # Save skipped words
    with open(os.path.join(config.EMOJI_MAP_DIR, "skipped_words.txt"), "w") as f:
        for word in sorted(mapper.skipped_words):
            f.write(word + "\n")
    
    # Save statistics
    stats = {
        "total_words": len(words),
        "mapped_words": len(mapper.word_to_emoji),
        "skipped_words": len(mapper.skipped_words),
        "llm_api_successes": mapper.api_success_count,
        "fallback_mappings": mapper.fallback_count,
        "unique_emoji_strings": len(mapper.used_emoji_strings)
    }
    
    with open(os.path.join(config.EMOJI_MAP_DIR, "mapping_stats.json"), "w") as f:
        json.dump(stats, f, indent=2)
    
    logger.info("=== Mapping Complete ===")
    logger.info(f"📊 Statistics:")
    logger.info(f"  Total words processed: {stats['total_words']:,}")
    logger.info(f"  Successfully mapped: {stats['mapped_words']:,}")
    logger.info(f"  LLM API successes: {stats['llm_api_successes']:,}")
    logger.info(f"  Fallback mappings: {stats['fallback_mappings']:,}")
    logger.info(f"  Skipped words: {stats['skipped_words']:,}")
    logger.info(f"  Unique emoji strings: {stats['unique_emoji_strings']:,}")
    
    success_rate = (stats['mapped_words'] / stats['total_words']) * 100
    logger.info(f"  Success rate: {success_rate:.2f}%")
    
    if mapper.skipped_words:
        logger.info(f"  First few skipped words: {', '.join(mapper.skipped_words[:10])}")

if __name__ == "__main__":
    main()
