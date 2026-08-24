# Pi Keysmith

`pi-instruct.py` is the Pi adapter for this repository. It deploys a Markdown prompt to Pi's global append hook:

```text
~/.pi/agent/APPEND_SYSTEM.md
```

This preserves Pi's built-in system prompt, tools, context files, skills, and extensions. It does not modify `settings.json`, `auth.json`, sessions, or installed packages.

## Usage

```bash
python3 pi-instruct.py --pi-dir ~/.pi/agent --status
python3 pi-instruct.py --pi-dir ~/.pi/agent --preset contract
python3 pi-instruct.py --pi-dir ~/.pi/agent --preset contract --yes
python3 pi-instruct.py --pi-dir ~/.pi/agent --uninstall --yes
```

Use `--file ./my-prompt.md` for a custom prompt. Every write is preview-only unless `--yes` is supplied. Existing `APPEND_SYSTEM.md` is backed up and restored by uninstall. If the managed file changes after installation, the tool refuses to overwrite or uninstall it.

After installation, restart Pi or run `/reload`.
