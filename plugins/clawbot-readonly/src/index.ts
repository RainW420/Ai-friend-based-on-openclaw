import { Type } from "typebox";
import { definePluginEntry } from "openclaw/plugin-sdk/plugin-entry";
import type { Dirent } from "node:fs";
import { readdir, readFile, stat } from "node:fs/promises";
import { readFileSync, writeFileSync, appendFileSync } from "node:fs";
import path from "node:path";

const HOME_DIR = process.env.HOME ?? "";
const PROJECT_ROOT = process.env.CLAWBOT_PROJECT_ROOT ?? path.resolve(process.cwd(), "../..");
const CONFIG_PATH = process.env.OPENCLAW_CONFIG ?? path.join(HOME_DIR, ".openclaw", "openclaw.json");
const ASSISTANT_LABEL = process.env.CLAWBOT_PERSONA_LABEL ?? "Companion";
const ROUTING_INJECTION_PATH = path.join(PROJECT_ROOT, "workspace", "clawbot", "memory", "latest-routing-decision.json");
const ROUTING_INJECTION_MD = path.join(PROJECT_ROOT, "workspace", "clawbot", "memory", "latest-routing-decision.md");
const SYNC_LOG_PATH = path.join(PROJECT_ROOT, "logs", "dialogue-router-sync.jsonl");
const DEEPSEEK_API = "https://api.deepseek.com/v1/chat/completions";

type JsonObject = Record<string, unknown>;
interface ChatEntry { role: string; text: string; timestamp?: string; }

const HEARTBEAT_MARKER = "[OpenClaw heartbeat poll]";
const ROUTER_TIMEOUT_MS = 15_000;
const MAX_CONTEXT_ENTRIES = 8;

async function exists(fp: string) { try { await stat(fp); return true; } catch { return false; } }
function asObject(v: unknown): JsonObject { return v && typeof v === "object" && !Array.isArray(v) ? v as JsonObject : {}; }
function asStringArray(v: unknown): string[] { return Array.isArray(v) ? v.filter((i): i is string => typeof i === "string") : []; }

function readJsonSyncSafe(fp: string): JsonObject | null {
  try {
    return JSON.parse(readFileSync(fp, "utf8")) as JsonObject;
  } catch {
    return null;
  }
}

function readJsonlTailSyncSafe(fp: string, limit = 80): JsonObject[] {
  try {
    return readFileSync(fp, "utf8")
      .split(/\r?\n/)
      .filter(Boolean)
      .slice(-limit)
      .map((line) => {
        try {
          const parsed = JSON.parse(line);
          return parsed && typeof parsed === "object" && !Array.isArray(parsed) ? parsed as JsonObject : null;
        } catch {
          return null;
        }
      })
      .filter((item): item is JsonObject => item !== null);
  } catch {
    return [];
  }
}

async function listProjectTopLevel(): Promise<string[]> {
  const entries = await readdir(PROJECT_ROOT, { withFileTypes: true });
  return entries.filter((e: Dirent) => e.name !== ".openclaw").map((e: Dirent) => `${e.name}${e.isDirectory() ? "/" : ""}`).sort().slice(0, 50);
}

async function countClawbotMemoryFiles(): Promise<JsonObject> {
  const memoryRoot = path.join(PROJECT_ROOT, "workspace", "clawbot", "memory");
  const counts = { totalFilesExcludingDreams: 0, markdownFiles: 0, jsonFiles: 0 };

  async function walk(dir: string): Promise<void> {
    let entries: Dirent[];
    try {
      entries = await readdir(dir, { withFileTypes: true });
    } catch {
      return;
    }
    for (const entry of entries) {
      const full = path.join(dir, entry.name);
      if (full.includes(`${path.sep}.dreams${path.sep}`)) continue;
      if (entry.isDirectory()) {
        await walk(full);
      } else if (entry.isFile()) {
        counts.totalFilesExcludingDreams += 1;
        if (entry.name.endsWith(".md")) counts.markdownFiles += 1;
        if (entry.name.endsWith(".json")) counts.jsonFiles += 1;
      }
    }
  }

  await walk(memoryRoot);
  return { path: memoryRoot, ...counts };
}

function readHeartbeatSummary(): JsonObject {
  const config = readJsonSyncSafe(path.join(PROJECT_ROOT, "config", "clawbot-heartbeat-runner.json")) ?? {};
  const state = readJsonSyncSafe(path.join(PROJECT_ROOT, "workspace", "clawbot", "memory", "heartbeat-state.json")) ?? {};
  const events = readJsonlTailSyncSafe(path.join(PROJECT_ROOT, "logs", "heartbeat-runner.jsonl"), 120);
  const sent = events.filter((event) => event.sent === true);
  return {
    dryRun: config.dryRun ?? null,
    slots: Array.isArray(config.slots) ? config.slots.length : 0,
    lastCheckAt: state.lastCheckAt ?? null,
    lastProactiveSentAt: state.lastProactiveSentAt ?? null,
    consecutiveUnrepliedProactive: state.consecutiveUnrepliedProactive ?? null,
    lastLogDecision: events.length ? events[events.length - 1].decision ?? null : null,
    lastSentAt: sent.length ? sent[sent.length - 1].ts ?? null : null,
  };
}

function readAffectiveSummary(): JsonObject {
  const config = readJsonSyncSafe(path.join(PROJECT_ROOT, "config", "clawbot-dialogue-router.json")) ?? {};
  const ac = asObject(config.affectiveState);
  const statePath = String(ac.statePath ?? "workspace/clawbot/memory/affective-state.json");
  const state = readJsonSyncSafe(path.join(PROJECT_ROOT, statePath)) ?? {};
  return {
    enabled: ac.enabled ?? null,
    writeState: ac.writeState ?? null,
    injectToMainModel: ac.injectToMainModel ?? null,
    warmth: state.warmth ?? null,
    energy: state.energy ?? null,
    updatedAt: state.updated_at ?? null,
    lastDeltaSource: state.last_delta_source ?? null,
  };
}

async function readConfigSummary() {
  const raw = JSON.parse(await readFile(CONFIG_PATH, "utf8")) as JsonObject;
  const gw = asObject(raw.gateway), auth = asObject(gw.auth);
  const tools = asObject(raw.tools), plugins = asObject(raw.plugins);
  const entries = asObject(plugins.entries), agents = asObject(raw.agents);
  const defaults = asObject(agents.defaults);
  return {
    gateway: { mode: gw.mode ?? null, bind: gw.bind ?? null, port: gw.port ?? null, authMode: auth.mode ?? null, hasToken: typeof auth.token === "string" && auth.token.length > 0 },
    tools: { profile: tools.profile ?? null, allow: asStringArray(tools.allow), alsoAllow: asStringArray(tools.alsoAllow), deny: asStringArray(tools.deny) },
    plugins: { bundledDiscovery: plugins.bundledDiscovery ?? null, allow: asStringArray(plugins.allow), enabledEntries: Object.entries(entries).filter(([,v]) => Boolean(asObject(v).enabled)).map(([n]) => n).sort() },
    model: { primary: defaults.primaryModel ?? defaults.model ?? null },
  };
}

async function readRoutingDecision(): Promise<JsonObject | null> {
  try { return JSON.parse(await readFile(ROUTING_INJECTION_PATH, "utf8")) as JsonObject; } catch { return null; }
}

interface AffectiveState {
  warmth: number;
  energy: number;
  updated_at: string;
  last_delta: { warmth: number; energy: number };
  last_delta_source: string;
  _reserved: Record<string, unknown>;
}

const DEFAULT_AFFECTIVE: AffectiveState = {
  warmth: 0.0, energy: 0.0,
  updated_at: "", last_delta: { warmth: 0.0, energy: 0.0 },
  last_delta_source: "init", _reserved: {}
};

function readAffectiveStateSync(): AffectiveState {
  try {
    const statePath = path.join(PROJECT_ROOT, affConfig.statePath);
    const raw = readFileSync(statePath, "utf8");
    const parsed = JSON.parse(raw);
    if (typeof parsed.warmth !== "number" || typeof parsed.energy !== "number") {
      return { ...DEFAULT_AFFECTIVE };
    }
    return {
      warmth: Number(parsed.warmth) || 0,
      energy: Number(parsed.energy) || 0,
      updated_at: String(parsed.updated_at ?? ""),
      last_delta: {
        warmth: Number(parsed.last_delta?.warmth) || 0,
        energy: Number(parsed.last_delta?.energy) || 0,
      },
      last_delta_source: String(parsed.last_delta_source ?? "unknown"),
      _reserved: typeof parsed._reserved === "object" && parsed._reserved !== null && !Array.isArray(parsed._reserved)
        ? parsed._reserved as Record<string, unknown>
        : {},
    };
  } catch {
    return { ...DEFAULT_AFFECTIVE };
  }
}

// ---- Router model call via DeepSeek API ----
function describeAffective(state: AffectiveState): string {
  const wLabel = state.warmth > 0.3 ? "较亲近" : state.warmth < -0.3 ? "较疏离" : "正常";
  const eLabel = state.energy > 0.3 ? "较活跃" : state.energy < -0.3 ? "较安静" : "正常";
  return `亲近感=${wLabel}，活力=${eLabel}`;
}

function buildRouterPrompt(userText: string, context: ChatEntry[], affective: AffectiveState): string {
  const ctxLines = context.map(m => {
    const speaker = m.role === "user" ? "用户" : "${ASSISTANT_LABEL}";
    return `- ${speaker}: ${m.text}`;
  });
  const memoryTriggers = "之前、上次、还记得、记得、我喜欢、我说过、那个后来、最近、以后、下次";
  return `你是 Clawbot 的对话路由器，不直接回复用户，只输出 JSON 决策。

当前时间：${new Date().toISOString()}
最新用户消息：${userText}

最近上下文：
${ctxLines.join("\n")}

任务：判断${ASSISTANT_LABEL}这一轮应该如何接话。只输出一个 JSON 对象，不要 markdown，不要解释。

字段要求：
- should_reply: boolean
- timing_gate: "reply_now" | "wait" | "no_reply"
- wait_minutes: 0-20 的整数；不需要等就填 0
- scene: "daily" | "study" | "emotional" | "technical" | "meta_project" | "safety" | "unknown"
- reply_mode: "short_ack" | "emotional_support" | "study_help" | "technical_help" | "playful_chat" | "boundary" | "no_reply"
- memory_needed: boolean；当用户提到"${memoryTriggers}"或回复依赖长期偏好/约定时为 true
- memory_queries: string[]；最多 3 个短关键词
- length: "one_liner" | "short" | "medium" | "structured"
- tone: "soft_direct" | "playful" | "calm" | "serious"
- avoid: string[]；最多 4 条
- reply_brief: 给后续 replyer 的一句短策略，不要写用户可见回复
- rationale: 20 字以内，说明判断原因
- affective_delta: { warmth: -0.2~0.2, energy: -0.2~0.2 }，表示${ASSISTANT_LABEL}的状态应该如何变化

当前${ASSISTANT_LABEL}状态：${describeAffective(affective)}

状态更新指引：
- 用户分享开心事 → warmth +0.10~0.15, energy +0.10~0.20
- 用户焦虑/疲惫 → warmth +0.05~0.10, energy -0.10~0.20
- 用户吐槽/抱怨 → warmth +0.05, energy +0~0.10
- 用户简短确认（嗯/好） → warmth 0, energy -0.05
- 用户纠正/批评${ASSISTANT_LABEL} → warmth -0.05~0.10
- 无特别触发 → 小幅向 0 回归（±0.02）

判断原则：
- 私聊里大多数用户消息都应该回复，但不要机械热情。
- 用户可能还没说完、只是发了一个很弱的确认、或上下文已自然结束时，可以 wait 或 no_reply。
- 情绪低落优先接情绪，学习/技术问题才展开解决。
- 默认短微信风格；只有用户明确要求整理、解释、写文档时才 structured。`;
}

function extractJson(raw: string): JsonObject {
  const text = raw.trim();
  if (text.startsWith("```")) {
    const cleaned = text.replace(/^```(?:json)?\s*/,"").replace(/\s*```$/,"");
    return JSON.parse(cleaned);
  }
  try { return JSON.parse(text); } catch {
    const match = text.match(/\{[\s\S]*\}/);
    if (!match) throw new Error("No JSON found");
    return JSON.parse(match[0]);
  }
}

function normalizeDecision(raw: JsonObject): JsonObject {
  const allowedTiming = ["reply_now","wait","no_reply"];
  const allowedScene = ["daily","study","emotional","technical","meta_project","safety","unknown"];
  const allowedReply = ["short_ack","emotional_support","study_help","technical_help","playful_chat","boundary","no_reply"];
  const allowedLength = ["one_liner","short","medium","structured"];
  const allowedTone = ["soft_direct","playful","calm","serious"];

  const timing = typeof raw.timing_gate === "string" && allowedTiming.includes(raw.timing_gate) ? raw.timing_gate : "reply_now";
  const scene = typeof raw.scene === "string" && allowedScene.includes(raw.scene) ? raw.scene : "daily";
  const replyMode = typeof raw.reply_mode === "string" && allowedReply.includes(raw.reply_mode) ? raw.reply_mode : "short_ack";
  const length = typeof raw.length === "string" && allowedLength.includes(raw.length) ? raw.length : "short";
  const tone = typeof raw.tone === "string" && allowedTone.includes(raw.tone) ? raw.tone : "soft_direct";
  const shouldReply = timing !== "no_reply";
  const waitMinutes = Math.max(0, Math.min(20, Number(raw.wait_minutes) || 0));

  const stringList = (v: unknown, limit: number): string[] => {
    if (!Array.isArray(v)) return [];
    return v.filter((i): i is string => typeof i === "string" && String(i).trim() !== "").map(i => String(i).slice(0, 80)).slice(0, limit);
  };

  return {
    should_reply: shouldReply,
    timing_gate: timing,
    wait_minutes: waitMinutes,
    scene,
    reply_mode: shouldReply ? replyMode : "no_reply",
    memory_needed: Boolean(raw.memory_needed),
    memory_queries: stringList(raw.memory_queries, 3),
    length,
    tone,
    avoid: stringList(raw.avoid, 4),
    reply_brief: String(raw.reply_brief ?? "").trim().slice(0, 160),
    rationale: String(raw.rationale ?? "").trim().slice(0, 60),
    affective_delta: raw.affective_delta,
  };
}

function heuristicDecision(userText: string, _affective?: AffectiveState): JsonObject {
  const emotional = ["累","烦","崩","难受","焦虑","撑不住","想哭","压力"].some(w => userText.includes(w));
  const weakAck = /^(嗯+|好+|行+|ok|okay|哈哈+|草|笑死)[。.!！~～ ]*$/i.test(userText.trim());
  const scene = emotional ? "emotional" : "daily";
  const tone = emotional ? "calm" : "playful";
  const timing = weakAck ? "wait" : "reply_now";
  return {
    should_reply: !weakAck,
    timing_gate: timing, wait_minutes: weakAck ? 3 : 0, scene,
    reply_mode: weakAck ? "no_reply" : "short_ack",
    memory_needed: false, memory_queries: [], length: "short", tone,
    avoid: ["长篇解释","暴露内部决策"],
    reply_brief: "先接住用户当下意图，再用短微信语气回应。",
    rationale: "本地启发式判断",
  };
}

async function modelDecision(userText: string, context: ChatEntry[], apiKey: string, affective: AffectiveState): Promise<JsonObject> {
  const prompt = buildRouterPrompt(userText, context, affective);
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), ROUTER_TIMEOUT_MS);

  try {
    const res = await fetch(DEEPSEEK_API, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${apiKey}`,
      },
      body: JSON.stringify({
        model: "deepseek-chat",
        messages: [{ role: "user", content: prompt }],
        max_tokens: 500,
        temperature: 0.3,
      }),
      signal: controller.signal,
    });
    if (!res.ok) throw new Error(`API ${res.status}`);
    const data = await res.json() as JsonObject;
    const choices = data.choices as Array<{ message: { content: string } }> | undefined;
    const content = choices?.[0]?.message?.content;
    if (!content) throw new Error("Empty response");
    return normalizeDecision(extractJson(content));
  } finally {
    clearTimeout(timer);
  }
}

function writeSyncLog(decision: JsonObject, userText: string, source: string, latencyMs: number, ids?: { sessionId?: string; runId?: string; messageId?: string }, error?: string, affDelta?: { warmth: number; energy: number } | null) {
  try {
    const entry = {
      ts: new Date().toISOString(),
      mode: "sync_pre_reply",
      sessionId: ids?.sessionId ?? "",
      runId: ids?.runId ?? "",
      messageId: ids?.messageId ?? "",
      userPreview: userText.slice(0, 80),
      decisionSource: source,
      decision,
      injected: true,
      affectiveDelta: affDelta ?? undefined,
      latencyMs,
      error: error ?? null,
    };
    appendFileSync(SYNC_LOG_PATH, JSON.stringify(entry) + "\n");
  } catch {}
}

function normalizeAffectiveDelta(delta: Record<string, unknown>): { warmth: number; energy: number } {
  const clamp = (v: number) => Math.max(-0.2, Math.min(0.2, Number(v) || 0));
  const round = (v: number) => Math.round(v * 100) / 100;
  return {
    warmth: round(clamp(Number(delta.warmth ?? 0))),
    energy: round(clamp(Number(delta.energy ?? 0))),
  };
}

function applyAffectiveDelta(current: AffectiveState, delta: { warmth: number; energy: number }, source: string): AffectiveState {
  const clampState = (v: number) => Math.max(-1.0, Math.min(1.0, v));
  const round = (v: number) => Math.round(v * 100) / 100;
  return {
    warmth: round(clampState(current.warmth + delta.warmth)),
    energy: round(clampState(current.energy + delta.energy)),
    updated_at: new Date().toISOString(),
    last_delta: delta,
    last_delta_source: source,
    _reserved: current._reserved ?? {},
  };
}

function writeAffectiveStateSync(state: AffectiveState): void {
  try {
    const statePath = path.join(PROJECT_ROOT, affConfig.statePath);
    writeFileSync(statePath, JSON.stringify(state, null, 2) + "\n");
  } catch {
    // 写入失败不阻断正常回复流程
  }
}

function buildInjectionText(decision: Record<string, unknown>): string {
  const parts: string[] = ["本轮内部对话决策："];
  if (decision.timing_gate === "no_reply") { parts.push("- 是否回复：否（本轮不回复用户）"); return parts.join("\n"); }
  if (decision.timing_gate === "wait") parts.push("- 时机：等一等再回，用户可能还没说完");
  const sceneLabels: Record<string, string> = { daily: "日常闲聊", emotional: "用户情绪受影响", study: "学习/考试相关", technical: "技术问题", meta_project: "讨论系统本身", safety: "安全相关", unknown: "一般话题" };
  parts.push(`- 当前局面：${sceneLabels[String(decision.scene ?? "")] ?? String(decision.scene ?? "一般话题")}`);
  const rb = String(decision.reply_brief ?? "").trim();
  if (rb) parts.push(`- 回复策略：${rb}`);
  const av = decision.avoid;
  if (Array.isArray(av) && av.length > 0) parts.push(`- 避免：${av.join("、")}`);
  return parts.join("\n");
}

function extractUserText(messages: unknown[], fallback: string): string {
  for (let i = (messages as Array<Record<string, unknown>>).length - 1; i >= 0; i--) {
    const m = messages[i] as Record<string, unknown>;
    if (String(m.role) === "user") {
      const c = m.content;
      const text = typeof c === "string" ? c : String((m as Record<string, unknown>).text ?? "");
      if (text && text !== HEARTBEAT_MARKER) return text;
    }
  }
  return fallback;
}

function extractRecentContext(messages: unknown[]): ChatEntry[] {
  return (messages as Array<Record<string, unknown>>).slice(-MAX_CONTEXT_ENTRIES).map(m => {
    const c = m.content;
    const text = typeof c === "string" ? c : String((m as Record<string, unknown>).text ?? "");
    return { role: String(m.role ?? "user"), text: text.slice(0, 500), timestamp: String(m.timestamp ?? "") };
  });
}

function getApiKey(): string {
  if (typeof process !== "undefined" && process.env?.DEEPSEEK_API_KEY) {
    return process.env.DEEPSEEK_API_KEY;
  }
  return "";
}

// --- affective state config (loaded once at plugin init, use restart to reload) ---
let affConfig = { enabled: false, writeState: false, injectToMainModel: false, statePath: "workspace/clawbot/memory/affective-state.json" };
try {
  const routerConfigPath = path.join(PROJECT_ROOT, "config", "clawbot-dialogue-router.json");
  const routerConfig = JSON.parse(readFileSync(routerConfigPath, "utf8")) as JsonObject;
  const ac = routerConfig.affectiveState;
  if (ac && typeof ac === "object") {
    const acObj = ac as Record<string, unknown>;
    affConfig = {
      enabled: Boolean(acObj.enabled),
      writeState: Boolean(acObj.writeState),
      injectToMainModel: Boolean(acObj.injectToMainModel),
      statePath: String(acObj.statePath || affConfig.statePath),
    };
  }
} catch {}

export default definePluginEntry({
  id: "clawbot-readonly",
  name: "Clawbot Readonly Tools",
  description: "Read-only status checks + sync dialogue router injection via agent_turn_prepare hook.",
  register(api) {
    api.registerTool({
      name: "clawbot_status", label: "Clawbot Status",
      description: "Return a fixed, read-only deployment status summary.",
      parameters: Type.Object({}),
      execute: async () => {
        const summary = await readConfigSummary();
        const decision = await readRoutingDecision();
        const topLevel = await listProjectTopLevel();
        const runtimeAlignment = {
          memoryFiles: await countClawbotMemoryFiles(),
          heartbeatRunner: readHeartbeatSummary(),
          affectiveState: readAffectiveSummary(),
        };
        const content = JSON.stringify({
          workspace: { root: PROJECT_ROOT, exists: await exists(PROJECT_ROOT), topLevel },
          config: { path: CONFIG_PATH, exists: await exists(CONFIG_PATH), summary },
          routing: { source: "dialogue-router", path: ROUTING_INJECTION_PATH, decision },
          runtimeAlignment,
          safety: {
            scope: "fixed-readonly-status",
            noShell: true,
            secretsRedacted: true,
            pathScope: path.basename(PROJECT_ROOT),
            execModeExpected: "deny",
          },
        }, null, 2);
        return { content: [{ type: "text", text: content }], details: { source: "clawbot-readonly" } };
      },
    });

    // ---- before_agent_reply: fast heuristic silence for weak acks ----
    api.on("before_agent_reply", async (event: Record<string, unknown>) => {
      try {
        const cleanedBody = String((event as Record<string, unknown>).cleanedBody ?? "").trim();
        if (!cleanedBody || cleanedBody.includes(HEARTBEAT_MARKER)) return;

        // Fast heuristic: silence obviously weak acknowledgments.
        // Model router runs later in agent_turn_prepare for prompt injection.
        const weakAck = /^(嗯+|好+|行+|ok|okay|哈哈+|草|笑死|好哦|好吧)$/i.test(cleanedBody);
        if (weakAck) {
          appendFileSync(path.join(PROJECT_ROOT, "logs", "hook-diag.log"),
            `${new Date().toISOString()} SILENCED: weak_ack | body=${cleanedBody}\n`);
          return { handled: true, reason: "router: weak_ack" };
        }
      } catch {}
    }, { priority: 50 });

    api.on("agent_turn_prepare", async (event: Record<string, unknown>) => {
      const evtPrompt = String(event.prompt ?? "").trim();
      if (!evtPrompt || evtPrompt.includes(HEARTBEAT_MARKER)) return;

      const messages = Array.isArray(event.messages) ? event.messages : [];
      const userText = extractUserText(messages, evtPrompt);
      if (!userText) return;

      const ctx = (event as Record<string, unknown>).ctx as Record<string, unknown> | undefined;

      // Extract IDs from the messages array — ctx provides none in agent_turn_prepare.
      // Message items only expose role/content/timestamp; no native id fields.
      let sessionId = "", messageId = "";
      try {
        for (let i = messages.length - 1; i >= 0; i--) {
          const m = messages[i] as Record<string, unknown>;
          if (String(m.role) === "user") {
            messageId = String(m.timestamp ?? m.ts ?? "");
            sessionId = String(m.sessionKey ?? m.sessionId ?? "");
            break;
          }
        }
      } catch {}
      const recentContext = extractRecentContext(messages);

      // Read affective state
      const affective = affConfig.enabled ? readAffectiveStateSync() : DEFAULT_AFFECTIVE;

      // Try model router, fall back to heuristic.
      const apiKey = getApiKey();
      let decision: JsonObject | null = null;
      let source = "heuristic";
      let error: string | undefined;
      const t0 = Date.now();

      if (apiKey) {
        try {
          decision = await modelDecision(userText, recentContext, apiKey, affective);
          source = "model";
        } catch (e) {
          error = String(e);
        }
      }

      if (!decision) {
        decision = heuristicDecision(userText, affective);
        source = apiKey ? "heuristic_fallback" : "heuristic";
      }

      const latencyMs = Date.now() - t0;

      // Affective state: extract delta and write back (only if enabled + writeState)
      let affDelta: { warmth: number; energy: number } | null = null;
      if (affConfig.enabled && affConfig.writeState) {
        const rawDelta = (decision as Record<string, unknown>).affective_delta;
        if (rawDelta && typeof rawDelta === "object") {
          affDelta = normalizeAffectiveDelta(rawDelta as Record<string, unknown>);
          const updated = applyAffectiveDelta(affective, affDelta, source);
          writeAffectiveStateSync(updated);
        }
      }

      writeSyncLog(decision, userText, source, latencyMs, { sessionId, messageId }, error, affDelta);

      const injection = buildInjectionText(decision as Record<string, unknown>);
      return { prependContext: injection };
    }, { priority: 50 });
  },
});
