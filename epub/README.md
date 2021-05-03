convert one epub to txt:

```
python epub2txt-all -nc -p -n -f -a '<|endoftext|>' -v "book.epub" "book.txt"
```

convert whole folder of epubs to txt:

```
python epubfolder.py -s epubs/ -o txts/
```

clean up stuff in folder of txts (not necessary for converted epubs, but can be useful for other txt files):

```
python clean.py -s txts/ -o clean/
```
