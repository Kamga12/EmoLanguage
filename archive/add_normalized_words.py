#!/usr/bin/env python3

# Read the existing dictionary
with open('documents/dictionary.txt', 'r') as f:
    existing_words = set(word.strip() for word in f if word.strip())

print(f"Found {len(existing_words)} existing words in dictionary")

# The 87 normalized words from the previous normalization
normalized_words = [
    "access", "afford", "all", "at", "away", "be", "become", "believe", "big", 
    "bother", "but", "buy", "call", "catch", "come", "consider", "cost", 
    "could", "create", "culture", "deal", "decide", "dictionary", "do", 
    "during", "entire", "even", "every", "experience", "far", "find", "fix", 
    "for", "free", "function", "get", "give", "go", "great", "grow", "have", 
    "help", "hey", "hi", "hold", "how", "identify", "if", "important", 
    "include", "incorporate", "information", "interesting", "involve", "item", 
    "just", "keep", "like", "look", "make", "many", "might", "most", "much", 
    "need", "only", "option", "or", "other", "over", "part", "place", 
    "prefer", "pretty", "probably", "problem", "provide", "put", "ready", 
    "really", "say", "see", "since", "so", "some", "take", "tell", "than", 
    "think", "time", "try", "understand", "until", "use", "vacation", "want", 
    "way", "with", "work", "would", "year", "you"
]

print(f"Have {len(normalized_words)} normalized words to potentially add")

# Find words that are not already in the dictionary
new_words = [word for word in normalized_words if word not in existing_words]

print(f"Found {len(new_words)} new words to add:")
for word in sorted(new_words):
    print(f"  {word}")

# Add new words to dictionary
if new_words:
    with open('documents/dictionary.txt', 'a') as f:
        for word in sorted(new_words):
            f.write(f"{word}\n")
    
    print(f"\nAdded {len(new_words)} new words to dictionary")
else:
    print("\nNo new words to add - all normalized words are already in the dictionary")
