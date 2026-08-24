#!/usr/bin/env python3
"""Deploy a managed global prompt append file for Pi.

Pi loads ~/.pi/agent/APPEND_SYSTEM.md after its built-in system prompt. This
small adapter deliberately does not modify settings, auth, sessions, or
extensions.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

VERSION = "0.1.0"
MANIFEST = ".pi-keysmith-manifest.json"
DEFAULT_TARGET = "APPEND_SYSTEM.md"
PRESETS = {"unrestricted": "examples/gpt-unrestricted.md", "contract": "examples/gpt-contract.md"}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def pi_dir(value: str | None) -> Path:
    return Path(value or os.environ.get("PI_CODING_AGENT_DIR", "~/.pi/agent")).expanduser().resolve()


def source_path(value: str | None, preset: str) -> Path:
    if value:
        path = Path(value).expanduser().resolve()
        if not path.is_file():
            raise ValueError(f"prompt file not found: {path}")
        return path
    path = Path(__file__).resolve().parent / PRESETS[preset]
    if not path.is_file():
        raise ValueError(f"bundled prompt not found: {path}")
    return path


def backup_name(path: Path) -> Path:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return path.with_name(f"{path.name}.bak_{stamp}")


def atomic_copy(source: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=f".{target.name}.", dir=target.parent)
    os.close(fd)
    temporary = Path(name)
    try:
        shutil.copyfile(source, temporary)
        os.replace(temporary, target)
    finally:
        temporary.unlink(missing_ok=True)


def load_manifest(root: Path) -> dict | None:
    path = root / MANIFEST
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"invalid manifest: {path}: {exc}") from exc
    if data.get("target") != DEFAULT_TARGET or not data.get("installed_sha256"):
        raise ValueError(f"invalid manifest: {path}")
    return data


def save_manifest(root: Path, data: dict) -> None:
    target = root / MANIFEST
    temporary = target.with_name(f".{target.name}.tmp")
    temporary.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    os.replace(temporary, target)


def install(args: argparse.Namespace) -> int:
    root = pi_dir(args.pi_dir)
    source = source_path(args.file, args.preset)
    target = root / DEFAULT_TARGET
    manifest = load_manifest(root)
    current = sha256(target) if target.is_file() and not target.is_symlink() else None
    if manifest and (current is None or current not in (manifest["installed_sha256"], manifest.get("previous_sha256"))):
        raise ValueError(f"target changed outside Pi Keysmith: {target}")

    backup = backup_name(target) if target.exists() else None
    print(f"Pi directory: {root}")
    print(f"Prompt source: {source}")
    print(f"Write: {target}")
    if backup:
        print(f"Backup: {backup}")
    if not args.yes:
        print("Dry run only; pass --yes to write.")
        return 0

    root.mkdir(parents=True, exist_ok=True)
    if target.exists():
        if target.is_symlink() or not target.is_file():
            raise ValueError(f"target is not a regular file: {target}")
        if backup is None:
            raise ValueError(f"backup path missing for existing target: {target}")
        shutil.copy2(target, backup)
    atomic_copy(source, target)
    save_manifest(root, {
        "version": 1,
        "target": DEFAULT_TARGET,
        "installed_sha256": sha256(target),
        "previous_sha256": current,
        "backup": backup.name if backup else None,
        "source": str(source),
    })
    print("Installed. Restart Pi or use /reload.")
    return 0


def status(args: argparse.Namespace) -> int:
    root = pi_dir(args.pi_dir)
    target = root / DEFAULT_TARGET
    manifest = load_manifest(root)
    if not manifest:
        print(f"not-installed: {root}")
        return 0
    if target.is_symlink() or not target.is_file():
        print(f"conflict: managed prompt is missing or not regular: {target}")
        return 1
    current = sha256(target)
    if current != manifest["installed_sha256"]:
        print(f"conflict: managed prompt changed: {target}")
        return 1
    print(f"active: {target}")
    print(f"sha256: {current}")
    return 0


def uninstall(args: argparse.Namespace) -> int:
    root = pi_dir(args.pi_dir)
    target = root / DEFAULT_TARGET
    manifest = load_manifest(root)
    if not manifest:
        print("not-installed: nothing to uninstall")
        return 0
    if target.is_symlink() or not target.is_file() or sha256(target) != manifest["installed_sha256"]:
        raise ValueError(f"managed prompt changed; refusing to uninstall: {target}")
    backup = root / manifest["backup"] if manifest.get("backup") else None
    print(f"Remove: {target}")
    if backup:
        print(f"Restore: {backup}")
    if not args.yes:
        print("Dry run only; pass --yes to write.")
        return 0
    if backup and backup.is_file():
        atomic_copy(backup, target)
    else:
        target.unlink()
    (root / MANIFEST).unlink()
    print("Uninstalled.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Install a managed global prompt append file for Pi.")
    parser.add_argument("--pi-dir", help="Pi config directory (default: PI_CODING_AGENT_DIR or ~/.pi/agent)")
    parser.add_argument("--file", help="external Markdown prompt")
    parser.add_argument("--preset", choices=sorted(PRESETS), default="unrestricted")
    parser.add_argument("--yes", action="store_true", help="apply the planned changes")
    parser.add_argument("--status", action="store_true")
    parser.add_argument("--uninstall", action="store_true")
    parser.add_argument("--version", action="version", version=VERSION)
    args = parser.parse_args()
    try:
        if args.status and (args.file or args.yes or args.uninstall):
            parser.error("--status cannot be combined with --file, --yes, or --uninstall")
        if args.uninstall and (args.file or args.preset != "unrestricted"):
            parser.error("--uninstall cannot be combined with --file or --preset")
        if args.status:
            return status(args)
        if args.uninstall:
            return uninstall(args)
        return install(args)
    except (OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
