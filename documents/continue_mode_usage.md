# Continue Mode Feature for semantic_mapping.py

## Overview

The `--continue` option has been added to `semantic_mapping.py` to allow processing only dictionary words that are missing from the existing `word_to_emoji.json` mapping file.

## Usage

```bash
# Only process words missing from word_to_emoji.json
python3 semantic_mapping.py --continue

# Combine with other options
python3 semantic_mapping.py --continue --batch-size 100 --dry-run

# Use with a custom dictionary file
python3 semantic_mapping.py --continue --dictionary custom_words.txt
```

## How It Works

1. **Load Dictionary**: Reads all words from the specified dictionary file (default: `dictionary.txt`)
2. **Load Existing Mappings**: Attempts to load existing mappings from `emoji_map/word_to_emoji.json`
3. **Filter Words**: Removes any dictionary words that already exist in the mapping file
4. **Process Only Missing**: Only generates mappings for the remaining words that don't have mappings yet
5. **Merge Results**: New mappings are merged with existing ones, preserving all previous work

## Benefits

- **Efficiency**: Avoid regenerating mappings for words that already have them
- **Incremental Processing**: Add new words to dictionary without starting from scratch  
- **Resource Conservation**: Save time and API calls by only processing what's needed
- **Safe Updates**: Existing mappings are preserved and extended rather than overwritten

## Example Output

```
2025-01-07 12:26:36,789 - INFO - Loaded 54321 words from dictionary.txt
2025-01-07 12:26:36,790 - INFO - Continue mode: filtered out 53278 existing words
2025-01-07 12:26:36,790 - INFO - Remaining words to process: 1043
```

## Integration with Existing Features

The continue mode works seamlessly with:
- `--batch-size`: Process missing words in specified batch sizes
- `--dry-run`: Preview what would be processed without making changes
- `--resume-from`: Can still resume from a specific word number within the filtered list
- Checkpointing: Automatic saving and resuming still works as expected

## Error Handling

- If `emoji_map/word_to_emoji.json` doesn't exist, processes all dictionary words (same as normal mode)
- If all dictionary words already have mappings, returns early with a success message
- Existing mappings are always preserved - new mappings are merged in, not replaced

This feature makes the semantic mapping system much more efficient for incremental updates and maintenance of large word-to-emoji mapping databases.
