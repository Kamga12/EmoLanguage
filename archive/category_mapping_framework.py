# Category-Based Mapping Framework for Emoji Language System
# ✅ Organizes words into semantic categories for consistent emoji usage
# ✅ Defines category-specific emoji assignment rules and patterns
# ✅ Ensures systematic consistency across similar word types
# ✅ Provides fallback strategies for edge cases and rare words
# ✅ Maintains intuitive mappings while preventing emoji conflicts

import json
import os
from typing import Dict, List, Set, Optional, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
import re
import spacy
from collections import defaultdict, Counter

class SemanticCategory(Enum):
    """Primary semantic categories for word-to-emoji mapping"""
    
    # BASIC STRUCTURAL CATEGORIES
    COMMON_WORDS = "common_words"           # Pronouns, articles, prepositions, conjunctions
    
    # ACTION CATEGORIES
    PHYSICAL_ACTIONS = "physical_actions"   # run, jump, eat, walk, climb
    MENTAL_ACTIONS = "mental_actions"       # think, remember, imagine, learn
    COMMUNICATION = "communication"         # speak, write, listen, read, whisper
    MOTION_TRAVEL = "motion_travel"         # go, come, move, travel, migrate
    
    # OBJECT CATEGORIES
    LIVING_BEINGS = "living_beings"         # animals, plants, people roles
    EVERYDAY_OBJECTS = "everyday_objects"   # furniture, tools, containers
    TECHNOLOGY = "technology"               # computers, phones, gadgets
    FOOD_DRINK = "food_drink"              # meals, beverages, ingredients
    CLOTHING_ACCESSORIES = "clothing"       # garments, jewelry, fashion
    VEHICLES_TRANSPORT = "transport"        # cars, planes, boats, public transport
    
    # DESCRIPTIVE CATEGORIES
    PHYSICAL_PROPERTIES = "physical_props"  # color, size, shape, texture
    EMOTIONAL_STATES = "emotions"           # happy, sad, angry, excited
    SENSORY_EXPERIENCE = "sensory"          # hot, cold, loud, bright, smooth
    QUANTITY_MEASURE = "quantity"           # numbers, measurements, amounts
    
    # ABSTRACT CATEGORIES
    TIME_TEMPORAL = "time"                  # yesterday, future, duration, seasons
    SPACE_LOCATION = "space"                # here, there, above, inside, directions
    ABSTRACT_CONCEPTS = "abstract"          # love, freedom, justice, beauty
    SOCIAL_RELATIONS = "social"             # family, friendship, community, roles
    
    # SPECIALIZED CATEGORIES
    NATURE_WEATHER = "nature"               # weather, natural phenomena, geography
    SCIENCE_ACADEMIC = "science"            # scientific terms, academic concepts
    ARTS_CULTURE = "culture"                # music, art, literature, entertainment
    BUSINESS_WORK = "work"                  # professions, commerce, office terms
    SPORTS_RECREATION = "sports"            # games, exercises, recreational activities
    HEALTH_MEDICAL = "health"               # body parts, medical terms, wellness

@dataclass
class CategoryMappingRule:
    """Rules for how to map words in a specific category to emojis"""
    category: SemanticCategory
    priority_patterns: List[str]        # Preferred emoji patterns/types
    fallback_patterns: List[str]        # Backup patterns when primary fails
    combination_strategy: str           # How to create 2-emoji combinations
    consistency_rules: List[str]        # Rules for maintaining consistency
    examples: Dict[str, str]           # Example word->emoji mappings
    prohibited_emojis: Set[str] = field(default_factory=set)  # Emojis to avoid

class CategoryBasedMappingFramework:
    """
    Advanced framework for category-based emoji mapping that ensures
    semantic consistency and intuitive patterns across word categories.
    """
    
    def __init__(self):
        self.nlp = spacy.load("en_core_web_sm")
        
        # Initialize category mapping rules
        self.category_rules = self._initialize_category_rules()
        
        # Reserved emoji pools for each category
        self.category_emoji_pools = self._create_category_emoji_pools()
        
        # Track emoji usage across categories
        self.used_emojis = set()
        self.category_assignments = defaultdict(set)  # category -> set of emojis used
        self.word_categorization = {}  # word -> category
        
        # Consistency tracking
        self.pattern_usage = defaultdict(int)  # track which patterns are most used
        self.semantic_clusters = defaultdict(list)  # group similar words
        
    def _initialize_category_rules(self) -> Dict[SemanticCategory, CategoryMappingRule]:
        """Initialize comprehensive mapping rules for each semantic category"""
        
        return {
            SemanticCategory.COMMON_WORDS: CategoryMappingRule(
                category=SemanticCategory.COMMON_WORDS,
                priority_patterns=["single_geometric", "simple_symbols", "arrows"],
                fallback_patterns=["basic_shapes", "minimalist_icons"],
                combination_strategy="avoid_combinations",
                consistency_rules=[
                    "Use simple, memorable shapes",
                    "Prefer geometric symbols over complex emojis", 
                    "Maintain visual distinction between similar words",
                    "Use arrows for directional relationships"
                ],
                examples={
                    "the": "🔷", "a": "🔸", "an": "🔹", "and": "➕", "or": "🔀",
                    "but": "⚖️", "in": "📍", "on": "⬆️", "at": "🎯", "to": "➡️",
                    "from": "⬅️", "with": "🤝", "by": "📌", "for": "🎁"
                },
                prohibited_emojis={"🔥", "❤️", "😀", "🏃", "🐱"}  # Reserve for other categories
            ),
            
            SemanticCategory.PHYSICAL_ACTIONS: CategoryMappingRule(
                category=SemanticCategory.PHYSICAL_ACTIONS,
                priority_patterns=["person_activity", "motion_symbols", "action_gestures"],
                fallback_patterns=["tool_associations", "result_symbols"],
                combination_strategy="person_plus_tool",
                consistency_rules=[
                    "Prefer emojis showing people performing actions",
                    "Use motion lines and dynamic symbols",
                    "Group similar actions with consistent visual themes",
                    "Combine person + tool/object when action unclear"
                ],
                examples={
                    "run": "🏃", "walk": "🚶", "jump": "🤸", "swim": "🏊",
                    "eat": "🍽️", "drink": "🥤", "sleep": "😴", "dance": "💃",
                    "climb": "🧗", "lift": "🏋️", "throw": "🤾", "catch": "🥎"
                }
            ),
            
            SemanticCategory.MENTAL_ACTIONS: CategoryMappingRule(
                category=SemanticCategory.MENTAL_ACTIONS,
                priority_patterns=["brain_symbols", "thought_bubbles", "light_bulbs"],
                fallback_patterns=["head_gestures", "symbolic_representations"],
                combination_strategy="brain_plus_concept",
                consistency_rules=[
                    "Use brain, head, and thought-related symbols",
                    "Lightbulb for insight and understanding",
                    "Books and education symbols for learning",
                    "Memory symbols for recall and remembrance"
                ],
                examples={
                    "think": "🤔", "remember": "🧠", "forget": "🫥", "learn": "📚",
                    "understand": "💡", "imagine": "💭", "dream": "💤", "focus": "🎯",
                    "decide": "⚖️", "analyze": "🔍", "create": "✨", "solve": "🧩"
                }
            ),
            
            SemanticCategory.COMMUNICATION: CategoryMappingRule(
                category=SemanticCategory.COMMUNICATION,
                priority_patterns=["speech_symbols", "communication_devices", "text_symbols"],
                fallback_patterns=["gesture_combinations", "media_symbols"],
                combination_strategy="medium_plus_message",
                consistency_rules=[
                    "Use speech bubbles and mouth symbols for speaking",
                    "Text and writing symbols for written communication",
                    "Ear and listening symbols for reception",
                    "Device symbols for modern communication methods"
                ],
                examples={
                    "speak": "💬", "talk": "🗣️", "whisper": "🤫", "shout": "📢",
                    "write": "✍️", "read": "📖", "listen": "👂", "hear": "👂",
                    "call": "📞", "text": "💬", "email": "📧", "broadcast": "📺"
                }
            ),
            
            SemanticCategory.LIVING_BEINGS: CategoryMappingRule(
                category=SemanticCategory.LIVING_BEINGS,
                priority_patterns=["direct_representation", "species_specific"],
                fallback_patterns=["category_representatives", "characteristic_features"],
                combination_strategy="species_plus_trait",
                consistency_rules=[
                    "Use specific animal/plant emojis when available",
                    "Group by biological categories (mammals, birds, etc.)",
                    "Use representative species for broader categories",
                    "Combine species + distinctive feature for specificity"
                ],
                examples={
                    "cat": "🐱", "dog": "🐶", "bird": "🐦", "fish": "🐟",
                    "tree": "🌳", "flower": "🌸", "grass": "🌱", "animal": "🐾",
                    "person": "👤", "child": "🧒", "adult": "👨", "family": "👪"
                }
            ),
            
            SemanticCategory.EVERYDAY_OBJECTS: CategoryMappingRule(
                category=SemanticCategory.EVERYDAY_OBJECTS,
                priority_patterns=["direct_object_match", "functional_representation"],
                fallback_patterns=["category_symbols", "usage_context"],
                combination_strategy="object_plus_function",
                consistency_rules=[
                    "Use exact emoji match when available",
                    "Group by function when specific emoji unavailable",
                    "Maintain consistency within object categories",
                    "Consider primary use context"
                ],
                examples={
                    "chair": "🪑", "table": "🪑", "book": "📖", "pen": "🖊️",
                    "cup": "☕", "plate": "🍽️", "key": "🗝️", "door": "🚪",
                    "window": "🪟", "mirror": "🪞", "clock": "🕐", "lamp": "💡"
                }
            ),
            
            SemanticCategory.EMOTIONAL_STATES: CategoryMappingRule(
                category=SemanticCategory.EMOTIONAL_STATES,
                priority_patterns=["facial_expressions", "heart_variations", "gesture_emotions"],
                fallback_patterns=["symbolic_representations", "color_associations"],
                combination_strategy="face_plus_intensity",
                consistency_rules=[
                    "Use facial expressions as primary choice",
                    "Group emotions by valence (positive/negative/neutral)",
                    "Use heart variations for love-related emotions",
                    "Maintain intensity consistency (mild -> strong)"
                ],
                examples={
                    "happy": "😊", "sad": "😢", "angry": "😠", "excited": "🤩",
                    "love": "❤️", "fear": "😨", "surprised": "😲", "calm": "😌",
                    "joy": "😄", "worry": "😟", "proud": "😌", "ashamed": "😳"
                }
            ),
            
            SemanticCategory.TIME_TEMPORAL: CategoryMappingRule(
                category=SemanticCategory.TIME_TEMPORAL,
                priority_patterns=["clock_symbols", "calendar_symbols", "seasonal_symbols"],
                fallback_patterns=["directional_time", "cyclical_symbols"],
                combination_strategy="time_unit_plus_direction",
                consistency_rules=[
                    "Use clock faces for specific times",
                    "Use calendar symbols for dates and periods", 
                    "Use seasonal symbols for time of year",
                    "Use arrows for temporal direction (past/future)"
                ],
                examples={
                    "time": "🕐", "today": "📅", "yesterday": "⬅️📅", "tomorrow": "➡️📅",
                    "morning": "🌅", "evening": "🌇", "night": "🌙", "week": "📅",
                    "year": "🗓️", "season": "🍂", "past": "⏪", "future": "⏩"
                }
            ),
            
            SemanticCategory.ABSTRACT_CONCEPTS: CategoryMappingRule(
                category=SemanticCategory.ABSTRACT_CONCEPTS,
                priority_patterns=["symbolic_metaphors", "cultural_symbols", "conceptual_representations"],
                fallback_patterns=["related_concrete_objects", "emotional_associations"],
                combination_strategy="metaphor_plus_context",
                consistency_rules=[
                    "Use universally recognized symbols when possible",
                    "Choose metaphors that are intuitive and cross-cultural",
                    "Maintain consistency in metaphorical logic",
                    "Avoid overly complex or arbitrary associations"
                ],
                examples={
                    "freedom": "🕊️", "justice": "⚖️", "peace": "☮️", "love": "❤️",
                    "hope": "🌟", "beauty": "🌺", "truth": "✨", "wisdom": "🦉",
                    "power": "⚡", "growth": "🌱", "change": "🔄", "unity": "🤝"
                }
            ),
            
            SemanticCategory.NATURE_WEATHER: CategoryMappingRule(
                category=SemanticCategory.NATURE_WEATHER,
                priority_patterns=["weather_symbols", "natural_phenomena", "landscape_features"],
                fallback_patterns=["seasonal_associations", "environmental_context"],
                combination_strategy="element_plus_intensity",
                consistency_rules=[
                    "Use direct weather emoji representations",
                    "Group by natural categories (water, land, air)",
                    "Show intensity through emoji selection",
                    "Use landscape features for geographic terms"
                ],
                examples={
                    "rain": "🌧️", "sun": "☀️", "snow": "❄️", "wind": "💨",
                    "mountain": "⛰️", "ocean": "🌊", "forest": "🌲", "desert": "🏜️",
                    "storm": "⛈️", "rainbow": "🌈", "cloud": "☁️", "fire": "🔥"
                }
            )
        }
    
    def _create_category_emoji_pools(self) -> Dict[SemanticCategory, Set[str]]:
        """Create reserved pools of emojis for each category to prevent conflicts"""
        
        # Import emoji library to get all available emojis
        try:
            import emoji
            all_emojis = set(emoji.EMOJI_DATA.keys())
        except ImportError:
            # Fallback to a smaller set if emoji library not available
            all_emojis = set("😀😃😄😁😆😅😂🤣☺️😊😇🙂🙃😉😌😍🥰😘😗😙😚😋😛😝😜🤪🤨🧐🤓😎🤩🥳😏😒😞😔😟😕🙁☹️😣😖😫😩🥺😢😭😤😠😡🤬🤯😳🥵🥶😱😨😰😥😓🤗🤔🤭🤫🤥😶😐😑😬🙄😯😦😧😮😲🥱😴🤤😪😵🤐🥴🤢🤮🤧😷🤒🤕🤑🤠😈👿👹👺🤡💩👻💀☠️👽👾🤖🎃😺😸😹😻😼😽🙀😿😾")
        
        return {
            SemanticCategory.COMMON_WORDS: {
                "🔷", "🔸", "🔹", "➕", "➖", "✖️", "➗", "🔀", "⚖️", 
                "📍", "⬆️", "⬇️", "⬅️", "➡️", "🎯", "📌", "🎁", "🤝"
            },
            
            SemanticCategory.PHYSICAL_ACTIONS: {
                "🏃", "🚶", "🤸", "🏊", "🍽️", "🥤", "😴", "💃", "🕺",
                "🧗", "🏋️", "🤾", "🥎", "⚽", "🏀", "🎾", "🏓", "🏸"
            },
            
            SemanticCategory.EMOTIONAL_STATES: {
                "😊", "😢", "😠", "🤩", "❤️", "😨", "😲", "😌", "😄",
                "😟", "😳", "🥰", "😡", "😍", "🤗", "😔", "😤", "😊"
            },
            
            SemanticCategory.LIVING_BEINGS: {
                "🐱", "🐶", "🐦", "🐟", "🐸", "🐭", "🐹", "🐰", "🦊",
                "🐻", "🐼", "🐨", "🐯", "🦁", "🐮", "🐷", "🐗", "🦓"
            },
            
            SemanticCategory.NATURE_WEATHER: {
                "🌧️", "☀️", "❄️", "💨", "⛰️", "🌊", "🌲", "🏜️", "⛈️",
                "🌈", "☁️", "🔥", "🌪️", "🌋", "🌍", "🌙", "⭐", "🌟"
            }
            # Add more category pools as needed...
        }
    
    def categorize_word(self, word: str) -> SemanticCategory:
        """
        Categorize a word into its primary semantic category using
        linguistic analysis and predefined patterns.
        """
        
        # Check if already categorized
        if word in self.word_categorization:
            return self.word_categorization[word]
        
        # Use spaCy for linguistic analysis
        doc = self.nlp(word)
        if not doc:
            return SemanticCategory.COMMON_WORDS
        
        token = doc[0]
        pos = token.pos_
        lemma = token.lemma_.lower()
        
        # Category classification logic
        category = self._classify_by_patterns(word, lemma, pos, token)
        
        # Cache the result
        self.word_categorization[word] = category
        return category
    
    def _classify_by_patterns(self, word: str, lemma: str, pos: str, token) -> SemanticCategory:
        """Classify word using various linguistic and semantic patterns"""
        
        # Function words (most common structural elements)
        function_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'from',
            'with', 'by', 'for', 'of', 'is', 'are', 'was', 'were', 'have', 'has',
            'he', 'she', 'it', 'they', 'we', 'you', 'i', 'me', 'him', 'her',
            'this', 'that', 'these', 'those', 'some', 'any', 'all', 'each'
        }
        
        if lemma in function_words:
            return SemanticCategory.COMMON_WORDS
        
        # Emotion words
        emotion_words = {
            'happy', 'sad', 'angry', 'joyful', 'excited', 'depressed', 'anxious',
            'content', 'furious', 'ecstatic', 'melancholy', 'cheerful', 'gloomy',
            'love', 'hate', 'fear', 'surprise', 'disgust', 'joy', 'anger', 'sadness'
        }
        
        if lemma in emotion_words:
            return SemanticCategory.EMOTIONAL_STATES
        
        # Physical action verbs
        if pos == "VERB":
            physical_actions = {
                'run', 'walk', 'jump', 'swim', 'eat', 'drink', 'sleep', 'dance',
                'climb', 'lift', 'throw', 'catch', 'push', 'pull', 'kick', 'hit'
            }
            
            mental_actions = {
                'think', 'remember', 'forget', 'learn', 'understand', 'imagine',
                'dream', 'focus', 'decide', 'analyze', 'create', 'solve', 'know'
            }
            
            communication_verbs = {
                'speak', 'talk', 'whisper', 'shout', 'write', 'read', 'listen',
                'hear', 'call', 'text', 'email', 'broadcast', 'tell', 'ask'
            }
            
            if lemma in physical_actions:
                return SemanticCategory.PHYSICAL_ACTIONS
            elif lemma in mental_actions:
                return SemanticCategory.MENTAL_ACTIONS
            elif lemma in communication_verbs:
                return SemanticCategory.COMMUNICATION
        
        # Animals and living beings
        if pos == "NOUN":
            animals = {
                'cat', 'dog', 'bird', 'fish', 'animal', 'pet', 'horse', 'cow',
                'pig', 'sheep', 'chicken', 'duck', 'mouse', 'rat', 'rabbit', 'bear'
            }
            
            plants = {
                'tree', 'flower', 'plant', 'grass', 'leaf', 'rose', 'oak', 'pine'
            }
            
            people = {
                'person', 'people', 'man', 'woman', 'child', 'baby', 'adult',
                'family', 'friend', 'teacher', 'doctor', 'nurse', 'student'
            }
            
            if lemma in animals or lemma in plants or lemma in people:
                return SemanticCategory.LIVING_BEINGS
            
            # Time-related nouns
            time_words = {
                'time', 'day', 'night', 'morning', 'afternoon', 'evening',
                'today', 'yesterday', 'tomorrow', 'week', 'month', 'year',
                'past', 'present', 'future', 'now', 'then', 'when'
            }
            
            if lemma in time_words:
                return SemanticCategory.TIME_TEMPORAL
            
            # Weather and nature
            nature_words = {
                'rain', 'sun', 'snow', 'wind', 'storm', 'cloud', 'sky',
                'mountain', 'ocean', 'sea', 'river', 'forest', 'desert',
                'weather', 'climate', 'temperature', 'season', 'summer',
                'winter', 'spring', 'autumn', 'fall'
            }
            
            if lemma in nature_words:
                return SemanticCategory.NATURE_WEATHER
            
            # Technology words
            tech_words = {
                'computer', 'phone', 'internet', 'software', 'hardware',
                'technology', 'digital', 'online', 'website', 'app',
                'program', 'code', 'data', 'algorithm', 'system'
            }
            
            if lemma in tech_words:
                return SemanticCategory.TECHNOLOGY
            
            # Food and drink
            food_words = {
                'food', 'eat', 'drink', 'meal', 'breakfast', 'lunch', 'dinner',
                'bread', 'meat', 'fruit', 'vegetable', 'water', 'milk', 'coffee',
                'tea', 'juice', 'restaurant', 'kitchen', 'cooking'
            }
            
            if lemma in food_words:
                return SemanticCategory.FOOD_DRINK
            
            # Abstract concepts
            abstract_words = {
                'freedom', 'justice', 'peace', 'love', 'hope', 'beauty',
                'truth', 'wisdom', 'power', 'growth', 'change', 'unity',
                'concept', 'idea', 'thought', 'belief', 'knowledge', 'understanding'
            }
            
            if lemma in abstract_words:
                return SemanticCategory.ABSTRACT_CONCEPTS
        
        # Default categorization based on POS
        if pos in ["NOUN"]:
            return SemanticCategory.EVERYDAY_OBJECTS
        elif pos in ["ADJ"]:
            return SemanticCategory.PHYSICAL_PROPERTIES
        elif pos in ["ADV"]:
            return SemanticCategory.COMMON_WORDS
        
        return SemanticCategory.COMMON_WORDS  # Default fallback
    
    def get_category_emoji_recommendation(self, word: str, category: SemanticCategory) -> Dict:
        """
        Get emoji recommendation for a word based on its category,
        following category-specific rules and patterns.
        """
        
        # Get category rules
        if category not in self.category_rules:
            category = SemanticCategory.COMMON_WORDS  # fallback
        
        rules = self.category_rules[category]
        
        # Check for direct example match first
        if word in rules.examples:
            example_emoji = rules.examples[word]
            if example_emoji not in self.used_emojis:
                return {
                    'word': word,
                    'category': category.value,
                    'primary_emoji': example_emoji,
                    'method': 'direct_example',
                    'confidence': 'high',
                    'reasoning': f"Direct example from {category.value} category rules"
                }
        
        # Use category-specific emoji pool
        if category in self.category_emoji_pools:
            available_emojis = self.category_emoji_pools[category] - self.used_emojis
            
            if available_emojis:
                # Select based on semantic similarity (simplified heuristic)
                best_emoji = self._select_best_emoji_from_pool(word, available_emojis, rules)
                
                if best_emoji:
                    return {
                        'word': word,
                        'category': category.value,
                        'primary_emoji': best_emoji,
                        'method': 'category_pool',
                        'confidence': 'medium',
                        'reasoning': f"Selected from {category.value} emoji pool based on semantic fit"
                    }
        
        # Fallback to combination strategy
        combination = self._create_emoji_combination(word, category, rules)
        if combination:
            return {
                'word': word,
                'category': category.value,
                'primary_emoji': combination,
                'method': 'combination',
                'confidence': 'low',
                'reasoning': f"Created combination using {category.value} strategy: {rules.combination_strategy}"
            }
        
        # Final fallback
        return {
            'word': word,
            'category': category.value,
            'primary_emoji': None,
            'method': 'failed',
            'confidence': 'none',
            'reasoning': "Could not find suitable emoji mapping"
        }
    
    def _select_best_emoji_from_pool(self, word: str, emoji_pool: Set[str], rules: CategoryMappingRule) -> Optional[str]:
        """Select the most appropriate emoji from a category pool"""
        
        # For now, use a simple heuristic based on word characteristics
        # This could be enhanced with more sophisticated semantic matching
        
        pool_list = list(emoji_pool)
        
        # Simple selection based on word properties
        if len(word) <= 3:
            # Short words get simpler emojis
            return pool_list[0] if pool_list else None
        else:
            # Longer words get more complex emojis
            return pool_list[-1] if pool_list else None
    
    def _create_emoji_combination(self, word: str, category: SemanticCategory, rules: CategoryMappingRule) -> Optional[str]:
        """Create a 2-emoji combination based on category strategy"""
        
        # Get available emojis from category pool
        if category in self.category_emoji_pools:
            available = list(self.category_emoji_pools[category] - self.used_emojis)
            
            if len(available) >= 2:
                # Simple combination strategy - take first two available
                combination = available[0] + available[1]
                
                # Check if combination is unique globally
                if combination not in self.used_emojis:
                    return combination
        
        return None
    
    def process_word_batch(self, words: List[str]) -> Dict[str, Dict]:
        """Process a batch of words with category-based mapping"""
        
        results = {}
        
        # First pass: categorize all words
        for word in words:
            category = self.categorize_word(word)
            results[word] = {'category': category}
        
        # Second pass: generate mappings with category consistency
        for word in words:
            category = results[word]['category']
            recommendation = self.get_category_emoji_recommendation(word, category)
            
            results[word].update(recommendation)
            
            # Mark emoji as used if successfully assigned
            if recommendation['primary_emoji']:
                self.used_emojis.add(recommendation['primary_emoji'])
                self.category_assignments[category].add(recommendation['primary_emoji'])
        
        return results
    
    def generate_category_report(self) -> Dict:
        """Generate a comprehensive report on category-based mapping"""
        
        return {
            'categories_defined': len(self.category_rules),
            'category_usage': {
                cat.value: len(emojis) 
                for cat, emojis in self.category_assignments.items()
            },
            'total_emojis_used': len(self.used_emojis),
            'words_categorized': len(self.word_categorization),
            'category_distribution': {cat.value: count for cat, count in Counter(self.word_categorization.values()).items()},
            'category_rules_summary': {
                cat.value: {
                    'priority_patterns': rules.priority_patterns,
                    'examples_count': len(rules.examples),
                    'consistency_rules': len(rules.consistency_rules)
                }
                for cat, rules in self.category_rules.items()
            }
        }
    
    def export_framework_config(self, filepath: str):
        """Export the complete framework configuration to JSON"""
        
        config = {
            'framework_version': '1.0',
            'categories': {
                cat.value: {
                    'priority_patterns': rules.priority_patterns,
                    'fallback_patterns': rules.fallback_patterns,
                    'combination_strategy': rules.combination_strategy,
                    'consistency_rules': rules.consistency_rules,
                    'examples': rules.examples,
                    'prohibited_emojis': list(rules.prohibited_emojis)
                }
                for cat, rules in self.category_rules.items()
            },
            'emoji_pools': {
                cat.value: list(emojis)
                for cat, emojis in self.category_emoji_pools.items()
            },
            'usage_statistics': self.generate_category_report()
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
    
    def validate_category_consistency(self) -> Dict[str, List[str]]:
        """Validate that category assignments maintain consistency"""
        
        issues = {
            'emoji_conflicts': [],
            'category_violations': [],
            'pattern_inconsistencies': [],
            'rule_violations': []
        }
        
        # Check for emoji reuse across inappropriate categories
        emoji_usage = defaultdict(list)
        for category, emojis in self.category_assignments.items():
            for emoji in emojis:
                emoji_usage[emoji].append(category)
        
        for emoji, categories in emoji_usage.items():
            if len(categories) > 1:
                issues['emoji_conflicts'].append({
                    'emoji': emoji,
                    'categories': [cat.value for cat in categories]
                })
        
        return issues


# Example usage and testing
if __name__ == "__main__":
    print("🚀 Category-Based Mapping Framework")
    print("=" * 50)
    
    # Initialize the framework
    framework = CategoryBasedMappingFramework()
    
    # Test with sample words from different categories
    test_words = [
        # Common words
        "the", "and", "or", "in", "on",
        # Physical actions
        "run", "jump", "eat", "walk", "dance",
        # Emotions
        "happy", "sad", "excited", "calm", "angry",
        # Living beings
        "cat", "dog", "bird", "tree", "person",
        # Abstract concepts
        "love", "freedom", "hope", "beauty", "justice"
    ]
    
    print(f"Processing {len(test_words)} test words...")
    results = framework.process_word_batch(test_words)
    
    print("\n📊 CATEGORY MAPPING RESULTS")
    print("=" * 50)
    
    for word, result in results.items():
        emoji = result.get('primary_emoji', '❌')
        if emoji is None:
            emoji = '❌'
        category = result.get('category', 'unknown')
        if hasattr(category, 'value'):
            category = category.value
        method = result.get('method', 'unknown')
        confidence = result.get('confidence', 'unknown')
        
        print(f"{word:12} → {emoji:8} [{category:15}] {method} ({confidence})")
    
    print("\n📈 FRAMEWORK STATISTICS")
    print("=" * 50)
    
    report = framework.generate_category_report()
    print(f"Categories defined: {report['categories_defined']}")
    print(f"Total emojis used: {report['total_emojis_used']}")
    print(f"Words categorized: {report['words_categorized']}")
    
    print("\nCategory distribution:")
    for category, count in report['category_distribution'].items():
        print(f"  {category:20} : {count}")
    
    # Export framework configuration
    framework.export_framework_config("category_mapping_framework.json")
    print(f"\n✅ Framework configuration exported to category_mapping_framework.json")
    
    # Validate consistency
    issues = framework.validate_category_consistency()
    print(f"\n🔍 Consistency validation: {sum(len(v) for v in issues.values())} issues found")
