
# Emo Language Encoder/Decoder

**Inspired by the series *Pantheon*, this project builds a full emoji-based language system** — where every English word is mapped to a unique emoji or emoji sequence. The result is a fully reversible, semantic emoji language: Emo.

---

## 🌟 Purpose

This project explores an expressive and human-readable language encoding method using emojis. Rather than assigning random emoji tokens, Emo seeks to semantically align English words with meaningful emoji representations.

We aim to:

- ✅ Encode and decode English text into emoji sequences
- ✅ Ensure every word has a **unique** emoji or emoji pair
- ✅ Preserve punctuation and word boundaries
- ✅ Maintain reversibility: **emoji ➜ exact original word**
- ✅ Use emoji combinations (`🐶🍖`) when a single emoji isn't semantically strong or available
- ✅ Prevent reuse of emoji strings to ensure 1:1 mapping

---

## 🔠 How It Works

### **New LLM-Based Approach** 🆕

1. **Word Source**
   - Uses `dictionary.txt` (comprehensive English word list)
   - Over 63,000 unique English words processed sequentially

2. **Semantic Emoji Generation**
   - Each word is analyzed by a local LLM for semantic meaning
   - LLM generates the most appropriate emoji(s) based on:
     - Clear semantic connection to word meaning
     - Universal cultural recognition
     - Simplicity (1-2 emojis max, prefer single)
     - Encoding/decoding suitability

3. **Categorization**
   - Words are automatically classified: common, action, object, abstract, technical
   - Enables consistent emoji usage patterns within categories
   - Confidence scoring filters out poor mappings

4. **Quality Control**
   - Confidence scoring (0.0-1.0) for each mapping
   - Only high-confidence mappings (≥0.5) are used
   - Batch processing for efficiency (50 words per LLM call)

### **Legacy Approach**

1. **Similarity-Based Matching**
   - Each word is semantically embedded using a language model
   - Compared with emoji descriptions using cosine similarity
   - If no single emoji meets threshold, pairs are created

### **Common Features**

3. **Reversibility**
   - Emoji strings are guaranteed to be unique
   - During decoding, the mapping is 1:1 back to the original word

4. **Preservation of Grammar**
   - Punctuation is left untouched
   - Spacing is preserved (each emoji string is a "word token")

---

## 📁 File Structure

### **Core System**
- `semantic_mapping.py`: **NEW** - LLM-based emoji mapping generator
- `encode.py`: Encodes English text into emoji
- `decode.py`: Decodes emoji back into English
- `apply_mapping_improvements.py`: Applies generated mappings to core system
- `source_builder.py`: Legacy similarity-based mapping builder

### **Data Files**
- `dictionary.txt`: Input word list (63k+ words)
- `emoji_map/word_to_emoji.json`: Active forward mapping
- `emoji_map/emoji_to_word.json`: Active reverse mapping
- `mapping_reviews/`: Generated mappings and analysis reports

### **Generated Outputs**
- `mapping_reviews/generated_mappings_{timestamp}.json`: Full mapping details
- `mapping_reviews/word_to_emoji_new.json`: Simple word→emoji mappings
- `mapping_reviews/generation_report.md`: Analysis and statistics

---

## ✨ Example

Input:
```
How does the quick brown fox jump so high?
```

Encoded:
```
⌚➕ ⚓ 🩳🧵 👩🏾‍⚖ 🦡 ⛹‍♀️ ➖💤 ✋🏾?
```

Decoded:
```
How does the quick brown fox jump so high?
```

---

## 📦 Installation

```bash
pip install emoji spacy tqdm sentence-transformers
python -m spacy download en_core_web_sm
python source_builder.py
```

---

## 👩‍💻 Attribution

Created by fans of *Pantheon* who wanted to build a working version of the “emoji language” shown in the series.
