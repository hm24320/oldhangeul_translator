import os
import sys
import unicodedata


def list_txt_basenames(directory_path: str) -> set[str]:

	if not os.path.isdir(directory_path):
		raise FileNotFoundError(f"Directory not found: {directory_path}")

	basenames: set[str] = set()
	for entry in os.listdir(directory_path):
		if not entry.lower().endswith(".txt"):
			continue
		# Normalize to NFC to avoid Unicode discrepancies across OS/filesystems
		normalized = unicodedata.normalize("NFC", entry)
		basename, _ = os.path.splitext(normalized)
		basenames.add(basename)
	return basenames


def main() -> int:

	# Base project directory (current working directory)
	project_root = os.getcwd()
	base_dir = os.path.join(project_root, "데이터셋 제작2")
	original_dir = os.path.join(base_dir, "고문서")
	translated_dir = os.path.join(base_dir, "번역본")

	try:
		original_titles = list_txt_basenames(original_dir)
		translated_titles = list_txt_basenames(translated_dir)
	except FileNotFoundError as e:
		print(str(e))
		return 1

	missing_in_translated = sorted(original_titles - translated_titles)

	if not missing_in_translated:
		print("No missing files: Every 고문서 title exists in 번역본.")
		return 0

	print("Titles present only in 고문서 (no matching .txt in 번역본):")
	for title in missing_in_translated:
		print(title)

	return 0


if __name__ == "__main__":
	sys.exit(main())


