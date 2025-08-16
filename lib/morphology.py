"""Morphological transformation utilities for the EmoLanguage system.

This module provides shared utilities for analyzing and reconstructing
morphological transformations used by both the encoder and decoder modules.
"""

from typing import Dict, Set

from .config import (
    MORPHOLOGICAL_MODIFIERS,
    IRREGULAR_PLURALS,
    IRREGULAR_PLURALS_REVERSE,
    IRREGULAR_COMPARATIVES,
    IRREGULAR_SUPERLATIVES,
    IRREGULAR_VERB_3RD_PERSON,
    IRREGULAR_VERB_3RD_FORMS,
    IRREGULAR_CONTRACTIONS,
    COMMON_VERBS,
    AGENT_NOUNS_ER,
    AGENT_NOUNS_OR
)


def is_likely_verb(word: str) -> bool:
    """Check if a word is likely a verb (simple heuristic).
    
    Args:
        word: Word to check
        
    Returns:
        True if word appears to be a verb
    """
    return word in COMMON_VERBS


def is_agent_noun_er(word: str) -> bool:
    """Check if a word ending in -er is an agent noun (like 'teacher').
    
    Args:
        word: Word to check
        
    Returns:
        True if word appears to be an agent noun ending in -er
    """
    return word in AGENT_NOUNS_ER


def is_agent_noun_or(word: str) -> bool:
    """Check if a word ending in -or is an agent noun (like 'actor').
    
    Args:
        word: Word to check
        
    Returns:
        True if word appears to be an agent noun ending in -or
    """
    return word in AGENT_NOUNS_OR


def make_plural_s(word: str) -> str:
    """Add simple 's' plural."""
    return word + 's'


def make_plural_es(word: str) -> str:
    """Add 'es' plural."""
    return word + 'es'


def make_plural_ies(word: str) -> str:
    """Convert 'y' to 'ies' plural."""
    if word.endswith('y'):
        return word[:-1] + 'ies'
    return word + 'ies'


def make_irregular_plural(word: str) -> str:
    """Handle irregular plurals."""
    return IRREGULAR_PLURALS.get(word, word + 's')


def make_verb_s(word: str) -> str:
    """Add 's' for 3rd person singular verb."""
    # If the word is already in irregular 3rd person form, return as-is
    if word in IRREGULAR_VERB_3RD_FORMS:
        return word
    
    # Handle irregular verb base forms that need special 3rd person forms
    if word in IRREGULAR_VERB_3RD_PERSON:
        return IRREGULAR_VERB_3RD_PERSON[word]
    
    # Apply regular verb_s transformation rules
    if word.endswith(('s', 'sh', 'ch', 'x', 'z')):
        return word + 'es'
    elif word.endswith('y') and len(word) > 1 and word[-2] not in 'aeiou':
        return word[:-1] + 'ies'
    else:
        return word + 's'


def make_verb_ed(word: str) -> str:
    """Add 'ed' for past tense."""
    if word.endswith('e'):
        return word + 'd'
    elif word.endswith('y') and len(word) > 1 and word[-2] not in 'aeiou':
        return word[:-1] + 'ied'
    else:
        return word + 'ed'


def make_verb_ing(word: str) -> str:
    """Add 'ing' for progressive form."""
    if word.endswith('e') and len(word) > 2:
        return word[:-1] + 'ing'
    else:
        return word + 'ing'


def make_comparative(word: str) -> str:
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


def make_superlative(word: str) -> str:
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


def make_adverb_ly(word: str) -> str:
    """Make adverb with 'ly' suffix."""
    if word.endswith('y'):
        return word[:-1] + 'ily'
    else:
        return word + 'ly'


def make_past_participle(word: str) -> str:
    """Make past participle form from base word."""
    # Handle irregular past participles (base -> past participle)
    irregular_past_participles_forward = {
        'buy': 'bought', 'bring': 'brought', 'catch': 'caught',
        'teach': 'taught', 'think': 'thought', 'fight': 'fought',
        'seek': 'sought', 'find': 'found', 'bind': 'bound',
        'wind': 'wound', 'hang': 'hung', 'sing': 'sung',
        'ring': 'rung', 'swing': 'swung', 'cling': 'clung',
        'fling': 'flung', 'sting': 'stung', 'wring': 'wrung',
        'sink': 'sunk', 'drink': 'drunk', 'shrink': 'shrunk',
        'begin': 'begun', 'run': 'run', 'come': 'come',  # Same form
        'do': 'done', 'go': 'gone', 'see': 'seen',
        'be': 'been', 'know': 'known', 'grow': 'grown',
        'show': 'shown', 'throw': 'thrown', 'blow': 'blown',
        'fly': 'flown', 'draw': 'drawn', 'withdraw': 'withdrawn',
        'hide': 'hidden', 'take': 'taken', 'break': 'broken',
        'speak': 'spoken', 'choose': 'chosen', 'freeze': 'frozen',
        'weave': 'woven', 'wake': 'waken', 'shake': 'shaken'
    }
    
    if word in irregular_past_participles_forward:
        return irregular_past_participles_forward[word]
    
    # Regular past participle rules (same as past tense for regular verbs)
    if word.endswith('e'):
        return word + 'd'
    elif word.endswith('y') and len(word) > 1 and word[-2] not in 'aeiou':
        return word[:-1] + 'ied'
    else:
        return word + 'ed'


def make_plural_simple(word: str) -> str:
    """Convert a word to its plural form using regular rules."""
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


def apply_morphological_transformations(base_word: str, transformations: Dict[str, str]) -> str:
    """Apply multiple morphological transformations to reconstruct original word form.
    
    Args:
        base_word: Base/normalized word form
        transformations: Dictionary of transformations to apply
        
    Returns:
        Reconstructed word with applied transformations
    """
    if not transformations or not base_word:
        return base_word
    
    word = base_word
    
    # Apply morphological transformations (not capitalization)
    for transformation in transformations:
        if transformation == 'capitalized':
            continue  # Handle capitalization last
        
        if transformation == 'plural_s':
            word = make_plural_s(word)
        elif transformation == 'plural_es':
            word = make_plural_es(word)
        elif transformation == 'plural_ies':
            word = make_plural_ies(word)
        elif transformation == 'irregular_plural':
            word = make_irregular_plural(word)
        elif transformation == 'verb_s':
            word = make_verb_s(word)
        elif transformation == 'verb_ed':
            word = make_verb_ed(word)
        elif transformation == 'verb_ing':
            word = make_verb_ing(word)
        elif transformation == 'comparative':
            word = make_comparative(word)
        elif transformation == 'superlative':
            word = make_superlative(word)
        elif transformation == 'adverb_ly':
            word = make_adverb_ly(word)
        elif transformation == 'past_participle':
            word = make_past_participle(word)
        elif transformation == 'contraction_nt':
            word = word + "n't"
        elif transformation == 'noun_tion':
            word = word + 'tion'
        elif transformation == 'noun_sion':
            word = word + 'sion'
        elif transformation == 'noun_ment':
            word = word + 'ment'
        elif transformation == 'noun_ness':
            word = word + 'ness'
        elif transformation == 'noun_ance':
            word = word + 'ance'
        elif transformation == 'noun_ence':
            word = word + 'ence'
        elif transformation == 'noun_ship':
            word = word + 'ship'
        elif transformation == 'noun_hood':
            word = word + 'hood'
        elif transformation == 'noun_ism':
            word = word + 'ism'
        elif transformation == 'noun_dom':
            word = word + 'dom'
        elif transformation == 'noun_age':
            word = word + 'age'
        elif transformation == 'noun_ity':
            word = word + 'ity'
        elif transformation == 'noun_er':
            word = word + 'er'
        elif transformation == 'noun_or':
            word = word + 'or'
        elif transformation == 'noun_ian':
            word = word + 'ian'
        elif transformation == 'noun_ist':
            word = word + 'ist'
        elif transformation == 'adjective_ible':
            word = word + 'ible'
        elif transformation == 'adjective_able':
            word = word + 'able'
        elif transformation == 'adjective_less':
            word = word + 'less'
        elif transformation == 'adjective_like':
            word = word + 'like'
        elif transformation == 'adjective_ive':
            word = word + 'ive'
        elif transformation == 'adjective_ful':
            word = word + 'ful'
        elif transformation == 'adjective_ous':
            word = word + 'ous'
        elif transformation == 'adjective_al':
            word = word + 'al'
        elif transformation == 'adjective_ic':
            word = word + 'ic'
        elif transformation == 'adverb_ward':
            word = word + 'ward'
        elif transformation == 'adverb_wise':
            word = word + 'wise'
        elif transformation == 'verb_ize':
            word = word + 'ize'
        elif transformation == 'verb_ify':
            word = word + 'ify'
        elif transformation == 'verb_ate':
            word = word + 'ate'
        elif transformation == 'diminutive_let':
            word = word + 'let'
        elif transformation == 'diminutive_ie':
            word = word + 'ie'
        elif transformation == 'diminutive_y':
            word = word + 'y'
        elif transformation == 'prefix_un':
            word = 'un' + word
        elif transformation == 'prefix_in':
            word = 'in' + word
        elif transformation == 'prefix_dis':
            word = 'dis' + word
        elif transformation == 'prefix_non':
            word = 'non' + word
    
    # Apply capitalization last
    if 'capitalized' in transformations:
        word = word.capitalize()
    
    return word


def identify_transformation_type(original: str, base: str) -> str:
    """Identify the type of morphological transformation.
    
    Args:
        original: Original word form
        base: Base/normalized form from word normalizer
        
    Returns:
        Appropriate modifier emoji for the transformation
    """
    # Handle irregular plurals first
    if original in IRREGULAR_PLURALS_REVERSE:
        return MORPHOLOGICAL_MODIFIERS['irregular_plural']
    
    # Handle irregular verb forms (3rd person singular) before generic suffix handling
    irregular_verb_forms = {
        'does': 'do',    # does -> do (3rd person singular)
        'goes': 'go',    # goes -> go (3rd person singular)
        'has': 'have',   # has -> have (3rd person singular)
        'is': 'be',      # is -> be (3rd person singular)
    }
    
    if original in irregular_verb_forms and base == irregular_verb_forms[original]:
        return MORPHOLOGICAL_MODIFIERS['verb_s']
    
    # Handle contractions (negations)
    if original.endswith("n't") and len(original) > 3:
        # Check if normalization removed the contraction
        expected_base = original[:-3]  # Remove "n't"
        if base == expected_base or (expected_base == 'ca' and base == 'can') or (expected_base == 'wo' and base == 'will'):
            return MORPHOLOGICAL_MODIFIERS['contraction_nt']
    
    # Handle prefixes first (negation patterns)
    if original.startswith('un') and len(original) > 3 and base == original[2:]:
        return MORPHOLOGICAL_MODIFIERS['prefix_un']
    elif original.startswith('in') and len(original) > 3 and base == original[2:]:
        return MORPHOLOGICAL_MODIFIERS['prefix_in']
    elif original.startswith('dis') and len(original) > 4 and base == original[3:]:
        return MORPHOLOGICAL_MODIFIERS['prefix_dis']
    elif original.startswith('non') and len(original) > 4 and base == original[3:]:
        return MORPHOLOGICAL_MODIFIERS['prefix_non']
    
    # Handle specific suffix patterns (longer suffixes first to avoid conflicts)
    suffix_patterns = [
        ('tion', 'noun_tion'), ('sion', 'noun_sion'), ('ment', 'noun_ment'), 
        ('ness', 'noun_ness'), ('ance', 'noun_ance'), ('ence', 'noun_ence'),
        ('ship', 'noun_ship'), ('hood', 'noun_hood'), ('ism', 'noun_ism'),
        ('dom', 'noun_dom'), ('age', 'noun_age'), ('ity', 'noun_ity'),
        ('ible', 'adjective_ible'), ('able', 'adjective_able'), ('less', 'adjective_less'),
        ('like', 'adjective_like'), ('ward', 'adverb_ward'), ('wise', 'adverb_wise'),
        ('ize', 'verb_ize'), ('ify', 'verb_ify'), ('ate', 'verb_ate'),
        ('ive', 'adjective_ive'), ('ful', 'adjective_ful'), ('ous', 'adjective_ous'),
        ('ical', 'adjective_ic'), ('ic', 'adjective_ic'), ('al', 'adjective_al'),
        ('let', 'diminutive_let'), ('ie', 'diminutive_ie'), ('ian', 'noun_ian'),
        ('ist', 'noun_ist')
    ]
    
    for suffix, transformation in suffix_patterns:
        if original.endswith(suffix) and len(original) > len(suffix):
            return MORPHOLOGICAL_MODIFIERS[transformation]
    
    # Handle regular morphological patterns
    if len(original) > len(base):
        # Word got shorter during normalization - analyze the suffix
        suffix = original[len(base):]
        
        if suffix == 's':
            # Could be plural noun or 3rd person verb
            if is_likely_verb(base):
                return MORPHOLOGICAL_MODIFIERS['verb_s']
            else:
                return MORPHOLOGICAL_MODIFIERS['plural_s']
        elif suffix == 'es':
            return MORPHOLOGICAL_MODIFIERS['plural_es']
        elif suffix == 'ies' and original.endswith('ies') and base.endswith('y'):
            return MORPHOLOGICAL_MODIFIERS['plural_ies']
        elif suffix == 'ed':
            return MORPHOLOGICAL_MODIFIERS['verb_ed']
        elif suffix == 'ing':
            return MORPHOLOGICAL_MODIFIERS['verb_ing']
        elif suffix == 'er':
            if is_agent_noun_er(original):
                return MORPHOLOGICAL_MODIFIERS['noun_er']
            else:
                return MORPHOLOGICAL_MODIFIERS['comparative']
        elif suffix == 'or' and is_agent_noun_or(original):
            return MORPHOLOGICAL_MODIFIERS['noun_or']
        elif suffix == 'est':
            return MORPHOLOGICAL_MODIFIERS['superlative']
        elif suffix == 'ly' and len(base) > 2:
            return MORPHOLOGICAL_MODIFIERS['adverb_ly']
    
    # Handle cases where normalization changed the ending
    elif original.endswith('ies') and base.endswith('y'):
        return MORPHOLOGICAL_MODIFIERS['plural_ies']
    
    # Handle irregular past participles (different length, not simple suffix)
    # Common patterns: -en endings (hidden->hide, taken->take, broken->break)
    # and other irregular forms (bought->buy, taught->teach)
    if len(original) != len(base) or original != base:
        # Check for common past participle patterns
        if original.endswith('en') and len(original) > len(base):
            # Could be past participle like hidden->hide, taken->take, broken->break
            return MORPHOLOGICAL_MODIFIERS['past_participle']
        
        # Other irregular past participle patterns
        irregular_past_participles = {
            'bought': 'buy', 'brought': 'bring', 'caught': 'catch',
            'taught': 'teach', 'thought': 'think', 'fought': 'fight',
            'sought': 'seek', 'found': 'find', 'bound': 'bind',
            'wound': 'wind', 'hung': 'hang', 'sung': 'sing',
            'rung': 'ring', 'swung': 'swing', 'clung': 'cling',
            'flung': 'fling', 'stung': 'sting', 'wrung': 'wring',
            'sunk': 'sink', 'drunk': 'drink', 'shrunk': 'shrink',
            'begun': 'begin', 'run': 'run', 'come': 'come',  # Same form
            'done': 'do', 'gone': 'go', 'seen': 'see',
            'been': 'be', 'known': 'know', 'grown': 'grow',
            'shown': 'show', 'thrown': 'throw', 'blown': 'blow',
            'flown': 'fly', 'drawn': 'draw', 'withdrawn': 'withdraw'
        }
        
        if original in irregular_past_participles and base == irregular_past_participles[original]:
            return MORPHOLOGICAL_MODIFIERS['past_participle']
    
    # Default: no specific transformation detected
    return ''
