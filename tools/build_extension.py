"""Build and validate the Blender Extension package.

This stages only runtime/user-facing files, generates blender_manifest.toml
from the template with an explicitly supplied SPDX license, then delegates
package creation and validation to Blender's Extension CLI.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import tempfile
from pathlib import Path

from extension_manifest import ROOT, addon_version, render_manifest


RUNTIME_FILES = (
    "__init__.py",
    "bz2xsi.py",
    "bz2pak.py",
    "softimage_pic.py",
    "xsi_blender_importer.py",
    "xsi_blender_exporter.py",
    "README.md",
    "Materials Readme.txt",
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--blender",
        default="blender",
        help="Blender executable (default: blender on PATH)",
    )
    parser.add_argument(
        "--license",
        required=True,
        help="SPDX identifier established for the upstream-derived code",
    )
    parser.add_argument(
        "--version",
        default=None,
        help="Extension semantic version; defaults to bl_info version",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=ROOT / "dist",
    )
    args = parser.parse_args()

    version = args.version or addon_version()
    manifest = render_manifest(version, args.license)
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    output_zip = output_dir / f"io_scene_bz2xsi-v{version}.zip"

    with tempfile.TemporaryDirectory(prefix="bz2xsi-extension-") as temp:
        stage = Path(temp) / "io_scene_bz2xsi"
        stage.mkdir()

        for name in RUNTIME_FILES:
            shutil.copy2(ROOT / name, stage / name)

        license_file = ROOT / "LICENSE"
        if license_file.is_file():
            shutil.copy2(license_file, stage / "LICENSE")

        (stage / "blender_manifest.toml").write_text(
            manifest,
            encoding="utf-8",
            newline="\n",
        )

        subprocess.run(
            [
                args.blender,
                "--command",
                "extension",
                "validate",
                str(stage),
            ],
            check=True,
        )
        subprocess.run(
            [
                args.blender,
                "--command",
                "extension",
                "build",
                "--source-dir",
                str(stage),
                "--output-filepath",
                str(output_zip),
            ],
            check=True,
        )
        subprocess.run(
            [
                args.blender,
                "--command",
                "extension",
                "validate",
                str(output_zip),
            ],
            check=True,
        )

    print(f"Built and validated {output_zip}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
