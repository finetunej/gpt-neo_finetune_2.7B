import sys
import subprocess
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

for file in os.listdir(args.source_folder):
    file = source / Path(file)
    out = output / Path(os.path.basename(file))
    print(repr(str(file)) + " to " + repr(str(out)))
    subprocess.call(["python3", "epub2txt-all", "-nc", "-p", "-n", "-f", "-a", "<|endoftext|>", "-v", str(file), str(out)])
