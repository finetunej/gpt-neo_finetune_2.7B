from tqdm import tqdm
import tensorflow as tf
import numpy as np

from pathlib import Path
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("-s", "--source", help="source numpy memmap", type=str, required=True)
parser.add_argument("-o", "--output", help="output tfrecord base name", type=str, required=True)
args = parser.parse_args()

source = str(Path(args.source))
output = str(Path(args.output))

tokens_per_sample = 2049
samples_per_part = 1000
part = 0

mmap = np.memmap(source, mode="r", dtype="uint16")
mmap = mmap.reshape((-1, tokens_per_sample))

def _int64_feature(value):
    """
    Returns an int64_list from a bool / enum / int / uint.
    """
    return tf.train.Feature(int64_list=tf.train.Int64List(value=list(map(int, list(value)))))

def write_to_file(writer, data):
    """
    writes data to tfrecord file
    """
    feature = {
        "text": _int64_feature(data)
    }
    tf_example = tf.train.Example(features=tf.train.Features(feature=feature))
    writer.write(tf_example.SerializeToString())

def format_name():
    global part
    fn = f"{output}_{part}_{samples_per_part}.tfrecords"
    part += 1
    return fn

print("writing")
print("#samples", mmap.shape[0])
samples = samples_per_part
writer = None
for i in tqdm(range(mmap.shape[0])):
    if samples == samples_per_part:
        if writer is not None:
            writer.close()
        writer = tf.io.TFRecordWriter(format_name())
        samples = 0
    write_to_file(writer, mmap[i])
    samples += 1

print("done")
