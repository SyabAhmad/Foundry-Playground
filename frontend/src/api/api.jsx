// Centralized API module for Foundry Playground frontend
// Uses Vite environment variable `VITE_API_BASE_URL` or default to http://localhost:5000/api

const API_BASE =
  import.meta.env.VITE_API_BASE_URL || "http://localhost:5000/api";

async function _fetch(url, options = {}) {
  const res = await fetch(`${API_BASE}${url}`, options);
  const data = await res.json().catch(() => null);
  if (!res.ok) {
    const err = new Error(data?.error || res.statusText || "API Error");
    err.status = res.status;
    err.body = data;
    throw err;
  }
  return data;
}

export async function getModels() {
  return _fetch("/models");
}

export async function getPullableModels() {
  return _fetch("/models/pull");
}

export async function getRunningModels() {
  return _fetch("/models/running");
}

export async function getAllModels() {
  return _fetch("/models/all");
}

export async function pullModel(modelId) {
  return _fetch(`/models/pull/${encodeURIComponent(modelId)}`, {
    method: "POST",
  });
}

export async function stopModel(modelId) {
  return _fetch(`/models/stop/${encodeURIComponent(modelId)}`, {
    method: "POST",
  });
}

// Conversations
export async function getConversations(userId) {
  return _fetch(`/conversations?user_id=${encodeURIComponent(userId)}`);
}

export async function getConversation(id) {
  return _fetch(`/conversations/${encodeURIComponent(id)}`);
}

export async function createConversation(payload) {
  return _fetch("/conversations", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export async function updateConversation(id, payload) {
  return _fetch(`/conversations/${encodeURIComponent(id)}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export async function deleteConversation(id) {
  const url = `/conversations/${encodeURIComponent(id)}`;
  const res = await fetch(`${API_BASE}${url}`, { method: "DELETE" });
  return { ok: res.ok, status: res.status };
}

export async function postConversationMessage(conversationId, payload) {
  return _fetch(
    `/conversations/${encodeURIComponent(conversationId)}/messages`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }
  );
}

// Chat & generate
export async function chat(conversationId, payload) {
  const url = conversationId
    ? `/chat/${encodeURIComponent(conversationId)}`
    : "/chat";
  return _fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export async function generate(payload) {
  return _fetch("/generate", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export async function generateEmbeddings(payload) {
  return _fetch("/embeddings", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export default {
  getModels,
  getPullableModels,
  getRunningModels,
  getAllModels,
  pullModel,
  stopModel,
  getConversations,
  getConversation,
  createConversation,
  updateConversation,
  deleteConversation,
  postConversationMessage,
  chat,
  generate,
  generateEmbeddings,
};
