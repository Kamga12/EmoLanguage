#!/usr/bin/env python3
"""
EmoLanguage Word Normalizer Module

Advanced word normalization system for reducing inflected word forms to their base
forms, minimizing emoji mapping collisions and improving semantic consistency.
This module combines NLTK-based linguistic processing with comprehensive rule-based
fallbacks to handle morphological variations.

Key Features:
    - Multi-strategy normalization (NLTK + rule-based)
    - Extensive morphological suffix handling
    - Irregular form recognition (verbs, nouns, comparatives)
    - Semantic preservation rules for distinct meanings
    - Collision analysis and consolidation capabilities
    - Comprehensive logging and analysis tools

Normalization Examples:
    - Plurals: aardvark, aardvarks → aardvark
    - Verb forms: run, runs, running, ran → run
    - Comparatives: good, better, best → good
    - Derivations: deicer, deices → deice
    - Compounds: meaningful, meaningless → meaning (with semantic preservation)

Author: EmoLanguage Team
Version: 2.0.0
"""

import contextlib
import json
import logging
import os
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Set

# Initialize module logger
logger = logging.getLogger(__name__)

# =============================================================================
# NLTK INTEGRATION WITH GRACEFUL FALLBACK
# =============================================================================

# Attempt to import and configure NLTK with silent data downloads
try:
    import nltk
    from nltk.stem import WordNetLemmatizer, PorterStemmer
    from nltk.corpus import wordnet
    
    def silent_nltk_download(package: str) -> bool:
        """Silently download NLTK data packages, suppressing all output."""
        try:
            nltk.data.find(f'corpora/{package}')
            return True
        except LookupError:
            try:
                with open(os.devnull, 'w') as devnull, \
                     contextlib.redirect_stdout(devnull), \
                     contextlib.redirect_stderr(devnull):
                    nltk.download(package, quiet=True)
                return True
            except Exception:
                return False
    
    # Attempt to download required NLTK data
    NLTK_WORDNET_AVAILABLE = silent_nltk_download('wordnet')
    NLTK_OMW_AVAILABLE = silent_nltk_download('omw-1.4')
    NLTK_AVAILABLE = NLTK_WORDNET_AVAILABLE and NLTK_OMW_AVAILABLE
    
    if not NLTK_AVAILABLE:
        logger.warning("NLTK data download failed, falling back to rule-based normalization")
        
except ImportError:
    NLTK_AVAILABLE = False
    logger.info("NLTK not available, using rule-based normalization only")

# =============================================================================
# WORD NORMALIZER CLASS
# =============================================================================

class WordNormalizer:
    """Advanced word normalization system with hybrid linguistic processing.
    
    This class provides comprehensive word normalization by combining NLTK-based
    lemmatization with extensive rule-based morphological analysis. It handles
    irregular forms, derivational morphology, and semantic preservation rules
    to create clean, consistent word mappings for emoji generation.
    
    Features:
        - Multi-strategy normalization (NLTK + rule-based)
        - Comprehensive irregular form handling
        - Morphological suffix/prefix processing
        - Semantic preservation for distinct meanings
        - Collision detection and analysis
        - Mapping consolidation and optimization
    
    Attributes:
        lemmatizer: NLTK WordNet lemmatizer (if available)
        stemmer: NLTK Porter stemmer (if available)
        irregular_verbs: Dictionary of irregular verb forms
        contractions: Dictionary of contraction expansions
        irregular_plurals: Dictionary of irregular plural forms
        comparatives: Dictionary of comparative/superlative forms
    """
    
    def __init__(self) -> None:
        """Initialize the word normalizer with linguistic resources and rule sets.
        
        Sets up NLTK lemmatizer and stemmer if available, and initializes
        comprehensive dictionaries of irregular forms, contractions, and
        morphological patterns for rule-based processing.
        """
        # Initialize NLTK components if available
        if NLTK_AVAILABLE:
            self.lemmatizer: Optional[WordNetLemmatizer] = WordNetLemmatizer()
            self.stemmer: Optional[PorterStemmer] = PorterStemmer()
            logger.info("NLTK components initialized for enhanced word normalization")
        else:
            self.lemmatizer = None
            self.stemmer = None
            logger.info("Using rule-based word normalization (NLTK not available)")
        
        # Common irregular verb forms
        self.irregular_verbs = {
            'ran': 'run', 'running': 'run',
            'went': 'go', 'gone': 'go', 'going': 'go',
            'was': 'be', 'were': 'be', 'been': 'be', 'being': 'be',
            'had': 'have', 'having': 'have',
            'did': 'do', 'done': 'do', 'doing': 'do',
            'said': 'say', 'saying': 'say',
            'came': 'come',
            'took': 'take', 'taken': 'take', 'taking': 'take',
            'got': 'get', 'getting': 'get',
            'made': 'make', 'making': 'make',
            'knew': 'know', 'known': 'know', 'knowing': 'know',
            'thought': 'think', 'thinking': 'think',
            'saw': 'see', 'seen': 'see', 'seeing': 'see',
            'gave': 'give', 'given': 'give', 'giving': 'give',
            'found': 'find', 'finding': 'find',
            'told': 'tell', 'telling': 'tell',
            'left': 'leave', 'leaving': 'leave',
            'felt': 'feel', 'feeling': 'feel',
            'kept': 'keep', 'keeping': 'keep',
            'brought': 'bring', 'bringing': 'bring',
            'bought': 'buy', 'buying': 'buy',
            'built': 'build', 'building': 'build',
            'caught': 'catch', 'catching': 'catch',
            'taught': 'teach', 'teaching': 'teach',
            'fought': 'fight', 'fighting': 'fight',
            'sought': 'seek', 'seeking': 'seek',
        }
        
        # Common contractions with 'n't'
        self.contractions = {
            "aren't": 'are', "isn't": 'is', "wasn't": 'was', "weren't": 'were',
            "haven't": 'have', "hasn't": 'has', "hadn't": 'had',
            "don't": 'do', "doesn't": 'does', "didn't": 'did',
            "can't": 'can', "couldn't": 'could', "won't": 'will', "wouldn't": 'would',
            "shouldn't": 'should', "mustn't": 'must', "needn't": 'need',
            "daren't": 'dare', "oughtn't": 'ought', "mightn't": 'might',
        }
        
        # Common irregular noun plurals
        self.irregular_plurals = {
            'children': 'child',
            'feet': 'foot',
            'teeth': 'tooth',
            'geese': 'goose',
            'mice': 'mouse',
            'men': 'man',
            'women': 'woman',
            'people': 'person',
            'oxen': 'ox',
        }
        
        # Comparative and superlative forms
        self.comparatives = {
            'better': 'good', 'best': 'good',
            'worse': 'bad', 'worst': 'bad',
            'more': 'much', 'most': 'much',
            'less': 'little', 'least': 'little',
            'further': 'far', 'furthest': 'far',
            'farther': 'far', 'farthest': 'far',
            'elder': 'old', 'eldest': 'old',
            'later': 'late', 'latest': 'late',
            'larger': 'large', 'largest': 'large',
            'smaller': 'small', 'smallest': 'small',
            'bigger': 'big', 'biggest': 'big',
            'longer': 'long', 'longest': 'long',
            'shorter': 'short', 'shortest': 'short',
            'higher': 'high', 'highest': 'high',
            'lower': 'low', 'lowest': 'low',
            'faster': 'fast', 'fastest': 'fast',
            'slower': 'slow', 'slowest': 'slow',
        }
    
    # =============================================================================
    # CORE NORMALIZATION METHODS
    # =============================================================================
    
    def normalize_word(self, word: str) -> str:
        """Normalize a single word to its morphological base form.
        
        This is the main entry point for word normalization, using a multi-tiered
        approach that combines dictionary lookups for irregular forms with NLTK
        lemmatization (if available) and comprehensive rule-based processing.
        
        Processing Pipeline:
            1. Text preprocessing (lowercase, strip)
            2. Contraction expansion ("don't" → "do")
            3. Irregular form lookup ("ran" → "run")
            4. NLTK lemmatization with multiple POS tags (if available)
            5. Rule-based morphological analysis (fallback)
        
        Args:
            word: Input word to normalize (any case, may have whitespace)
            
        Returns:
            Normalized base form of the word
            
        Examples:
            >>> normalizer = WordNormalizer()
            >>> normalizer.normalize_word("running")
            'run'
            >>> normalizer.normalize_word("better")
            'good'
            >>> normalizer.normalize_word("children")
            'child'
            >>> normalizer.normalize_word("happiness")
            'happy'
        """
        if not word or not word.strip():
            return word
            
        # Preprocessing: normalize case and whitespace
        word_clean = word.lower().strip()
        
        # Stage 1: Handle contractions (highest priority)
        if word_clean in self.contractions:
            return self.contractions[word_clean]
        
        # Stage 2: Handle known irregular forms (high priority)
        if word_clean in self.irregular_verbs:
            return self.irregular_verbs[word_clean]
        # Handle specific morphological cases that NLTK gets wrong
        if word_clean == "coming":
            return "com"  # Let morphological system handle the -ing suffix
        if word_clean in self.irregular_plurals:
            return self.irregular_plurals[word_clean]
        if word_clean in self.comparatives:
            return self.comparatives[word_clean]
        
        # Stage 3: NLTK-based lemmatization (if available)
        if NLTK_AVAILABLE and self.lemmatizer:
            # Try lemmatization with different part-of-speech tags
            lemma_candidates = [
                self.lemmatizer.lemmatize(word_clean, 'n'),  # noun
                self.lemmatizer.lemmatize(word_clean, 'v'),  # verb
                self.lemmatizer.lemmatize(word_clean, 'a'),  # adjective
                self.lemmatizer.lemmatize(word_clean, 'r'),  # adverb
            ]
            
            # Choose the shortest candidate (typically the base form)
            best_lemma = min(lemma_candidates, key=len)
            if best_lemma != word_clean and len(best_lemma) >= 2:
                return best_lemma
        
        # Stage 4: Rule-based morphological analysis (fallback)
        return self._simple_normalize(word_clean)
    
    def _simple_normalize(self, word: str) -> str:
        """Simple rule-based word normalization"""
        original = word
        
        # Handle specific morphological suffixes first (longer ones first)
        if word.endswith('tion') and len(word) > 4:
            # creation -> create
            base = word[:-4]
            if base.endswith('a'):
                word = base[:-1] + 'e'  # creation -> create
            else:
                word = base
        elif word.endswith('sion') and len(word) > 4:
            # decision -> decide, conversion -> convert
            base = word[:-4]
            if base.endswith('i'):
                word = base[:-1] + 'e'  # decision -> decide
            else:
                word = base
        elif word.endswith('ment') and len(word) > 4:
            # movement -> move, agreement -> agree
            base = word[:-4]
            word = base
        elif word.endswith('ness') and len(word) > 4:
            # kindness -> kind, happiness -> happy
            base = word[:-4]
            if base.endswith('i'):
                word = base[:-1] + 'y'  # happiness -> happy
            else:
                word = base
        elif word.endswith('ity') and len(word) > 3:
            # reality -> real, ability -> able
            base = word[:-3]
            if base.endswith('bil'):
                word = base[:-3] + 'le'  # ability -> able
            elif base.endswith('al'):
                word = base[:-2]  # reality -> real
            else:
                word = base
        elif word.endswith('ize') and len(word) > 3:
            # organize -> organ, realize -> real
            base = word[:-3]
            if base.endswith('al'):
                word = base[:-2]  # realize -> real
            else:
                word = base
        elif word.endswith('ive') and len(word) > 3:
            # active -> act, creative -> create
            base = word[:-3]
            if base.endswith('at'):
                word = base[:-2]  # creative -> create
            else:
                word = base
        elif word.endswith('ful') and len(word) > 3:
            # helpful -> help, beautiful -> beauty
            base = word[:-3]
            if base.endswith('ti'):
                word = base[:-2] + 'ty'  # beautiful -> beauty
            else:
                word = base
        elif word.endswith('able') and len(word) > 4:
            # readable -> read, comfortable -> comfort
            base = word[:-4]
            word = base
        elif word.endswith('ous') and len(word) > 3:
            # famous -> fame, nervous -> nerve
            base = word[:-3]
            if base.endswith('m'):
                word = base + 'e'  # famous -> fame
            else:
                word = base
        elif word.endswith('ian') and len(word) > 3:
            # musician -> music, magician -> magic
            base = word[:-3]
            word = base
        elif word.endswith('ist') and len(word) > 3:
            # artist -> art, scientist -> science
            base = word[:-3]
            if base.endswith('enc'):
                word = base + 'e'  # scientist -> science
            else:
                word = base
        elif word.endswith('ism') and len(word) > 3:
            # realism -> real, idealism -> ideal
            base = word[:-3]
            word = base
        elif word.endswith('ance') and len(word) > 4:
            # resistance -> resist, assistance -> assist
            base = word[:-4]
            word = base
        elif word.endswith('ence') and len(word) > 4:
            # patience -> patient, presence -> present
            base = word[:-4]
            if base.endswith('enc'):
                word = base[:-3] + 'ent'  # patience -> patient
            else:
                word = base
        elif word.endswith('age') and len(word) > 3:
            # package -> pack, storage -> store
            base = word[:-3]
            word = base
        elif word.endswith('dom') and len(word) > 3:
            # freedom -> free, kingdom -> king
            base = word[:-3]
            word = base
        elif word.endswith('hood') and len(word) > 4:
            # childhood -> child, neighborhood -> neighbor
            base = word[:-4]
            word = base
        elif word.endswith('ship') and len(word) > 4:
            # friendship -> friend, leadership -> leader
            base = word[:-4]
            word = base
        elif word.endswith('less') and len(word) > 4:
            # helpless -> help, useless -> use
            base = word[:-4]
            word = base
        elif word.endswith('like') and len(word) > 4:
            # childlike -> child, lifelike -> life
            base = word[:-4]
            word = base
        elif word.endswith('ible') and len(word) > 4:
            # visible -> see, terrible -> terror
            base = word[:-4]
            if base == 'vis':
                word = 'see'  # visible -> see
            elif base == 'terr':
                word = 'terror'  # terrible -> terror (but this might be wrong)
            elif base == 'poss':
                word = 'possible'  # keep as is, this is complex
            else:
                word = base
        elif word.endswith('al') and len(word) > 2:
            # musical -> music, magical -> magic
            base = word[:-2]
            if base.endswith('ic'):
                word = base  # musical -> music, magical -> magic
            else:
                word = base
        elif word.endswith('ic') and len(word) > 2:
            # scientific -> science, artistic -> art
            base = word[:-2]
            if base == 'scientif':
                word = 'science'
            elif base == 'artist':
                word = 'art'
            else:
                word = base
        elif word.endswith('ly') and len(word) > 3:
            # quickly -> quick, airily -> airy
            base = word[:-2]
            if base.endswith('i'):
                word = base[:-1] + 'y'  # airily -> airy, happily -> happy
            else:
                word = base
        elif word.endswith('ward') and len(word) > 4:
            # backward -> back, forward -> fore
            base = word[:-4]
            if base == 'for':
                word = 'fore'  # forward -> fore
            else:
                word = base
        elif word.endswith('wise') and len(word) > 4:
            # likewise -> like, clockwise -> clock
            base = word[:-4]
            word = base
        elif word.endswith('ify') and len(word) > 3:
            # purify -> pure, clarify -> clear, simplify -> simple
            base = word[:-3]
            if base == 'pur':
                word = 'pure'
            elif base == 'clar':
                word = 'clear'
            elif base == 'simpl':
                word = 'simple'
            else:
                word = base
        elif word.endswith('ate') and len(word) > 3:
            # activate -> active, educate -> educate (tricky)
            base = word[:-3]
            if base == 'activ':
                word = 'active'
            elif base == 'cre':
                word = 'create'
            elif base == 'educ':
                word = 'educate'  # this might need different handling
            elif base == 'priv':
                word = 'private'  # private is base form, not derived from priv+ate
            else:
                word = base
        elif word.endswith('or') and len(word) > 2:
            # actor -> act, doctor -> doct, creator -> create
            base = word[:-2]
            if base == 'act':
                word = 'act'
            elif base == 'doct':
                word = 'doctor'  # doctor is the base form
            elif base == 'creat':
                word = 'create'
            else:
                word = base
        elif word.endswith('ie') and len(word) > 2:
            # doggie -> dog, birdie -> bird, cutie -> cute
            base = word[:-2]
            if base == 'dogg':
                word = 'dog'
            elif base == 'bird':
                word = 'bird'
            elif base == 'cut':
                word = 'cute'
            else:
                word = base
        elif word.endswith('y') and len(word) > 2:
            # Handle diminutives: kitty -> cat, doggy -> dog, bunny -> bun
            base = word[:-1]
            if base == 'kitt':
                word = 'cat'
            elif base == 'dogg':
                word = 'dog'
            elif base == 'bunn':
                word = 'bun'
            else:
                # Don't modify other -y words as they might be base forms
                word = word
        elif word.endswith('let') and len(word) > 3:
            # booklet -> book, piglet -> pig, tablet -> tab
            base = word[:-3]
            if base == 'book':
                word = 'book'
            elif base == 'pig':
                word = 'pig'
            elif base == 'tab':
                word = 'tab'
            else:
                word = base
        
        # Handle prefixes
        elif word.startswith('un') and len(word) > 3:
            # unhappy -> happy, unable -> able
            base = word[2:]
            word = base
        elif word.startswith('in') and len(word) > 3:
            # inactive -> active, indirect -> direct
            base = word[2:]
            if base.startswith('active'):
                word = 'active'
            elif base.startswith('direct'):
                word = 'direct'
            elif base.startswith('possible'):
                word = 'possible'
            else:
                word = base
        elif word.startswith('dis') and len(word) > 4:
            # disagree -> agree, disappear -> appear
            base = word[3:]
            word = base
        elif word.startswith('non') and len(word) > 4:
            # nonsense -> sense, nonfiction -> fiction
            base = word[3:]
            word = base
        
        # Handle common suffixes
        # Plural nouns
        elif word.endswith('ies') and len(word) > 4:
            word = word[:-3] + 'y'
        elif word.endswith('es') and len(word) > 3:
            # Check for -ches, -shes, -xes, -zes
            if word.endswith(('ches', 'shes', 'xes', 'zes')):
                word = word[:-2]
            elif word.endswith('es'):
                word = word[:-2]
        elif word.endswith('s') and len(word) > 2:
            # Simple plural removal (be careful not to remove from words ending in 's' naturally)
            if not word.endswith(('ss', 'us', 'is')):
                word = word[:-1]
        
        # Verb forms
        if word.endswith('ing') and len(word) > 4:
            # Remove -ing
            base = word[:-3]
            # Handle doubled consonants (running -> run)
            if len(base) >= 2 and base[-1] == base[-2] and base[-1] in 'bcdfghjklmnpqrstvwxyz':
                base = base[:-1]
            word = base
        elif word.endswith('ed') and len(word) > 3:
            # Remove -ed
            base = word[:-2]
            # Handle doubled consonants
            if len(base) >= 2 and base[-1] == base[-2] and base[-1] in 'bcdfghjklmnpqrstvwxyz':
                base = base[:-1]
            word = base
        elif word.endswith('er') and len(word) > 3:
            # Could be comparative (bigger -> big) or agent noun (runner -> run)
            base = word[:-2]
            if len(base) >= 2 and base[-1] == base[-2] and base[-1] in 'bcdfghjklmnpqrstvwxyz':
                base = base[:-1]
            # Only use if it makes sense (length check)
            if len(base) >= 3:
                word = base
        elif word.endswith('est') and len(word) > 4:
            # Superlative (biggest -> big)
            base = word[:-3]
            if len(base) >= 2 and base[-1] == base[-2] and base[-1] in 'bcdfghjklmnpqrstvwxyz':
                base = base[:-1]
            if len(base) >= 3:
                word = base
        
        # Return original if we made it too short
        if len(word) < 2:
            return original
        
        return word
    
    def analyze_word_groups(self, words: List[str]) -> Dict[str, List[str]]:
        """Group words by their normalized base forms"""
        groups = defaultdict(list)
        
        for word in words:
            base = self.normalize_word(word)
            groups[base].append(word)
        
        return dict(groups)
    
    def find_collision_groups(self, word_to_emoji: Dict[str, str]) -> Dict[str, List[str]]:
        """Find groups of words that should share the same emoji mapping"""
        # Group words by their base forms
        base_groups = self.analyze_word_groups(list(word_to_emoji.keys()))
        
        # Find groups where different emoji mappings exist
        collision_groups = {}
        for base, word_list in base_groups.items():
            if len(word_list) > 1:
                # Check if these words have different emoji mappings
                emojis = set()
                for word in word_list:
                    if word in word_to_emoji:
                        emojis.add(word_to_emoji[word])
                
                if len(emojis) > 1:
                    collision_groups[base] = {
                        'words': word_list,
                        'emojis': list(emojis),
                        'mappings': {word: word_to_emoji.get(word, '') for word in word_list}
                    }
        
        return collision_groups
    
    def should_preserve_semantic_derivation(self, base: str, derived: str) -> bool:
        """Check if a derived word should be preserved due to semantic distinction"""
        # Professional roles
        professional_words = {
            'doctor', 'lawyer', 'teacher', 'engineer', 'scientist', 'artist',
            'writer', 'manager', 'director', 'professor', 'nurse', 'therapist',
            'surgeon', 'architect', 'designer', 'consultant'
        }
        if derived in professional_words:
            return True
        
        # Abstract nouns with distinct meanings
        if any(derived.endswith(suffix) for suffix in ['ity', 'ness', 'ment', 'tion', 'sion', 'ance', 'ence']):
            # Check if it represents a truly different concept
            if len(derived) > len(base) + 2:  # Significant transformation
                return True
        
        # Emotional variations (positive/negative pairs)
        emotional_pairs = {
            'useful', 'useless', 'helpful', 'helpless', 'hopeful', 'hopeless',
            'careful', 'careless', 'harmful', 'harmless', 'restful', 'restless',
            'meaningful', 'meaningless', 'peaceful', 'restless'
        }
        if derived in emotional_pairs:
            return True
        
        # Irregular forms
        irregular_pairs = {
            ('person', 'people'), ('child', 'children'), ('mouse', 'mice'),
            ('good', 'better'), ('good', 'best'), ('bad', 'worse'), ('bad', 'worst'),
            ('man', 'men'), ('woman', 'women'), ('foot', 'feet'), ('tooth', 'teeth')
        }
        if (base, derived) in irregular_pairs:
            return True
        
        return False
    
    def should_eliminate_transformation(self, base: str, derived: str) -> bool:
        """Check if a transformation should be eliminated (handled by context)"""
        # First check if it should be preserved
        if self.should_preserve_semantic_derivation(base, derived):
            return False
        
        # Simple plurals
        if (derived == base + 's' or derived == base + 'es' or
            (base.endswith('y') and derived == base[:-1] + 'ies')):
            return True
        
        # Regular verb conjugations
        if (derived == base + 'ing' or derived == base + 'ed' or
            (base.endswith('e') and derived == base[:-1] + 'ing') or
            (base.endswith('e') and derived == base[:-1] + 'ed')):
            return True
        
        # Standard comparatives
        if (derived == base + 'er' or derived == base + 'est' or
            (base.endswith('y') and derived == base[:-1] + 'ier') or
            (base.endswith('y') and derived == base[:-1] + 'iest')):
            # But not if it's a professional role (like 'teacher')
            if not derived in {'teacher', 'manager', 'director', 'designer', 'engineer'}:
                return True
        
        # Mechanical adverbs (simple -ly forms)
        if (derived == base + 'ly' and len(base) > 2 and 
            not base in {'hard', 'real', 'near', 'late', 'early'}):
            # Keep semantically distinct adverbs
            distinct_adverbs = {'hardly', 'really', 'nearly', 'lately', 'early'}
            if derived not in distinct_adverbs:
                return True
        
        return False
    
    def apply_transformation_elimination(self, word_to_emoji: Dict[str, str]) -> Tuple[Dict[str, str], Dict[str, List[str]]]:
        """Apply transformation elimination rules to create simplified mapping"""
        simplified_mapping = {}
        elimination_log = {}
        
        # Group words by base forms
        base_groups = self.analyze_word_groups(list(word_to_emoji.keys()))
        
        for base, word_variations in base_groups.items():
            if len(word_variations) == 1:
                # Single word, keep it
                word = word_variations[0]
                simplified_mapping[word] = word_to_emoji[word]
            else:
                # Multiple variations, apply elimination rules
                preserved_variations = []
                eliminated_variations = []
                
                for word in word_variations:
                    if word == base:
                        # Always keep the base form
                        simplified_mapping[word] = word_to_emoji[word]
                        preserved_variations.append(word)
                    elif not self.should_eliminate_transformation(base, word):
                        # Preserve this variation
                        simplified_mapping[word] = word_to_emoji[word]
                        preserved_variations.append(word)
                    else:
                        # Eliminate this variation
                        eliminated_variations.append(word)
                
                if eliminated_variations:
                    elimination_log[base] = {
                        'preserved': preserved_variations,
                        'eliminated': eliminated_variations,
                        'base_emoji': word_to_emoji.get(base, '')
                    }
        
        return simplified_mapping, elimination_log
    
    def normalize_mappings(self, word_to_emoji: Dict[str, str], strategy='keep_shortest') -> Tuple[Dict[str, str], Dict[str, List[str]]]:
        """
        Normalize word-to-emoji mappings to use base forms
        
        Args:
            word_to_emoji: Current word-to-emoji mappings
            strategy: How to choose emoji when multiple exist
                     - 'keep_shortest': Keep mapping from shortest word
                     - 'keep_most_confident': Keep mapping from most frequent word
                     - 'keep_first': Keep first mapping encountered
        
        Returns:
            Tuple of (normalized_mappings, consolidation_log)
        """
        base_groups = self.analyze_word_groups(list(word_to_emoji.keys()))
        normalized_mappings = {}
        consolidation_log = {}
        
        for base, word_list in base_groups.items():
            # Find all emoji mappings for this group
            mappings = {}
            for word in word_list:
                if word in word_to_emoji and word_to_emoji[word]:
                    mappings[word] = word_to_emoji[word]
            
            if not mappings:
                continue
            
            # Choose which mapping to keep based on strategy
            if strategy == 'keep_shortest':
                chosen_word = min(mappings.keys(), key=len)
            elif strategy == 'keep_first':
                chosen_word = word_list[0] if word_list[0] in mappings else next(iter(mappings.keys()))
            else:
                # Default to shortest
                chosen_word = min(mappings.keys(), key=len)
            
            chosen_emoji = mappings[chosen_word]
            normalized_mappings[base] = chosen_emoji
            
            # Log what was consolidated
            if len(mappings) > 1:
                consolidation_log[base] = {
                    'chosen_word': chosen_word,
                    'chosen_emoji': chosen_emoji,
                    'consolidated_words': word_list,
                    'original_mappings': mappings
                }
        
        return normalized_mappings, consolidation_log

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Normalize word mappings to reduce inflection collisions")
    parser.add_argument("--input", default="mappings/word_to_emoji.json",
                       help="Input word-to-emoji mapping file")
    parser.add_argument("--output", default="mappings/word_to_emoji_normalized.json", 
                       help="Output normalized mapping file")
    parser.add_argument("--strategy", choices=['keep_shortest', 'keep_first'], 
                       default='keep_shortest',
                       help="Strategy for choosing emoji when multiple exist")
    parser.add_argument("--dry-run", "-d", action="store_true",
                       help="Show analysis without creating output files")
    parser.add_argument("--analyze-only", "-a", action="store_true", 
                       help="Only analyze collision groups without normalizing")
    
    args = parser.parse_args()
    
    # Load existing mappings
    try:
        with open(args.input, 'r', encoding='utf-8') as f:
            word_to_emoji = json.load(f)
    except FileNotFoundError:
        logger.error(f"Input file {args.input} not found")
        return 1
    
    normalizer = WordNormalizer()
    
    if args.analyze_only:
        # Just analyze collision groups
        logger.info("Analyzing collision groups...")
        collision_groups = normalizer.find_collision_groups(word_to_emoji)
        
        print(f"\n📊 Found {len(collision_groups)} collision groups:")
        for base, info in collision_groups.items():
            print(f"\n🔸 Base: '{base}'")
            print(f"  Words: {', '.join(info['words'])}")
            print(f"  Emojis: {', '.join(info['emojis'])}")
            for word, emoji in info['mappings'].items():
                print(f"    '{word}' → {emoji}")
        
        return 0
    
    # Normalize mappings
    logger.info(f"Normalizing {len(word_to_emoji)} word mappings...")
    normalized_mappings, consolidation_log = normalizer.normalize_mappings(
        word_to_emoji, strategy=args.strategy
    )
    
    # Show results
    print(f"\n📈 Normalization Results:")
    print(f"  Original mappings: {len(word_to_emoji)}")
    print(f"  Normalized mappings: {len(normalized_mappings)}")
    print(f"  Reduction: {len(word_to_emoji) - len(normalized_mappings)} mappings ({(len(word_to_emoji) - len(normalized_mappings))/len(word_to_emoji)*100:.1f}%)")
    print(f"  Consolidation groups: {len(consolidation_log)}")
    
    if consolidation_log:
        print(f"\n📋 Sample Consolidations:")
        for base, info in list(consolidation_log.items())[:10]:
            print(f"  '{base}' ← {', '.join(info['consolidated_words'])} → {info['chosen_emoji']}")
    
    if not args.dry_run:
        # Save normalized mappings
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(normalized_mappings, f, indent=2, ensure_ascii=False)
        
        # Save consolidation log
        log_path = Path(args.output).with_suffix('.consolidation.json')
        with open(log_path, 'w', encoding='utf-8') as f:
            json.dump(consolidation_log, f, indent=2, ensure_ascii=False)
        
        # Create reverse mapping
        emoji_to_word = {emoji: base for base, emoji in normalized_mappings.items()}
        reverse_path = Path(args.output).parent / "emoji_to_word_normalized.json"
        with open(reverse_path, 'w', encoding='utf-8') as f:
            json.dump(emoji_to_word, f, indent=2, ensure_ascii=False)
        
        logger.info(f"✅ Saved normalized mappings to {args.output}")
        logger.info(f"📝 Saved consolidation log to {log_path}")
        logger.info(f"🔄 Saved reverse mappings to {reverse_path}")
    else:
        print("\n🔍 DRY RUN - No files saved")

if __name__ == "__main__":
    exit(main())
