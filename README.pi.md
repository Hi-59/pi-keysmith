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

Agent-only deployment guide: [`docs/agent-deploy-pi.md`](docs/agent-deploy-pi.md).

## Session toggle

To switch the managed prompt without leaving the current Pi session, install the optional extension:

```bash
mkdir -p ~/.pi/agent/extensions
cp pi-keysmith-toggle.ts ~/.pi/agent/extensions/
```

In Pi, run `/reload` once. Then use either the normal input phrases or the slash commands:

```text
感受未来       # enable for this session
回到现在       # disable for this session
/keysmith-on
/keysmith-off
/keysmith-status
/keysmith-test
```

`/keysmith-test` 自动检查 `APPEND_SYSTEM.md` 并向模型发送一次性测试消息。正常结果是模型只回复 `PI_KEYSMITH_ACTIVE`；它不会替换正式提示词，也不需要手动恢复文件。

The two Chinese phrases are intercepted before the message reaches the model, so they do not become conversation messages. `/keysmith-on` and `/keysmith-off` affect the current session's system prompt on the next request. They do not edit `APPEND_SYSTEM.md`; uninstall remains the permanent switch. The extension starts enabled so existing deployments keep their current behavior.
