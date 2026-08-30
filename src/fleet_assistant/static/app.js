const form = document.querySelector("#chat-form");
const input = document.querySelector("#message");
const messages = document.querySelector("#messages");
const reset = document.querySelector("#reset");
let conversationId = crypto.randomUUID();

function addMessage(kind, text, meta = "") {
  const node = document.createElement("article");
  node.className = kind;
  node.dir = /[\u0600-\u06ff]/.test(text) ? "rtl" : "ltr";
  node.textContent = text;
  messages.appendChild(node);
  if (meta) {
    const trace = document.createElement("article");
    trace.className = "meta";
    trace.textContent = meta;
    messages.appendChild(trace);
  }
  messages.scrollTop = messages.scrollHeight;
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const text = input.value.trim();
  if (!text) return;
  addMessage("user", text);
  input.value = "";
  try {
    const response = await fetch("/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text, conversation_id: conversationId }),
    });
    const payload = await response.json();
    conversationId = payload.conversation_id;
    addMessage("bot", payload.reply, `${payload.status} · ${payload.route.intent} · confidence ${payload.route.confidence}`);
  } catch (_) {
    addMessage("bot", "The local API could not be reached.");
  }
});

reset.addEventListener("click", async () => {
  await fetch(`/sessions/${conversationId}`, { method: "DELETE" });
  conversationId = crypto.randomUUID();
  messages.innerHTML = "";
  addMessage("bot", "New synthetic demo session started.");
});
