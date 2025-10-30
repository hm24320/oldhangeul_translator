import json
import random


def extract_random_sample(
    input_file,
    training_output_file,
    validation_output_file,
    sample_ratio=0.1,
):
    """
    Split a JSONL dataset into a reproducible random training sample and the remaining validation set.

    Args:
        input_file (str): Path to the source JSONL file.
        training_output_file (str): Path to write the sampled training JSONL file.
        validation_output_file (str): Path to write the remaining validation JSONL file.
        sample_ratio (float): Ratio of lines to include in the training sample (default 0.1 = 10%).
    """

    with open(input_file, "r", encoding="utf-8") as f:
        all_lines = f.readlines()

    total_lines = len(all_lines)
    sample_size = int(total_lines * sample_ratio)

    print(f"Total lines: {total_lines}")
    print(f"Training sample size: {sample_size}")
    print(f"Validation sample size: {total_lines - sample_size}")

    if total_lines == 0:
        training_lines = []
        validation_lines = []
    else:
        random.seed(42)  # Keep results reproducible
        sampled_indices = sorted(random.sample(range(total_lines), sample_size))
        sampled_index_set = set(sampled_indices)

        training_lines = [all_lines[i] for i in sampled_indices]
        validation_lines = [
            line for idx, line in enumerate(all_lines) if idx not in sampled_index_set
        ]

    with open(training_output_file, "w", encoding="utf-8") as f:
        for line in training_lines:
            f.write(line)

    with open(validation_output_file, "w", encoding="utf-8") as f:
        for line in validation_lines:
            f.write(line)

    print(f"Training sample written to '{training_output_file}'.")
    print(f"Validation sample written to '{validation_output_file}'.")

    if training_lines:
        print("\nFirst 3 training samples")
        for i, line in enumerate(training_lines[:3]):
            try:
                data = json.loads(line.strip())
                print(
                    f"Sample {i + 1}: "
                    f"{data.get('messages', [{}])[0].get('role', 'unknown')} - "
                    f"{data.get('messages', [{}])[0].get('content', '')[:50]}..."
                )
            except (json.JSONDecodeError, TypeError):
                print(f"Sample {i + 1}: {line.strip()[:50]}...")
    else:
        print("\nTraining sample is empty; no preview available.")


if __name__ == "__main__":
    input_file = "merged_filtered.jsonl"
    training_output_file = "training_data.jsonl"
    validation_output_file = "validation_data.jsonl"

    extract_random_sample(
        input_file,
        training_output_file,
        validation_output_file,
        sample_ratio=0.1,
    )
