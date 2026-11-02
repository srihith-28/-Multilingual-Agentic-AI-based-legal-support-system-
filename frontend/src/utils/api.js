/**
 * Agent Forge - Frontend API Utility
 *
 * Centralized fetch wrapper for all backend API calls.
 * Handles error normalisation, timeout, and streaming (SSE) support.
 */

const API_HOST = (import.meta.env.VITE_API_URL || '').trim().replace(/\/+$/, '');
const BASE_URL = `${API_HOST}/api`;
const REQUEST_TIMEOUT_MS = 300_000; // 5 minutes to accommodate multi-agent legal verification

// ------------------------------------------------------------------------------
// Custom error class
// ------------------------------------------------------------------------------

export class ApiError extends Error {
  constructor(status, message, path = '') {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.path = path;
  }
}

// ------------------------------------------------------------------------------
// Generic fetch wrapper
// ------------------------------------------------------------------------------

async function apiFetch(path, options = {}) {
  const controller = new AbortController();
  const timerId = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);

  try {
    const res = await fetch(`${BASE_URL}${path}`, {
      ...options,
      signal: controller.signal,
    });

    if (!res.ok) {
      const errorText = await res.text().catch(() => res.statusText);
      throw new ApiError(res.status, errorText || res.statusText, path);
    }

    return res;
  } catch (err) {
    if (err.name === 'AbortError') {
      throw new ApiError(408, 'Request timed out. Please try a shorter query.', path);
    }
    if (err instanceof ApiError) throw err;
    throw new ApiError(0, err.message || 'Network error', path);
  } finally {
    clearTimeout(timerId);
  }
}

// ------------------------------------------------------------------------------
// Health
// ------------------------------------------------------------------------------

export async function fetchHealth() {
  const res = await apiFetch('/health');
  return res.json();
}

// ------------------------------------------------------------------------------
// Chat
// ------------------------------------------------------------------------------

export async function sendChatMessage({ message, session_id, language, input_mode = 'text' }) {
  const res = await apiFetch('/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message, session_id, language, input_mode }),
  });
  return res.json();
}

export async function sendChatMessageStreaming({
  message, session_id, language, input_mode = 'text',
  onChunk, onComplete, onError,
}) {
  try {
    const res = await apiFetch('/chat/stream', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message, session_id, language, input_mode }),
    });

    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop();

      for (const line of lines) {
        const trimmed = line.trim();
        if (!trimmed || trimmed.startsWith(':')) continue; // Ignore SSE keep-alive comments
        if (!trimmed.startsWith('data:')) continue;
        const raw = trimmed.slice(5).trim();
        if (raw === '[DONE]') continue;

        try {
          const parsed = JSON.parse(raw);
          if (parsed.type === 'chunk') onChunk?.(parsed.text);
          else if (parsed.type === 'complete') onComplete?.(parsed.data);
          else if (parsed.type === 'error') onError?.(new ApiError(500, parsed.message, '/chat/stream'));
        } catch { /* partial JSON */ }
      }
    }
  } catch (err) {
    onError?.(err);
  }
}

// ------------------------------------------------------------------------------
// Audio
// ------------------------------------------------------------------------------

export async function transcribeAudio(audioBlob, languageHint = 'en') {
  const formData = new FormData();
  formData.append('audio', audioBlob, 'query.webm');
  formData.append('language_hint', languageHint);
  const res = await apiFetch('/audio/transcribe', { method: 'POST', body: formData });
  return res.json();
}

export async function synthesizeSpeech(text, language = 'en') {
  const res = await apiFetch('/audio/synthesize', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text, language }),
  });
  return res.blob();
}
