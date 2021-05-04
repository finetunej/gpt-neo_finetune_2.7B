import sys
import ftfy
import os
import argparse
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("-s", "--source-folder", help="source folder with epubs", type=str, required=True)
parser.add_argument("-o", "--output-folder", help="output folder with txts", type=str, required=True)
args = parser.parse_args()

source = Path(args.source_folder)
output = Path(args.output_folder)

if not os.path.isdir(source):
    print("source has to be a folder")
    sys.exit(1)

if not os.path.isdir(output):
    print("output has to be a folder")
    sys.exit(1)

print("Source: " + args.source_folder + "\nOutput: " + args.output_folder)

for root, subdirs, files in os.walk(args.source_folder):
    for file in files:
        file = str(Path(root) / Path(file))
        if not file.lower().endswith('txt'):
            print("skip: " + repr(file))
            continue
        out = str(output / Path(file).stem)
        postfix = ".txt"
        i = 0
        while os.path.isfile(out + postfix):
            i += 1
            postfix = "-" + str(i) + ".txt"
        out += postfix
        print(repr(file) + " to " + repr(out))
        with open(file, 'r', encoding='utf-8') as fh:
            text = fh.read()
        text = ftfy.fix_text(text).replace(' …', '...').replace('…', '...').replace("»", "\"").replace("«", "\"").replace('\r\n', '\n').replace('\r', '\n').replace('\n\n\n', '\n').replace('\n\n', '\n')
        text = "\n".join(map(lambda x: x.strip(), text.split()))
        text += "<|endoftext|>"
        text = text.replace("<|endoftext|>\n<|endoftext|>", "<|endoftext|>").replace("<|endoftext|><|endoftext|>", "<|endoftext|>").replace("<|endoftext|><|endoftext|>", "<|endoftext|>")
        with open(out, 'w', encoding='utf-8') as fh:
            fh.write(text)
