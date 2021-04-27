# gpt-neo_finetune_2.7B

I document my experience finetuning gpt-neo-2.7B here. My basis was:

https://github.com/Xirider/finetune-gpt2xl

I used AWS p3.8xlarge through a cheap reseller that's no longer in business. p3.2xlarge	ran out of system memory. To make everything easier, I ran the whole process as root in the root home dir. You can clone the repo listed above and put in the files from this.

If you are looking for the results, check out this repository:

https://github.com/finetuneanon/gpt-neo_dungeon

# Dataset preparation

There is no '<|startoftext|>' token, only '<|endoftext|>'. If you have a weird dataset with '<|startoftext|>' tokens, remove them.

Tokenizing the data at runtime is a waste of time, so I prepare a pretokenized dataset in the form of a numpy memmap which is fast to access. The system you run this on should have enough RAM to fit the whole dataset in tokenized form.

```
cat inputs/*.txt | python encode.py
```

Your dataset is now in fb-2048.map. A good way of getting that on your instance is to upload it to google drive and download it with gdown. I uploaded my datasets here:

https://mega.nz/folder/WIMl1a6K#j8av_rSB4nBf8nys0FxX8g

aidungeon-2048.map is the original text adventure dataset without '<|startoftext|>' tokens and processed through encode.py. I haven't actually used this one.

# Instance setup

The image I was using had multiple CUDA versions preinstalled, so first I select the right one:

```
echo 'PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/usr/games:/usr/local/games:/snap/bin:/usr/local/cuda/bin"' > /etc/environment
echo 'LD_LIBRARY_PATH="/usr/local/cuda/lib64"' >> /etc/environment
rm /usr/local/cuda
ln -s /usr/local/cuda-11.1 /usr/local/cuda
```

Then relogin and install dependencies:

```
apt update
apt upgrade
apt install vim git python3.8 python3-numpy python3-pip cmake python3-arrow wget build-essential
pip3 install cython
pip3 install torch==1.8.1+cu111 torchvision==0.9.1+cu111 torchaudio==0.8.1 -f https://download.pytorch.org/whl/torch_stable.html
pip3 install pyarrow==0.17.1
git clone https://github.com/microsoft/DeepSpeed/
cd DeepSpeed
TORCH_CUDA_ARCH_LIST="11.1" pip3 install .
cd
pip3 install transformers
pip3 install -r requirements.txt
pip3 install datasets==1.5.0 pyarrow==0.17.1 packaging
ds_report
```

In the output of ds_report, check that the pytorch cuda version is the same as the cuda version. If it's not, everything will break.

# Run the training

```
deepspeed --num_gpus=4 run_clm.py \
--deepspeed ds_config_gptneo.json \
--model_name_or_path EleutherAI/gpt-neo-2.7B \
--model_type gpt_neo \
--do_train \
--fp16 \
--overwrite_cache \
--overwrite_output_dir \
--output_dir finetuned \
--validation_file validation.csv \
--num_train_epochs 1 \
--gradient_accumulation_steps 2 \
--per_device_train_batch_size 2 \
--use_fast_tokenizer False \
--learning_rate 5e-06 \
--save_total_limit 1 \
--save_steps 400 \
--save_strategy steps \
--block_size 2048 \
--seed 5 \
--warmup_steps 10 \
--train_file fb-2048.map
```

Trying to do evaluation would crash with OOM and I broke it in the code anyways. On 4x V100, I got about 9.3s per batch, with a total batch size of 16. For a bigger dataset, using this I calculated from the duration I was willing to train for the number of samples I wanted to train for. It can be limited with this inserted above --train_file:

```
--max_train_samples 99200 \
```

With the speed above, 99200 samples run for about 12h.

I was running without big storage, so I used --save_total_limit 1, because each checkpoint is about 50GB.


# Finetuning a finetune

Trying to load deepspeed snapshots would OOM for me, so I replaced the cache weights file huggingface downloaded:

```
CACHED="$(python3 get_cache_filename.py)"
mv "$CACHED" "$CACHED.backup"
ln -s /root/finetune/pytorch_model.bin "$CACHED"
```
