const wrap = document.getElementById("chat-wrap");
const form = document.getElementById("chat-form");
const input = document.getElementById("chat-input");
const sendBtn = document.getElementById("chat-send");

function addBubble(text, role) {
  const el = document.createElement("div");
  el.className = `bubble ${role}`;
  el.textContent = text;
  wrap.appendChild(el);
  el.scrollIntoView({ behavior: "smooth", block: "end" });
  return el;
}

async function sendMessage(text) {
  if (!text.trim()) return;
  input.value = "";
  sendBtn.disabled = true;

  addBubble(text, "user");
  const typing = addBubble("…", "bot typing");

  try {
    const data = await post("/chat/", { message: text });
    typing.textContent = data.response;
    typing.classList.remove("typing");
  } catch (e) {
    typing.textContent = "Erreur : impossible de contacter l'assistant.";
    typing.classList.remove("typing");
  } finally {
    sendBtn.disabled = false;
    input.focus();
  }
}

form.addEventListener("submit", e => {
  e.preventDefault();
  sendMessage(input.value);
});

document.querySelectorAll(".suggestion").forEach(btn => {
  btn.addEventListener("click", () => sendMessage(btn.dataset.q));
});

// Message de bienvenue
addBubble("Bonjour ! Je suis votre assistant apicole. Posez-moi vos questions sur l'état de vos ruches.", "bot");
