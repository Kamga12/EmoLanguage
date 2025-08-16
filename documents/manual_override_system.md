# Manual Override System with LLM Assistance

The Manual Override System is a comprehensive tool for improving word-emoji mappings in the Emo Language platform. It integrates with LLM to suggest better alternatives, provides systematic review workflows, and maintains a curated list of high-priority mappings.

## 🎯 Features

### ✅ LLM-Suggested Alternatives
- Generates 3-5 alternative emoji mappings for each word using LLM
- Evaluates alternatives based on semantic fit, visual clarity, and cultural universality
- Provides confidence scores and detailed reasoning for each suggestion

### ✅ Easy Review and Selection
- Interactive command-line interface for reviewing mappings
- Shows current mapping vs. alternatives with scores
- Allows selection from alternatives or manual entry
- Documents reasoning behind each override decision

### ✅ Documented Reasoning
- Stores detailed reasoning for each override decision
- Tracks who made the decision and when
- Maintains audit trail of all changes
- Supports different sources (LLM, manual, semantic analysis)

### ✅ High-Frequency Word Curation
- Identifies top 1000+ most frequent words that need perfect mappings
- Prioritizes critical vocabulary (emotions, animals, actions, colors, tech)
- Generates curated lists for systematic review
- Tracks completion status for high-priority words

## 📁 System Architecture

### Core Components

1. **ManualOverrideSystem** (`manual_override_system.py`)
   - Main system class managing all override operations
   - Integrates with LLM API for generating alternatives
   - Manages word frequency analysis and priority assignment

2. **InteractiveReviewer** (`interactive_review.py`)
   - Command-line interface for reviewing override entries
   - Supports filtering by priority and batch processing
   - Provides guided review workflow with help system

3. **OverrideIntegration** (`override_integration.py`)
   - Bridges override system with existing source builders
   - Analyzes current mappings using semantic validation
   - Generates reports and exports curated lists

### Data Structures

```python
@dataclass
class OverrideEntry:
    word: str                           # Word being overridden
    current_emoji: str                  # Current mapping
    alternatives: List[OverrideAlternative]  # LLM suggestions
    selected_override: Optional[str]    # Chosen override
    status: OverrideStatus             # pending/approved/rejected
    priority: OverridePriority         # critical/high/medium/low
    frequency_rank: Optional[int]      # Word frequency ranking
    category: str                      # Semantic category
    reasoning: str                     # Decision reasoning
    reviewed_by: Optional[str]         # Reviewer identity
    # ... timestamps and metadata
```

### File Organization

```
manual_overrides/
├── override_entries.json          # All override entries
├── critical_words.json           # High-frequency word list
├── word_frequencies.json         # Word frequency data
├── override_statistics.json      # System statistics
├── high_frequency_words.json     # Top words report (JSON)
├── high_frequency_words.md       # Top words report (Markdown)
└── improvement_candidates.md     # Analysis report

emoji_map/
├── manual_overrides.json         # Approved overrides (used by builders)
├── word_to_emoji.json           # Current mappings
└── emoji_to_word.json           # Reverse mappings
```

## 🚀 Quick Start

### 1. Initialize the System

```bash
# Create sample override entries for testing
python interactive_review.py --create-sample 20
```

### 2. Run Analysis Pipeline

```bash
# Analyze current mappings and create improvement candidates
python override_integration.py full-analysis --sample-size 500
```

### 3. Review Override Entries

```bash
# Start interactive review session (critical priority only)
python interactive_review.py --priority critical

# Review all pending entries
python interactive_review.py
```

### 4. Generate Reports

```bash
# Generate comprehensive system report
python manual_override_system.py report

# Export high-frequency words list
python override_integration.py high-frequency
```

## 📋 Detailed Usage

### Creating Override Entries

```bash
# Create override entry for a specific word
python manual_override_system.py create --word "happy" --priority critical

# Batch create entries for top critical words
python manual_override_system.py batch-create --limit 50
```

### Interactive Review Process

The interactive reviewer guides you through each pending override:

1. **Word Information**: Shows word, priority, frequency rank, and category
2. **Current Mapping**: Displays current emoji with reasoning (if available)
3. **Alternatives**: Lists LLM-generated alternatives with scores
4. **Selection**: Choose option A (keep current) or B/C/D... (alternatives)
5. **Reasoning**: Document why you made this choice
6. **Progress**: Track completion status

#### Review Commands
- `A`, `B`, `C`, etc. - Select option
- `skip` - Skip current entry
- `quit` - Save and exit
- `help` - Show help information

### Priority Levels

- **CRITICAL**: High frequency words (top 1000), core vocabulary
- **HIGH**: Important words with poor current mappings
- **MEDIUM**: Good candidates for improvement
- **LOW**: Nice-to-have improvements

### LLM Integration

The system calls a local LLM API (compatible with OpenAI format) to generate alternatives:

```python
# Default endpoint
LLM_BASE_URL = "http://127.0.0.1:1234"

# The system auto-detects available models
# Generates 3-5 alternatives per word with scoring:
# - semantic_fit: How well emoji matches word meaning
# - visual_clarity: How obvious the connection is  
# - cultural_universality: Works across cultures
# - confidence_score: Overall confidence in suggestion
```

## 📊 Semantic Categories

The system categorizes words for consistency analysis:

- **emotions**: happy, sad, angry, love, fear, joy, etc.
- **animals**: cat, dog, bird, fish, horse, cow, etc.
- **actions**: run, walk, jump, swim, fly, eat, etc.
- **colors**: red, blue, green, yellow, purple, etc.
- **technology**: computer, phone, internet, software, etc.
- **general**: Everything else

## 🔄 Integration with Source Builders

The system integrates seamlessly with existing source builders:

1. **Export Approved Overrides**: `export_approved_overrides()` 
2. **Update Manual Overrides File**: Updates `emoji_map/manual_overrides.json`
3. **Source Builder Integration**: Builders automatically apply overrides during mapping

### Builder Integration Points

```python
# In source_builder.py and llm_source_builder.py
manual_path = "emoji_map/manual_overrides.json"
if os.path.exists(manual_path):
    with open(manual_path) as f:
        overrides = json.load(f)
        word_to_emoji.update(overrides)  # Apply overrides
```

## 📈 Analysis and Reports

### Mapping Quality Analysis

The system uses semantic validation to identify improvement candidates:

- **Critical Improvements**: High-priority words with poor mappings
- **High-Frequency Weak**: Common words with low semantic scores  
- **Rejected Mappings**: Mappings scoring very poorly
- **Inconsistent Mappings**: Words with consistency issues

### Generated Reports

1. **System Report**: Overall statistics and status
2. **Improvement Candidates**: Detailed analysis of mapping issues
3. **High-Frequency Words**: Top 1000 words with completion status
4. **Quality Statistics**: Validation scores and distributions

## 🛠 Advanced Features

### Batch Operations

```bash
# Process multiple words at once
python manual_override_system.py batch-create --limit 100

# Analyze large sample for candidates  
python override_integration.py create-from-analysis --sample-size 1000
```

### Custom Priority Assignment

```python
# Auto-priority based on frequency and category
if word in self.critical_words:
    priority = OverridePriority.CRITICAL
elif self.word_frequencies.get(word, 0) > 500:
    priority = OverridePriority.HIGH
# ... etc
```

### Consistency Checking

The system checks for consistency within semantic fields:
- Similar words should use similar emoji approaches
- Quality scores should be comparable within categories
- Mixed single/combination emoji usage is flagged

## 🎛 Configuration

### System Settings

```python
# In manual_override_system.py
class Config:
    LLM_BASE_URL = "http://127.0.0.1:1234"
    EMOJI_MAP_DIR = "emoji_map" 
    OVERRIDE_DIR = "manual_overrides"
    CRITICAL_WORD_COUNT = 1000
    MAX_ALTERNATIVES = 5
```

### LLM Configuration

```python
# LLM API parameters
{
    "max_tokens": 800,
    "temperature": 0.3,    # Low temperature for consistent results
    "timeout": 45,         # Request timeout
    "retry_attempts": 3    # Retry failed requests
}
```

## 🔍 Troubleshooting

### Common Issues

1. **LLM API Connection**
   ```bash
   # Check if LLM server is running
   curl http://127.0.0.1:1234/v1/models
   ```

2. **Missing Dependencies**
   ```bash
   pip install requests emoji dataclasses
   ```

3. **File Permissions**
   ```bash
   # Ensure write permissions for override directories
   chmod -R 755 manual_overrides/
   ```

### Debug Mode

```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 📚 API Reference

### ManualOverrideSystem

```python
system = ManualOverrideSystem()

# Core methods
system.create_override_entry(word, priority)
system.review_override(word, selected_emoji, reasoning, reviewer)  
system.batch_create_critical_overrides(limit)
system.export_approved_overrides()
system.generate_review_interface(priority_filter)
system.save_all_data()
```

### InteractiveReviewer

```python
reviewer = InteractiveReviewer()

# Main workflow
reviewer.run_interactive_review(priority_filter)
reviewer.load_pending_entries(priority_filter)
reviewer.show_final_summary()
```

### OverrideIntegration  

```python
integration = OverrideIntegration()

# Analysis pipeline
analysis = integration.analyze_current_mappings(sample_size)
integration.create_overrides_from_analysis(analysis, max_per_category)
integration.save_high_frequency_report()
integration.update_manual_overrides_file()
```

## 🤝 Contributing

When contributing to the manual override system:

1. **Follow Priority Guidelines**: Use appropriate priority levels
2. **Document Reasoning**: Always provide clear reasoning for overrides
3. **Test LLM Integration**: Ensure alternatives are semantically meaningful
4. **Update Documentation**: Keep this README current with changes
5. **Run Full Pipeline**: Test the complete analysis → review → integration flow

## 📝 Changelog

See `/documents/changelog.md` for detailed change history.

---

The Manual Override System provides a systematic approach to improving emoji mappings through LLM assistance, human review, and priority-based curation. It ensures that the most critical words have perfect mappings while providing tools to continuously improve the overall mapping quality.
