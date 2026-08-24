import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";
import { readFileSync } from "node:fs";
import { homedir } from "node:os";
import { join } from "node:path";

const PROMPT_PATH = join(
  process.env.PI_CODING_AGENT_DIR || join(homedir(), ".pi", "agent"),
  "APPEND_SYSTEM.md",
);

function promptText(): string {
  try {
    return readFileSync(PROMPT_PATH, "utf8").trim();
  } catch {
    return "";
  }
}

export default function keysmithToggle(pi: ExtensionAPI) {
  let enabled = true;
  let testPending = false;

  const setState = (next: boolean, ctx: any) => {
    enabled = next;
    ctx.ui.setStatus("pi-keysmith", next ? "未来已至" : "已到现实");
    ctx.ui.notify(next ? "未来已至" : "已到现实", "info");
  };

  pi.registerCommand("keysmith-on", {
    description: "Enable the Pi Keysmith prompt for this session",
    handler: (_args, ctx) => {
      setState(true, ctx);
    },
  });

  pi.registerCommand("keysmith-off", {
    description: "Disable the Pi Keysmith prompt for this session",
    handler: (_args, ctx) => {
      setState(false, ctx);
    },
  });

  pi.registerCommand("keysmith-status", {
    description: "Show the Pi Keysmith prompt state",
    handler: (_args, ctx) => {
      ctx.ui.notify(
        `Pi Keysmith ${enabled ? "enabled" : "disabled"} (${PROMPT_PATH})`,
        "info",
      );
    },
  });

  pi.registerCommand("keysmith-test", {
    description: "Verify the managed prompt without changing it",
    handler: (_args, ctx) => {
      if (!promptText()) {
        ctx.ui.notify(`未找到 APPEND_SYSTEM.md：${PROMPT_PATH}`, "error");
        return;
      }
      if (!enabled) {
        ctx.ui.notify("请先输入“感受未来”再测试", "warning");
        return;
      }
      testPending = true;
      ctx.ui.notify(
        "正在测试 Keysmith，等待模型回复 PI_KEYSMITH_ACTIVE",
        "info",
      );
      pi.sendUserMessage("PI_KEYSMITH_PROBE");
    },
  });

  pi.on("input", (_event, ctx) => {
    const text = _event.text.trim();
    if (text === "感受未来") {
      setState(true, ctx);
      return { action: "handled" };
    }
    if (text === "回到现在") {
      setState(false, ctx);
      return { action: "handled" };
    }
    return { action: "continue" };
  });

  pi.on("before_agent_start", (event) => {
    const prompt = promptText();
    if (!prompt) return undefined;

    const withoutPrompt = event.systemPrompt.split(prompt).join("").trim();
    const probe = testPending
      ? "\n\nKEYSMITH SELF-TEST: If the user message is exactly PI_KEYSMITH_PROBE, reply with exactly PI_KEYSMITH_ACTIVE and nothing else."
      : "";
    testPending = false;
    return {
      systemPrompt: enabled
        ? `${withoutPrompt}\n\n${prompt}${probe}`
        : withoutPrompt,
    };
  });
}
