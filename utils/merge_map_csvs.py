import csv
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Set, Tuple


def find_map_dir(start: Path) -> Path:
	"""Return the `map` directory relative to repository root inferred from this file location."""
	# Try <repo_root>/map relative to this script's parent directories
	for parent in [start] + list(start.parents):
		candidate = parent / "map"
		if candidate.exists() and candidate.is_dir():
			return candidate
	# Fallback: assume sibling `map` next to current working directory
	cwd_candidate = Path.cwd() / "map"
	if cwd_candidate.exists() and cwd_candidate.is_dir():
		return cwd_candidate
	raise FileNotFoundError("Could not locate a 'map' directory from script or CWD.")


def read_mappings_from_csv(csv_path: Path) -> Iterable[Tuple[str, str]]:
	"""Yield (old_char, mapped_char) tuples from a CSV if both columns exist.

	Skips rows where either value is missing/empty. Ignores files without the
	required headers.
	"""
	with csv_path.open("r", encoding="utf-8-sig", newline="") as f:
		reader = csv.DictReader(f)
		fieldnames = [fn.strip() for fn in (reader.fieldnames or [])]
		if "old_char" not in fieldnames or "mapped_char" not in fieldnames:
			print(f"[skip] Missing required columns in {csv_path.name}: {fieldnames}")
			return []
		for row in reader:
			old_char = (row.get("old_char") or "").strip()
			mapped_char = (row.get("mapped_char") or "").strip()
			if not old_char or not mapped_char:
				continue
			yield (old_char, mapped_char)


def deduplicate_pairs(pairs: Iterable[Tuple[str, str]]) -> List[Tuple[str, str]]:
	seen: Set[Tuple[str, str]] = set()
	unique: List[Tuple[str, str]] = []
	for pair in pairs:
		if pair in seen:
			continue
		seen.add(pair)
		unique.append(pair)
	return unique


def merge_map_csvs(map_dir: Path, output_csv: Path, deduplicate: bool = True) -> None:
	csv_files = sorted([p for p in map_dir.glob("*.csv") if p.is_file()])
	if not csv_files:
		raise FileNotFoundError(f"No CSV files found in {map_dir}")

	all_pairs: List[Tuple[str, str]] = []
	for csv_path in csv_files:
		pairs = list(read_mappings_from_csv(csv_path))
		if not pairs:
			continue
		print(f"[read] {csv_path.name}: {len(pairs)} pairs")
		all_pairs.extend(pairs)

	if deduplicate:
		before = len(all_pairs)
		all_pairs = deduplicate_pairs(all_pairs)
		print(f"[dedup] {before} -> {len(all_pairs)} unique pairs")

	output_csv.parent.mkdir(parents=True, exist_ok=True)
	with output_csv.open("w", encoding="utf-8", newline="") as f:
		writer = csv.writer(f)
		writer.writerow(["old_char", "mapped_char"])
		writer.writerows(all_pairs)
	print(f"[done] Wrote {len(all_pairs)} rows to {output_csv}")


def main(argv: List[str]) -> int:
	this_file = Path(__file__).resolve()
	repo_root = this_file.parents[1]  # project root
	map_dir = find_map_dir(repo_root)

	# Default output inside map directory
	default_output = map_dir / "combined_old_mapped.csv"

	out_path: Path
	if len(argv) >= 2:
		out_path = Path(argv[1]).resolve()
		if out_path.is_dir():
			out_path = out_path / default_output.name
	else:
		out_path = default_output

	try:
		merge_map_csvs(map_dir=map_dir, output_csv=out_path, deduplicate=True)
		return 0
	except Exception as e:
		print(f"[error] {e}")
		return 1


if __name__ == "__main__":
	sys.exit(main(sys.argv))
