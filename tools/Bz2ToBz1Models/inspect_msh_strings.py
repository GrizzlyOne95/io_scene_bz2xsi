"""Extract likely helper and animation names from BZ2/BZCC .msh binaries.

Useful when a full structural parser fails on variant mesh blocks.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path


PRINTABLE_RE = re.compile(rb"[\x20-\x7E]{4,}")
HELPER_RE = re.compile(r"\bhp_[a-z0-9_]+\b", re.IGNORECASE)
ANIM_RE = re.compile(
    r"\b(idle|walk|run|eat\d*|attack\d*|death\d*|die\d*|jump\d*|turn[a-z0-9_]*|stand\d*)\b",
    re.IGNORECASE,
)


def extract_ascii_strings(data: bytes) -> list[str]:
    seen: set[str] = set()
    strings: list[str] = []
    for match in PRINTABLE_RE.finditer(data):
        text = match.group().decode("ascii", "ignore")
        if text not in seen:
            seen.add(text)
            strings.append(text)
    return strings


def inspect_file(path: Path) -> dict[str, object]:
    data = path.read_bytes()
    strings = extract_ascii_strings(data)
    helpers = [s for s in strings if HELPER_RE.search(s)]
    anims = [s for s in strings if ANIM_RE.search(s)]
    return {
        "path": str(path),
        "size": len(data),
        "helpers": helpers,
        "animations": anims,
        "all_strings": strings,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Inspect .msh printable strings for helpers and animation names.")
    parser.add_argument("paths", nargs="+", help="Paths to .msh files")
    parser.add_argument("--show-all", action="store_true", help="Also print all extracted printable strings")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    for raw_path in args.paths:
        path = Path(raw_path)
        result = inspect_file(path)
        print(f"FILE {result['path']}")
        print(f"size={result['size']}")
        print("helpers:")
        for helper in result["helpers"]:
            print(f"  {helper}")
        print("animations:")
        for anim in result["animations"]:
            print(f"  {anim}")
        if args.show_all:
            print("strings:")
            for text in result["all_strings"]:
                print(f"  {text}")
        print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
