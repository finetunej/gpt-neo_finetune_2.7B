import os
import random
from secrets import randbelow
import numpy as np
import json
import sys

import argparse
from pathlib import Path

from tqdm import tqdm
from tqdm.contrib.concurrent import process_map
import functools
from transformers import AutoTokenizer

parser = argparse.ArgumentParser()
parser.add_argument("-s", "--source-folder", help="source folder with epubs", type=str, required=True)
parser.add_argument("-o", "--output", help="output numpy memmap", type=str, required=True)
args = parser.parse_args()

source = Path(args.source_folder)
output = Path(args.output)

data = []

print("listing")
for root, subdirs, files in os.walk(args.source_folder):
    for file in files:
        file = str(Path(root) / Path(file))
        if not file.lower().endswith('txt'):
            continue
        data.append(file)

random.shuffle(data)

tokenizer = AutoTokenizer.from_pretrained("gpt2")

text = ""
chunks = []
token_buf = []

def tokenize_file(tokenize, filename):
    with open(filename, "rb") as fh:
        text = fh.read().decode('utf-8', 'surrogateescape')
        if len(text) < 1:
            return
        text = text + '<|endoftext|>'
        tokens = tokenizer.encode(text, truncation=False)
        if tokens is None or len(tokens) < 1:
            return
        return np.array(tokens, dtype=np.uint16)

print("tokenize", flush=True)
token_buf = process_map(functools.partial(tokenize_file, tokenizer), data, chunksize=20, max_workers=8)
token_buf = np.concatenate(token_buf)

print("save", flush=True)
n_samples = len(token_buf) // 2048
print("#samples", n_samples)
mmap = np.memmap(output, mode="w+", dtype="uint16", shape=(n_samples, 2048))

indexes = list(range(n_samples))
random.shuffle(indexes)

for target, source in tqdm(enumerate(indexes)):
    mmap[target, :] = np.array(token_buf[source * 2048:(source + 1) * 2048], dtype=np.uint16)

mmap.flush()

print("done", flush=True)
