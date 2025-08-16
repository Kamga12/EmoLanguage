# Context Grammar Rules

## Overview
This document defines how grammatical variations (plurals, tenses, comparatives) will be handled through context rather than separate emoji mappings, enabling a cleaner base-word system while maintaining full grammatical expressiveness.

## Core Principle
**Semantic Base + Contextual Grammar = Complete Expression**
- Store only base semantic forms in emoji mappings
- Apply grammatical context through intelligent encoding/decoding rules
- Preserve full meaning while reducing mapping complexity

## Grammar Categories & Rules

### 1. PLURALIZATION

#### A. Regular Plurals
**Rule**: Base form + context detection
```
Input: "cats are sleeping"
Process: "cat" → 🐱 + plural context
Output: 🐱 are 😴
Decode: Multiple subjects → "cats are sleeping"
```

#### B. Plural Context Indicators
- **Multiple subjects**: "cats and dogs" → 🐱 and 🐶
- **Quantity words**: "many", "several", "few", "three"  
- **Collective contexts**: "group of", "pack of", "flock of"

#### C. Irregular Plurals (Preserved)
Keep distinct mappings for irregular forms:
```
person → 👤, people → 👥
child → 👶, children → 👶👶👶  
mouse → 🐭, mice → 🐭🐭
```

### 2. VERB TENSES

#### A. Present Tense (Default)
Base verb form represents present/infinitive:
```
"run" → 🏃 (covers: run, runs, running)
"eat" → 🍽️ (covers: eat, eats, eating)
```

#### B. Past Tense Context
**Method 1: Temporal Emoji Markers**
```
"ran yesterday" → 🏃 🕐 (base verb + time past)
"walked home" → 🚶 🏠 (context implies completion)
```

**Method 2: Auxiliary Verb Detection**
```
"has eaten" → 🍽️ (perfect aspect implied by "has")
"was running" → 🏃 (progressive aspect implied by "was")
```

#### C. Future Tense Context  
```
"will run" → 🏃 ➡️ (base verb + future direction)
"going to eat" → 🍽️ ⏭️ (base verb + future indicator)
```

### 3. COMPARATIVE & SUPERLATIVE FORMS

#### A. Comparative Handling
**Method 1: Modifier Emojis**
```
"bigger" → 🔍 + (big base form)
"faster" → ⚡ + (fast base form) 
"better" → ⭐ + (good base form)
```

**Method 2: Context Recognition**
```
"John is taller than Mike" → John is 📏⬆️ than Mike
"This car is faster" → This 🚗 is ⚡➕
```

#### B. Superlative Handling
```
"biggest" → 🔍⭐ + (big base form)
"fastest" → ⚡⭐ + (fast base form)
"best" → ⭐⭐ + (good base form)
```

### 4. ADVERB CONTEXT RULES

#### A. Manner Adverbs (-ly forms)
Transform adjective base + context:
```
"quickly" → 🏃 (run/fast concept)
"slowly" → 🐌 (slow concept)
"carefully" → 👀 (attention concept)
```

#### B. Degree Adverbs
Use intensity markers:
```
"very big" → 📏⭐⭐
"quite small" → 📐➕
"extremely fast" → ⚡🔥
```

## Implementation Strategy

### 1. ENCODING PROCESS

#### Step 1: Base Word Lookup
```python
def encode_with_context(text: str) -> str:
    tokens = tokenize(text)
    result = []
    
    for i, token in enumerate(tokens):
        base_word = normalizer.normalize_word(token)
        emoji = word_to_emoji.get(base_word)
        
        if emoji:
            # Check for grammatical context
            context = analyze_grammar_context(tokens, i)
            modified_emoji = apply_context_rules(emoji, context)
            result.append(modified_emoji)
        else:
            result.append(token)
    
    return ''.join(result)
```

#### Step 2: Context Analysis
```python
def analyze_grammar_context(tokens: List[str], position: int) -> GrammarContext:
    return GrammarContext(
        is_plural=detect_plural_context(tokens, position),
        tense=detect_tense_context(tokens, position),
        comparison=detect_comparison_context(tokens, position),
        intensity=detect_intensity_context(tokens, position)
    )
```

### 2. DECODING PROCESS

#### Step 1: Context Recognition
```python
def decode_with_context(emoji_text: str) -> str:
    # Parse emoji sequences
    emoji_tokens = parse_emoji_sequence(emoji_text)
    
    # Reconstruct with grammar
    result = []
    for token in emoji_tokens:
        base_word = emoji_to_word.get(token.base_emoji)
        if base_word:
            grammatical_form = apply_grammar_rules(base_word, token.context)
            result.append(grammatical_form)
    
    return ' '.join(result)
```

#### Step 2: Grammar Application
```python
def apply_grammar_rules(base_word: str, context: GrammarContext) -> str:
    word = base_word
    
    if context.is_plural and not is_irregular_plural(base_word):
        word = pluralize(word)
    
    if context.tense == 'past' and not is_irregular_verb(base_word):
        word = past_tense(word)
    
    if context.comparison == 'comparative':
        word = comparative_form(word)
    
    return word
```

## Context Detection Rules

### 1. PLURAL DETECTION

#### Linguistic Indicators:
- **Determiners**: "many", "several", "few", "some", "all"
- **Numbers**: "two", "three", "dozens", "hundreds"
- **Verbs**: "are", "were", "have" (vs "is", "was", "has")
- **Pronouns**: "they", "them", "their"

#### Algorithmic Rules:
```python
def detect_plural_context(tokens: List[str], pos: int) -> bool:
    # Look for plural determiners
    if pos > 0 and tokens[pos-1] in PLURAL_DETERMINERS:
        return True
    
    # Look for plural verb forms
    if pos < len(tokens)-1 and tokens[pos+1] in PLURAL_VERBS:
        return True
    
    # Look for explicit numbers > 1
    if pos > 0 and is_plural_number(tokens[pos-1]):
        return True
    
    return False
```

### 2. TENSE DETECTION

#### Past Tense Indicators:
- **Time expressions**: "yesterday", "last week", "ago", "before"
- **Auxiliary verbs**: "had", "was", "were" + verb
- **Context verbs**: "finished", "completed", "ended"

#### Future Tense Indicators:
- **Modal verbs**: "will", "shall", "going to"
- **Time expressions**: "tomorrow", "next week", "later", "soon"
- **Intention verbs**: "plan to", "intend to", "hope to"

### 3. COMPARISON DETECTION

#### Comparative Context:
- **Words**: "than", "more...than", "less...than"
- **Structures**: "A is [adj]er than B", "A is more [adj] than B"

#### Superlative Context:
- **Determiners**: "the most", "the least", "the [adj]est"
- **Context**: "in the group", "of all", "ever"

## Performance Optimization

### 1. PREPROCESSING
- Build context lookup tables
- Cache common grammatical patterns
- Precompute regular transformation rules

### 2. RUNTIME EFFICIENCY
- Use sliding window for context analysis (±3 words)
- Implement early termination for obvious cases
- Cache context decisions within sentence scope

### 3. ACCURACY VALIDATION
- Test against grammatical corpora
- Validate roundtrip accuracy (encode→decode)
- Monitor edge cases and exceptions

## Examples in Practice

### Input Sentence: "The cats were running quickly home yesterday"

#### Traditional System (Multiple Mappings):
```
"The" → 📰, "cats" → 🐱, "were" → 🅰️, "running" → 🏃, "quickly" → ⚡, "home" → 🏠, "yesterday" → 🕐
```

#### Context System (Base Forms + Grammar):
```
"The" → 📰, "cat" → 🐱 [+plural], "be" → 🅰️ [+past], "run" → 🏃 [+progressive], "quick" → ⚡ [+manner], "home" → 🏠, "yesterday" → 🕐
Result: 📰 🐱 🅰️ 🏃 ⚡ 🏠 🕐
Decode: Context rules restore: "The cats were running quickly home yesterday"
```

### Benefits:
- **Mapping Reduction**: 7 words → 6 base forms
- **Semantic Clarity**: Core meanings preserved
- **Grammatical Completeness**: Full expression maintained
- **System Efficiency**: Fewer mapping conflicts

## Integration with Word_Normalizer

The Word_Normalizer class will be enhanced to support context grammar rules:

```python
class EnhancedWordNormalizer(WordNormalizer):
    def normalize_with_context(self, word: str, context: GrammarContext) -> tuple[str, GrammarContext]:
        base_word = self.normalize_word(word)
        preserved_context = self.extract_grammar_context(word, base_word)
        return base_word, preserved_context
    
    def should_preserve_derivation(self, base: str, derived: str) -> bool:
        # Check preserved derivations list
        # Apply semantic distinction rules
        # Consider professional/cultural importance
        pass
```

This context-driven approach maintains full grammatical expressiveness while dramatically simplifying the emoji mapping system.
