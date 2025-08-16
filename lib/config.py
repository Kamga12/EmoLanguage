#!/usr/bin/env python3
"""
EmoLanguage Configuration Module

This module contains all configuration constants, file paths, LLM prompt templates,
and system defaults for the emoji mapping system. It serves as the central
configuration hub with no external dependencies.

Module Structure:
    - API Configuration: LLM service settings and defaults
    - File System Paths: Directory and file location constants
    - Processing Parameters: Batch sizes and operational limits
    - LLM Prompts: Complete prompt templates for generation and collision resolution
    - System Markers: Special identifiers used throughout the system
    - Logging Configuration: Format and level settings

Author: EmoLanguage Team
Version: 2.0.0
"""

from typing import Final

# =============================================================================
# API CONFIGURATION
# =============================================================================

# LLM Service Configuration
DEFAULT_BASE_URL: Final[str] = "http://127.0.0.1:1234"
"""Default base URL for the local LLM API service."""

DEFAULT_MODEL: Final[str] = "openai/gpt-oss-20b"
"""Default model identifier for emoji generation tasks."""

# =============================================================================
# PROCESSING PARAMETERS
# =============================================================================

# Batch Processing Configuration
DEFAULT_MAPPING_BATCH_SIZE: Final[int] = 50
"""Default number of words to process in a single LLM generation request.

Larger batches are more efficient but may hit token limits or reduce quality.
Smaller batches provide better error isolation and quality control.
"""

DEFAULT_COLLISION_BATCH_SIZE: Final[int] = 10
"""Default number of collision pairs to resolve in a single LLM request.

Collision resolution requires more detailed analysis per word, so smaller
batches are preferred to maintain response quality and avoid token limits.
"""

# =============================================================================
# FILE SYSTEM PATHS
# =============================================================================

# Input/Output Directories
DEFAULT_DICTIONARY_PATH: Final[str] = "documents/dictionary.txt"
"""Default path to the input dictionary file containing words to map."""

MAPPING_FILE_PATH: Final[str] = "mappings/mapping.json"
"""Primary storage location for word-to-emoji mappings.

This file serves as the authoritative source of truth for all
generated and validated emoji mappings.
"""

LOGS_DIR: Final[str] = "logs"
"""Directory for storing generation logs, debug information, and reports."""

MAPPINGS_DIR: Final[str] = "mappings"
"""Directory containing mapping files and related data structures."""

# =============================================================================
# LLM PROMPT TEMPLATES
# =============================================================================

BATCH_GENERATION_PROMPT_TEMPLATE: Final[str] = """
# Role
You are an expert in semantic analysis and emoji composition. Assign a unique emoji combo to each input word.

# Inputs
- `words_text`: a numbered list of words, one per line. Keep output order identical to this list.

words_text:
{words_text}

# Definitions
- Emoji combo: a sequence of emoji characters with no spaces. Use as many emojis as necessary to accurately convey the word's meaning.
- Focus on semantic accuracy - choose the most appropriate emoji representation for each word's meaning.

# Rules (selection priority)
Apply in this order:
1) Direct and literal over abstract. Physical, depictable meanings win.
2) Concrete over abstract. Tangible objects beat concepts.
3) Specific over general. Narrow meanings beat broad categories.
4) Common usage over rare. Everyday terms beat obscure synonyms.
Tie-breakers: prefer visually iconic emoji; if still tied, build descriptive sequences that capture key attributes.

# Mapping Strategy by Word Complexity
**Simple Words (basic objects, actions, emotions):** Use single emojis when perfect matches exist.
- Examples: "cat" → 🐱, "happy" → 😊, "book" → 📖, "tree" → 🌳, "run" → 🏃
- Only use single emoji if it directly and clearly represents the word's primary meaning.

**Complex Words (abstract concepts, compound meanings, specialized terms):** Use multi-emoji combinations.
- Examples: "democracy" → 🗳️⚖️🏛️, "photosynthesis" → 🌱☀️🔬, "nostalgia" → 💭⏰❤️
- Build sequences that capture multiple dimensions: action + object, concept + context, cause + effect.
- Prioritize semantic completeness over brevity for complex concepts.

# Constraints
- Every word must receive exactly one combo.
- All combos must be unique within your output.
- **Simple words:** Use single emoji only if it's a perfect semantic match. If no perfect single emoji exists, use combinations.
- **Complex words:** Always use 2+ emojis to capture full meaning, even if a single emoji could partially represent it.
- Use emoji only. No letters, digits, or ASCII punctuation. No spaces inside combos.
- Avoid skin tones and gendered variants unless essential to meaning. Avoid national flags unless the word is a country or nationality.
- Preserve the word text exactly as given in `words_text`. Strip only the numeric list prefix when parsing.

# Creativity guidance
- **For simple concrete words:** Check if a single emoji perfectly captures the meaning. If yes, use it. If not, build a combination.
- **For complex/abstract concepts:** Always use multi-emoji sequences that break down the concept into recognizable components.
- Combine emoji to encode multiple dimensions: physical + emotional, action + context, cause + effect.
- Keep all combos intuitive and universally recognizable, whether single or multi-emoji.
- You may reuse an emoji character across different combos as long as the full combo strings differ.

# Output format (strict)
Return only a JSON array. No preface, no comments, no code fences. Each element is an object with word, emoji_combo, and match_score: `{{"word":"...", "emoji_combo":"...", "match_score": 0.95}}`. Output order must match `words_text`.

Match score should be a float from 0.0 to 1.0 indicating your confidence in the emoji mapping quality:
- 1.0: Perfect semantic match, universally recognizable
- 0.8-0.9: Very good match, clear connection
- 0.6-0.7: Good match, reasonable representation
- 0.4-0.5: Acceptable match, some ambiguity
- 0.0-0.3: Poor match, forced or unclear

Example output for the sample list above:
[
    {{"word":"cat", "emoji_combo":"🐱", "match_score": 0.95}},
    {{"word":"democracy", "emoji_combo":"🗳️⚖️🏛️", "match_score": 0.85}},
    {{"word":"book", "emoji_combo":"📖", "match_score": 0.98}},
    {{"word":"photosynthesis", "emoji_combo":"🌱☀️🔬", "match_score": 0.78}},
    {{"word":"happy", "emoji_combo":"😊", "match_score": 0.92}},
    {{"word":"entrepreneurship", "emoji_combo":"💡🏢📈", "match_score": 0.82}},
    {{"word":"dog", "emoji_combo":"🐕", "match_score": 0.94}},
    {{"word":"nostalgia", "emoji_combo":"💭⏰❤️", "match_score": 0.75}},
    {{"word":"tree", "emoji_combo":"🌳", "match_score": 0.96}},
    {{"word":"biochemistry", "emoji_combo":"🧬⚗️🔬", "match_score": 0.80}}
]

# Preflight checklist
- One mapping per input word, in the same order.
- All combos unique within your output.
- Combos use as many emojis as needed to accurately represent meaning.
- Valid JSON array, no trailing commas, no extra text.

# Now do the task
Generate the most semantically appropriate emoji combos for all words in `words_text` and return only the JSON array.
"""
"""Template for batch emoji generation requests.

This comprehensive prompt guides the LLM through semantic analysis and emoji
composition for multiple words simultaneously. It includes detailed rules for
handling word complexity, ensuring uniqueness, and maintaining consistency.

Template Variables:
    words_text: Formatted list of words to process
    
Expected Output:
    JSON array of word-to-emoji mappings
"""

COLLISION_RESOLUTION_PROMPT_TEMPLATE: Final[str] = """
# Role
You are an expert in semantic analysis and emoji composition. Your job is to assign emoji combinations to words and resolve collisions with clear, intuitive choices.

# Inputs
- `collisions_text`: a list of items. Each item is either a CONFLICT or a RETRY. Items include two words and, for CONFLICT, the disputed emoji combo.
collisions_text: 
{collisions_text}

- `existing_emojis`: a set of emoji combos already assigned elsewhere. Treat these as taken. Order matters. Example: "🎯📚" is different from "📚🎯".
existing_emojis: {existing_emojis}

{word_usage_context}

# Definitions
- Emoji combo: a sequence of emoji characters with no spaces. Use as many emojis as necessary to accurately convey the word's meaning.
- CONFLICT: two words want the exact same emoji combo. One word keeps it. The other must receive a new unique combo.
- RETRY: both words need new unique combos because the previous attempt failed or was incomplete.

# Decision rules (apply in this order)
1) Direct and literal over abstract. Physical, depictable meanings win.
2) Concrete over abstract. Tangible objects beat concepts.
3) Specific over general. Narrow meanings beat broad categories.
4) Common usage over rare. Everyday words beat obscure synonyms.
If still tied: choose the word that is more visually iconic as an emoji. If still tied: choose alphabetically.

# Alternative mapping principles
- **Simple words (basic objects, actions, emotions):** Use single emojis when perfect matches exist.
  Examples: "dog" → 🐕, "smile" → 😊, "car" → 🚗, "water" → 💧
- **Complex words (abstract concepts, compound meanings, specialized terms):** Always use multi-emoji combinations.
  Examples: "democracy" → 🗳️⚖️🏛️, "melancholy" → 😔🌧️💭, "entrepreneurship" → 💡🏢📈
- Prioritize meaning accuracy over brevity. Use as many emojis as needed to clearly represent the word.
- **For simple concrete words:** Check if a single emoji perfectly captures the meaning. If yes, use it. If not, build a combination.
- **For complex/abstract concepts:** Always use 2+ emojis to break down the concept into recognizable semantic components.
- Keep combos intuitive and universally recognizable, whether single or multi-emoji.
- You may reuse emoji characters in different combos. Uniqueness is for the full combo string.
- Avoid skin tones and gender variants unless essential. Prefer neutral forms. Avoid national flags unless the word is a country or nationality.
- Do not use text, digits, or ASCII punctuation. Use emoji only. No spaces inside combos.

# Hard constraints
- Uniqueness within output: every combo you output must be unique.
- Do not output any combo that appears in `existing_emojis`.
- Single exception: in a CONFLICT, the winner keeps the disputed combo even if it appears in `existing_emojis`.
- Include exactly one mapping for every input word. No omissions, no extras.
- Preserve input order: output mappings in the same word order as they appear in `collisions_text`.

# Procedure
For each item in `collisions_text`:
- If CONFLICT:
    1) Decide the winner using the decision rules. The winner keeps the disputed combo exactly.
    2) Assign the loser a new unique combo that does not appear in `existing_emojis` and does not duplicate any combo you already assigned in this response.
- If RETRY:
    1) Assign both words new unique combos that do not appear in `existing_emojis` and does not duplicate any combo you already assigned in this response.

**When creating alternatives:** Apply the complexity strategy:
- Simple words: Use single emoji if it's a perfect semantic match, otherwise use combinations.
- Complex words: Always use multi-emoji sequences that break down the concept into recognizable components.
Build alternatives that accurately represent the word's meaning, using the appropriate level of complexity.

# Examples

**CONFLICT Example:**
Input: CONFLICT: "dog" vs "puppy" both want 🐕
Decision: "dog" is more general, "puppy" is more specific → "puppy" wins (rule 3)
Output: 
- "puppy": 🐕 (keeps the disputed combo)
- "dog": 🐶 (gets new simple alternative)

**RETRY Example:**
Input: RETRY: "cat" and "democracy" both need new combos
Analysis: "cat" = simple word, "democracy" = complex concept
Output:
- "cat": 🐱 (simple single emoji)
- "democracy": 🗳️⚖️🏛️ (complex multi-emoji sequence)

**Mixed Complexity Example:**
Input: CONFLICT: "tree" vs "environmentalism" both want 🌳
Decision: "tree" is concrete, "environmentalism" is abstract → "tree" wins (rule 2)
Output:
- "tree": 🌳 (keeps the disputed combo)
- "environmentalism": 🌍🌱♻️ (gets complex alternative capturing multiple aspects)

# Output format (strict)
Output a JSON array only. No preface, no comments, no trailing commas, no code fences. Each element is an object with word, emoji_combo, and match_score: `{{"word":"...", "emoji_combo":"...", "match_score": 0.95}}`.

Match score should be a float from 0.0 to 1.0 indicating your confidence in the emoji mapping quality:
- 1.0: Perfect semantic match, universally recognizable
- 0.8-0.9: Very good match, clear connection
- 0.6-0.7: Good match, reasonable representation
- 0.4-0.5: Acceptable match, some ambiguity
- 0.0-0.3: Poor match, forced or unclear

Example:
[
    {{"word":"dog", "emoji_combo":"🐕", "match_score": 0.94}},
    {{"word":"nostalgia", "emoji_combo":"💭⏰❤️", "match_score": 0.75}},
    {{"word":"tree", "emoji_combo":"🌳", "match_score": 0.96}},
    {{"word":"biochemistry", "emoji_combo":"🧬⚗️🔬", "match_score": 0.80}},
    {{"word":"cat", "emoji_combo":"🐱", "match_score": 0.95}},
    {{"word":"democracy", "emoji_combo":"🗳️⚖️🏛️", "match_score": 0.85}},
    {{"word":"book", "emoji_combo":"📖", "match_score": 0.98}},
    {{"word":"photosynthesis", "emoji_combo":"🌱☀️🔬", "match_score": 0.78}},
    {{"word":"entrepreneurship", "emoji_combo":"💡🏢📈", "match_score": 0.82}}
]

# Preflight checklist before you output
- Did you produce exactly one mapping for every input word?
- Are all combos unique inside your output?
- Do none of your new combos appear in `existing_emojis`?
- Did the CONFLICT winner keep the exact disputed combo?
- Do the emoji sequences accurately convey each word's meaning?
- Is the result valid JSON with no extra text?

# Now do the task
Resolve all items in `collisions_text` and return only the JSON array of mappings.
"""
"""Template for collision resolution requests.

This prompt specializes in resolving emoji conflicts between words by applying
semantic prioritization rules and generating alternative mappings. It handles
both CONFLICT scenarios (two words wanting the same emoji) and RETRY scenarios
(both words needing new mappings).

Template Variables:
    collisions_text: Formatted collision descriptions
    existing_emojis: Currently used emoji combinations to avoid
    
Expected Output:
    JSON array of resolved word-to-emoji mappings
"""


# =============================================================================
# SYSTEM MARKERS AND IDENTIFIERS
# =============================================================================

RETRY_EMOJI_MARKER: Final[str] = '🔄_RETRY'
"""Special marker used to identify retry scenarios in collision resolution.

This marker is used internally to signal that both words in a collision pair
need new emoji mappings rather than competing for the same emoji.
"""

# =============================================================================
# LOGGING CONFIGURATION
# =============================================================================

LOG_FORMAT: Final[str] = '%(asctime)s - %(levelname)s - %(message)s'
"""Standard logging format for all system components.

Includes timestamp, log level, and message for comprehensive debugging
and operational monitoring.
"""

LOG_LEVEL: Final[str] = 'INFO'
"""Default logging level for the application.

Set to INFO to capture important operational events while filtering out
detailed debug information. Can be overridden at runtime.
"""

# =============================================================================
# EMOJI AND MORPHOLOGICAL CONSTANTS
# =============================================================================

# Character fallback mappings for unknown words
# Only contains lowercase letters and digits - uppercase handled by capitalization modifier
CHARACTER_FALLBACK_MAPPINGS = {
    # Lowercase letters (a-z) - using circled letters for proper individual letter representation
    # All letters from the same Unicode range U+24B6-24CF (circled capital letters)
    'a': 'Ⓐ', 'b': 'Ⓑ', 'c': 'Ⓒ', 'd': 'Ⓓ', 'e': 'Ⓔ', 'f': 'Ⓕ',
    'g': 'Ⓖ', 'h': 'Ⓗ', 'i': 'Ⓘ', 'j': 'Ⓙ', 'k': 'Ⓚ', 'l': 'Ⓛ',
    'm': 'Ⓜ', 'n': 'Ⓝ', 'o': 'Ⓞ', 'p': 'Ⓟ', 'q': 'Ⓠ', 'r': 'Ⓡ',
    's': 'Ⓢ', 't': 'Ⓣ', 'u': 'Ⓤ', 'v': 'Ⓥ', 'w': 'Ⓦ', 'x': 'Ⓧ',
    'y': 'Ⓨ', 'z': 'Ⓩ',
    
    # Numbers (0-9) - using double-circled number emojis to avoid conflict with morphological modifiers
    '0': '⓿', '1': '❶', '2': '❷', '3': '❸', '4': '❹',
    '5': '❺', '6': '❻', '7': '❼', '8': '❽', '9': '❾'
}

# Reverse character fallback mappings for decoding
CHARACTER_FALLBACK_REVERSE = {v: k for k, v in CHARACTER_FALLBACK_MAPPINGS.items()}

# Morphological modifier constants - encode the transformations that normalizer removes
MORPHOLOGICAL_MODIFIERS = {
    # Plurality
    'plural_s': '🔢',        # cats → cat + 🔢
    'plural_es': '🔢🔢',     # boxes → box + 🔢🔢
    'plural_ies': '🔢⭐',    # flies → fly + 🔢⭐
    'irregular_plural': '🔢👑',  # children → child + 🔢👑
    
    # Verb forms
    'verb_s': '3️⃣',         # runs → run + 3️⃣ (3rd person singular)
    'verb_ed': '⏪',         # walked → walk + ⏪ (past tense)
    'verb_ing': '🔄',        # walking → walk + 🔄 (progressive)
    'verb_ize': '🔧',        # organize → organ + 🔧 (verbalize)
    'verb_ify': '⚡',        # purify → pure + ⚡ (make/cause to be)
    'verb_ate': '🎬',        # activate → active + 🎬 (cause to become)
    
    # Adjective forms
    'comparative': '➕',      # faster → fast + ➕
    'superlative': '⭐',     # fastest → fast + ⭐
    'adjective_ive': '🎭',   # active → act + 🎭 (adjective forming)
    'adjective_ful': '🌟',   # helpful → help + 🌟 (full of)
    'adjective_able': '✅',  # readable → read + ✅ (able to be)
    'adjective_ible': '✅',  # visible → see + ✅ (able to be)
    'adjective_ous': '💫',   # famous → fame + 💫 (characterized by)
    'adjective_al': '📐',    # musical → music + 📐 (relating to)
    'adjective_ic': '🔬',    # scientific → science + 🔬 (relating to)
    'adjective_less': '🚫',  # helpless → help + 🚫 (without)
    'adjective_like': '👥',  # childlike → child + 👥 (similar to)
    
    # Adverb forms
    'adverb_ly': '🎯',       # quickly → quick + 🎯
    'adverb_ward': '➡️',     # backward → back + ➡️ (direction)
    'adverb_wise': '🧠',     # likewise → like + 🧠 (manner)
    
    # Noun forms
    'noun_tion': '📋',       # creation → create + 📋 (action/result)
    'noun_sion': '📋',       # decision → decide + 📋 (action/result)
    'noun_ment': '📦',       # movement → move + 📦 (result/means)
    'noun_ness': '🎪',       # kindness → kind + 🎪 (state/quality)
    'noun_ity': '🏛️',        # reality → real + 🏛️ (state/condition)
    'noun_ance': '🌊',       # resistance → resist + 🌊 (state/quality)
    'noun_ence': '🌊',       # patience → patient + 🌊 (state/quality)
    'noun_age': '📊',        # package → pack + 📊 (collection/result)
    'noun_dom': '👑',        # freedom → free + 👑 (state/realm)
    'noun_hood': '🏠',       # childhood → child + 🏠 (state/period)
    'noun_ship': '🚢',       # friendship → friend + 🚢 (state/skill)
    'noun_er': '👤',         # teacher → teach + 👤 (agent/doer)
    'noun_or': '👤',         # actor → act + 👤 (agent/doer)
    'noun_ist': '🎨',        # artist → art + 🎨 (practitioner)
    'noun_ian': '🎓',        # musician → music + 🎓 (specialist)
    'noun_ism': '💭',        # realism → real + 💭 (doctrine/practice)
    
    # Diminutive forms
    'diminutive_ie': '🐣',   # doggie → dog + 🐣 (small/cute)
    'diminutive_y': '🐣',    # kitty → cat + 🐣 (small/cute)
    'diminutive_let': '🔸',  # booklet → book + 🔸 (small version)
    
    # Past participle (when used as adjective)
    'past_participle': '🏁', # finished → finish + 🏁 (completed state)
    
    # Contractions (negation)
    'contraction_nt': '❌',   # isn't → is + ❌ (negation)
    
    # Prefix negations
    'prefix_un': '🔃',       # unhappy → happy + 🔄 (reverse/not)
    'prefix_in': '🚪',       # inactive → active + 🚪 (not/into)
    'prefix_dis': '💥',      # disagree → agree + 💥 (apart/not)
    'prefix_non': '🔕',      # nonsense → sense + 🔕 (not/without)
    
    # Capitalization
    'capitalized': '🔠',     # Hello → hello + 🔠
}

# Reverse morphological modifiers mapping for decoding
MORPHOLOGICAL_MODIFIERS_REVERSE = {v: k for k, v in MORPHOLOGICAL_MODIFIERS.items()}

# Grammar context sets for efficient lookup
PLURAL_CONTEXTS = {'are', 'were', 'have', 'many', 'several', 'few', 'some', 'all'}
PAST_CONTEXTS = {'yesterday', 'ago', 'was', 'were', 'had', 'before', 'last'}
FUTURE_CONTEXTS = {'will', 'shall', 'tomorrow', 'next', 'soon', 'going'}

# Irregular word forms for grammar reconstruction
IRREGULAR_COMPARATIVES = {
    'good': 'better', 'bad': 'worse', 'much': 'more', 'little': 'less'
}

IRREGULAR_SUPERLATIVES = {
    'good': 'best', 'bad': 'worst', 'much': 'most', 'little': 'least'
}

IRREGULAR_PLURALS = {
    'person': 'people', 'child': 'children', 'mouse': 'mice', 
    'man': 'men', 'woman': 'women', 'foot': 'feet', 'tooth': 'teeth',
    'goose': 'geese', 'ox': 'oxen'
}

# Reverse irregular plurals mapping
IRREGULAR_PLURALS_REVERSE = {v: k for k, v in IRREGULAR_PLURALS.items()}

# Common verb patterns for heuristic detection
COMMON_VERBS = {
    'run', 'walk', 'jump', 'eat', 'sleep', 'work', 'play', 'read',
    'write', 'speak', 'listen', 'watch', 'see', 'hear', 'feel',
    'think', 'know', 'understand', 'learn', 'teach', 'help',
    'make', 'create', 'build', 'destroy', 'fix', 'break'
}

# Common agent nouns ending in -er
AGENT_NOUNS_ER = {
    'teacher', 'worker', 'player', 'reader', 'writer', 'speaker',
    'helper', 'maker', 'builder', 'runner', 'walker', 'singer',
    'dancer', 'driver', 'manager', 'leader', 'owner'
}

# Common agent nouns ending in -or
AGENT_NOUNS_OR = {
    'actor', 'doctor', 'director', 'editor', 'author', 'creator',
    'inventor', 'investor', 'conductor', 'instructor', 'professor',
    'counselor', 'advisor', 'supervisor', 'administrator', 'operator'
}

# Irregular verb forms for 3rd person singular
IRREGULAR_VERB_3RD_PERSON = {
    'do': 'does', 'go': 'goes', 'have': 'has', 'be': 'is'
}

# Irregular verb forms (already in 3rd person singular)
IRREGULAR_VERB_3RD_FORMS = {'does', 'goes', 'has', 'is'}

# Irregular contractions
IRREGULAR_CONTRACTIONS = {
    "can't": 'can', "won't": 'will'
}
