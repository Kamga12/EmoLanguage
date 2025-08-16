# Final source_builder.py that:
# ✅ Assigns unique emoji strings (1–2 emoji) to each word
# ✅ Uses top N emoji for permutations, regardless of score
# ✅ Ensures emoji string uniqueness
# ✅ Supports up to 73k+ words without reuse conflicts

import os
import json
import emoji
import spacy
import torch
import multiprocessing
from tqdm import tqdm
from itertools import permutations
from sentence_transformers import SentenceTransformer, util

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

# --------------------------
# Config
# --------------------------
MIN_SIMILARITY = 0.28
MAX_PERMUTATION_POOL = 100  # Allow top 100 emojis for permutation fallback

# --------------------------
# Load NLP and model
# --------------------------
nlp = spacy.load("en_core_web_sm")
model = SentenceTransformer("all-MiniLM-L6-v2", device=DEVICE)

# --------------------------
# Load emoji data
# --------------------------
mappings = {emj: data.get("en", "") for emj, data in emoji.EMOJI_DATA.items()}
emoji_keys = list(mappings.keys())
emoji_texts = list(mappings.values())
emoji_embeddings = model.encode(emoji_texts, convert_to_tensor=True, device=DEVICE)

# --------------------------
# Load and sort dictionary
# --------------------------
with open("/usr/share/dict/words", "r") as f:
    words = [w.strip().lower() for w in f if w.strip().isalpha()]
words = sorted(set(words), key=len)

# --------------------------
# Mapping setup
# --------------------------
word_to_emoji = {}
used_emoji_strings = set()
skipped_words = []

def is_unique_combo(emoji_str):
    return emoji_str not in used_emoji_strings

def mark_used_combo(emoji_str):
    used_emoji_strings.add(emoji_str)

# --------------------------
# Main loop
# --------------------------
for word in tqdm(words):
    lemma = nlp(word)[0].lemma_
    embedding = model.encode(lemma, convert_to_tensor=True, device=DEVICE)
    scores = util.pytorch_cos_sim(embedding, emoji_embeddings)[0]

    top_indices = scores.argsort(descending=True)
    top_emojis_strict = [emoji_keys[i] for i in top_indices if float(scores[i]) >= MIN_SIMILARITY]
    top_emojis_loose = [emoji_keys[i] for i in top_indices[:MAX_PERMUTATION_POOL]]

    # Try single emoji (high similarity only)
    for emj in top_emojis_strict:
        if is_unique_combo(emj):
            word_to_emoji[word] = emj
            mark_used_combo(emj)
            break
    else:
        # Try 2-emoji permutations from a larger pool (even if lower similarity)
        found = False
        for combo in permutations(top_emojis_loose, 2):
            combined = ''.join(combo)
            if is_unique_combo(combined):
                word_to_emoji[word] = combined
                mark_used_combo(combined)
                found = True
                break
        if not found:
            skipped_words.append(word)

# --------------------------
# Manual overrides
# --------------------------
manual_path = "mappings/manual_overrides.json"
if os.path.exists(manual_path):
    with open(manual_path) as f:
        overrides = json.load(f)
        word_to_emoji.update(overrides)

# --------------------------
# Reverse mapping
# --------------------------
emoji_to_word = {v: k for k, v in word_to_emoji.items()}

# --------------------------
# Output files
# --------------------------
os.makedirs("mappings", exist_ok=True)
with open("mappings/word_to_emoji.json", "w") as f:
    json.dump(word_to_emoji, f, indent=2)
with open("mappings/emoji_to_word.json", "w") as f:
    json.dump(emoji_to_word, f, indent=2)
with open("mappings/skipped_words.txt", "w") as f:
    for word in sorted(skipped_words):
        f.write(word + "\n")
