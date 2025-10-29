let ws;
let currentUser = localStorage.getItem("username");
let selectedUser;

async function loadUsers() {
  const res = await fetch("http://127.0.0.1:8000/auth/users");
  const users = await res.json();
  const listDiv = document.getElementById("user-list");
  listDiv.innerHTML = "<h3>Users:</h3>";

  console.log("Fetched users:", users); // 🧠 debug line

  users.forEach(u => {
    if (u.username !== currentUser) {      // ✅ use u.username
      const btn = document.createElement("button");
      btn.innerText = u.username;          // ✅ show username
      btn.onclick = () => startChat(u.username);
      listDiv.appendChild(btn);
    }
  });
}

function startChat(username) {
  selectedUser = username;
  document.getElementById("chat-with").innerText = `Chat with ${username}`;
  document.getElementById("chat-box").innerHTML = "";

  if (ws && ws.readyState === WebSocket.OPEN) ws.close();

  ws = new WebSocket(`ws://127.0.0.1:8000/ws/${currentUser}/${selectedUser}`);

  ws.onopen = () => console.log("✅ Connected to chat:", selectedUser);
  ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    showMessage(data.sender, data.message);
  };
  ws.onclose = () => console.log("❌ Disconnected from chat:", selectedUser);
}

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

function showMessage(sender, msg) {
  const chatBox = document.getElementById("chat-box");
  const div = document.createElement("div");
  div.classList.add(sender === currentUser ? "sent" : "received");
  div.innerHTML = `<b>${sender}:</b> ${msg}`;
  chatBox.appendChild(div);
  chatBox.scrollTop = chatBox.scrollHeight;
}

loadUsers();
