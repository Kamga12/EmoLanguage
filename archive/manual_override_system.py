# Manual Override System with LLM Assistance
# ✅ Store LLM-suggested alternatives for each word
# ✅ Allow easy review and selection of best mappings
# ✅ Document the reasoning behind each override
# ✅ Generate a curated list of high-frequency words that need perfect mappings

import os
import json
import time
import logging
from typing import Dict, List, Optional, Set, Tuple, NamedTuple
from dataclasses import dataclass, asdict
from enum import Enum
from collections import defaultdict, Counter
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import emoji

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OverrideStatus(Enum):
    """Status of manual override entries"""
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    NEEDS_ALTERNATIVES = "needs_alternatives"
    IN_PROGRESS = "in_progress"

class OverridePriority(Enum):
    """Priority levels for override review"""
    CRITICAL = "critical"      # High frequency words, core vocabulary
    HIGH = "high"             # Important words with poor mappings
    MEDIUM = "medium"         # Good candidates for improvement
    LOW = "low"              # Nice-to-have improvements

@dataclass
class OverrideAlternative:
    """Alternative emoji suggestion with reasoning"""
    emoji: str
    reasoning: str
    source: str  # "llm", "manual", "semantic_analysis"
    confidence_score: float  # 0.0-1.0
    semantic_fit: float     # How well it matches the word meaning
    visual_clarity: float   # How clear the connection is
    cultural_universality: float  # How universal the meaning is
    suggested_by: str       # Who/what suggested this
    timestamp: str

@dataclass
class OverrideEntry:
    """Complete manual override entry"""
    word: str
    current_emoji: str
    current_reasoning: str
    alternatives: List[OverrideAlternative]
    selected_override: Optional[str]
    override_reasoning: str
    status: OverrideStatus
    priority: OverridePriority
    frequency_rank: Optional[int]  # Word frequency ranking
    category: str  # Semantic category (emotions, animals, actions, etc.)
    review_notes: List[str]
    created_timestamp: str
    last_modified: str
    reviewed_by: Optional[str]

class ManualOverrideSystem:
    """
    Comprehensive manual override system for word-emoji mappings.
    Integrates with LLM to suggest alternatives and allows systematic review.
    """
    
    def __init__(self, 
                 mappings_dir: str = "mappings",
                 override_dir: str = "manual_overrides",
                 llm_base_url: str = "http://127.0.0.1:1234"):
        
        self.mappings_dir = mappings_dir
        self.override_dir = override_dir
        self.llm_base_url = llm_base_url.rstrip('/')
        
        # Create directories
        os.makedirs(self.override_dir, exist_ok=True)
        
        # Initialize HTTP session for LLM
        self.session = self._create_http_session()
        self.model_name = self._get_model_name()
        
        # Load existing data
        self.word_to_emoji = self._load_current_mappings()
        self.override_entries = self._load_existing_overrides()
        self.word_frequencies = self._load_word_frequencies()
        
        # High-frequency words that need perfect mappings
        self.critical_words = self._identify_critical_words()
        
        logger.info(f"Manual Override System initialized")
        logger.info(f"Current mappings: {len(self.word_to_emoji)}")
        logger.info(f"Existing overrides: {len(self.override_entries)}")
        logger.info(f"Critical words identified: {len(self.critical_words)}")
        
    def _create_http_session(self) -> requests.Session:
        """Create HTTP session with retry strategy"""
        session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=1.5,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        return session
        
    def _get_model_name(self) -> str:
        """Auto-detect available model"""
        try:
            response = self.session.get(
                f"{self.llm_base_url}/v1/models",
                timeout=10
            )
            response.raise_for_status()
            models = response.json().get('data', [])
            if models:
                model_name = models[0].get('id', 'local-model')
                logger.info(f"Detected LLM model: {model_name}")
                return model_name
            return 'local-model'
        except Exception as e:
            logger.warning(f"Could not detect LLM model, using default: {e}")
            return 'local-model'
    
    def _load_current_mappings(self) -> Dict[str, str]:
        """Load current word-to-emoji mappings"""
        mapping_file = os.path.join(self.mappings_dir, "word_to_emoji.json")
        if os.path.exists(mapping_file):
            with open(mapping_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def _load_existing_overrides(self) -> Dict[str, OverrideEntry]:
        """Load existing override entries"""
        overrides_file = os.path.join(self.override_dir, "override_entries.json")
        if os.path.exists(overrides_file):
            with open(overrides_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                result = {}
                for word, entry_data in data.items():
                    # Convert enum strings back to enums
                    entry_data['status'] = OverrideStatus(entry_data['status'])
                    entry_data['priority'] = OverridePriority(entry_data['priority'])
                    # Convert alternatives back to dataclass objects
                    alternatives = []
                    for alt_data in entry_data.get('alternatives', []):
                        alternatives.append(OverrideAlternative(**alt_data))
                    entry_data['alternatives'] = alternatives
                    
                    result[word] = OverrideEntry(**entry_data)
                return result
        return {}
    
    def _load_word_frequencies(self) -> Dict[str, int]:
        """Load or generate word frequency data"""
        freq_file = os.path.join(self.override_dir, "word_frequencies.json")
        
        if os.path.exists(freq_file):
            with open(freq_file, 'r') as f:
                return json.load(f)
        
        # Generate basic frequency data based on word length and common patterns
        # This is a simplified approach - in production you'd use actual corpus data
        frequencies = {}
        for word in self.word_to_emoji.keys():
            # Assign higher frequency to shorter words and common patterns
            base_freq = max(1000 - len(word) * 50, 1)
            
            # Boost common words
            if word in ['the', 'and', 'a', 'to', 'of', 'in', 'it', 'you', 'that', 'he', 
                       'was', 'for', 'on', 'are', 'as', 'with', 'his', 'they', 'i', 
                       'at', 'be', 'this', 'have', 'from', 'or', 'one', 'had', 'by',
                       'word', 'but', 'not', 'what', 'all', 'were', 'we', 'when']:
                base_freq *= 10
            
            frequencies[word] = base_freq
        
        # Save for future use
        with open(freq_file, 'w') as f:
            json.dump(frequencies, f, indent=2)
            
        return frequencies
    
    def _identify_critical_words(self) -> List[str]:
        """Identify high-frequency words that need perfect mappings"""
        # Sort words by frequency
        sorted_words = sorted(
            self.word_frequencies.items(), 
            key=lambda x: x[1], 
            reverse=True
        )
        
        # Top 1000 most frequent words are critical
        critical_words = [word for word, freq in sorted_words[:1000]]
        
        # Add semantic categories that are critical
        critical_categories = [
            # Basic emotions
            'happy', 'sad', 'angry', 'excited', 'calm', 'worried', 'surprised',
            'love', 'hate', 'fear', 'joy', 'anger', 'disgust',
            
            # Common animals
            'cat', 'dog', 'bird', 'fish', 'horse', 'cow', 'sheep', 'pig', 'chicken',
            'mouse', 'elephant', 'lion', 'tiger', 'bear', 'rabbit', 'deer',
            
            # Basic actions
            'run', 'walk', 'jump', 'swim', 'fly', 'eat', 'drink', 'sleep',
            'work', 'play', 'read', 'write', 'speak', 'listen', 'see', 'hear',
            
            # Colors
            'red', 'blue', 'green', 'yellow', 'purple', 'orange', 'black', 'white',
            'pink', 'brown', 'gray', 'silver', 'gold',
            
            # Technology
            'computer', 'phone', 'internet', 'email', 'website', 'app', 'software',
            'technology', 'digital', 'online', 'data', 'algorithm',
            
            # Time/weather
            'day', 'night', 'morning', 'evening', 'today', 'tomorrow', 'yesterday',
            'sun', 'moon', 'rain', 'snow', 'wind', 'hot', 'cold', 'warm',
            
            # Family
            'mother', 'father', 'parent', 'child', 'son', 'daughter', 'brother',
            'sister', 'family', 'friend', 'baby', 'grandmother', 'grandfather'
        ]
        
        # Add critical categories to list if they exist in mappings
        for word in critical_categories:
            if word in self.word_to_emoji and word not in critical_words:
                critical_words.append(word)
        
        return critical_words
    
    def generate_llm_alternatives(self, word: str, current_emoji: str, count: int = 5) -> List[OverrideAlternative]:
        """Generate alternative emoji suggestions using LLM"""
        
        prompt = f"""
You are an expert in semantic emoji mapping. I need better alternatives for a word-emoji mapping.

Current Mapping:
Word: "{word}"
Current Emoji: {current_emoji}

Task: Suggest {count} alternative emoji mappings that would be MORE intuitive and semantically accurate.

For each alternative, consider:
1. Semantic accuracy (how well does it represent the word's meaning?)
2. Visual clarity (how obvious is the connection?)
3. Cultural universality (works across cultures?)
4. Disambiguation (specific enough for this word?)

Format your response as JSON:
{{
  "alternatives": [
    {{
      "emoji": "🔥",
      "reasoning": "Direct representation of fire/heat concept",
      "semantic_fit": 0.95,
      "visual_clarity": 0.90,
      "cultural_universality": 0.85,
      "confidence": 0.90
    }}
  ]
}}

Word to analyze: {word}
Current emoji: {current_emoji}
"""

        try:
            response = self.session.post(
                f"{self.llm_base_url}/v1/chat/completions",
                json={
                    "model": self.model_name,
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 800,
                    "temperature": 0.3,
                },
                timeout=45
            )
            
            response.raise_for_status()
            result = response.json()
            
            if 'choices' not in result or not result['choices']:
                logger.error(f"Invalid LLM response for {word}")
                return []
                
            content = result['choices'][0]['message']['content'].strip()
            return self._parse_llm_alternatives(content, word)
            
        except Exception as e:
            logger.error(f"LLM call failed for {word}: {e}")
            return []
    
    def _parse_llm_alternatives(self, content: str, word: str) -> List[OverrideAlternative]:
        """Parse LLM response into OverrideAlternative objects"""
        alternatives = []
        
        try:
            # Try to extract JSON from the response
            import re
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
                
                for alt_data in data.get('alternatives', []):
                    # Validate emoji
                    emoji_text = alt_data.get('emoji', '')
                    if not any(char in emoji.EMOJI_DATA for char in emoji_text):
                        continue
                    
                    alternative = OverrideAlternative(
                        emoji=emoji_text,
                        reasoning=alt_data.get('reasoning', ''),
                        source="llm",
                        confidence_score=float(alt_data.get('confidence', 0.5)),
                        semantic_fit=float(alt_data.get('semantic_fit', 0.5)),
                        visual_clarity=float(alt_data.get('visual_clarity', 0.5)),
                        cultural_universality=float(alt_data.get('cultural_universality', 0.5)),
                        suggested_by=f"LLM-{self.model_name}",
                        timestamp=time.strftime('%Y-%m-%d %H:%M:%S')
                    )
                    alternatives.append(alternative)
                    
        except Exception as e:
            logger.warning(f"Failed to parse LLM alternatives for {word}: {e}")
        
        return alternatives
    
    def create_override_entry(self, word: str, priority: OverridePriority = None) -> OverrideEntry:
        """Create a new override entry for a word"""
        
        if word not in self.word_to_emoji:
            raise ValueError(f"Word '{word}' not found in current mappings")
        
        current_emoji = self.word_to_emoji[word]
        
        # Auto-determine priority if not specified
        if priority is None:
            if word in self.critical_words:
                priority = OverridePriority.CRITICAL
            elif self.word_frequencies.get(word, 0) > 500:
                priority = OverridePriority.HIGH
            elif self.word_frequencies.get(word, 0) > 100:
                priority = OverridePriority.MEDIUM
            else:
                priority = OverridePriority.LOW
        
        # Generate LLM alternatives
        logger.info(f"Generating alternatives for '{word}' -> {current_emoji}")
        alternatives = self.generate_llm_alternatives(word, current_emoji)
        
        # Determine semantic category
        category = self._determine_semantic_category(word)
        
        entry = OverrideEntry(
            word=word,
            current_emoji=current_emoji,
            current_reasoning="",
            alternatives=alternatives,
            selected_override=None,
            override_reasoning="",
            status=OverrideStatus.PENDING_REVIEW,
            priority=priority,
            frequency_rank=self._get_frequency_rank(word),
            category=category,
            review_notes=[],
            created_timestamp=time.strftime('%Y-%m-%d %H:%M:%S'),
            last_modified=time.strftime('%Y-%m-%d %H:%M:%S'),
            reviewed_by=None
        )
        
        self.override_entries[word] = entry
        logger.info(f"Created override entry for '{word}' with {len(alternatives)} alternatives")
        
        return entry
    
    def _determine_semantic_category(self, word: str) -> str:
        """Determine semantic category for a word"""
        # Simple categorization - in production, this could use more sophisticated NLP
        emotion_words = {'happy', 'sad', 'angry', 'excited', 'calm', 'love', 'hate', 'fear', 'joy'}
        animal_words = {'cat', 'dog', 'bird', 'fish', 'horse', 'cow', 'sheep', 'pig', 'mouse'}
        action_words = {'run', 'walk', 'jump', 'swim', 'fly', 'eat', 'drink', 'sleep', 'work'}
        color_words = {'red', 'blue', 'green', 'yellow', 'purple', 'orange', 'black', 'white'}
        tech_words = {'computer', 'phone', 'internet', 'software', 'app', 'digital', 'online'}
        
        if word in emotion_words:
            return "emotions"
        elif word in animal_words:
            return "animals"
        elif word in action_words:
            return "actions"
        elif word in color_words:
            return "colors"
        elif word in tech_words:
            return "technology"
        else:
            return "general"
    
    def _get_frequency_rank(self, word: str) -> Optional[int]:
        """Get frequency rank for a word"""
        sorted_words = sorted(
            self.word_frequencies.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        for rank, (w, freq) in enumerate(sorted_words, 1):
            if w == word:
                return rank
        
        return None
    
    def batch_create_critical_overrides(self, limit: int = 100) -> int:
        """Create override entries for critical words that don't have them yet"""
        created_count = 0
        
        for word in self.critical_words[:limit]:
            if word not in self.override_entries:
                try:
                    self.create_override_entry(word, OverridePriority.CRITICAL)
                    created_count += 1
                    time.sleep(0.2)  # Rate limiting
                except Exception as e:
                    logger.error(f"Failed to create override for '{word}': {e}")
        
        logger.info(f"Created {created_count} new critical override entries")
        return created_count
    
    def review_override(self, word: str, selected_emoji: str, reasoning: str, reviewer: str) -> bool:
        """Review and approve/reject an override"""
        
        if word not in self.override_entries:
            logger.error(f"No override entry found for '{word}'")
            return False
        
        entry = self.override_entries[word]
        
        # Validate selected emoji is in alternatives or is manual override
        valid_selection = False
        if selected_emoji == entry.current_emoji:
            # Keeping current emoji
            entry.status = OverrideStatus.REJECTED
            entry.override_reasoning = f"Current emoji retained: {reasoning}"
            valid_selection = True
        else:
            # Check if it's one of the alternatives
            for alt in entry.alternatives:
                if alt.emoji == selected_emoji:
                    valid_selection = True
                    break
            
            if not valid_selection:
                # Manual selection - add as new alternative
                manual_alt = OverrideAlternative(
                    emoji=selected_emoji,
                    reasoning=reasoning,
                    source="manual",
                    confidence_score=1.0,
                    semantic_fit=0.8,  # Default values for manual selections
                    visual_clarity=0.8,
                    cultural_universality=0.8,
                    suggested_by=reviewer,
                    timestamp=time.strftime('%Y-%m-%d %H:%M:%S')
                )
                entry.alternatives.append(manual_alt)
                valid_selection = True
        
        if valid_selection:
            entry.selected_override = selected_emoji
            entry.override_reasoning = reasoning
            entry.status = OverrideStatus.APPROVED
            entry.reviewed_by = reviewer
            entry.last_modified = time.strftime('%Y-%m-%d %H:%M:%S')
            
            logger.info(f"Override approved for '{word}': {entry.current_emoji} -> {selected_emoji}")
            return True
        
        return False
    
    def generate_review_interface(self, priority_filter: OverridePriority = None) -> str:
        """Generate a human-readable review interface"""
        
        entries_to_review = []
        for word, entry in self.override_entries.items():
            if entry.status == OverrideStatus.PENDING_REVIEW:
                if priority_filter is None or entry.priority == priority_filter:
                    entries_to_review.append(entry)
        
        # Sort by priority and frequency
        priority_order = {
            OverridePriority.CRITICAL: 0,
            OverridePriority.HIGH: 1,
            OverridePriority.MEDIUM: 2,
            OverridePriority.LOW: 3
        }
        
        entries_to_review.sort(key=lambda e: (
            priority_order[e.priority],
            -(e.frequency_rank or 9999)
        ))
        
        interface_lines = [
            "# Manual Override Review Interface",
            "=" * 50,
            "",
            f"**Entries pending review:** {len(entries_to_review)}",
            f"**Filter:** {priority_filter.value if priority_filter else 'All priorities'}",
            "",
            "## Review Instructions",
            "1. For each word below, choose the best emoji mapping",
            "2. Consider semantic accuracy, visual clarity, and cultural universality",
            "3. You can select from alternatives or keep the current mapping",
            "4. Document your reasoning for the choice",
            "",
            "---",
            ""
        ]
        
        for i, entry in enumerate(entries_to_review[:20], 1):  # Limit to 20 for readability
            interface_lines.extend([
                f"## {i}. {entry.word} ({entry.priority.value.upper()})",
                f"**Current mapping:** {entry.word} → {entry.current_emoji}",
                f"**Frequency rank:** {entry.frequency_rank or 'Unknown'}",
                f"**Category:** {entry.category}",
                "",
                "**Alternatives:**"
            ])
            
            # Show current as option A
            interface_lines.append(f"A. {entry.current_emoji} (CURRENT)")
            
            # Show alternatives
            for j, alt in enumerate(entry.alternatives, 1):
                option_letter = chr(ord('A') + j)
                confidence_str = f"{alt.confidence_score:.2f}" if alt.confidence_score else "N/A"
                interface_lines.append(
                    f"{option_letter}. {alt.emoji} - {alt.reasoning} "
                    f"(Confidence: {confidence_str}, Source: {alt.source})"
                )
            
            interface_lines.extend([
                "",
                f"**Your choice for '{entry.word}':** [A/B/C/...] ",
                f"**Reasoning:** _______________",
                "",
                "---",
                ""
            ])
        
        return "\n".join(interface_lines)
    
    def export_approved_overrides(self) -> Dict[str, str]:
        """Export approved overrides in the format expected by the mapping system"""
        
        approved_overrides = {}
        
        for word, entry in self.override_entries.items():
            if entry.status == OverrideStatus.APPROVED and entry.selected_override:
                # Only include if different from current mapping
                if entry.selected_override != entry.current_emoji:
                    approved_overrides[word] = entry.selected_override
        
        return approved_overrides
    
    def save_all_data(self):
        """Save all override data to files"""
        
        # Save override entries
        entries_data = {}
        for word, entry in self.override_entries.items():
            # Convert dataclass to dict for JSON serialization
            entry_dict = asdict(entry)
            # Convert enum values to strings
            entry_dict['status'] = entry.status.value
            entry_dict['priority'] = entry.priority.value
            # Convert alternatives list
            for alt in entry_dict['alternatives']:
                # No enum conversion needed for alternatives
                pass
            entries_data[word] = entry_dict
        
        with open(os.path.join(self.override_dir, "override_entries.json"), 'w', encoding='utf-8') as f:
            json.dump(entries_data, f, indent=2, ensure_ascii=False)
        
        # Save approved overrides in the format the main system expects
        approved_overrides = self.export_approved_overrides()
        with open(os.path.join(self.mappings_dir, "manual_overrides.json"), 'w', encoding='utf-8') as f:
            json.dump(approved_overrides, f, indent=2, ensure_ascii=False)
        
        # Save critical words list
        with open(os.path.join(self.override_dir, "critical_words.json"), 'w') as f:
            json.dump(self.critical_words, f, indent=2)
        
        # Generate summary statistics
        stats = self._generate_statistics()
        with open(os.path.join(self.override_dir, "override_statistics.json"), 'w') as f:
            json.dump(stats, f, indent=2)
        
        logger.info("All override data saved successfully")
    
    def _generate_statistics(self) -> Dict:
        """Generate statistics about the override system"""
        
        status_counts = defaultdict(int)
        priority_counts = defaultdict(int)
        category_counts = defaultdict(int)
        
        for entry in self.override_entries.values():
            status_counts[entry.status.value] += 1
            priority_counts[entry.priority.value] += 1
            category_counts[entry.category] += 1
        
        approved_improvements = sum(
            1 for entry in self.override_entries.values()
            if entry.status == OverrideStatus.APPROVED 
            and entry.selected_override != entry.current_emoji
        )
        
        return {
            "total_override_entries": len(self.override_entries),
            "critical_words_count": len(self.critical_words),
            "status_distribution": dict(status_counts),
            "priority_distribution": dict(priority_counts),
            "category_distribution": dict(category_counts),
            "approved_improvements": approved_improvements,
            "completion_rate": (
                status_counts['approved'] + status_counts['rejected']
            ) / max(len(self.override_entries), 1) * 100,
            "improvement_rate": approved_improvements / max(len(self.override_entries), 1) * 100
        }
    
    def generate_report(self) -> str:
        """Generate comprehensive override system report"""
        
        stats = self._generate_statistics()
        
        report_lines = [
            "# Manual Override System Report",
            "=" * 50,
            "",
            f"**Generated:** {time.strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "## Summary Statistics",
            f"- Total override entries: {stats['total_override_entries']}",
            f"- Critical words identified: {stats['critical_words_count']}",
            f"- Approved improvements: {stats['approved_improvements']}",
            f"- Completion rate: {stats['completion_rate']:.1f}%",
            f"- Improvement rate: {stats['improvement_rate']:.1f}%",
            "",
            "## Status Distribution"
        ]
        
        for status, count in stats['status_distribution'].items():
            percentage = count / stats['total_override_entries'] * 100
            report_lines.append(f"- {status.replace('_', ' ').title()}: {count} ({percentage:.1f}%)")
        
        report_lines.extend([
            "",
            "## Priority Distribution"
        ])
        
        for priority, count in stats['priority_distribution'].items():
            percentage = count / stats['total_override_entries'] * 100
            report_lines.append(f"- {priority.title()}: {count} ({percentage:.1f}%)")
        
        # Top approved improvements
        approved_entries = [
            entry for entry in self.override_entries.values()
            if entry.status == OverrideStatus.APPROVED
            and entry.selected_override != entry.current_emoji
        ]
        
        if approved_entries:
            report_lines.extend([
                "",
                "## Recent Approved Improvements",
                ""
            ])
            
            # Sort by modification time (most recent first)
            approved_entries.sort(key=lambda e: e.last_modified, reverse=True)
            
            for entry in approved_entries[:10]:  # Show top 10
                report_lines.append(
                    f"- **{entry.word}**: {entry.current_emoji} → {entry.selected_override} "
                    f"({entry.priority.value}) - {entry.override_reasoning}"
                )
        
        return "\n".join(report_lines)

# Command-line interface functions
def main():
    """Main function for command-line usage"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Manual Override System for Emoji Mappings")
    parser.add_argument('command', choices=['create', 'review', 'batch-create', 'export', 'report'], 
                       help='Command to execute')
    parser.add_argument('--word', help='Word to create override for')
    parser.add_argument('--priority', choices=['critical', 'high', 'medium', 'low'], 
                       help='Priority level')
    parser.add_argument('--limit', type=int, default=100, 
                       help='Limit for batch operations')
    
    args = parser.parse_args()
    
    # Initialize system
    override_system = ManualOverrideSystem()
    
    if args.command == 'create':
        if not args.word:
            logger.error("--word required for create command")
            return
        
        priority = OverridePriority(args.priority) if args.priority else None
        entry = override_system.create_override_entry(args.word, priority)
        print(f"Created override entry for '{args.word}' with {len(entry.alternatives)} alternatives")
        
    elif args.command == 'batch-create':
        count = override_system.batch_create_critical_overrides(args.limit)
        print(f"Created {count} critical override entries")
        
    elif args.command == 'review':
        priority_filter = OverridePriority(args.priority) if args.priority else None
        interface = override_system.generate_review_interface(priority_filter)
        print(interface)
        
    elif args.command == 'export':
        approved = override_system.export_approved_overrides()
        print(f"Exported {len(approved)} approved overrides")
        for word, emoji in approved.items():
            print(f"  {word} -> {emoji}")
    
    elif args.command == 'report':
        report = override_system.generate_report()
        print(report)
    
    # Always save data after operations
    override_system.save_all_data()

if __name__ == "__main__":
    main()
