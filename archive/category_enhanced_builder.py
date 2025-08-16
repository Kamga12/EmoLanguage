# Category-Enhanced Source Builder
# ✅ Integrates the category-based mapping framework with the existing source builder
# ✅ Provides category-aware emoji selection and fallback strategies
# ✅ Maintains consistency across semantic categories
# ✅ Enhanced conflict resolution and mapping validation

import os
import json
import spacy
import torch
import multiprocessing
from tqdm import tqdm
from itertools import permutations
from sentence_transformers import SentenceTransformer, util
from category_mapping_framework import CategoryBasedMappingFramework, SemanticCategory

# --------------------------
# Enhanced Configuration
# --------------------------
class EnhancedConfig:
    # Original source builder settings
    MIN_SIMILARITY = 0.28
    MAX_PERMUTATION_POOL = 100
    
    # Category framework settings
    USE_CATEGORY_FRAMEWORK = True
    CATEGORY_PRIORITY = True  # Prefer category-based assignments
    FALLBACK_TO_SEMANTIC = True  # Fall back to semantic similarity if category fails
    
    # Enhanced features
    VALIDATE_CONSISTENCY = True
    EXPORT_CATEGORY_STATS = True
    SAVE_REASONING = True

config = EnhancedConfig()

# --------------------------
# Environment setup
# --------------------------
cpu_cores = multiprocessing.cpu_count()
os.environ["OMP_NUM_THREADS"] = str(cpu_cores)
os.environ["MKL_NUM_THREADS"] = str(cpu_cores)
os.environ["TOKENIZERS_PARALLELISM"] = "true"
print(f"Using {cpu_cores} CPU threads")

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
print(f"Running on: {DEVICE.upper()}")

class CategoryEnhancedBuilder:
    """
    Enhanced source builder that combines category-based mapping 
    with semantic similarity for optimal emoji assignments.
    """
    
    def __init__(self):
        print("🚀 Initializing Category-Enhanced Builder...")
        
        # Initialize category framework
        self.category_framework = CategoryBasedMappingFramework()
        
        # Initialize traditional semantic components
        self.nlp = spacy.load("en_core_web_sm")
        self.model = SentenceTransformer("all-MiniLM-L6-v2", device=DEVICE)
        
        # Load emoji data for semantic similarity
        import emoji
        self.mappings = {emj: data.get("en", "") for emj, data in emoji.EMOJI_DATA.items()}
        self.emoji_keys = list(self.mappings.keys())
        self.emoji_texts = list(self.mappings.values())
        self.emoji_embeddings = self.model.encode(self.emoji_texts, convert_to_tensor=True, device=DEVICE)
        
        # Tracking variables
        self.word_to_emoji = {}
        self.used_emoji_strings = set()
        self.skipped_words = []
        self.mapping_methods = {}  # Track which method was used for each word
        self.category_stats = {}
        
    def map_word_enhanced(self, word: str) -> dict:
        """
        Enhanced word mapping that combines category-based and semantic approaches.
        Returns detailed mapping information including method and reasoning.
        """
        
        mapping_result = {
            'word': word,
            'emoji': None,
            'method': 'failed',
            'category': None,
            'confidence': 'none',
            'reasoning': '',
            'semantic_score': 0.0
        }
        
        try:
            # Step 1: Try category-based mapping first (if enabled)
            if config.USE_CATEGORY_FRAMEWORK:
                category_result = self._try_category_mapping(word)
                if category_result['emoji'] and self.is_unique_combo(category_result['emoji']):
                    mapping_result.update(category_result)
                    self.mark_used_combo(category_result['emoji'])
                    return mapping_result
            
            # Step 2: Fallback to semantic similarity mapping
            if config.FALLBACK_TO_SEMANTIC:
                semantic_result = self._try_semantic_mapping(word)
                if semantic_result['emoji']:
                    mapping_result.update(semantic_result)
                    self.mark_used_combo(semantic_result['emoji'])
                    return mapping_result
            
            # Step 3: No mapping found
            mapping_result['reasoning'] = "No suitable mapping found using either category or semantic methods"
            
        except Exception as e:
            mapping_result['reasoning'] = f"Error during mapping: {str(e)}"
        
        return mapping_result
    
    def _try_category_mapping(self, word: str) -> dict:
        """Try category-based mapping using the framework."""
        
        # Categorize the word
        category = self.category_framework.categorize_word(word)
        
        # Get category-based recommendation
        recommendation = self.category_framework.get_category_emoji_recommendation(word, category)
        
        return {
            'emoji': recommendation.get('primary_emoji'),
            'method': f"category_{recommendation.get('method', 'unknown')}",
            'category': category.value if category else 'unknown',
            'confidence': recommendation.get('confidence', 'none'),
            'reasoning': recommendation.get('reasoning', ''),
            'semantic_score': 0.0  # Category method doesn't use semantic scores
        }
    
    def _try_semantic_mapping(self, word: str) -> dict:
        """Try semantic similarity mapping (original method)."""
        
        # Get word embedding
        lemma = self.nlp(word)[0].lemma_
        embedding = self.model.encode(lemma, convert_to_tensor=True, device=DEVICE)
        scores = util.pytorch_cos_sim(embedding, self.emoji_embeddings)[0]
        
        top_indices = scores.argsort(descending=True)
        top_emojis_strict = [self.emoji_keys[i] for i in top_indices if float(scores[i]) >= config.MIN_SIMILARITY]
        top_emojis_loose = [self.emoji_keys[i] for i in top_indices[:config.MAX_PERMUTATION_POOL]]
        
        best_score = 0.0
        best_emoji = None
        method = 'failed'
        
        # Try single emoji (high similarity only)
        for i, emj in enumerate(top_emojis_strict):
            if self.is_unique_combo(emj):
                best_emoji = emj
                best_score = float(scores[top_indices[i]])
                method = 'semantic_single'
                break
        
        # Try 2-emoji combinations if no single emoji worked
        if not best_emoji:
            for combo in permutations(top_emojis_loose, 2):
                combined = ''.join(combo)
                if self.is_unique_combo(combined):
                    best_emoji = combined
                    # Average score of the two emojis
                    idx1 = self.emoji_keys.index(combo[0])
                    idx2 = self.emoji_keys.index(combo[1])
                    best_score = (float(scores[idx1]) + float(scores[idx2])) / 2
                    method = 'semantic_combination'
                    break
        
        return {
            'emoji': best_emoji,
            'method': method,
            'category': 'semantic_fallback',
            'confidence': 'high' if best_score > 0.4 else 'medium' if best_score > 0.28 else 'low',
            'reasoning': f"Semantic similarity mapping with score {best_score:.3f}",
            'semantic_score': best_score
        }
    
    def is_unique_combo(self, emoji_str):
        """Check if emoji string is unique across both category framework and global usage."""
        return (emoji_str not in self.used_emoji_strings and 
                emoji_str not in self.category_framework.used_emojis)
    
    def mark_used_combo(self, emoji_str):
        """Mark emoji string as used in both systems."""
        self.used_emoji_strings.add(emoji_str)
        self.category_framework.used_emojis.add(emoji_str)
    
    def build_enhanced_mappings(self, words):
        """Build mappings for all words using the enhanced approach."""
        
        print(f"🔧 Processing {len(words)} words with category-enhanced mapping...")
        print(f"⚙️ Configuration: Category Framework={config.USE_CATEGORY_FRAMEWORK}, "
              f"Semantic Fallback={config.FALLBACK_TO_SEMANTIC}")
        
        method_counts = {
            'category_direct_example': 0,
            'category_category_pool': 0,
            'category_combination': 0,
            'semantic_single': 0,
            'semantic_combination': 0,
            'failed': 0
        }
        
        category_success = {}  # Track success by category
        
        for word in tqdm(words, desc="Enhanced mapping"):
            result = self.map_word_enhanced(word)
            
            if result['emoji']:
                self.word_to_emoji[word] = result['emoji']
                self.mapping_methods[word] = result
                
                # Update statistics
                method_counts[result['method']] = method_counts.get(result['method'], 0) + 1
                
                if result['category']:
                    if result['category'] not in category_success:
                        category_success[result['category']] = {'success': 0, 'total': 0}
                    category_success[result['category']]['success'] += 1
                
            else:
                self.skipped_words.append(word)
                method_counts['failed'] += 1
            
            # Track category totals
            if result['category']:
                if result['category'] not in category_success:
                    category_success[result['category']] = {'success': 0, 'total': 0}
                category_success[result['category']]['total'] += 1
        
        self.category_stats = {
            'method_counts': method_counts,
            'category_success_rates': {
                cat: f"{stats['success']}/{stats['total']} ({stats['success']/stats['total']*100:.1f}%)"
                for cat, stats in category_success.items() if stats['total'] > 0
            }
        }
        
        # Generate reverse mapping
        self.emoji_to_word = {v: k for k, v in self.word_to_emoji.items()}
    
    def save_enhanced_results(self):
        """Save results with enhanced metadata and statistics."""
        
        os.makedirs("mappings", exist_ok=True)
        
        # Save basic mappings (compatible with existing system)
        with open("mappings/word_to_emoji.json", "w") as f:
            json.dump(self.word_to_emoji, f, indent=2, ensure_ascii=False)
        
        with open("mappings/emoji_to_word.json", "w") as f:
            json.dump(self.emoji_to_word, f, indent=2, ensure_ascii=False)
        
        with open("mappings/skipped_words.txt", "w") as f:
            for word in sorted(self.skipped_words):
                f.write(word + "\\n")
        
        # Save enhanced information
        if config.SAVE_REASONING:
            with open("mappings/enhanced_mapping_details.json", "w") as f:
                json.dump(self.mapping_methods, f, indent=2, ensure_ascii=False)
        
        if config.EXPORT_CATEGORY_STATS:
            enhanced_stats = {
                **self.category_stats,
                'total_words_processed': len(self.word_to_emoji) + len(self.skipped_words),
                'successful_mappings': len(self.word_to_emoji),
                'failed_mappings': len(self.skipped_words),
                'success_rate': f"{len(self.word_to_emoji) / (len(self.word_to_emoji) + len(self.skipped_words)) * 100:.2f}%",
                'category_framework_report': self.category_framework.generate_category_report()
            }
            
            with open("mappings/enhanced_statistics.json", "w") as f:
                json.dump(enhanced_stats, f, indent=2, ensure_ascii=False)
    
    def validate_enhanced_results(self):
        """Validate the enhanced mapping results."""
        
        if not config.VALIDATE_CONSISTENCY:
            return
        
        print("\\n🔍 Validating enhanced mapping consistency...")
        
        # Validate category consistency
        category_issues = self.category_framework.validate_category_consistency()
        
        # Validate unique mappings
        duplicate_emojis = {}
        for word, emoji in self.word_to_emoji.items():
            if emoji in duplicate_emojis:
                duplicate_emojis[emoji].append(word)
            else:
                duplicate_emojis[emoji] = [word]
        
        conflicts = {emoji: words for emoji, words in duplicate_emojis.items() if len(words) > 1}
        
        # Report validation results
        total_issues = sum(len(v) for v in category_issues.values()) + len(conflicts)
        print(f"📊 Validation complete: {total_issues} issues found")
        
        if conflicts:
            print(f"⚠️ Emoji conflicts detected: {len(conflicts)}")
            for emoji, words in list(conflicts.items())[:3]:  # Show first 3
                print(f"   {emoji} → {words}")
        
        if category_issues['emoji_conflicts']:
            print(f"⚠️ Category conflicts: {len(category_issues['emoji_conflicts'])}")
        
        # Save validation report
        validation_report = {
            'emoji_conflicts': conflicts,
            'category_issues': category_issues,
            'total_issues': total_issues,
            'validation_passed': total_issues == 0
        }
        
        with open("mappings/validation_report.json", "w") as f:
            json.dump(validation_report, f, indent=2, ensure_ascii=False)

# --------------------------
# Main execution
# --------------------------
def main():
    """Main function with enhanced category-based building."""
    
    print("🚀 Category-Enhanced Emoji Language Builder")
    print("=" * 60)
    
    # Load dictionary words
    print("📚 Loading dictionary words...")
    try:
        with open("/usr/share/dict/words", "r") as f:
            words = [w.strip().lower() for w in f if w.strip().isalpha()]
        words = sorted(set(words), key=len)
        
        # For testing, use a subset
        # words = words[:1000]  # Uncomment for testing
        
        print(f"📊 Loaded {len(words):,} unique words")
        
    except FileNotFoundError:
        print("❌ Dictionary file not found at /usr/share/dict/words")
        return
    
    # Initialize enhanced builder
    builder = CategoryEnhancedBuilder()
    
    # Build enhanced mappings
    builder.build_enhanced_mappings(words)
    
    # Validate results
    builder.validate_enhanced_results()
    
    # Save results
    builder.save_enhanced_results()
    
    # Print summary
    print("\\n" + "=" * 60)
    print("✅ Enhanced emoji mapping complete!")
    print(f"📊 Statistics Summary:")
    for method, count in builder.category_stats['method_counts'].items():
        if count > 0:
            print(f"   {method}: {count:,}")
    
    print(f"\\n📁 Output files saved to mappings/:")
    print("   • word_to_emoji.json (main mappings)")
    print("   • enhanced_mapping_details.json (detailed info)")
    print("   • enhanced_statistics.json (statistics)")
    print("   • validation_report.json (consistency check)")

if __name__ == "__main__":
    main()
