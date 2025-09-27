import os


def merge_jsonl_files(directory: str, output_filename: str = "merged.jsonl") -> None:
    """
    Merge all top-level .jsonl files in the given directory into a single output file.
    - Scans only the specified directory (no recursion)
    - Excludes the output file if it already exists
    - Merges files in alphabetical order for determinism
    """

    entries = os.listdir(directory)
    jsonl_files = [f for f in entries if f.lower().endswith(".jsonl")]

    # Exclude the output file if present
    jsonl_files = [f for f in jsonl_files if f != output_filename]

    if not jsonl_files:
        print("No .jsonl files found to merge.")
        return

    jsonl_files.sort()

    output_path = os.path.join(directory, output_filename)

    total_lines_written = 0
    with open(output_path, "w", encoding="utf-8") as outfile:
        for filename in jsonl_files:
            path = os.path.join(directory, filename)
            lines_written_for_file = 0
            with open(path, "r", encoding="utf-8") as infile:
                for line in infile:
                    # Ensure newline termination
                    if not line.endswith("\n"):
                        line = line + "\n"
                    outfile.write(line)
                    total_lines_written += 1
                    lines_written_for_file += 1
            print(f"Merged {filename}: {lines_written_for_file} lines")

    print("-" * 40)
    print(f"Output: {output_filename}")
    print(f"Total files merged: {len(jsonl_files)}")
    print(f"Total lines written: {total_lines_written}")


if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.abspath(__file__))
    merge_jsonl_files(current_dir)


