# Semantic Prioritization Rules for Emoji Mapping

This document defines the semantic prioritization rules used by the Emo Language system to ensure consistent, intuitive emoji assignments across all words in the dictionary.

## Core Principle

**One Word = One Unique Emoji Sequence (1-3 emojis maximum)**

Every English word maps to exactly one unique emoji or emoji sequence. No two words share the same emoji representation, ensuring perfect reversibility during encoding/decoding.

## Prioritization Hierarchy

When choosing which emoji(s) should represent a word, follow this priority order:

### 1. PERFECT SEMANTIC MATCH 🎯

**FIRST: Check if any word has a perfect semantic match**

Some words have direct, one-to-one emoji representations where the emoji was specifically designed to represent that exact concept. These get absolute priority.

**Examples:**
- ✅ `"fox"` → 🦊 (emoji exists specifically for foxes)
- ✅ `"calculator"` → 🧮 (abacus emoji, but calculator gets precedence for calculation tools)
- ✅ `"rose"` → 🌹 (emoji designed specifically for roses)
- ✅ `"bicycle"` → 🚲 (direct bicycle representation)
- ✅ `"key"` → 🔑 (literal key object)

**THEN: Assign new creative emojis to the remaining words**

After perfect semantic matches are claimed, remaining words get assigned through the following prioritization rules:

### 2. DIRECT/LITERAL over ABSTRACT 🔨

Words with direct physical representations always get the literal emoji representation.

**Examples:**
- ✅ `"abacus"` → 🧮 (literal counting tool)
- ❌ `"abacus"` → 🔢 (abstract calculation symbol)
- ✅ `"fox"` → 🦊 (direct animal representation)  
- ❌ `"fox"` → 🧠 (abstract cunning/clever symbol)
- ✅ `"tree"` → 🌳 (physical tree)
- ❌ `"tree"` → 🌿 (abstract nature/growth concept)

### 2. CONCRETE over ABSTRACT 🔨

Physical, tangible objects take priority over their conceptual meanings.

**Examples:**
- ✅ `"clock"` → 🕐 (physical timepiece)
- ❌ `"clock"` → ⏰ (abstract time management)
- ✅ `"book"` → 📖 (physical object)
- ❌ `"book"` → 🧠 (abstract knowledge symbol)
- ✅ `"hammer"` → 🔨 (concrete tool)
- ❌ `"hammer"` → 🏗️ (abstract construction concept)
- ✅ `"key"` → 🔑 (physical object)
- ❌ `"key"` → 🗝️ (abstract access/solution symbol)

### 3. SPECIFIC over GENERAL 🎸

More specific words claim the most direct emoji representation.

**Examples:**
- ✅ `"rose"` → 🌹 (specific flower type)
- ❌ `"flower"` → 🌹 (generic flower gets less specific emoji)
- ✅ `"bicycle"` → 🚲 (specific transport)
- ❌ `"vehicle"` → 🚲 (generic transport gets different emoji)
- ✅ `"guitar"` → 🎸 (specific instrument)
- ❌ `"instrument"` → 🎸 (generic instrument gets different emoji)
- ✅ `"tiger"` → 🐅 (specific big cat)
- ❌ `"cat"` → 🐅 (generic cat gets different emoji)

### 4. COMMON USAGE over RARE 🏠

Everyday, frequently used words get priority for the most obvious emoji representations.

**Examples:**
- ✅ `"house"` → 🏠 (common word gets obvious emoji)
- ❌ `"dwelling"` → 🏠 (rare word gets alternative)
- ✅ `"car"` → 🚗 (common usage)
- ❌ `"automobile"` → 🚗 (formal term gets alternative)
- ✅ `"dog"` → 🐕 (everyday term)
- ❌ `"canine"` → 🐕 (technical term gets alternative)
- ✅ `"happy"` → 😊 (common emotion word)
- ❌ `"joyful"` → 😊 (less common gets alternative)

### 5. UNIVERSAL RECOGNITION 🌍

Choose emojis that are widely understood across different cultures and contexts.

**Guidelines:**
- Avoid region-specific symbols unless the word is inherently regional
- Prefer emojis with clear, universal visual meanings
- Choose symbols that work across different cultural contexts
- Avoid ambiguous or culturally sensitive representations

## Handling Abstract vs. Concrete Words

### Concrete Words (Physical Objects, Living Things)
- Always use the most direct visual representation
- Prioritize literal appearance over symbolic meaning
- Examples: `"apple"` → 🍎, `"elephant"` → 🐘, `"mountain"` → ⛰️

### Abstract Words (Concepts, Emotions, Ideas)
- Use widely recognized symbolic representations
- Choose symbols that clearly convey the concept
- Examples: `"love"` → ❤️, `"peace"` → ☮️, `"danger"` → ⚠️

### Action Words (Verbs)
- Use human figure emojis performing the action when available
- Use symbolic representations for non-physical actions
- Examples: `"run"` → 🏃, `"think"` → 🤔, `"sleep"` → 😴

## Word Family Prioritization

When dealing with related words (base forms and derivatives):

### Base Forms Get Priority
The base form of a word gets the most direct emoji representation:
- ✅ `"sing"` → 🎤 (base verb gets direct representation)
- ✅ `"singer"` → 🎤👤 (derivative gets compound representation)

### Semantic Distinctions Preserved
Words with truly different meanings keep separate representations:
- `"use"` → 🔧 (functional action)
- `"useful"` → ✅ (positive quality)
- `"useless"` → ❌ (negative quality)

## Conflict Resolution Examples

### When Multiple Words Want the Same Emoji

**Scenario:** Both "calculator" and "abacus" could use calculation-related emojis.

**Resolution:** 
- `"abacus"` → 🧮 (gets the literal representation - DIRECT/LITERAL wins)
- `"calculator"` → 🔢 (gets symbolic representation)

**Scenario:** Both "house" and "home" could use 🏠.

**Resolution:**
- `"house"` → 🏠 (gets direct representation - CONCRETE wins)
- `"home"` → 🏡 (gets alternative house emoji)

## Implementation in Prompts

The LLM receives these rules as explicit guidance:

```
🎯 SEMANTIC PRIORITIZATION RULES:

• DIRECT/LITERAL over ABSTRACT: Words with direct physical representations get the literal emoji
• CONCRETE over ABSTRACT: Physical objects take priority over conceptual meanings  
• SPECIFIC over GENERAL: More specific words claim the most direct emoji
• COMMON USAGE over RARE: Everyday words get priority for obvious emojis
• UNIVERSAL RECOGNITION: Choose emojis widely understood across cultures
```

## Quality Assurance

### Validation Checks
1. **Uniqueness**: Every emoji sequence maps to exactly one word
2. **Reversibility**: Decoding must return the exact original word
3. **Semantic Clarity**: The emoji choice should be intuitive to most users
4. **Cultural Neutrality**: Avoid culturally specific symbols unless appropriate

### Examples of Good Mappings
- `"abacus"` → 🧮 ✅ (literal object, culturally clear)
- `"fox"` → 🦊 ✅ (direct animal, universally recognized)
- `"bicycle"` → 🚲 ✅ (specific transport, clear meaning)
- `"rose"` → 🌹 ✅ (specific flower, widely understood)

### Examples to Avoid
- `"abacus"` → 🔢 ❌ (too abstract, could apply to many calculation words)
- `"fox"` → 🧠 ❌ (symbolic rather than literal)
- `"bicycle"` → 🚶 ❌ (too generic, doesn't specify type of transport)

## Future Considerations

As the system evolves, these rules ensure:
- **Consistency**: All mapping decisions follow the same logical principles
- **Predictability**: Users can guess likely emoji mappings based on the rules
- **Maintainability**: New words can be added following established patterns
- **Cultural Adaptation**: Rules can be adjusted for different language/cultural contexts while maintaining core principles

---

*These rules are implemented in `semantic_mapping.py` and guide the LLM's emoji selection process for all 63,000+ words in the dictionary.*
