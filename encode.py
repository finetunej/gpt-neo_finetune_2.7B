from secrets import randbelow
import numpy as np
import json
import sys
from transformers import AutoTokenizer
tokenizer = AutoTokenizer.from_pretrained("gpt2")

text = ""
chunks = []
token_buf = []
max_chars = 5000000
for line in sys.stdin:
    text += line
    if len(text) >= max_chars:
        text = text.replace('<|endoftext|>\n', '<|endoftext|>')
        text = text.replace('<|endoftext|>\n', '<|endoftext|>')
        tokens = tokenizer.encode(text[0:max_chars], truncation=False)[8:-8]
        if tokens is None or len(tokens) < 1:
            continue
        text = text[max_chars:]
        token_buf = tokens
        while len(token_buf) > 2048:
            chunks.append(np.array(token_buf[0:2048], dtype=np.uint16))
            token_buf = token_buf[2048:]
while len(text) > 0:
    tokens = tokenizer.encode(text)
    tokens = tokens[8:-8]
    token_buf = tokens
    text = ""
    while len(token_buf) > 2048:
        chunks.append(np.array(token_buf[0:2048], dtype=np.uint16))
        token_buf = token_buf[2048:]
chunks = np.array(chunks, dtype=np.uint16)
print("save", flush=True)
print(chunks.shape, flush=True)
indexes = list(range(chunks.shape[0]))

def shuffle(x):
    n = len(x)
    for i in range(n-1):
        j = i + randbelow(n - i)
        t = x[i]
        x[i] = x[j]
        x[j] = t
        yield x[i]
    yield x[n-1]

mmap = np.memmap("fb-2048.map", mode="w+", dtype="uint16", shape=chunks.shape)
for target, source in enumerate(shuffle(indexes)):
    mmap[target, :] = chunks[source, :]
mmap.flush()
print("\nDone", flush=True)
