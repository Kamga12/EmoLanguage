#!/usr/bin/env python3
"""
Test script to show the exact prompt sent to the LLM during multi-pass generation
"""

import sys
sys.path.append('/home/mike/Projects/EmoLanguage')

from lib.semantic_mapping_generator import SemanticMappingGenerator

def main():
    # Initialize generator
    generator = SemanticMappingGenerator()
    
    # Test words
    test_words = ["serendipitous", "ephemeral"]
    
    # Generate the context-aware prompt for pass 1
    prompt = generator._create_context_aware_prompt(test_words, pass_num=0, total_passes=2)
    
    print("=" * 80)
    print("CONTEXT-AWARE PROMPT SENT TO LLM (Pass 1/2):")
    print("=" * 80)
    print(prompt)
    print("=" * 80)
    
    # Generate the context-aware prompt for pass 2
    prompt2 = generator._create_context_aware_prompt(test_words, pass_num=1, total_passes=2)
    
    print("\nCONTEXT-AWARE PROMPT SENT TO LLM (Pass 2/2):")
    print("=" * 80)
    print(prompt2)
    print("=" * 80)

if __name__ == "__main__":
    main()
