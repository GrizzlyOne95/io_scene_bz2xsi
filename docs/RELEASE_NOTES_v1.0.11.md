# Battlezone II XSI Importer / Exporter v1.0.11

## Summary

v1.0.11 is a documentation and release-process update built from the same runtime code as v1.0.10.

It records the current Blender Extensions migration status, documents the unresolved upstream software-license question, and aligns the public documentation with the repository's merge-triggered release workflow.

## Runtime

There are no intentional importer/exporter behavior changes in this release compared with v1.0.10.

The Blender 5.x, animation, skinning, PAK, parser/writer, exporter, material, and texture fixes from v1.0.10 remain included.

## Blender Extensions migration

A migration to Blender's current Extensions format is in progress, with a future **v1.1.0** targeted as the first Extension-format release.

The original upstream project is:

- `frute94/io_scene_bz2xsi`

At the time of this release, the upstream repository does not declare a software license in a root license file, README, or inspected source headers, and GitHub reports no detected license.

Because this fork contains and modifies that upstream code, this project is not assigning a new license to the inherited code without an explicit license grant from the original copyright holder.

Until that is clarified, public releases remain in Blender's legacy add-on ZIP format.

## Release automation

Releases are now published by merging a `release/*` pull request into `main`.

The workflow:

- derives the release version from `bl_info["version"]`;
- validates the matching release-notes file;
- creates the `vX.Y.Z` tag;
- byte-compiles the runtime Python files;
- builds and verifies the Blender add-on ZIP;
- uploads the workflow artifact; and
- publishes the GitHub Release.

Tag pushes and manual workflow dispatch remain available as fallback release paths.

## Compatibility

- Add-on metadata requires **Blender 4.1+**.
- Blender 4.4+/5.x layered Actions are supported.
- The last full regression run was performed with **Blender 5.2**.
- The planned Blender Extension package will target **Blender 4.2+** once licensing is resolved.

## Installation

1. Download `io_scene_bz2xsi-v1.0.11.zip` from this release.
2. In Blender, open **Edit > Preferences > Add-ons**.
3. Choose **Install from Disk** and select the ZIP.
4. Enable **BZ2 XSI format**.
5. Use **File > Import > BZ2 XSI / PAK** or **File > Export > BZ2 XSI**.
