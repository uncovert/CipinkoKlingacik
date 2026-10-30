# v0.1.0-alpha.1 — engineering-prototype prerelease

This is a public-source/design handoff of **ČipinkoKlingáčik C3**, not a qualified
PCBA product. Mark it as a **GitHub prerelease**, not a stable/production release.
Firmware and SWD synchronization are not implemented. Hardware has not been built
or measured; supplier, stackup, rotation, socket/USB and thermal/transient gates
remain open. All safety/measurement limits in DESIGN.md and VALIDATION.md apply.

## Included

Editable KiCad sources and pinned libraries; exact candidate parts/population;
strict check reports and hashes; baseline engineering-prototype manufacturing
data; illustrated assembly views; build/verification tools and tests; licences.
No obsolete design variants, one-shot repair scripts, private review transcripts,
downloaded manufacturer PDFs, virtual environments or temporary boards are bundled.

## Prepare an asset locally

```sh
python3 scripts/package_release.py
```

The output is `dist/cipinkoklingacik-v0.1.0-alpha.1.zip` and `dist/SHA256SUMS`.
The ZIP has a single versioned root and an internal SHA-256 inventory. The script
verifies metadata, fresh report/export/render hashes and documentation/licensing,
then runs all tests. It does not run fresh KiCad; do the full BUILD.md sequence
after hardware edits. Packaging never creates a remote repository or publishes.

## Publish manually when ready

1. Review the contents/licences and static/physical qualification distinction.
2. Run tests and packaging; inspect the archive and checksum inventory.
3. Commit to the local `main` branch and create your GitHub repository using the
   ASCII name **`cipinkoklingacik`**. Set the display name to **ČipinkoKlingáčik**.
4. Configure your chosen remote, push the commit and tag `v0.1.0-alpha.1`.
5. Create a **prerelease**, attach the ZIP and SHA256SUMS, and use these notes.

No GitHub owner/remote, commit, tag or publication is assumed by these files.
CI checks repository/export consistency and packages an artifact; without KiCad
it does **not** claim a new ERC/DRC or hardware qualification result.
