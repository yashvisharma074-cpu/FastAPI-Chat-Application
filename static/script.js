let ws; // WebSocket for active chat
let notifyWS; // WebSocket for global notifications
let currentUser = localStorage.getItem("username");
let selectedUser = null; // currently chatting user

// ----------------------------
// Load all users in sidebar
// ----------------------------
async function loadUsers() {
  const res = await fetch("http://127.0.0.1:8000/auth/users");
  const users = await res.json();
  const listDiv = document.getElementById("user-list");
  listDiv.innerHTML = "<h3>Users:</h3>";

  console.log("Fetched users:", users);
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

// ----------------------------
// Start a personal chat
// ----------------------------
function startChat(username) {
  selectedUser = username;
  document.getElementById("chat-with").innerText = `Chat with ${username}`;
  document.getElementById("chat-box").innerHTML = "";

  // 🔕 Remove badge when opening chat
  const btn = document.querySelector(`button[data-user='${username}']`);
  if (btn) {
    const badge = btn.querySelector(".badge");
    if (badge) badge.remove();
  }

  // Close any existing chat WebSocket
  if (ws && ws.readyState === WebSocket.OPEN) ws.close();

  // Connect to chat WebSocket
  ws = new WebSocket(`ws://127.0.0.1:8000/chat/ws/${currentUser}/${selectedUser}`);

  ws.onopen = () => console.log("✅ Connected to chat:", selectedUser);

  ws.onmessage = (event) => {
    const data = JSON.parse(event.data);

    // 🔔 Handle notification type (sent when chatting with another user)
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
      return; // don't show this message in active chat box
    }

    // 🗨️ Normal message
    showMessage(data.sender, data.message);
  };

  ws.onclose = () => console.log("❌ Disconnected from chat:", selectedUser);
}

// ----------------------------
// Send message to current chat
// ----------------------------
function sendMessage() {
  const input = document.getElementById("messageInput");
  const msg = input.value.trim();
  if (!msg || !ws || ws.readyState !== WebSocket.OPEN) {
    console.warn("⚠️ WebSocket not ready or message empty");
    return;
  }

  ws.send(JSON.stringify({
    sender: currentUser,
    receiver: selectedUser,
    message: msg
  }));

  input.value = "";
}

// ----------------------------
// Show message in chat box
// ----------------------------
function showMessage(sender, msg) {
  const chatBox = document.getElementById("chat-box");
  const div = document.createElement("div");
  div.classList.add(sender === currentUser ? "sent" : "received");
  div.innerHTML = `<b>${sender}:</b> ${msg}`;
  chatBox.appendChild(div);
  chatBox.scrollTop = chatBox.scrollHeight;
}

// ----------------------------
// Notification WebSocket
// (active even if no chat opened)
// ----------------------------
function connectNotificationSocket() {
  notifyWS = new WebSocket(`ws://127.0.0.1:8000/chat/ws/notify/${currentUser}`);

  notifyWS.onopen = () => console.log("🔔 Notification WebSocket connected");

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
      console.log(`🔔 Notification: New message from ${senderName}`);
    }
  };

  notifyWS.onclose = () => {
    console.log("⚠️ Notification WebSocket closed. Reconnecting in 3s...");
    setTimeout(connectNotificationSocket, 3000);
  };
}

// ----------------------------
// Initialize on page load
// ----------------------------
window.addEventListener("DOMContentLoaded", () => {
  loadUsers();
  connectNotificationSocket();
});
