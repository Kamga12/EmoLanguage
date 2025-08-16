# Enhanced LLM Source Builder with Sophisticated Prompt Engineering
# ✅ Integrates the sophisticated prompt engineering system with the existing LLM builder
# ✅ Uses context-aware prompts for better semantic word-to-emoji mapping
# ✅ Implements validation and conflict resolution
# ✅ Provides detailed reasoning and explanations for mappings

import os
import json
import time
import spacy
import multiprocessing
from tqdm import tqdm
from typing import List, Dict, Optional, Set, Tuple
from dataclasses import dataclass
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import logging
from prompt_engineering import PromptEngineeringSystem, WordType, EmojiMappingContext

# --------------------------
# Enhanced Configuration
# --------------------------
@dataclass
class EnhancedConfig:
    # LLM API Configuration
    LLM_BASE_URL: str = "http://127.0.0.1:1234"
    LLM_MODEL: str = "local-model"
    
    # Enhanced prompt settings
    USE_SOPHISTICATED_PROMPTS: bool = True
    ENABLE_WORD_ANALYSIS: bool = True
    ENABLE_VALIDATION: bool = True
    ENABLE_CONFLICT_RESOLUTION: bool = True
    
    # Batch processing
    BATCH_SIZE: int = 5  # Smaller batches for detailed prompts
    REQUESTS_PER_SECOND: int = 3  # Slower rate for complex prompts
    MAX_RETRIES: int = 3
    RETRY_DELAY: float = 1.5
    TIMEOUT: int = 45  # Longer timeout for complex reasoning
    
    # Output configuration
    EMOJI_MAP_DIR: str = "mappings"
    REASONING_OUTPUT: bool = True  # Save reasoning for each mapping

config = EnhancedConfig()

# --------------------------
# Logging setup
# --------------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --------------------------
# Word Type Classification
# --------------------------
class WordClassifier:
    """Classify words into types for specialized prompt handling"""
    
    def __init__(self):
        self.nlp = spacy.load("en_core_web_sm")
        
        # Common word patterns for classification
        self.emotion_words = {
            'happy', 'sad', 'angry', 'joyful', 'excited', 'depressed', 'anxious',
            'content', 'furious', 'ecstatic', 'melancholy', 'cheerful', 'gloomy'
        }
        
        self.technical_terms = {
            'algorithm', 'database', 'software', 'hardware', 'network', 'protocol',
            'encryption', 'debugging', 'compilation', 'framework', 'interface'
        }
    
    def classify_word(self, word: str) -> WordType:
        """Classify a word into its appropriate type"""
        doc = self.nlp(word)
        
        if not doc:
            return WordType.CONCRETE_NOUN
            
        token = doc[0]
        pos = token.pos_
        
        # Check for specific word categories first
        if word.lower() in self.emotion_words:
            return WordType.EMOTIONAL_ADJECTIVE
        
        if word.lower() in self.technical_terms:
            return WordType.TECHNICAL_TERM
            
        # POS-based classification
        if pos == "NOUN":
            # Distinguish concrete vs abstract nouns
            if self._is_abstract_noun(word, token):
                return WordType.ABSTRACT_NOUN
            else:
                return WordType.CONCRETE_NOUN
                
        elif pos == "VERB":
            # Distinguish action vs state verbs  
            if self._is_state_verb(word, token):
                return WordType.STATE_VERB
            else:
                return WordType.ACTION_VERB
                
        elif pos == "ADJ":
            # Distinguish emotional vs descriptive adjectives
            if self._is_emotional_adjective(word, token):
                return WordType.EMOTIONAL_ADJECTIVE
            else:
                return WordType.DESCRIPTIVE_ADJECTIVE
                
        elif pos == "ADV":
            return WordType.ADVERB
        elif pos == "ADP":  # Preposition
            return WordType.PREPOSITION
        elif pos == "PRON":
            return WordType.PRONOUN
        elif pos == "CCONJ" or pos == "SCONJ":
            return WordType.CONJUNCTION
        elif pos == "INTJ":
            return WordType.INTERJECTION
        else:
            return WordType.CONCRETE_NOUN  # Default fallback
    
    def _is_abstract_noun(self, word: str, token) -> bool:
        """Determine if a noun is abstract"""
        abstract_indicators = {
            'concept', 'idea', 'thought', 'emotion', 'feeling', 'belief', 
            'knowledge', 'wisdom', 'freedom', 'justice', 'beauty', 'love',
            'hate', 'fear', 'hope', 'dream', 'memory', 'imagination'
        }
        
        # Check if word is in abstract indicators or has abstract suffixes
        if word.lower() in abstract_indicators:
            return True
            
        abstract_suffixes = ['ness', 'tion', 'sion', 'ment', 'ity', 'ism', 'dom']
        return any(word.lower().endswith(suffix) for suffix in abstract_suffixes)
    
    def _is_state_verb(self, word: str, token) -> bool:
        """Determine if a verb describes a state rather than action"""
        state_verbs = {
            'be', 'am', 'is', 'are', 'was', 'were', 'been', 'being',
            'seem', 'appear', 'look', 'sound', 'feel', 'taste', 'smell',
            'exist', 'remain', 'stay', 'become', 'contain', 'own', 'have',
            'know', 'understand', 'believe', 'think', 'love', 'hate', 'like'
        }
        return word.lower() in state_verbs
    
    def _is_emotional_adjective(self, word: str, token) -> bool:
        """Determine if adjective describes emotion"""
        return word.lower() in self.emotion_words

# --------------------------
# Enhanced LLM API Client
# --------------------------
class EnhancedLLMApiClient:
    """Enhanced LLM client with sophisticated prompt integration"""
    
    def __init__(self, base_url: str, timeout: int = 45):
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.session = requests.Session()
        
        # Configure retry strategy
        retry_strategy = Retry(
            total=config.MAX_RETRIES,
            backoff_factor=1.5,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        self.model_name = self._get_model_name()
        self.last_request_time = 0
        
        # Initialize prompt engineering system
        self.prompt_system = PromptEngineeringSystem()
        
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
    
    def get_sophisticated_mappingsping(self, word: str, word_type: WordType, 
                                      context: Optional[EmojiMappingContext] = None) -> Dict:
        """Get emoji mapping using sophisticated prompts"""
        self._rate_limit()
        
        # Generate sophisticated prompt
        prompt = self.prompt_system.generate_mapping_prompt(word, word_type, context)
        
        try:
            response = self.session.post(
                f"{self.base_url}/v1/chat/completions",
                json={
                    "model": self.model_name,
                    "messages": [
                        {"role": "user", "content": prompt}
                    ],
                    "max_tokens": 800,  # More tokens for detailed reasoning
                    "temperature": 0.2,  # Lower temperature for consistency
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
            return self._parse_sophisticated_response(content, word)
            
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed for '{word}': {e}")
            return {}
        except Exception as e:
            logger.error(f"Unexpected error for '{word}': {e}")
            return {}
    
    def _parse_sophisticated_response(self, content: str, word: str) -> Dict:
        """Parse the sophisticated LLM response"""
        result = {
            'word': word,
            'primary_emoji': None,
            'alternatives': [],
            'reasoning': content,
            'confidence': 'medium',
            'validation_notes': []
        }
        
        # Extract primary mapping
        lines = content.split('\n')
        for i, line in enumerate(lines):
            line = line.strip()
            
            if line.startswith('Emoji:') or 'PRIMARY MAPPING:' in line:
                # Look for emoji in this line or next few lines
                for j in range(i, min(i+3, len(lines))):
                    emoji_line = lines[j]
                    # Find emojis in the line
                    import emoji
                    emojis = [char for char in emoji_line if char in emoji.EMOJI_DATA]
                    if emojis:
                        result['primary_emoji'] = ''.join(emojis[:2])  # Take first 1-2 emojis
                        break
            
            elif line.startswith('ALTERNATIVES:') or 'alternative' in line.lower():
                # Parse alternatives
                for j in range(i+1, min(i+5, len(lines))):
                    alt_line = lines[j].strip()
                    if alt_line and ('.' in alt_line or '|' in alt_line):
                        import emoji
                        emojis = [char for char in alt_line if char in emoji.EMOJI_DATA]
                        if emojis:
                            result['alternatives'].append(''.join(emojis[:2]))
            
            elif 'confidence:' in line.lower() or 'intuitive rating:' in line.lower():
                if 'high' in line.lower() or '5' in line or '4' in line:
                    result['confidence'] = 'high'
                elif 'low' in line.lower() or '1' in line or '2' in line:
                    result['confidence'] = 'low'
        
        return result
    
    def validate_mapping(self, word: str, emoji: str, reasoning: str) -> Dict:
        """Validate an emoji mapping using sophisticated prompts"""
        self._rate_limit()
        
        validation_prompt = self.prompt_system.generate_validation_prompt(word, emoji, reasoning)
        
        try:
            response = self.session.post(
                f"{self.base_url}/v1/chat/completions",
                json={
                    "model": self.model_name,
                    "messages": [
                        {"role": "user", "content": validation_prompt}
                    ],
                    "max_tokens": 600,
                    "temperature": 0.1,  # Very low temperature for validation
                    "top_p": 0.8,
                },
                timeout=self.timeout
            )
            
            response.raise_for_status()
            result = response.json()
            
            if 'choices' not in result or not result['choices']:
                return {'validation': 'failed', 'reason': 'Invalid API response'}
            
            content = result['choices'][0]['message']['content'].strip()
            return self._parse_validation_response(content)
            
        except Exception as e:
            logger.error(f"Validation failed for '{word}': {e}")
            return {'validation': 'error', 'reason': str(e)}
    
    def _parse_validation_response(self, content: str) -> Dict:
        """Parse validation response"""
        result = {
            'validation': 'unknown',
            'scores': {},
            'issues': [],
            'recommendations': [],
            'overall_score': 0
        }
        
        lines = content.split('\n')
        for line in lines:
            line = line.strip().lower()
            
            if 'approve' in line:
                result['validation'] = 'approved'
            elif 'reject' in line:
                result['validation'] = 'rejected'
            elif 'revise' in line:
                result['validation'] = 'needs_revision'
            
            # Extract scores
            if any(criterion in line for criterion in ['semantic', 'visual', 'cultural', 'disambiguation', 'cognitive']):
                import re
                scores = re.findall(r'[1-5]', line)
                if scores:
                    score = int(scores[0])
                    if 'semantic' in line:
                        result['scores']['semantic'] = score
                    elif 'visual' in line:
                        result['scores']['visual'] = score
                    elif 'cultural' in line:
                        result['scores']['cultural'] = score
                    elif 'disambiguation' in line:
                        result['scores']['disambiguation'] = score
                    elif 'cognitive' in line:
                        result['scores']['cognitive'] = score
        
        # Calculate overall score
        if result['scores']:
            result['overall_score'] = sum(result['scores'].values()) / len(result['scores'])
        
        return result

# --------------------------
# Enhanced Emoji Mapper
# --------------------------
class EnhancedEmojiMapper:
    """Enhanced emoji mapper with sophisticated prompt engineering"""
    
    def __init__(self):
        self.llm_client = EnhancedLLMApiClient(config.LLM_BASE_URL, config.TIMEOUT)
        self.word_classifier = WordClassifier()
        
        self.word_to_emoji = {}
        self.emoji_to_word = {}
        self.used_emoji_strings = set()
        self.skipped_words = []
        self.mapping_reasoning = {}  # Store reasoning for each mapping
        self.validation_results = {}  # Store validation results
        
        self.stats = {
            'total_processed': 0,
            'successful_mappings': 0,
            'validated_mappings': 0,
            'high_confidence': 0,
            'conflicts_resolved': 0
        }
    
    def is_unique_combo(self, emoji_str: str) -> bool:
        """Check if emoji string is unique"""
        return emoji_str not in self.used_emoji_strings
    
    def mark_used_combo(self, emoji_str: str):
        """Mark emoji string as used"""
        self.used_emoji_strings.add(emoji_str)
    
    def process_word(self, word: str) -> Dict:
        """Process a single word with sophisticated prompts"""
        logger.debug(f"Processing word: {word}")
        self.stats['total_processed'] += 1
        
        # Classify the word type
        word_type = self.word_classifier.classify_word(word)
        logger.debug(f"Classified '{word}' as {word_type}")
        
        # Create context (could be enhanced with external data)
        context = None  # For now, but could be populated with dictionary definitions, etc.
        
        # Get sophisticated emoji mapping
        mapping_result = self.llm_client.get_sophisticated_mappingsping(
            word, word_type, context
        )
        
        if not mapping_result or not mapping_result.get('primary_emoji'):
            logger.warning(f"No mapping result for '{word}'")
            self.skipped_words.append(word)
            return {}
        
        # Try to assign unique emoji
        primary_emoji = mapping_result['primary_emoji']
        alternatives = mapping_result.get('alternatives', [])
        
        final_emoji = None
        
        # Try primary first
        if primary_emoji and self.is_unique_combo(primary_emoji):
            final_emoji = primary_emoji
        else:
            # Try alternatives
            for alt_emoji in alternatives:
                if alt_emoji and self.is_unique_combo(alt_emoji):
                    final_emoji = alt_emoji
                    break
        
        if final_emoji:
            # Assign the mapping
            self.word_to_emoji[word] = final_emoji
            self.emoji_to_word[final_emoji] = word
            self.mark_used_combo(final_emoji)
            
            # Store reasoning
            self.mapping_reasoning[word] = mapping_result.get('reasoning', '')
            
            # Update confidence stats
            if mapping_result.get('confidence') == 'high':
                self.stats['high_confidence'] += 1
            
            self.stats['successful_mappings'] += 1
            
            # Validate if enabled
            if config.ENABLE_VALIDATION:
                validation_result = self.llm_client.validate_mapping(
                    word, final_emoji, mapping_result.get('reasoning', '')
                )
                self.validation_results[word] = validation_result
                
                if validation_result.get('validation') == 'approved':
                    self.stats['validated_mappings'] += 1
            
            logger.debug(f"Successfully mapped '{word}' to '{final_emoji}'")
            return {
                'word': word,
                'emoji': final_emoji,
                'reasoning': mapping_result.get('reasoning', ''),
                'confidence': mapping_result.get('confidence', 'medium'),
                'validation': validation_result if config.ENABLE_VALIDATION else None
            }
        else:
            logger.warning(f"Could not find unique emoji for '{word}'")
            self.skipped_words.append(word)
            return {}
    
    def build_mappingspings(self, words: List[str]):
        """Build emoji mappings for all words with enhanced processing"""
        logger.info(f"Processing {len(words)} words with sophisticated prompt engineering...")
        logger.info(f"Configuration: Validation={config.ENABLE_VALIDATION}, Analysis={config.ENABLE_WORD_ANALYSIS}")
        
        # Process words individually with sophisticated prompts
        for word in tqdm(words, desc="Enhanced processing"):
            result = self.process_word(word)
            
            # Small delay to be gentle on the API
            time.sleep(0.2)
        
        logger.info("=== Processing Complete ===")
        logger.info(f"📊 Enhanced Statistics:")
        logger.info(f"  Total processed: {self.stats['total_processed']:,}")
        logger.info(f"  Successful mappings: {self.stats['successful_mappings']:,}")
        logger.info(f"  High confidence: {self.stats['high_confidence']:,}")
        logger.info(f"  Validated mappings: {self.stats['validated_mappings']:,}")
        logger.info(f"  Skipped words: {len(self.skipped_words):,}")
        
        success_rate = (self.stats['successful_mappings'] / self.stats['total_processed']) * 100
        logger.info(f"  Success rate: {success_rate:.2f}%")
        
        if config.ENABLE_VALIDATION and self.stats['successful_mappings'] > 0:
            validation_rate = (self.stats['validated_mappings'] / self.stats['successful_mappings']) * 100
            logger.info(f"  Validation approval rate: {validation_rate:.2f}%")

    def save_enhanced_results(self):
        """Save results with enhanced information"""
        os.makedirs(config.EMOJI_MAP_DIR, exist_ok=True)
        
        # Save basic mappings
        with open(os.path.join(config.EMOJI_MAP_DIR, "word_to_emoji.json"), "w") as f:
            json.dump(self.word_to_emoji, f, indent=2, ensure_ascii=False)
        
        with open(os.path.join(config.EMOJI_MAP_DIR, "emoji_to_word.json"), "w") as f:
            json.dump(self.emoji_to_word, f, indent=2, ensure_ascii=False)
        
        # Save enhanced information if enabled
        if config.REASONING_OUTPUT:
            with open(os.path.join(config.EMOJI_MAP_DIR, "mapping_reasoning.json"), "w") as f:
                json.dump(self.mapping_reasoning, f, indent=2, ensure_ascii=False)
        
        if config.ENABLE_VALIDATION:
            with open(os.path.join(config.EMOJI_MAP_DIR, "validation_results.json"), "w") as f:
                json.dump(self.validation_results, f, indent=2, ensure_ascii=False)
        
        # Save enhanced statistics
        enhanced_stats = {
            **self.stats,
            "configuration": {
                "sophisticated_prompts": config.USE_SOPHISTICATED_PROMPTS,
                "validation_enabled": config.ENABLE_VALIDATION,
                "reasoning_saved": config.REASONING_OUTPUT,
            },
            "unique_emoji_strings": len(self.used_emoji_strings),
            "skipped_word_count": len(self.skipped_words)
        }
        
        with open(os.path.join(config.EMOJI_MAP_DIR, "enhanced_stats.json"), "w") as f:
            json.dump(enhanced_stats, f, indent=2)
        
        # Save skipped words
        with open(os.path.join(config.EMOJI_MAP_DIR, "skipped_words.txt"), "w") as f:
            for word in sorted(self.skipped_words):
                f.write(word + "\n")

# --------------------------
# Main execution
# --------------------------
def main():
    """Main function with enhanced emoji mapping"""
    logger.info("🚀 Starting Enhanced LLM Emoji Mapping System")
    logger.info(f"Using sophisticated prompts: {config.USE_SOPHISTICATED_PROMPTS}")
    
    # Load dictionary words (using a smaller set for testing)
    logger.info("Loading dictionary words...")
    try:
        with open("/usr/share/dict/words", "r") as f:
            words = [w.strip().lower() for w in f if w.strip().isalpha()]
        words = sorted(set(words), key=len)
        
        # For testing, use only the first 100 words
        test_words = words[:100]
        logger.info(f"Using {len(test_words)} words for enhanced processing (testing mode)")
        
    except FileNotFoundError:
        logger.error("Dictionary file not found at /usr/share/dict/words")
        return
    
    # Initialize enhanced mapper
    mapper = EnhancedEmojiMapper()
    
    # Build mappings
    mapper.build_mappingspings(test_words)
    
    # Save results
    mapper.save_enhanced_results()
    
    logger.info("✅ Enhanced emoji mapping complete!")
    logger.info(f"Check {config.EMOJI_MAP_DIR}/ for results including reasoning and validation")

if __name__ == "__main__":
    main()
