# 🚀 New LLM-Based Semantic Mapping Workflow

## Quick Start

### Prerequisites
1. **Local LLM Server**: Start LM Studio, Ollama, or similar at `http://127.0.0.1:1234`
2. **Dictionary File**: Ensure `dictionary.txt` exists (63,635 words)
3. **Dependencies**: `pip install openai pathlib unicodedata`

### Basic Usage

```bash
# Generate fresh emoji mappings (dry run first)
python3 semantic_mapping.py --dry-run

# Generate actual mappings - creates emoji_map/ files directly!
python3 semantic_mapping.py --batch-size 50

# Ready to use immediately!
python3 encode.py "Hello world"
```

## Key Changes from Old System

### ❌ Old `semantic_mapping.py`
- **Purpose**: Review existing emoji mappings from `emoji_map/`
- **Input**: Existing word-to-emoji mappings 
- **Process**: LLM reviews and suggests improvements
- **Output**: Improvement suggestions for existing mappings

### ✅ New `semantic_mapping.py`
- **Purpose**: Generate fresh emoji mappings from scratch
- **Input**: Word list from `dictionary.txt`
- **Process**: LLM creates new semantic mappings
- **Output**: Brand new word-to-emoji mappings with confidence scores

## Files Generated

| File | Description |
|------|-------------|
| `emoji_map/word_to_emoji.json` | **CORE** - Word→emoji mappings for encode.py |
| `emoji_map/emoji_to_word.json` | **CORE** - Emoji→word mappings for decode.py |
| `mapping_reviews/generated_mappings_{timestamp}.json` | Complete mapping details with reasoning |
| `mapping_reviews/generation_report.md` | Analysis and statistics |

## Command Options

```bash
python3 semantic_mapping.py [OPTIONS]

--batch-size N     # Words per LLM call (default: 50)
--dictionary PATH  # Dictionary file path (default: dictionary.txt)
--base-url URL     # LLM server URL (default: http://127.0.0.1:1234)
--model NAME       # Model name (default: openai/gpt-oss-120b)
--dry-run          # Preview without saving results
```

## Example Output

```
🎯 Generating emoji mappings for all words from dictionary.txt...
2025-01-06 15:30:01 - INFO - Reading words from dictionary.txt...
2025-01-06 15:30:01 - INFO - Loaded 63635 words from dictionary
2025-01-06 15:30:01 - INFO - Processing batch 1/1273 (50 words)...
2025-01-06 15:30:15 - INFO - Batch 1 complete
...

✅ Generation complete!
📄 Mappings saved to: mapping_reviews/generated_mappings_1736280615.json
📊 Report saved to: mapping_reviews/generation_report.md
🗂️ Word-to-emoji mapping saved to: mapping_reviews/word_to_emoji_new.json

📊 Summary:
   • Total words processed: 63635
   • Successful mappings: 58420
   • Success rate: 91.8%
   • Average confidence: 0.73
   • High confidence mappings: 42180
```

## Workflow Integration

1. **Generate** fresh mappings with `semantic_mapping.py` → **Directly creates `emoji_map/` files**
2. **Use immediately** with `encode.py` and `decode.py`
3. **Review** results in `mapping_reviews/generation_report.md`
4. **Fix duplicates** (optional) with `resolve_duplicate_mappings.py`
5. **Refine** (optional) using other quality tools

## Performance Tips

- **Smaller batches** (20-30) = higher quality, slower processing
- **Larger batches** (50-100) = faster processing, may reduce quality
- **Monitor LLM server** for timeout/rate limiting issues
- **Start small** with `--dry-run` to verify setup

## Quality Control

- **Confidence filtering**: Only mappings ≥0.5 confidence included
- **Category classification**: Common, action, object, abstract, technical
- **Semantic reasoning**: Each mapping includes explanation
- **Batch consistency**: Related words processed together

## Migration from Old System

The new system **replaces** the old semantic mapping reviewer:
- No more `--sample-size` or `--all` flags
- No more dependency on existing `emoji_map/` files
- Simplified CLI focused on batch processing
- Dictionary-driven rather than sample-based

Ready to generate semantically perfect emoji mappings! 🎯✨
