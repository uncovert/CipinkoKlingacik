#!/usr/bin/env python3
"""Verify and package a local engineering-prototype prerelease; never publish."""
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
from urllib.parse import unquote
import zipfile

ROOT = Path(__file__).resolve().parent.parent
ROOT_FILES = ("README.md", "CHANGELOG.md", "CONTRIBUTING.md", "LICENSE", "LICENSE-MIT",
              "NOTICE.md", "VERSION", ".gitignore", ".gitattributes", ".editorconfig")
DIRECTORIES = ("hardware", "docs", "reference", "scripts", "tests", ".github")


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def release_files():
    result = [ROOT / name for name in ROOT_FILES]
    for directory in DIRECTORIES:
        for path in (ROOT / directory).rglob("*"):
            if not path.is_file():
                continue
            if any(part in ("__pycache__", ".pytest_cache", ".venv") for part in path.parts):
                continue
            if path.suffix in (".pyc", ".pyo", ".kicad_prl") or path.name.startswith((".baseline-", ".pcba-visuals-", ".env")):
                continue
            if path.is_symlink():
                raise RuntimeError(f"Do not package symlinks: {path.relative_to(ROOT)}")
            result.append(path)
    return sorted(result, key=lambda p: p.relative_to(ROOT).as_posix())


def verify_repository():
    version = (ROOT / "VERSION").read_text().strip()
    if not re.fullmatch(r"\d+\.\d+\.\d+-alpha\.\d+", version):
        raise RuntimeError("This unqualified design must remain an explicitly alpha prerelease")
    for name in ROOT_FILES:
        if not (ROOT / name).is_file():
            raise RuntimeError(f"Missing release file: {name}")
    if "CERN Open Hardware Licence Version 2 - Permissive" not in (ROOT / "LICENSE").read_text():
        raise RuntimeError("Missing hardware licence")
    if "MIT License" not in (ROOT / "LICENSE-MIT").read_text():
        raise RuntimeError("Missing software/documentation licence")
    hw = ROOT / "hardware"
    status = json.loads((hw / "cipinkoklingacik-pcb-status.json").read_text())
    manufacturing = json.loads((hw / "manufacturing/manifest.json").read_text())
    for key, filename in (("board_sha256", "cipinkoklingacik.kicad_pcb"),
                          ("schematic_sha256", "cipinkoklingacik.kicad_sch"),
                          ("project_sha256", "cipinkoklingacik.kicad_pro"),
                          ("drc_sha256", "cipinkoklingacik-drc.json")):
        if status[key] != digest(hw / filename) or manufacturing[key] != status[key]:
            raise RuntimeError(f"Stale source/report binding: {filename}")
    drc = json.loads((hw / "cipinkoklingacik-drc.json").read_text())
    if any(drc[key] for key in ("violations", "unconnected_items", "schematic_parity", "ignored_checks")):
        raise RuntimeError("PCB check is not fully clean")
    if not re.search(r"ERC messages: 0\s+Errors 0\s+Warnings 0", (hw / "cipinkoklingacik-erc.rpt").read_text()):
        raise RuntimeError("ERC is not clean")
    if manufacturing["fabrication_release"] is not False or manufacturing["hardware_qualification"] != "NOT PERFORMED":
        raise RuntimeError("Prototype qualification/release state changed without review")
    for folder in ("manufacturing", "visuals"):
        manifest = json.loads((hw / folder / "manifest.json").read_text())
        for name, item in manifest["artifacts"].items():
            path = hw / folder / name
            if not path.is_file() or digest(path) != item["sha256"] or path.stat().st_size != item["bytes"]:
                raise RuntimeError(f"Stale {folder} artifact: {name}")
    files = release_files()
    for path in files:
        relative = path.relative_to(ROOT).as_posix()
        if "glitchpico" in relative.lower() or path.suffix in (".dsn", ".ses"):
            raise RuntimeError(f"Retired name/intermediate in release: {relative}")
        if path.suffix in (".md", ".py", ".json", ".csv", ".net", ".kicad_sch", ".kicad_pro", ".kicad_pcb", ".kicad_sym"):
            text = path.read_text()
            if re.search(r"/(?:home|tmp)/[^\s\"<>]+", text):
                raise RuntimeError(f"Local machine path in release: {relative}")
        if path.suffix == ".md":
            for target in re.findall(r"\]\(([^)]+)\)", path.read_text()):
                if target.startswith(("http://", "https://", "#", "mailto:")):
                    continue
                target = unquote(target.split("#", 1)[0])
                if target and not (path.parent / target).exists():
                    raise RuntimeError(f"Broken Markdown link: {relative} -> {target}")
    return version, files


def main():
    version, files = verify_repository()
    subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"], cwd=ROOT, check=True)
    out = ROOT / "dist"
    out.mkdir(exist_ok=True)
    name = "cipinkoklingacik-v" + version
    target = out / (name + ".zip")
    sums = "".join(f"{digest(path)}  {path.relative_to(ROOT).as_posix()}\n" for path in files)
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in files:
            info = zipfile.ZipInfo(name + "/" + path.relative_to(ROOT).as_posix(), date_time=(2026, 10, 30, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, path.read_bytes())
        info = zipfile.ZipInfo(name + "/SHA256SUMS", date_time=(2026, 10, 30, 0, 0, 0))
        info.compress_type = zipfile.ZIP_DEFLATED
        info.external_attr = 0o100644 << 16
        archive.writestr(info, sums.encode())
    (out / "SHA256SUMS").write_text(f"{digest(target)}  {target.name}\n")
    print(f"Packaged {len(files)} files: {target.relative_to(ROOT)}")
    print("Local alpha package only. No remote publication or hardware qualification performed.")


if __name__ == "__main__":
    main()
