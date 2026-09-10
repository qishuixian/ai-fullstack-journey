<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, ref } from "vue";
import { ElMessage } from "element-plus";
type Session = { id: string; title: string };
type AgentEvent = {
  type: string;
  content?: string;
  step?: number;
  tool?: string;
  args?: Record<string, unknown>;
  call_id?: string;
  approval_id?: string;
  approved?: boolean;
  status?: string;
};
type Turn = { id: string; user: string; events: AgentEvent[] };
const sessions = ref<Session[]>([]);
const selected = ref("");
const turns = ref<Turn[]>([]);
const input = ref("");
const busy = ref(false);
const loading = ref(false);
const configured = ref(true);
const approval = ref<AgentEvent | null>(null);
const approving = ref(false);
const feed = ref<HTMLElement>();
let source: EventSource | null = null;
let buffer: { event: AgentEvent; chars: string[] }[] = [];
let completed = false;
const examples = [
  "查询北京天气，再计算 12 × 8",
  "模拟发邮件给 demo@example.com，主题：学习进度，正文：Week 11 已完成",
  "调用 slow_tool 测试超时降级",
];
const currentTitle = computed(
  () => sessions.value.find((s) => s.id === selected.value)?.title || "新会话",
);
function persist() {
  localStorage.setItem("week11.sessions", JSON.stringify(sessions.value));
  localStorage.setItem("week11.selected", selected.value);
}
async function api(path: string, body?: unknown) {
  const response = await fetch(
    path,
    body === undefined
      ? undefined
      : {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(body),
        },
  );
  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || `请求失败 (${response.status})`);
  }
  return response.json();
}
async function scroll() {
  await nextTick();
  feed.value?.scrollTo({ top: feed.value.scrollHeight, behavior: "smooth" });
}
async function newSession() {
  if (busy.value || loading.value) return;
  loading.value = true;
  try {
    const s = await api("/sessions", {});
    sessions.value.unshift(s);
    selected.value = s.id;
    turns.value = [];
    persist();
  } catch (error) {
    ElMessage.error(String(error));
  } finally {
    loading.value = false;
  }
}
async function selectSession(id: string) {
  if (busy.value || loading.value) return;
  loading.value = true;
  try {
    const data = await api(`/sessions/${encodeURIComponent(id)}`);
    selected.value = id;
    // 存储的是原始 SSE 分片；恢复时合并，避免每个 token 变成独立段落。
    turns.value = (data.turns as Turn[]).map((turn) => {
      const events: AgentEvent[] = [];
      for (const event of turn.events) {
        const previous = events.at(-1);
        if (
          event.type === "token" &&
          previous?.type === "token" &&
          previous.step === event.step
        ) {
          previous.content = (previous.content || "") + (event.content || "");
        } else {
          events.push({ ...event });
        }
      }
      return { ...turn, events };
    });
    persist();
    if (data.turns.length) scroll();
  } catch (error) {
    ElMessage.error(String(error));
  } finally {
    loading.value = false;
  }
}
function closeStream() {
  source?.close();
  source = null;
  approval.value = null;
}
function finish() {
  closeStream();
  completed = true;
  if (!buffer.length) busy.value = false;
}
function stop() {
  if (!busy.value) return;
  closeStream();
  buffer = [];
  busy.value = false;
  completed = true;
  turns.value.at(-1)?.events.push({
    type: "error",
    content:
      "连接已停止。本轮是否已完成请以重新载入的历史为准；未完成的对话不会保存。",
  });
}
const timer = window.setInterval(() => {
  const item = buffer[0];
  if (item) {
    item.event.content =
      (item.event.content || "") + item.chars.splice(0, 3).join("");
    if (!item.chars.length) buffer.shift();
    scroll();
  }
  if (completed && !buffer.length) busy.value = false;
}, 20);
async function send() {
  if (busy.value || loading.value || !input.value.trim()) return;
  if (!selected.value) await newSession();
  if (!selected.value) return;
  const text = input.value.trim();
  input.value = "";
  busy.value = true;
  completed = false;
  turns.value.push({ id: crypto.randomUUID(), user: text, events: [] });
  const turn = turns.value[turns.value.length - 1]!;
  const session = sessions.value.find((s) => s.id === selected.value);
  if (session?.title === "新会话") {
    session.title = text.slice(0, 24);
    persist();
  }
  source = new EventSource(
    `/chat?${new URLSearchParams({ session_id: selected.value, request_id: turn.id, message: text })}`,
  );
  source.onmessage = ({ data }) => {
    const event: AgentEvent = JSON.parse(data);
    if (event.type === "done") {
      finish();
      return;
    }
    if (event.type === "token") {
      let target = turn.events.at(-1);
      if (target?.type !== "token" || target.step !== event.step) {
        turn.events.push({ ...event, content: "" });
        target = turn.events[turn.events.length - 1]!;
      }
      const queued = buffer.find((b) => b.event === target);
      if (queued) queued.chars.push(...Array.from(event.content || ""));
      else
        buffer.push({ event: target, chars: Array.from(event.content || "") });
    } else {
      turn.events.push(event);
      if (event.type === "approval_required") approval.value = event;
      if (event.type === "approval_result") approval.value = null;
      if (event.type === "error") finish();
    }
    scroll();
  };
  source.onerror = () => {
    turn.events.push({
      type: "error",
      content:
        "连接中断或请求被拒绝，请检查后端状态。为避免重复执行工具，已关闭自动重连；可重新载入会话查看已保存结果。",
    });
    finish();
  };
  scroll();
}
async function decide(approved: boolean) {
  if (!approval.value || approving.value) return;
  approving.value = true;
  try {
    await api("/approve", {
      session_id: selected.value,
      approval_id: approval.value.approval_id,
      approved,
    });
    approval.value = null;
  } catch (error) {
    ElMessage.error(String(error));
  } finally {
    approving.value = false;
  }
}
onMounted(async () => {
  try {
    const saved = JSON.parse(localStorage.getItem("week11.sessions") || "[]");
    if (Array.isArray(saved))
      sessions.value = saved.filter(
        (s) => typeof s.id === "string" && typeof s.title === "string",
      );
  } catch {
    sessions.value = [];
  }
  try {
    configured.value = (await api("/health")).model_configured;
  } catch {
    ElMessage.error("后端未连接，请启动 8083 服务");
  }
  const id = localStorage.getItem("week11.selected");
  if (sessions.value.length)
    await selectSession(
      sessions.value.find((s) => s.id === id)?.id || sessions.value[0]!.id,
    );
  else await newSession();
});
onUnmounted(() => {
  closeStream();
  clearInterval(timer);
});
</script>

<template>
  <div class="studio">
    <aside class="sidebar">
      <a class="brand" href="/"
        >◈ <span>ReAct <b>Studio</b></span></a
      >
      <div class="chapter">WEEK 11 / AGENT WORKSPACE</div>
      <button
        class="new-session"
        :disabled="busy || loading"
        @click="newSession"
      >
        ＋ 新建会话
      </button>
      <div class="section-label">
        会话记录 <span>{{ sessions.length }}</span>
      </div>
      <nav>
        <button
          v-for="s in sessions"
          :key="s.id"
          :class="['session', { selected: s.id === selected }]"
          :disabled="busy || loading"
          @click="selectSession(s.id)"
        >
          ◌ <span>{{ s.title }}</span>
        </button>
      </nav>
      <div class="sidebar-footer">
        <span class="live-dot"></span> 手写 ReAct 内核
        <div>从命令行，到可交互的 Agent。</div>
      </div>
    </aside>
    <main>
      <header>
        <div><span class="eyebrow">WORKSPACE / </span>{{ currentTitle }}</div>
        <span class="badge">{{ busy ? "● Agent 工作中" : "● 准备就绪" }}</span>
      </header>
      <div v-if="!configured" class="config-warning">
        尚未配置模型：请在 backend/.env 填写 DEEPSEEK_API_KEY，然后重启后端。
      </div>
      <section ref="feed" class="feed" aria-live="polite">
        <div v-if="!turns.length" class="welcome">
          <div class="hero-icon">◈</div>
          <div class="eyebrow">THINK · ACT · OBSERVE</div>
          <h1>让 Agent 的每一步，<br /><span>清晰可见。</span></h1>
          <p>
            提出一个任务，观察模型回复、工具调用与执行结果。<br />需要你的决定时，Agent
            会停下来等待审核。
          </p>
          <div class="examples">
            <button
              v-for="(example, i) in examples"
              :key="example"
              @click="input = example"
            >
              <span
                >0{{ i + 1 }} /
                {{ ["多工具协作", "人工审核", "超时降级"][i] }}</span
              >
              <p>{{ example }}</p>
              <b>↗</b>
            </button>
          </div>
          <div class="demo-note">
            教学工具 · 天气为模拟数据 · 邮件不会真实发送
          </div>
        </div>
        <article v-for="turn in turns" :key="turn.id" class="turn">
          <div class="user-row">
            <div class="user-bubble">{{ turn.user }}</div>
            <span class="avatar user-avatar">你</span>
          </div>
          <div class="agent-row">
            <span class="avatar agent-avatar">◈</span>
            <div class="agent-content">
              <div class="agent-name">ReAct Agent <span>执行轨迹</span></div>
              <template v-for="(event, i) in turn.events" :key="i">
                <div v-if="event.type === 'step'" class="step">
                  <span>{{ event.step }}</span
                  ><b>推理轮次 {{ event.step }}</b
                  ><small>{{ event.content }}</small>
                </div>
                <div v-else-if="event.type === 'token'" class="answer">
                  {{ event.content }}
                </div>
                <div v-else-if="event.type === 'tool_call'" class="tool-card">
                  <div>
                    ↗ 工具调用 <code>{{ event.tool }}</code
                    ><span v-if="event.tool === 'send_email'"
                      >需要审核 · 模拟</span
                    >
                  </div>
                  <pre>{{ JSON.stringify(event.args, null, 2) }}</pre>
                </div>
                <div
                  v-else-if="event.type === 'tool_result'"
                  :class="['result', event.status]"
                >
                  ↳ {{ event.content }}
                </div>
                <div
                  v-else-if="event.type === 'approval_required'"
                  class="approval-note"
                >
                  ◇ 已请求人工审核：{{ event.tool }}
                </div>
                <div
                  v-else-if="event.type === 'approval_result'"
                  class="approval-note"
                >
                  {{ event.approved ? "✓" : "⊘" }} {{ event.content }}
                </div>
                <div v-else-if="event.type === 'error'" class="error">
                  {{ event.content }}
                </div>
              </template>
              <div v-if="busy && turn === turns.at(-1)" class="working">
                ● ● ● <span>{{ approval ? "等待你的审核" : "正在处理" }}</span>
              </div>
            </div>
          </div>
        </article>
      </section>
      <footer class="composer-wrap">
        <form class="composer" @submit.prevent="send">
          <textarea
            v-model="input"
            aria-label="输入任务"
            placeholder="告诉 Agent，你想完成什么任务…"
            maxlength="2000"
            rows="2"
            :disabled="busy || loading"
            @keydown.enter.exact="
              (e: KeyboardEvent) => {
                if (!e.isComposing) {
                  e.preventDefault();
                  send();
                }
              }
            "
          ></textarea>
          <div class="composer-bottom">
            <span>↵ 发送 · Shift + Enter 换行</span
            ><button v-if="busy" type="button" class="send" @click="stop">
              停止</button
            ><button v-else class="send" :disabled="loading || !input.trim()">
              发送任务 ↑
            </button>
          </div>
        </form>
        <p>公开回复与工具轨迹可视化 · 不展示模型内部隐藏思维链</p>
      </footer>
    </main>
    <el-dialog
      :model-value="!!approval"
      title="确认工具执行"
      width="min(520px, 92vw)"
      :close-on-click-modal="false"
      :close-on-press-escape="false"
      :show-close="false"
    >
      <p>
        Agent 请求执行 <strong>{{ approval?.tool }}</strong
        >。请检查以下参数。
      </p>
      <p class="approval-note">
        这是模拟邮件工具，不会发送真实邮件；审核超时将自动拒绝（默认 120 秒）。
      </p>
      <pre class="approval-args">{{
        JSON.stringify(approval?.args, null, 2)
      }}</pre>
      <template #footer
        ><el-button :disabled="approving" @click="decide(false)"
          >拒绝执行</el-button
        ><el-button type="primary" :loading="approving" @click="decide(true)"
          >批准执行</el-button
        ></template
      >
    </el-dialog>
  </div>
</template>
