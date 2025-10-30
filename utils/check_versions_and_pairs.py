import argparse
import hashlib
import json
import os
import re
import sys
import unicodedata
from collections import defaultdict
from typing import Dict, List, Tuple


VERSION_SUFFIX_PATTERN = re.compile(r"\((\d+)\)$")


def read_text_file(file_path: str) -> str:
    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
        return f.read()


def normalize_text(text: str, *, use_nfc: bool = True, strip_bom: bool = True, collapse_ws: bool = False) -> str:
    if strip_bom and text.startswith("\ufeff"):
        text = text.lstrip("\ufeff")
    if use_nfc:
        text = unicodedata.normalize("NFC", text)
    if collapse_ws:
        # Collapse sequences of whitespace to a single space, preserve newlines structure
        lines = [re.sub(r"\s+", " ", line).strip() for line in text.splitlines()]
        text = "\n".join(lines).strip()
    return text


def sha256_digest(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def get_stem_without_version(filename_stem: str) -> Tuple[str, int]:
    match = VERSION_SUFFIX_PATTERN.search(filename_stem)
    if match:
        version_num = int(match.group(1))
        base = filename_stem[: match.start()].rstrip()
        return base, version_num
    return filename_stem, 1


def index_folder(folder: str, *, normalize: bool, collapse_ws: bool) -> Dict[str, Dict]:
    index: Dict[str, Dict] = {}
    for entry in os.listdir(folder):
        if not entry.lower().endswith(".txt"):
            continue
        file_path = os.path.join(folder, entry)
        if not os.path.isfile(file_path):
            continue
        stem = os.path.splitext(entry)[0]
        base_stem, version_num = get_stem_without_version(stem)
        raw = read_text_file(file_path)
        norm = normalize_text(raw, use_nfc=normalize, strip_bom=True, collapse_ws=collapse_ws)
        digest = sha256_digest(norm)
        index[stem] = {
            "path": file_path,
            "stem": stem,
            "base_stem": base_stem,
            "version": version_num,
            "size_bytes": os.path.getsize(file_path),
            "num_lines": norm.count("\n") + (1 if norm else 0),
            "digest": digest,
        }
    return index


def compare_versions_in_old(folder_old: str, *, normalize: bool, collapse_ws: bool) -> Dict:
    idx = index_folder(folder_old, normalize=normalize, collapse_ws=collapse_ws)
    groups: Dict[str, List[Dict]] = defaultdict(list)
    for meta in idx.values():
        groups[meta["base_stem"]].append(meta)

    identical_groups = []
    mixed_groups = []

    for base, metas in groups.items():
        if len(metas) == 1:
            continue
        digests = {m["digest"] for m in metas}
        versions = sorted((m["stem"], m["version"]) for m in metas)
        if len(digests) == 1:
            identical_groups.append({
                "base_title": base,
                "versions": [m[0] for m in versions],
                "digest": list(digests)[0],
                "status": "identical",
            })
        else:
            # find which differ
            by_digest: Dict[str, List[str]] = defaultdict(list)
            for m in metas:
                by_digest[m["digest"]].append(m["stem"])
            mixed_groups.append({
                "base_title": base,
                "clusters": [{"digest": d, "versions": sorted(vs)} for d, vs in by_digest.items()],
                "status": "different",
            })

    return {
        "identical_groups": sorted(identical_groups, key=lambda x: x["base_title"]),
        "different_groups": sorted(mixed_groups, key=lambda x: x["base_title"]),
        "total_groups_with_versions": sum(1 for v in groups.values() if len(v) > 1),
    }


def check_pairs(folder_old: str, folder_modern: str) -> Dict:
    idx_old = index_folder(folder_old, normalize=True, collapse_ws=False)
    idx_modern = index_folder(folder_modern, normalize=True, collapse_ws=False)

    old_stems = set(idx_old.keys())
    modern_stems = set(idx_modern.keys())

    # Exact filename matches
    exact_pairs = sorted(old_stems & modern_stems)
    missing_in_modern = sorted(old_stems - modern_stems)
    missing_in_old = sorted(modern_stems - old_stems)

    # Base-stem matches (ignore (n))
    old_base_to_stems: Dict[str, List[str]] = defaultdict(list)
    for stem, meta in idx_old.items():
        old_base_to_stems[meta["base_stem"]].append(stem)
    modern_base_to_stems: Dict[str, List[str]] = defaultdict(list)
    for stem, meta in idx_modern.items():
        modern_base_to_stems[meta["base_stem"]].append(stem)

    base_keys_old = set(old_base_to_stems.keys())
    base_keys_modern = set(modern_base_to_stems.keys())
    base_pairs = sorted(base_keys_old & base_keys_modern)
    base_missing_in_modern = sorted(base_keys_old - base_keys_modern)
    base_missing_in_old = sorted(base_keys_modern - base_keys_old)

    return {
        "exact_pairs_count": len(exact_pairs),
        "exact_pairs_sample": exact_pairs[:50],
        "missing_in_modern_count": len(missing_in_modern),
        "missing_in_modern_sample": missing_in_modern[:50],
        "missing_in_old_count": len(missing_in_old),
        "missing_in_old_sample": missing_in_old[:50],
        "base_pairs_count": len(base_pairs),
        "base_missing_in_modern_count": len(base_missing_in_modern),
        "base_missing_in_modern_sample": base_missing_in_modern[:50],
        "base_missing_in_old_count": len(base_missing_in_old),
        "base_missing_in_old_sample": base_missing_in_old[:50],
    }


def main(argv: List[str]) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Check (n) version duplicates in 고문서 and verify 고문서-번역본 filename pairs.\n"
            "This script DOES NOT modify any files."
        )
    )
    parser.add_argument("old_folder", help="Path to '데이터셋 제작2/고문서'")
    parser.add_argument("modern_folder", help="Path to '데이터셋 제작2/번역본'")
    parser.add_argument("--collapse-ws", action="store_true", help="Collapse whitespace when comparing contents")
    parser.add_argument("--no-nfc", action="store_true", help="Disable NFC normalization when comparing contents")
    parser.add_argument("--json", dest="as_json", action="store_true", help="Print full JSON reports")

    args = parser.parse_args(argv)

    if not os.path.isdir(args.old_folder):
        print(f"Old folder not found: {args.old_folder}", file=sys.stderr)
        return 1
    if not os.path.isdir(args.modern_folder):
        print(f"Modern folder not found: {args.modern_folder}", file=sys.stderr)
        return 1

    version_report = compare_versions_in_old(
        args.old_folder,
        normalize=not args.no_nfc,
        collapse_ws=args.collapse_ws,
    )

    pair_report = check_pairs(args.old_folder, args.modern_folder)

    if args.as_json:
        print(json.dumps({
            "version_report": version_report,
            "pair_report": pair_report,
        }, ensure_ascii=False, indent=2))
    else:
        print("== 고문서 (n) 버전 비교 ==")
        print(f"그룹 수(버전>1): {version_report['total_groups_with_versions']}")
        print(f"완전 동일 그룹 수: {len(version_report['identical_groups'])}")
        print(f"내용 상이 그룹 수: {len(version_report['different_groups'])}")
        if version_report["identical_groups"]:
            sample = version_report["identical_groups"][:10]
            print("-- 동일 그룹 예시 최대 10건 --")
            for g in sample:
                print(f"  {g['base_title']}: {', '.join(g['versions'])}")
        if version_report["different_groups"]:
            sample = version_report["different_groups"][:10]
            print("-- 상이 그룹 예시 최대 10건 --")
            for g in sample:
                clusters = [f"[{len(c['versions'])}개]" for c in g["clusters"]]
                print(f"  {g['base_title']}: 클러스터 {', '.join(clusters)}")

        print("\n== 고문서-번역본 파일명 매칭 ==")
        print(f"정확 일치 쌍 수: {pair_report['exact_pairs_count']}")
        if pair_report["exact_pairs_sample"]:
            print("-- 정확 일치 예시 최대 50건 --")
            for s in pair_report["exact_pairs_sample"]:
                print(f"  {s}")
        print(f"번역본에 누락된(정확파일명) 수: {pair_report['missing_in_modern_count']}")
        if pair_report["missing_in_modern_sample"]:
            for s in pair_report["missing_in_modern_sample"]:
                print(f"  - {s}")
        print(f"고문서에 누락된(정확파일명) 수: {pair_report['missing_in_old_count']}")
        if pair_report["missing_in_old_sample"]:
            for s in pair_report["missing_in_old_sample"]:
                print(f"  - {s}")

        print("\n-- (참고) 버전 무시한 기본 제목 기준 --")
        print(f"기본 제목 일치 수: {pair_report['base_pairs_count']}")
        print(f"번역본에 누락된(기본제목) 수: {pair_report['base_missing_in_modern_count']}")
        print(f"고문서에 누락된(기본제목) 수: {pair_report['base_missing_in_old_count']}")

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))


