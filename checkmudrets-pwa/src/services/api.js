import { supabase } from './supabase';

const API_BASE = (import.meta.env.VITE_API_URL || 'http://localhost:8000').replace(/\/+$/, '');
const adviceKey = (userId) => `checkmudrets:last-advice:${userId}`;

export function getLastAdvice(userId) {
  return localStorage.getItem(adviceKey(userId)) || '';
}

async function getSession(expectedUser) {
  const { data, error } = await supabase.auth.getSession();
  if (error) throw error;
  if (!data.session || (expectedUser && data.session.user.id !== expectedUser)) {
    throw new Error('Сессия изменилась. Войди снова.');
  }
  return data.session;
}

async function request(path, options = {}, session) {
  const current = session ?? await getSession();
  const headers = new Headers(options.headers);
  headers.set('Authorization', `Bearer ${current.access_token}`);
  const response = await fetch(`${API_BASE}${path}`, { ...options, headers, cache: 'no-store' });
  if (!response.ok) {
    if (response.status === 401) {
      const { data } = await supabase.auth.getSession();
      if (data.session?.access_token === current.access_token) {
        await supabase.auth.signOut({ scope: 'local' });
      }
    }
    const error = new Error(`Ошибка сервера (${response.status})`);
    error.status = response.status;
    throw error;
  }
  return response.json();
}

export async function getMe(userId, signal) {
  return request('/auth/me', { signal }, await getSession(userId));
}

export async function recordConsents(userId, consents, signal) {
  return request('/auth/consents', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ consents }),
    signal,
  }, await getSession(userId));
}

export async function uploadReceipt(file) {
  const session = await getSession();
  const form = new FormData();
  form.append('file', file);
  const result = await request('/receipts', { method: 'POST', body: form }, session);
  if (result.success && result.mini_advice) {
    try {
      localStorage.setItem(adviceKey(session.user.id), result.mini_advice);
    } catch {
      // Чек уже сохранён на сервере, даже если кеш браузера недоступен.
    }
  }
  return result;
}

export function getReceipts(limit = 20, signal) {
  return request(`/receipts?limit=${limit}`, { signal });
}

export function getStats(month = '', signal) {
  return request(month ? `/stats?month=${encodeURIComponent(month)}` : '/stats', { signal });
}

export function getAdvice() {
  return request('/advice');
}

export function getReport(signal) {
  return request('/report', { signal });
}
