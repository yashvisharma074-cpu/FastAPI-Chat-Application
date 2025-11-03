let ws;
let notifyWS;
let currentUser = localStorage.getItem("username");
let selectedUser = null;

async function loadUsers() {
  const res = await fetch("http://127.0.0.1:8000/auth/users");
  const users = await res.json();
  const listDiv = document.getElementById("user-list");
  listDiv.innerHTML = "<h4>Users:</h4>";

  users.forEach(u => {
    if (u.username !== currentUser) {
      const btn = document.createElement("button");
      btn.innerText = u.username;
      btn.dataset.user = u.username;
      btn.onclick = () => startChat(u.username);
      listDiv.appendChild(btn);
    }
  });
}

async function startChat(username) {
  selectedUser = username;
  document.getElementById("chat-header").innerText = `Chat with ${username}`;
  document.getElementById("chat-box").innerHTML = "";

  const btn = document.querySelector(`button[data-user='${username}']`);
  if (btn) {
    const badge = btn.querySelector(".badge");
    if (badge) badge.remove();
  }

  if (ws && ws.readyState === WebSocket.OPEN) ws.close();

  const res = await fetch(`http://127.0.0.1:8000/chat/messages/${currentUser}/${selectedUser}`);
  const history = await res.json();
  history.forEach(m => showMessage(m.sender, m.message, m.content_type, m.timestamp));

  ws = new WebSocket(`ws://127.0.0.1:8000/chat/ws/${currentUser}/${selectedUser}`);

  ws.onopen = () => console.log("✅ Connected to chat with", selectedUser);

  ws.onmessage = (event) => {
    const data = JSON.parse(event.data);

    if (data.type === "notification") return;
    showMessage(data.sender, data.message, data.content_type, data.timestamp);
  };

  ws.onclose = () => console.log("❌ Disconnected from chat");
}

function sendMessage() {
  const input = document.getElementById("messageInput");
  const msg = input.value.trim();
  if (!msg || !ws || ws.readyState !== WebSocket.OPEN) return;

  ws.send(JSON.stringify({
    sender: currentUser,
    receiver: selectedUser,
    message: msg,
    content_type: "text"
  }));

  input.value = "";
}

async function uploadImage(event) {
  const file = event.target.files[0];
  if (!file || !ws || ws.readyState !== WebSocket.OPEN) return;

  const formData = new FormData();
  formData.append("file", file);

  const res = await fetch("http://127.0.0.1:8000/chat/upload-image", {
    method: "POST",
    body: formData,
  });

  const data = await res.json();
  if (data.success) {
    ws.send(JSON.stringify({
      sender: currentUser,
      receiver: selectedUser,
      message: data.url,
      content_type: "image"
    }));
  }
}

function showMessage(sender, msg, type = "text", timestamp = "") {
  const chatBox = document.getElementById("chat-box");
  const div = document.createElement("div");
  div.classList.add("message", sender === currentUser ? "sent" : "received");

  if (type === "image") {
    div.innerHTML = `<img src="${msg}" alt="Image" style="max-width:200px;border-radius:8px;"><div class="timestamp">${new Date(timestamp).toLocaleTimeString()}</div>`;
  } else {
    div.innerHTML = `<b>${sender}:</b> ${msg}<div class="timestamp">${new Date(timestamp).toLocaleTimeString()}</div>`;
  }

  chatBox.appendChild(div);
  chatBox.scrollTop = chatBox.scrollHeight;
}

function connectNotificationSocket() {
  notifyWS = new WebSocket(`ws://127.0.0.1:8000/chat/ws/notify/${currentUser}`);

  notifyWS.onmessage = (event) => {
    const data = JSON.parse(event.data);
    if (data.type === "notification") {
      const senderName = data.from;
      const userButton = document.querySelector(`button[data-user='${senderName}']`);
      if (userButton) {
        let badge = userButton.querySelector(".badge");
        if (!badge) {
          badge = document.createElement("span");
          badge.className = "badge";
          badge.textContent = "1";
          userButton.appendChild(badge);
        } else {
          badge.textContent = parseInt(badge.textContent) + 1;
        }
      }
    }
  };
}

window.addEventListener("DOMContentLoaded", () => {
  loadUsers();
  connectNotificationSocket();
});
