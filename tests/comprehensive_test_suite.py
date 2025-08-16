#!/usr/bin/env python3
"""
Comprehensive Test Suite for Emo Language Encoder/Decoder

Generates and tests sample encoded/decoded text pairs, tests common phrases and sentences,
validates mapping principles and patterns.

Usage:
    python tests/comprehensive_test_suite.py
"""

import json
import sys
import os
from typing import List, Dict, Tuple, Any
from dataclasses import dataclass
import time
import random

# Add parent directory to path to import encode/decode modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from encode import encode
    from decode import decode
except ImportError:
    print("Error: Could not import encode/decode modules. Make sure you're running from the project root.")
    sys.exit(1)

@dataclass
class TestResult:
    """Results from a single encoding/decoding test"""
    original: str
    encoded: str
    decoded: str
    is_reversible: bool
    encoding_time: float
    decoding_time: float
    emoji_count: int
    word_count: int
    mapping_accuracy: float

@dataclass
class TestCategory:
    """Category of test cases"""
    name: str
    description: str
    test_cases: List[str]

class ComprehensiveTestSuite:
    """Comprehensive testing suite for the Emo Language system"""
    
    def __init__(self):
        self.results: List[TestResult] = []
        self.test_categories = self._create_test_categories()
        self.load_mappings()
    
    def load_mappings(self):
        """Load the word-to-emoji mapping and build the reverse in memory"""
        try:
            with open("mappings/mapping.json", "r", encoding="utf-8") as f:
                self.word_to_emoji = json.load(f)
            self.emoji_to_word = {v: k for k, v in self.word_to_emoji.items()}
            print(f"✅ Loaded mappings: {len(self.word_to_emoji)} word→emoji, {len(self.emoji_to_word)} emoji→word (in memory)")
        except FileNotFoundError as e:
            print(f"❌ Error loading mappings: {e}")
            sys.exit(1)
    
    def _create_test_categories(self) -> List[TestCategory]:
        """Create comprehensive test categories covering various language patterns"""
        return [
            TestCategory(
                name="Basic Communication",
                description="Simple, everyday communication patterns",
                test_cases=[
                    "Hello, how are you?",
                    "I am fine, thank you.",
                    "What is your name?",
                    "My name is Alex.",
                    "Nice to meet you!",
                    "Have a good day.",
                    "See you later.",
                    "How was your weekend?",
                    "I love this weather.",
                    "Are you free tonight?"
                ]
            ),
            TestCategory(
                name="Complex Sentences",
                description="Multi-clause sentences with various grammatical structures",
                test_cases=[
                    "The quick brown fox jumps over the lazy dog.",
                    "Although it was raining, we decided to go for a walk in the park.",
                    "She bought groceries, cooked dinner, and cleaned the house before her guests arrived.",
                    "If you finish your homework early, you can watch television or play video games.",
                    "The scientist who discovered the cure worked tirelessly for twenty years.",
                    "Not only did he win the race, but he also broke the world record.",
                    "While I was reading a book, my cat was sleeping peacefully in the sunshine.",
                    "The conference, which was scheduled for next month, has been postponed indefinitely.",
                    "Because the weather was perfect, we decided to have our picnic by the lake.",
                    "Either we leave now, or we will be late for the movie."
                ]
            ),
            TestCategory(
                name="Emotional Expression",
                description="Sentences expressing various emotions and feelings",
                test_cases=[
                    "I am so happy today!",
                    "This makes me really sad.",
                    "I feel angry about what happened.",
                    "She was excited about the surprise party.",
                    "He seemed worried about the test results.",
                    "We are proud of your achievements.",
                    "I feel grateful for your help.",
                    "The movie was absolutely terrifying.",
                    "This is frustrating and confusing.",
                    "I love spending time with my family."
                ]
            ),
            TestCategory(
                name="Questions and Answers",
                description="Various question types and corresponding answers",
                test_cases=[
                    "What time is it?",
                    "Where did you go yesterday?",
                    "Who is coming to the party?",
                    "Why did you choose this option?",
                    "How do you make chocolate cake?",
                    "Which book do you recommend?",
                    "When will the meeting start?",
                    "Can you help me with this problem?",
                    "Would you like some coffee?",
                    "Did you enjoy the concert last night?"
                ]
            ),
            TestCategory(
                name="Technical and Academic",
                description="Technical, scientific, and academic language",
                test_cases=[
                    "The algorithm processes data efficiently using machine learning techniques.",
                    "Photosynthesis converts carbon dioxide and water into glucose using sunlight.",
                    "The economic theory suggests that supply and demand determine market prices.",
                    "Quantum physics explores the behavior of matter and energy at atomic scales.",
                    "The research methodology involved collecting and analyzing statistical data.",
                    "Software development requires planning, coding, testing, and deployment phases.",
                    "Climate change affects global weather patterns and environmental systems.",
                    "The historical analysis reveals patterns in social and political movements.",
                    "Artificial intelligence systems learn from large datasets to make predictions.",
                    "The mathematical proof demonstrates the relationship between variables."
                ]
            ),
            TestCategory(
                name="Narrative and Storytelling",
                description="Story fragments and narrative structures",
                test_cases=[
                    "Once upon a time, there was a brave knight who lived in a castle.",
                    "The old man walked slowly down the cobblestone street in the moonlight.",
                    "Sarah opened the mysterious box and found an ancient treasure map inside.",
                    "Thunder crashed overhead as the storm approached the small village.",
                    "The children laughed and played in the garden while their parents watched.",
                    "He had been waiting at the station for hours before the train finally arrived.",
                    "The secret door opened to reveal a hidden library filled with magical books.",
                    "Every morning, she would feed the birds that gathered in her backyard.",
                    "The detective carefully examined the evidence at the crime scene.",
                    "They traveled through mountains, forests, and deserts to reach their destination."
                ]
            ),
            TestCategory(
                name="Modern Digital Communication",
                description="Contemporary digital and social communication patterns",
                test_cases=[
                    "Can you send me the link to that website?",
                    "I'll tag you in the photo on social media.",
                    "The video went viral and got millions of views.",
                    "Please update your password for security reasons.",
                    "The app crashed when I tried to upload the file.",
                    "Let's schedule a video call for tomorrow morning.",
                    "I received your email and will respond shortly.",
                    "The wifi connection is really slow today.",
                    "Don't forget to backup your important documents to the cloud.",
                    "She posted an update about her vacation on Instagram."
                ]
            ),
            TestCategory(
                name="Numbers and Measurements",
                description="Sentences involving numbers, quantities, and measurements",
                test_cases=[
                    "The building is fifty stories tall and cost ten million dollars.",
                    "I need three cups of flour and two eggs for this recipe.",
                    "The temperature outside is twenty-five degrees Celsius.",
                    "She ran five kilometers in thirty minutes this morning.",
                    "The concert starts at eight o'clock and lasts two hours.",
                    "We need to buy twelve apples and six oranges from the store.",
                    "The project will take approximately six months to complete.",
                    "His new car gets forty miles per gallon of gasoline.",
                    "The population of the city is over one million people.",
                    "I have been studying Spanish for three years now."
                ]
            ),
            TestCategory(
                name="Cultural References",
                description="Sentences with cultural, historical, and geographical references",
                test_cases=[
                    "We visited the Eiffel Tower during our trip to Paris, France.",
                    "Shakespeare wrote many famous plays including Hamlet and Romeo and Juliet.",
                    "The Great Wall of China is one of the most impressive architectural achievements.",
                    "Christmas is celebrated on December twenty-fifth in many countries.",
                    "The American Revolution took place in the late eighteenth century.",
                    "Sushi is a traditional Japanese dish that has become popular worldwide.",
                    "The Olympics bring together athletes from countries around the globe.",
                    "Leonardo da Vinci painted the Mona Lisa during the Renaissance period.",
                    "The Amazon rainforest is located in South America and is incredibly biodiverse.",
                    "English, Spanish, and Mandarin are among the most widely spoken languages."
                ]
            ),
            TestCategory(
                name="Edge Cases and Special Characters",
                description="Testing punctuation, symbols, and formatting",
                test_cases=[
                    "Hello! How are you? I'm doing great, thanks for asking.",
                    "The cost is $25.99 (including tax) - quite reasonable, don't you think?",
                    "She said, \"I'll be there at 3:00 PM\" and then hung up.",
                    "The email address is user@example.com; please write it down.",
                    "Here's a list: apples, bananas, oranges & grapes.",
                    "The percentage is 95.7% - almost perfect!",
                    "Use hashtag #EmoLanguage for social media posts.",
                    "The website URL is https://www.example.com/page",
                    "Temperature range: -10°C to +35°C (14°F to 95°F)",
                    "Formula: H₂O + CO₂ → C₆H₁₂O₆ + O₂"
                ]
            )
        ]
    
    def run_single_test(self, text: str) -> TestResult:
        """Run a single encoding/decoding test and return results"""
        # Time encoding
        start_time = time.time()
        encoded = encode(text)
        encoding_time = time.time() - start_time
        
        # Time decoding
        start_time = time.time()
        decoded = decode(encoded)
        decoding_time = time.time() - start_time
        
        # Analyze results
        is_reversible = decoded.strip().lower() == text.strip().lower()
        emoji_count = len([c for c in encoded if ord(c) > 127])  # Rough emoji count
        words = text.split()
        word_count = len(words)
        
        # Calculate mapping accuracy (percentage of words that have emoji mappings)
        mapped_words = 0
        for word in words:
            clean_word = ''.join(c for c in word.lower() if c.isalpha())
            if clean_word in self.word_to_emoji:
                mapped_words += 1
        
        mapping_accuracy = (mapped_words / word_count * 100) if word_count > 0 else 0
        
        return TestResult(
            original=text,
            encoded=encoded,
            decoded=decoded,
            is_reversible=is_reversible,
            encoding_time=encoding_time,
            decoding_time=decoding_time,
            emoji_count=emoji_count,
            word_count=word_count,
            mapping_accuracy=mapping_accuracy
        )
    
    def run_category_tests(self, category: TestCategory) -> List[TestResult]:
        """Run tests for a specific category"""
        print(f"\n🧪 Testing Category: {category.name}")
        print(f"   Description: {category.description}")
        print(f"   Test cases: {len(category.test_cases)}")
        
        category_results = []
        for i, test_case in enumerate(category.test_cases, 1):
            print(f"   [{i:2d}/{len(category.test_cases)}] Testing: {test_case[:50]}{'...' if len(test_case) > 50 else ''}")
            result = self.run_single_test(test_case)
            category_results.append(result)
            
            # Show result status
            status = "✅ PASS" if result.is_reversible else "❌ FAIL"
            print(f"        → {status} | Accuracy: {result.mapping_accuracy:.1f}% | Emojis: {result.emoji_count}")
            
            if not result.is_reversible:
                print(f"          Original: {result.original}")
                print(f"          Encoded:  {result.encoded}")
                print(f"          Decoded:  {result.decoded}")
        
        return category_results
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all test categories and return comprehensive results"""
        print("🚀 Starting Comprehensive Test Suite for Emo Language")
        print("=" * 60)
        
        start_time = time.time()
        all_results = {}
        
        for category in self.test_categories:
            category_results = self.run_category_tests(category)
            all_results[category.name] = category_results
            self.results.extend(category_results)
        
        total_time = time.time() - start_time
        
        # Generate summary statistics
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r.is_reversible)
        failed_tests = total_tests - passed_tests
        
        avg_encoding_time = sum(r.encoding_time for r in self.results) / total_tests
        avg_decoding_time = sum(r.decoding_time for r in self.results) / total_tests
        avg_mapping_accuracy = sum(r.mapping_accuracy for r in self.results) / total_tests
        
        summary = {
            "test_summary": {
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "failed_tests": failed_tests,
                "pass_rate": (passed_tests / total_tests) * 100,
                "total_execution_time": total_time,
                "average_encoding_time": avg_encoding_time,
                "average_decoding_time": avg_decoding_time,
                "average_mapping_accuracy": avg_mapping_accuracy
            },
            "category_results": all_results,
            "detailed_results": [
                {
                    "original": r.original,
                    "encoded": r.encoded,
                    "decoded": r.decoded,
                    "is_reversible": r.is_reversible,
                    "encoding_time": r.encoding_time,
                    "decoding_time": r.decoding_time,
                    "emoji_count": r.emoji_count,
                    "word_count": r.word_count,
                    "mapping_accuracy": r.mapping_accuracy
                } for r in self.results
            ]
        }
        
        return summary
    
    def print_summary(self, results: Dict[str, Any]):
        """Print a comprehensive summary of test results"""
        summary = results["test_summary"]
        
        print("\n" + "=" * 60)
        print("🎯 COMPREHENSIVE TEST RESULTS SUMMARY")
        print("=" * 60)
        
        print(f"Total Tests Run:      {summary['total_tests']}")
        print(f"Tests Passed:         {summary['passed_tests']} ({summary['pass_rate']:.1f}%)")
        print(f"Tests Failed:         {summary['failed_tests']}")
        print(f"Execution Time:       {summary['total_execution_time']:.2f} seconds")
        print(f"Avg Encoding Time:    {summary['average_encoding_time']*1000:.2f} ms")
        print(f"Avg Decoding Time:    {summary['average_decoding_time']*1000:.2f} ms")
        print(f"Avg Mapping Accuracy: {summary['average_mapping_accuracy']:.1f}%")
        
        print("\n📊 CATEGORY BREAKDOWN:")
        for category_name, category_results in results["category_results"].items():
            total = len(category_results)
            passed = sum(1 for r in category_results if r.is_reversible)
            pass_rate = (passed / total) * 100 if total > 0 else 0
            avg_accuracy = sum(r.mapping_accuracy for r in category_results) / total if total > 0 else 0
            
            print(f"  {category_name:25} | {passed:2d}/{total:2d} passed ({pass_rate:5.1f}%) | Avg Accuracy: {avg_accuracy:5.1f}%")
        
        print("\n❌ FAILED TESTS (if any):")
        failed_count = 0
        for result in self.results:
            if not result.is_reversible:
                failed_count += 1
                print(f"  {failed_count}. Original: {result.original}")
                print(f"     Encoded:  {result.encoded}")
                print(f"     Decoded:  {result.decoded}")
                print()
        
        if failed_count == 0:
            print("  🎉 No failed tests! All encoding/decoding is perfectly reversible!")
        
        print("\n✨ TEST SUITE COMPLETED SUCCESSFULLY ✨")
    
    def save_results(self, results: Dict[str, Any], filename: str = "tests/test_results.json"):
        """Save test results to JSON file"""
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"💾 Test results saved to: {filename}")
    
    def generate_sample_pairs(self, count: int = 20) -> List[Tuple[str, str]]:
        """Generate random sample encoded/decoded pairs for demonstration"""
        sample_sentences = []
        for category in self.test_categories:
            sample_sentences.extend(category.test_cases)
        
        selected = random.sample(sample_sentences, min(count, len(sample_sentences)))
        pairs = []
        
        for sentence in selected:
            encoded = encode(sentence)
            pairs.append((sentence, encoded))
        
        return pairs


def main():
    """Main execution function"""
    # Create test suite
    suite = ComprehensiveTestSuite()
    
    # Run all tests
    results = suite.run_all_tests()
    
    # Print summary
    suite.print_summary(results)
    
    # Save results
    suite.save_results(results)
    
    # Generate and display sample pairs
    print("\n" + "=" * 60)
    print("📝 SAMPLE ENCODED/DECODED PAIRS")
    print("=" * 60)
    
    sample_pairs = suite.generate_sample_pairs(10)
    for i, (original, encoded) in enumerate(sample_pairs, 1):
        print(f"\n{i:2d}. Original: {original}")
        print(f"    Encoded:  {encoded}")
        decoded = decode(encoded)
        print(f"    Decoded:  {decoded}")
        status = "✅" if decoded.strip().lower() == original.strip().lower() else "❌"
        print(f"    Status:   {status}")


if __name__ == "__main__":
    main()
