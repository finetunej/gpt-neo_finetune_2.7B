from transformers.file_utils import cached_path, WEIGHTS_NAME, hf_bucket_url
model_name = "EleutherAI/gpt-neo-2.7B"
archive_file = hf_bucket_url(model_name, filename=WEIGHTS_NAME)
resolved_archive_file = cached_path(archive_file)
print(resolved_archive_file)
