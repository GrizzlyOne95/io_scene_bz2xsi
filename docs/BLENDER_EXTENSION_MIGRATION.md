# Blender Extensions Migration

## Status

Technical migration has started. The runtime code is already in unusually good shape for Blender Extensions:

- Internal imports are package-relative.
- There are no add-on preferences keyed to a hard-coded module name.
- PAK cache data defaults to the system temporary directory rather than the installed add-on directory.
- User-selected import/export and converted-texture paths remain external to the package.

The remaining hard blocker is **software licensing**.

## Upstream provenance and license finding

This repository is a GitHub fork of:

- https://github.com/frute94/io_scene_bz2xsi

The upstream repository currently has:

- no `LICENSE`, `LICENSE.txt`, or `COPYING` file;
- no license declaration in its README;
- no license header in the inspected Python source files;
- no license-related issue or commit found in the upstream repository;
- GitHub repository metadata reporting no detected license.

Because the current repository contains and modifies that upstream code, this project should not unilaterally declare the inherited code GPL-3.0-or-later (or another open-source license) without permission from the upstream copyright holder.

This specifically blocks publication to **extensions.blender.org**, which requires add-ons to be GPL-3.0-or-later.

## Migration target

The intended first Extension release is **v1.1.0** with:

- Extension ID: `io_scene_bz2xsi`
- Type: `add-on`
- Minimum Blender: **4.2.0**
- Tag: `Import-Export`
- File-system permission for importing/exporting assets and converted textures
- GitHub repository as the project website
- Blender's native Extension build/validation commands

The existing v1.0.10 legacy release remains the stable fallback while this work is completed.

## Files added in this migration

### `blender_manifest.toml.in`

Contains all known Extension metadata except the unresolved software-license identifier.

It is deliberately a template rather than a checked-in `blender_manifest.toml`. A real manifest should only be generated after the upstream-derived source has an explicit license.

### `tools/extension_manifest.py`

Generates a real `blender_manifest.toml` from the template.

It requires an explicit SPDX identifier and refuses placeholder values such as `UNKNOWN` or `NOASSERTION`.

Example after licensing is resolved:

```bash
python tools/extension_manifest.py --license GPL-3.0-or-later --version 1.1.0
```

### `tools/build_extension.py`

Stages the runtime files, generates the manifest, and delegates packaging and validation to Blender:

```bash
python tools/build_extension.py \
  --blender /path/to/blender \
  --license GPL-3.0-or-later \
  --version 1.1.0
```

Internally this runs Blender's native:

```text
blender --command extension validate
blender --command extension build
blender --command extension validate <package.zip>
```

The generated ZIP is written to `dist/`.

## Finalization work after upstream licensing is clarified

1. Record the granted/upstream license in the repository, including the license text when required.
2. Replace `blender_manifest.toml.in` with the final `blender_manifest.toml`.
3. Remove the manifest-generation license argument and make the manifest the canonical version source.
4. Decide whether to keep `bl_info` for dual legacy/Extension installation or remove it for Extension-only releases.
5. Update the release workflow to build with Blender's Extension CLI instead of manually zipping legacy add-on files.
6. Install the generated ZIP through **Get Extensions > Install from Disk** and run the importer/exporter regression suite in that installed namespace.
7. Publish v1.1.0 on GitHub.
8. Optionally submit to extensions.blender.org if the resulting license satisfies Blender's catalog requirements.

## Upstream request needed

The cleanest resolution is for the original author to add an explicit license to `frute94/io_scene_bz2xsi`, or otherwise provide a clear license grant covering the existing source.

Until then, the migration branch should be treated as engineering preparation rather than a redistributable Blender Extension release.
