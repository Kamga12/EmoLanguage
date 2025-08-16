# Emo Language System - Complete Process Guide

This document outlines the complete workflow for running, testing, and improving the Emo Language Encoder/Decoder system.

## � **Quick Start Commands**

```bash
# Basic usage (requires existing mappings)
python3 encode.py "Hello world, how are you?"    # → 👋🌍, ❓🫵?
python3 decode.py "👋🌍, ❓🫵?"                    # → hello world, how are you?

# Generate fresh mappings (requires LLM server)
python3 build_mapping.py --mapping-size 50       # Generate 50-word batches
python3 build_mapping.py --dry-run               # Preview without saving
```

## �🔄 **Complete Emo Language Workflow**

### **Step 1: Generate Fresh Emoji Mappings** 
Create semantic word-to-emoji mappings from scratch:
```bash
# Start your local LLM server first (LM Studio, Ollama, etc.)
# Default: http://127.0.0.1:1234

# Generate mappings for all words in dictionary.txt (63k+ words)
python3 build_mapping.py --mapping-size 50

# Or try a dry run first to see sample results
python3 build_mapping.py --dry-run

# Use smaller batches for higher quality (slower but better)
python3 build_mapping.py --mapping-size 20
```

### **Step 2: Basic Testing** 
Test the current system to see how it works:
```bash
# Test encoding a sentence
python3 encode.py "Hello world, how are you?"

# Test decoding emoji back to text
python3 decode.py "👋🌍❓🫵"

# Run comprehensive test suite
python3 tests/comprehensive_test_suite.py
```

### **Step 3: Resolve Duplicate Conflicts**
Fix any duplicate emoji mappings that break reversibility:
```bash
# Check for duplicates (dry run)
python3 resolve_duplicate_mappings.py --dry-run

# Apply duplicate resolutions
python3 resolve_duplicate_mappings.py
```

### **Step 4: Progressive Refinement** (Optional)
Run iterative quality improvement cycles:
```bash
# Run refinement process
python3 progressive_refinement.py --sample-size 100 --max-iterations 3
```

### **Step 5: Validation & Testing**
Verify everything works properly:
```bash
# Test the improved system
python3 tests/comprehensive_test_suite.py

# Test specific sentences
python3 encode_text.py "The quick brown fox jumps over the lazy dog"
python3 decode_text.py [output from above]

# Generate demo samples
python3 demo_emo_language.py
```

### **Step 6: Generate Reports** (Optional)
Create documentation of your improvements:
```bash
# Create mapping analysis report
python3 -c "
from semantic_mapping_reviewer import SemanticMappingReviewer
reviewer = SemanticMappingReviewer()
reviewer.create_analysis_report(reviewer.emoji_map[:100])
"
```

## 📋 **Recommended Order for First Run:**

1. **Start Here:** `python3 tests/comprehensive_test_suite.py`
2. **Check Quality:** `python3 semantic_mapping_reviewer.py --sample-size 20 --dry-run`
3. **Fix Semantics:** `python3 semantic_mapping_reviewer.py --sample-size 50` (if needed)
4. **Fix Duplicates:** `python3 resolve_duplicate_mappings.py --dry-run` then without `--dry-run`
5. **Final Test:** `python3 tests/comprehensive_test_suite.py`

## 🎯 **Quick Start Command:**

If you just want to see the system working right now:
```bash
python3 encode_text.py "Hello, how are you today?"
```

## 🛠️ **Troubleshooting Commands:**

If something breaks:
```bash
# Check if mapping files exist and are valid
ls -la emoji_map/
python3 -c "import json; print(len(json.load(open('emoji_map/word_to_emoji.json'))))"

# Regenerate mappings if needed
python3 source_builder.py
```

## 🔧 **Advanced Configuration Options:**

### LLM Server Configuration
Most scripts support custom LLM settings:
```bash
# Use different LLM server
python3 semantic_mapping_reviewer.py --base-url http://localhost:8080 --model "custom-model"

# Use different model
python3 resolve_duplicate_mappings.py --model "different-model-name"
```

### Sample Size Control
Control how many mappings to process:
```bash
# Small test run
python3 semantic_mapping_reviewer.py --sample-size 10

# Large improvement run
python3 semantic_mapping_reviewer.py --sample-size 500
```

## 📊 **Expected Output Locations:**

- **Test Results:** `test_results/`
- **Semantic Reviews:** `semantic_reviews/`
- **Duplicate Resolutions:** `duplicate_resolutions/`
- **Refinement Reports:** `refinement_results/`
- **Mapping Files:** `emoji_map/`

## ⚠️ **Important Notes:**

1. **Always run with `--dry-run` first** to preview changes
2. **Backup your mapping files** before making changes
3. **The LLM server must be running** at http://127.0.0.1:1234 (or specified URL)
4. **Large sample sizes take time** - start small and increase gradually
5. **Check the reports** generated in each step to understand changes

## 🎭 **System Requirements:**

- Python 3.7+
- Local LLM server (LM Studio, Ollama, etc.)
- Required packages: `openai`, `pathlib`, `unicodedata`
- At least 1GB free disk space for reports and backups

## 🚀 **Quick Health Check:**

Run this command to verify everything is working:
```bash
python3 -c "
import json
from pathlib import Path

# Check files exist
files = ['emoji_map/word_to_emoji.json', 'emoji_map/emoji_to_word.json']
for f in files:
    if Path(f).exists():
        data = json.load(open(f))
        print(f'✅ {f}: {len(data)} mappings')
    else:
        print(f'❌ Missing: {f}')

# Test encoding
from emo_encoder_decoder import EmoEncoderDecoder
encoder = EmoEncoderDecoder()
test = encoder.encode_text('Hello world')
print(f'✅ Encoding test: \"Hello world\" → {test}')
"
```
