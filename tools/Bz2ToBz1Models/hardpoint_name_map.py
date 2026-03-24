"""Infer BZ1 legacy GEO hardpoint roles from common BZ2 helper names.

This is intentionally conservative. Names with no clean BZ1 analogue are
reported as ambiguous instead of being forced into a role that is likely wrong.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable
import argparse
import re
import sys


GEO_NONE = 0
GEO_HEADLIGHT_MASK = 38
GEO_EYEPOINT = 40
GEO_COM = 42
GEO_COCKPIT_GEOMETRY = 69
GEO_WEAPON_HARDPOINT = 70
GEO_CANNON_HARDPOINT = 71
GEO_ROCKET_HARDPOINT = 72
GEO_MORTAR_HARDPOINT = 73
GEO_SPECIAL_HARDPOINT = 74
GEO_FLAME_EMITTER = 75
GEO_SMOKE_EMITTER = 76
GEO_DUST_EMITTER = 77


@dataclass(frozen=True)
class MappingResult:
    name: str
    geo_type: int | None
    confidence: str
    reason: str


def _normalize_tokens(name: str) -> list[str]:
    normalized = re.sub(r"[^a-z0-9]+", "_", name.strip().lower()).strip("_")
    return [token for token in normalized.split("_") if token]


def infer_geo_type(name: str) -> MappingResult:
    tokens = _normalize_tokens(name)
    token_set = set(tokens)
    lower = name.strip().lower()

    if not tokens:
        return MappingResult(name, None, "none", "empty name")

    if "eyepoint" in token_set or lower.startswith("hp_eyepoint"):
        return MappingResult(name, GEO_EYEPOINT, "high", "BZ2 eyepoint maps cleanly to legacy EYEPOINT")

    if "com" in token_set or lower.startswith("hp_com"):
        return MappingResult(name, GEO_COM, "high", "center-of-mass helper")

    if "cockpit" in token_set:
        return MappingResult(name, GEO_COCKPIT_GEOMETRY, "medium", "cockpit helper/mesh")

    if "cannon" in token_set:
        return MappingResult(name, GEO_CANNON_HARDPOINT, "high", "named cannon hardpoint")

    if "rocket" in token_set:
        return MappingResult(name, GEO_ROCKET_HARDPOINT, "high", "named rocket hardpoint")

    if "mortar" in token_set:
        return MappingResult(name, GEO_MORTAR_HARDPOINT, "high", "named mortar hardpoint")

    if "special" in token_set:
        return MappingResult(name, GEO_SPECIAL_HARDPOINT, "high", "named special hardpoint")

    if "gun" in token_set or "weapon" in token_set:
        return MappingResult(name, GEO_WEAPON_HARDPOINT, "high", "named generic weapon hardpoint")

    if "shield" in token_set or "hand" in token_set or "pack" in token_set:
        return MappingResult(
            name,
            GEO_SPECIAL_HARDPOINT,
            "medium",
            "BZ2 inventory slot has no direct BZ1 type; SPECIAL_HARDPOINT is the closest catchall",
        )

    if "powerup" in token_set or "vehicle" in token_set or "spray" in token_set:
        return MappingResult(
            name,
            GEO_SPECIAL_HARDPOINT,
            "low",
            "no direct BZ1 equivalent; SPECIAL_HARDPOINT is the least-wrong fallback",
        )

    if "fire" in token_set or "flame" in token_set or lower.startswith("flame_"):
        return MappingResult(name, GEO_FLAME_EMITTER, "high", "named flame/fire emitter")

    if "dust" in token_set:
        return MappingResult(name, GEO_DUST_EMITTER, "high", "named dust emitter")

    if "smoke" in token_set or "trail" in token_set or "emit" in token_set:
        return MappingResult(
            name,
            GEO_SMOKE_EMITTER,
            "medium",
            "generic particle anchor; smoke is the safer default than dust",
        )

    if "light" in token_set:
        return MappingResult(
            name,
            GEO_HEADLIGHT_MASK,
            "medium",
            "user-selected default: map BZ2 hp_light helpers to GEO 38 HEADLIGHT_MASK",
        )

    if tokens[0] == "hp":
        return MappingResult(
            name,
            GEO_WEAPON_HARDPOINT,
            "low",
            "generic hp_* helper with no subtype; defaulting to generic weapon hardpoint",
        )

    return MappingResult(name, None, "none", "no known hardpoint/emitter pattern")


def iter_results(names: Iterable[str]) -> Iterable[MappingResult]:
    for name in names:
        stripped = name.strip()
        if stripped:
            yield infer_geo_type(stripped)


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Infer legacy BZ1 GEO hardpoint roles from BZ2 helper names."
    )
    parser.add_argument("names", nargs="*", help="Helper names to classify")
    parser.add_argument(
        "--tsv",
        action="store_true",
        help="Emit tab-separated output: name, geo_type, confidence, reason",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_arg_parser()
    args = parser.parse_args(argv)

    names = list(args.names)
    if not names:
        names = [line.rstrip("\r\n") for line in sys.stdin]

    results = list(iter_results(names))
    if args.tsv:
        for result in results:
            geo_type = "" if result.geo_type is None else str(result.geo_type)
            print(f"{result.name}\t{geo_type}\t{result.confidence}\t{result.reason}")
    else:
        for result in results:
            geo_label = "unmapped" if result.geo_type is None else f"GEO {result.geo_type}"
            print(f"{result.name}: {geo_label} [{result.confidence}] {result.reason}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
