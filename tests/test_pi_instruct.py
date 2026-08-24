#!/usr/bin/env python3
import json
import shutil
import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).parents[1] / "pi-instruct.py"


def run(*args):
    return subprocess.run([sys.executable, str(SCRIPT), *args], text=True, capture_output=True)


def test_install_status_conflict_and_uninstall(tmp_path):
    pi = tmp_path / "agent"
    dry = run("--pi-dir", str(pi), "--preset", "contract")
    assert dry.returncode == 0
    assert not (pi / "APPEND_SYSTEM.md").exists()

    installed = run("--pi-dir", str(pi), "--preset", "contract", "--yes")
    assert installed.returncode == 0
    assert (pi / "APPEND_SYSTEM.md").is_file()
    assert run("--pi-dir", str(pi), "--status").stdout.startswith("active:")

    (pi / "APPEND_SYSTEM.md").write_text("changed\n", encoding="utf-8")
    conflict = run("--pi-dir", str(pi), "--uninstall", "--yes")
    assert conflict.returncode == 1
    assert json.loads((pi / ".pi-keysmith-manifest.json").read_text())["target"] == "APPEND_SYSTEM.md"

    shutil.copyfile(
        Path(__file__).parents[1] / "examples/gpt-contract.md",
        pi / "APPEND_SYSTEM.md",
    )
    assert run("--pi-dir", str(pi), "--uninstall", "--yes").returncode == 0
    assert not (pi / ".pi-keysmith-manifest.json").exists()


if __name__ == "__main__":
    import tempfile

    with tempfile.TemporaryDirectory() as directory:
        test_install_status_conflict_and_uninstall(Path(directory))
    print("ok")
