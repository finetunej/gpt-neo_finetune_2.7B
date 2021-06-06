# recommended for gpt-neo tfrecords: clean.py -C -u -r -s -i input/ -o clean/
import random
import re
import sys
import ftfy
import os
import argparse
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("-i", "--input-folder", help="input folder with epubs", type=str, required=True)
parser.add_argument("-o", "--output-folder", help="output folder with txts", type=str, required=True)
parser.add_argument("-u", "--unmarkdown", help="remove markdown formatting if detected", action='store_true')
parser.add_argument("-r", "--remove-eot", help="remove final <|endoftext|> in file", action='store_true')
parser.add_argument("-a", "--add-eot", help="add final <|endoftext|> to files", action='store_true')
parser.add_argument("-s", "--split-eot", help="split into multiple files at <|endoftext|>", action='store_true')
parser.add_argument("-x", "--shuffle", help="shuffle input file order and give numbered names", action='store_true')
parser.add_argument("-c", "--collapse-newlines", help="collapse multiple newlines into one", action='store_true')
parser.add_argument("-C", "--chapter-removal", help="replace chapter and part headers with ***", action='store_true')
args = parser.parse_args()

source = Path(args.input_folder)
output = Path(args.output_folder)

if not os.path.isdir(source):
    print("input has to be a folder")
    sys.exit(1)

if not os.path.isdir(output):
    print("output has to be a folder")
    sys.exit(1)

print("Input: " + args.input_folder + "\nOutput: " + args.output_folder)

from markdown import Markdown
from io import StringIO

def unmark_element(element, stream=None):
    if stream is None:
        stream = StringIO()
    if element.text:
        stream.write(element.text)
    for sub in element:
        unmark_element(sub, stream)
    if element.tail:
        stream.write(element.tail)
    return stream.getvalue()

# patching Markdown
Markdown.output_formats["plain"] = unmark_element
__md = Markdown(output_format="plain")
__md.stripTopLevelTags = False


def unmark(text):
    return __md.convert(text)

def space_fix(s):
    have_open = False
    need_space = False
    need_now = False
    was_space = False
    no_space = False
    r = ""
    for i in range(len(s)):
        if s[i] == '"':
            if have_open:
                need_space = True
                need_now = True
                have_open = False
                if was_space:
                    r = r[:-1]
            else:
                if need_space:
                    r += " "
                have_open = True
                no_space = True
            r += s[i]
            was_space = False
            continue
        if need_space and need_now:
            if not s[i].isspace():
                r += " "
            need_space = False
            need_now = False
        if s[i].isspace():
            if no_space:
                continue
            need_space = False
            was_space = True
        else:
            need_space = True
            was_space = False
        no_space = False
        r += s[i]
    return r

punctuation = ['.', '?', '!', ',', ':', ';', '-', ']', ')', '}', '[', '(', '{']
def punctuation_fix(s):
    r = ""
    was_punctuation = False
    was_space = True
    was_no_post = False
    needs_pre = False
    was_quote = False
    for i in range(len(s)):
        if s[i] in punctuation:
            needs_pre = s[i] in ['[', '(', '{']
            if not needs_pre and not was_quote and was_space:
                if i > 0 and r[-1] != '\n':
                    r = r[:-1]
            was_punctuation = True
            was_no_post = s[i] in ['-', '[', '(', '{']
        else:
            if was_punctuation and not was_no_post and s[i] not in ['"', "'"] and not s[i].isspace():
                r += " "
            was_punctuation = False
            was_no_post = False
        was_space = s[i].isspace()
        if not was_space:
            was_quote = s[i] == '"'
        r += s[i]
    return r

all_files = []

for root, subdirs, files in os.walk(args.input_folder):
    for file in files:
        file = str(Path(root) / Path(file))
        if not file.lower().endswith('txt'):
            print("skip: " + repr(file))
            continue
        all_files.append(file)

file_id = 0
if args.shuffle:
    random.shuffle(all_files)

for file in all_files:
    out = str(output / Path(file).stem)
    if args.shuffle:
        out = str(output / Path(f"clean-{file_id:05d}"))
        file_id += 1
    with open(file, 'r', encoding='utf-8') as fh:
        text = fh.read()
    text = re.sub(r"(\b|\s)''(\b|\s)", r'\1"\2', text) # turn '' into "
    text = re.sub(r'"+', '"', text) # fix multiple quotes
    text = re.sub(r"'+", "'", text) # fix multiple quotes
    text = re.sub(r'( |\t)+', ' ', text) # unindent
    text = re.sub(r'(^|\n)( |\t)+', r'\1', text) # unindent
    text = ftfy.fix_text(text).replace(' …', '...').replace('…', '...').replace("»", "\"").replace("«", "\"").replace('\N{SOFT HYPHEN}', '').replace('\u200b', '') # clean up special
    text = text.replace('\r\n', '\n').replace('\r', '\n') # normalize newlines
    if args.collapse_newlines:
        text = text.replace('\n\n\n', '\n').replace('\n\n', '\n')
    text = re.sub(r'https?:\/\/[^\s\)\]\}]*', '(Link removed)', text)
    text = re.sub(r'\bwww\.[a-zA-Z0-9\-\.\/\~\_]+', '(Link removed)', text)
    lines = text.split("\n")
    for i in range(len(lines)):
        lines[i] = punctuation_fix(space_fix(lines[i].strip()))
    if args.chapter_removal:
        text = re.sub(r'(^|\n)(PART|CHAPTER)\s+([a-z0-9]+)(\n|$)', r'\1***\4', text, flags=re.I) # remove chapter headers
    text = re.sub(r"(\d+)\s*'\s*(\d+)\s*(\")(\s*([\.\!\?]))?", r"\1'\2\3\5", text) # fix formatting of 4'2"
    text = re.sub(r"(\d+):\s*(\d+)", r"\1:\2", text) # fix formatting of 6:30
    text = re.sub(r"([^a-zA-Z][a-zA-Z]\.) (?=[a-zA-Z]\.)", r"\1", text) # fix a.m. and similar
    text = re.sub(r"([^a-zA-Z][a-zA-Z]\.) (?=[a-zA-Z]\.)", r"\1", text) # run twice for repeated occurences
    text = "\n".join(lines)
    text = re.sub(r"\s*$", "", text)
    if args.unmarkdown and re.search(r'(^|\n)#', text) and re.search(r'_.*_', text):
        text = unmark(text)
    if args.add_eot:
        text = text + "<|endoftext|>"
    text = re.sub(r"(\s*<\|endoftext\|>\s*)+", "<|endoftext|>", text)
    if args.remove_eot:
        text = re.sub(r"<\|endoftext\|>$", "", text)
    if args.split_eot:
        text = text.split("<|endoftext|>")
    else:
        text = [text]
    for out_text in text:
        outname = out
        postfix = ".txt"
        i = 0
        while os.path.isfile(outname + postfix):
            i += 1
            postfix = f"-{i:05d}.txt"
        outname += postfix
        print(repr(file) + " to " + repr(outname))
        with open(outname, 'w', encoding='utf-8') as fh:
            fh.write(out_text)
