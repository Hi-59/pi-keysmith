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

  pi.registerCommand("keysmith-on", {
    description: "Enable the Pi Keysmith prompt for this session",
    handler: (_args, ctx) => {
      enabled = true;
      ctx.ui.notify("Pi Keysmith enabled for this session", "info");
    },
  });

  pi.registerCommand("keysmith-off", {
    description: "Disable the Pi Keysmith prompt for this session",
    handler: (_args, ctx) => {
      enabled = false;
      ctx.ui.notify("Pi Keysmith disabled for this session", "info");
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

  pi.on("input", (_event, ctx) => {
    const text = _event.text.trim();
    if (text === "感受未来") {
      enabled = true;
      ctx.ui.notify("Pi Keysmith enabled for this session", "info");
      return { action: "handled" };
    }
    if (text === "回到现在") {
      enabled = false;
      ctx.ui.notify("Pi Keysmith disabled for this session", "info");
      return { action: "handled" };
    }
    return { action: "continue" };
  });

  pi.on("before_agent_start", (event) => {
    const prompt = promptText();
    if (!prompt) return undefined;

    const withoutPrompt = event.systemPrompt.split(prompt).join("").trim();
    return {
      systemPrompt: enabled ? `${withoutPrompt}\n\n${prompt}` : withoutPrompt,
    };
  });
}
