"""Generate the Blender Extensions manifest after licensing is resolved.

The upstream project (frute94/io_scene_bz2xsi) currently has no declared
software license. This tool therefore requires an explicit SPDX identifier
instead of silently assigning one.
"""

from __future__ import annotations

import argparse
import ast
import re
import tomllib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "blender_manifest.toml.in"
SEMVER_RE = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+(?:[-+][0-9A-Za-z.-]+)?$")
SPDX_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9.+-]*$")


def addon_version() -> str:
    tree = ast.parse((ROOT / "__init__.py").read_text(encoding="utf-8"))
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        if not any(isinstance(target, ast.Name) and target.id == "bl_info" for target in node.targets):
            continue
        info = ast.literal_eval(node.value)
        return ".".join(str(part) for part in info["version"])
    raise RuntimeError("bl_info version not found in __init__.py")


def render_manifest(version: str, license_id: str) -> str:
    if not SEMVER_RE.fullmatch(version):
        raise ValueError(f"invalid semantic version: {version!r}")

    license_id = license_id.removeprefix("SPDX:")
    if not SPDX_ID_RE.fullmatch(license_id):
        raise ValueError(f"invalid SPDX identifier: {license_id!r}")

    if license_id.casefold() in {"unknown", "noassertion", "none"}:
        raise ValueError("an explicit software license is required")

    text = TEMPLATE.read_text(encoding="utf-8")
    text = text.replace("@VERSION@", version).replace("@LICENSE@", license_id)
    if "@VERSION@" in text or "@LICENSE@" in text:
        raise RuntimeError("manifest template contains unresolved placeholders")

    parsed = tomllib.loads(text)
    if parsed["version"] != version:
        raise RuntimeError("rendered manifest version mismatch")
    if parsed["license"] != [f"SPDX:{license_id}"]:
        raise RuntimeError("rendered manifest license mismatch")
    return text


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--license",
        required=True,
        help="SPDX license identifier established for the upstream-derived code",
    )
    parser.add_argument(
        "--version",
        default=None,
        help="Extension semantic version; defaults to bl_info version",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "blender_manifest.toml",
        help="Output manifest path",
    )
    args = parser.parse_args()

    version = args.version or addon_version()
    content = render_manifest(version, args.license)
    args.output.write_text(content, encoding="utf-8", newline="\n")
    print(f"Wrote {args.output} for version {version}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
