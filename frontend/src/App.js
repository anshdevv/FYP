import { useState } from "react";

export default function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");

  const sendMessage = async () => {
    if (!input.trim()) return;

    const userMsg = { sender: "user", text: input };
    setMessages([...messages, userMsg]);
    setInput("");

    const res = await fetch("http://localhost:8000/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ user_id: "u1", message: input }),
    });
    const data = await res.json();

    const botMsg = { sender: "bot", text: data.response };
    setMessages((m) => [...m, botMsg]);
  };

  return (
    <div className="flex flex-col items-center h-screen bg-gray-100 p-4">
      <h1 className="text-xl font-bold mb-4">🏥 Hospital CSR Chatbot</h1>

      <div className="w-full max-w-md bg-white shadow rounded-lg p-3 overflow-y-auto flex-1 mb-3">
        {messages.map((msg, i) => (
          <div key={i} className={`mb-2 ${msg.sender === "user" ? "text-right" : "text-left"}`}>
            <span
              className={`inline-block px-3 py-2 rounded-xl ${
                msg.sender === "user" ? "bg-blue-500 text-white" : "bg-gray-200"
              }`}
            >
              {msg.text}
            </span>
          </div>
        ))}
      </div>

      <div className="flex w-full max-w-md">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Type your message..."
          className="flex-1 border rounded-l-lg p-2"
        />
        <button onClick={sendMessage} className="bg-blue-500 text-white px-4 rounded-r-lg">
          Send
        </button>
      </div>
    </div>
  );
}
